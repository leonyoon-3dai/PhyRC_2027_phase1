"""Public-payload and action rejection tests, independent of GPU or model access."""
import copy
import json
from pathlib import Path
import tempfile
import sys
import time
import unittest
from unittest import mock

import numpy as np
from PIL import Image
from participant.collection.boundary import CONTRACT
from participant.collection import codex_client
from participant.collection.codex_client import (Simulator, TokenUsageAccounting, prepare_observation,
                                                 public_interface, validate_decision)


def observation():
    dims = CONTRACT['default_dimensions']
    return {name: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
            for name, spec in CONTRACT['observations'].items()}


class CodexClientTest(unittest.TestCase):
    def test_transport_drains_after_invalid_initial_response(self):
        command = [sys.executable, '-c',
                   "import sys; print('native-not-json',flush=True); "
                   "[print('x'*1000,flush=True) for _ in range(10000)]; sys.stdin.read()"]
        with tempfile.TemporaryDirectory() as tmp, open(Path(tmp)/'log', 'w') as log:
            sim = Simulator(command, Path(tmp), log, timeout_s=5)
            with self.assertRaisesRegex(ValueError, 'non-JSON simulator output'):
                sim.receive()
            time.sleep(.1)
            started = time.monotonic()
            self.assertEqual(sim.close(), 0)
            self.assertLess(time.monotonic() - started, 5)

    def test_public_payload_ignores_privileged_fields_and_preserves_rgb(self):
        obs = observation()
        obs['rgb'][2, 12, 27] = [17, 222, 80]
        obs['depth'][0, :16, :16, 0] = 1.2345
        obs['depth_valid'][0, :16, :16, 0] = True
        obs.update(score=50, success=True, seed=54321, cloth_world_positions='do-not-copy')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'observation'
            payload, images = prepare_observation(obs, path)
            self.assertEqual(len(images), 5)
            text = json.dumps(payload)
            for secret in ('do-not-copy', '54321', '"success"', '"score"'):
                self.assertNotIn(secret, text)
            self.assertEqual(np.asarray(Image.open(images[2]))[12, 27].tolist(), [17, 222, 80])
            self.assertEqual(payload['depth_16x16_grid_m']['overview'][0][0], 1.235)
            self.assertIsNone(payload['depth_16x16_grid_m']['overview'][1][0])
            with np.load(path / 'public_depth.npz') as archive:
                self.assertEqual(set(archive.files), {'depth', 'depth_valid'})
            with self.assertRaises(FileExistsError):
                prepare_observation(obs, path)

    def test_invalid_public_sensor_data_fails_closed(self):
        for field in ('joint_position', 'depth'):
            obs = observation()
            obs[field].flat[0] = np.nan
            with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
                prepare_observation(obs, Path(tmp) / 'obs')

    def test_decision_validation_and_wiring_bounds(self):
        valid = dict(tool='act', action=[[0.0]*9, [0.0]*9], steps=2,
                     stage='preparation', visual_assessment='uncertain', reason='small lift')
        valid['action'][0][3] = .03
        self.assertEqual(validate_decision(valid, wiring=True).dtype, np.float32)
        invalid = []
        for key, value in [('steps', True), ('stage', '50_points'), ('tool', 'reset'),
                           ('score', 50), ('reason', ''), ('tool', 'finish_episode')]:
            item = copy.deepcopy(valid); item[key] = value; invalid.append(item)
        for value in (True, float('inf'), float('nan'), 1.001, '0'):
            item = copy.deepcopy(valid); item['action'][0][0] = value; invalid.append(item)
        for item in invalid:
            with self.subTest(item=item), self.assertRaises(ValueError):
                validate_decision(item)
        excessive = copy.deepcopy(valid); excessive['action'][0][3] = .1
        with self.assertRaises(ValueError):
            validate_decision(excessive, wiring=True)

    def test_static_metadata_allowlist(self):
        value = dict(action_scales={'LIFT_RATE': .2}, joint_names=['lift'], joint_units=['m'],
                     camera_intrinsics=[1, 2], camera_poses='dynamic-forbidden', human_spawn='forbidden',
                     episode_seed=99, evaluation={'success': True})
        result = public_interface(value)
        self.assertEqual(set(result), {'action_scales', 'joint_names', 'joint_units', 'camera_intrinsics'})


def usage_result(thread, input_tokens, cached=0, output=0, reasoning=0):
    return {'session_id': thread, 'usage': {
        'input_tokens': input_tokens, 'cached_input_tokens': cached,
        'cache_write_input_tokens': 0, 'output_tokens': output,
        'reasoning_output_tokens': reasoning}}


class TokenUsageAccountingTest(unittest.TestCase):
    def test_real_resumed_counter_pattern_is_not_summed(self):
        accounting = TokenUsageAccounting()
        snapshots = [(16858, 0, 151, 53), (41730, 16768, 238, 53), (74558, 41472, 330, 53)]
        records = [accounting.record(i, usage_result('private-thread', *row))
                   for i, row in enumerate(snapshots)]
        self.assertEqual(accounting.totals['input_tokens'], 74558)
        self.assertEqual(accounting.totals['output_tokens'], 330)
        self.assertEqual([r['incremental_usage']['input_tokens'] for r in records], [16858, 24872, 32828])
        self.assertEqual([r['incremental_usage']['reasoning_output_tokens'] for r in records], [53, 0, 0])
        self.assertTrue(accounting.summary()['fully_known'])

    def test_duplicate_and_interleaved_threads_keep_separate_baselines(self):
        accounting = TokenUsageAccounting()
        accounting.record(0, usage_result('thread-a', 100, 20, 10))
        repeated = accounting.record(1, usage_result('thread-a', 100, 20, 10))
        self.assertEqual(repeated['status'], 'duplicate_snapshot')
        self.assertTrue(all(v == 0 for v in repeated['incremental_usage'].values()))
        new = accounting.record(2, usage_result('thread-b', 40, 0, 4))
        self.assertEqual(new['incremental_usage']['input_tokens'], 40)
        resumed = accounting.record(3, usage_result('thread-a', 160, 50, 15))
        self.assertEqual(resumed['incremental_usage']['input_tokens'], 60)
        self.assertEqual(accounting.totals['input_tokens'], 200)
        self.assertEqual([t['thread_index'] for t in accounting.summary()['threads']], [0, 1])
        with self.assertRaisesRegex(ValueError, 'already recorded'):
            accounting.record(3, usage_result('thread-a', 160, 50, 15))
        self.assertEqual(accounting.totals['input_tokens'], 200)

    def test_regression_is_unknown_and_does_not_reset_the_baseline(self):
        accounting = TokenUsageAccounting()
        accounting.record(0, usage_result('a', 100, 50, 10))
        bad = accounting.record(1, usage_result('a', 90, 40, 12))
        self.assertEqual(bad['status'], 'counter_regressed')
        self.assertIsNone(bad['incremental_usage'])
        self.assertEqual(accounting.totals['input_tokens'], 100)
        recovered = accounting.record(2, usage_result('a', 140, 60, 20))
        self.assertEqual(recovered['incremental_usage']['input_tokens'], 40)
        self.assertEqual(accounting.totals['output_tokens'], 20)
        self.assertFalse(accounting.summary()['fully_known'])
        self.assertEqual(accounting.summary()['unknown_call_indices'], [1])

    def test_missing_failed_usage_is_not_zero_but_returned_failed_usage_counts(self):
        accounting = TokenUsageAccounting()
        missing = accounting.record(0, None, call_failed=True)
        self.assertIsNone(missing['cumulative_usage'])
        self.assertIsNone(missing['incremental_usage'])
        self.assertEqual(accounting.totals, {})
        returned = accounting.record(1, usage_result('a', 100, output=10), call_failed=True)
        self.assertTrue(returned['call_failed'])
        self.assertTrue(returned['usage_known'])
        self.assertEqual(accounting.totals['input_tokens'], 100)
        self.assertFalse(accounting.summary()['fully_known'])

    def test_bad_counters_are_unknown_and_unrelated_metadata_is_excluded(self):
        cases = [usage_result('a', True), usage_result('a', -1), usage_result('a', 2, cached=3),
                 usage_result('a', 2, output=1, reasoning=2), {'session_id': 'a', 'usage': {}},
                 {'usage': usage_result('a', 10)['usage']}]
        for case in cases:
            with self.subTest(case=case):
                accounting = TokenUsageAccounting()
                record = accounting.record(0, case)
                self.assertFalse(record['usage_known'])
                self.assertEqual(accounting.totals, {})
        accounting = TokenUsageAccounting()
        result = usage_result('PRIVATE_SESSION_SENTINEL', 100, output=10)
        result['hidden_reasoning'] = 'PRIVATE_REASONING_SENTINEL'
        accounting.record(0, result)
        snapshot = accounting.summary()
        accounting.record(1, usage_result('PRIVATE_SESSION_SENTINEL', 200, output=20))
        self.assertEqual(snapshot['observed_usage']['input_tokens'], 100)
        self.assertNotIn('PRIVATE_', json.dumps(snapshot))

    def run_client(self, failure=None):
        """Exercise the real manifest/event paths with CPU-only boundary fakes."""
        from participant.collection import codex_actor
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / 'camera.png'
            image.write_bytes(b'public-image-fixture')
            class FakeSimulator:
                def __init__(self, *args, **kwargs):
                    self.process = mock.Mock(pid=123)
                    self.process.poll.return_value = None
                    self.step = 0
                def receive(self):
                    return {'ready': True, 'observation': {'simulation_time_s': 0.0}}
                def dispatch(self, tool, arguments=None):
                    self.step += int(tool == 'stop')
                    return {'active': True, 'observation': {'simulation_time_s': self.step / 20}}
                def close(self):
                    return 0
            class FakeActor:
                last_call_timing = {'process_wall_s': 0.25, 'completed': False}
                def __init__(self, *args, **kwargs):
                    pass
                def invoke(self, *args):
                    if failure == 'interrupted':
                        raise KeyboardInterrupt('SIGTERM')
                    value = usage_result('PRIVATE_SESSION_SENTINEL', 100, output=10)
                    value.update(wall_s=0.25, decision={
                        'tool': 'invalid' if failure == 'decision' else 'finish_episode',
                        'action': [[0.0]*9, [0.0]*9], 'steps': 1, 'stage': 'preparation',
                        'visual_assessment': 'uncertain', 'reason': 'test'})
                    return value
                def close(self):
                    pass
            with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/codex_client.py')), \
                 mock.patch.object(codex_client, 'Simulator', FakeSimulator), \
                 mock.patch.object(codex_actor, 'Actor', FakeActor), \
                 mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                 mock.patch.object(codex_client, 'prepare_observation', return_value=({}, [image])), \
                 mock.patch.object(codex_client.signal, 'signal'), \
                 mock.patch.object(sys, 'argv', ['codex_client', '--run-id', 'cpu-test', '--decisions', '1']), \
                 mock.patch('builtins.print'):
                if failure:
                    with self.assertRaises(KeyboardInterrupt if failure == 'interrupted' else ValueError):
                        codex_client.main()
                else:
                    codex_client.main()
            trace = root / 'output/operator-traces/cpu-test'
            return (json.loads((trace/'attempt.json').read_text()),
                    [json.loads(line) for line in (trace/'decisions.jsonl').read_text().splitlines()])

    def test_client_records_success_original_counters_and_accounting_scope(self):
        manifest, events = self.run_client()
        self.assertEqual(manifest['actor_usage']['input_tokens'], 100)
        self.assertTrue(manifest['actor_usage_accounting']['fully_known'])
        decision = next(e for e in events if e['type'] == 'decision')
        self.assertEqual(decision['usage']['input_tokens'], 100)
        self.assertEqual(decision['usage_scope'], 'thread_cumulative')
        self.assertEqual(decision['usage_accounting']['incremental_usage']['input_tokens'], 100)

    def test_client_records_interrupted_usage_as_unknown_and_preserves_timing(self):
        manifest, events = self.run_client('interrupted')
        self.assertEqual(manifest['status'], 'interrupted')
        self.assertEqual(manifest['actor_usage'], {})
        self.assertFalse(manifest['actor_usage_accounting']['fully_known'])
        error = next(e for e in events if e['type'] == 'model_error')
        self.assertIsNone(error['usage_accounting']['incremental_usage'])
        self.assertEqual(error['actor_call_timing']['process_wall_s'], 0.25)

    def test_client_counts_paid_usage_even_when_returned_decision_is_rejected(self):
        manifest, events = self.run_client('decision')
        self.assertEqual(manifest['status'], 'failed')
        self.assertEqual(manifest['actor_usage']['input_tokens'], 100)
        self.assertTrue(manifest['actor_usage_accounting']['fully_known'])
        error = next(e for e in events if e['type'] == 'model_error')
        self.assertTrue(error['usage_accounting']['call_failed'])
        self.assertTrue(error['usage_accounting']['usage_known'])


if __name__ == '__main__':
    unittest.main()
