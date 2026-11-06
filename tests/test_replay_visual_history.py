"""CPU replay history tests: new observations, temporal labels and input isolation."""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
from PIL import Image

from participant.collection import codex_actor, codex_client
from participant.collection.boundary import CONTRACT


def observation(step):
    dims = CONTRACT['default_dimensions']
    obs = {k: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
           for k, spec in CONTRACT['observations'].items()}
    obs['simulation_time_s'] = np.asarray(2.5 + step / 20, np.float64)
    obs['joint_position'].fill(step)
    for camera in range(5):
        obs['rgb'][camera] = [step % 256, step // 256, camera]
    # These are forbidden even if a buggy transport includes extra metadata.
    obs.update(seed=912345678, evaluation='PRIVATE_EVALUATION_CANARY',
               lineage='PRIVATE_LINEAGE_CANARY')
    return obs


class ReplayVisualHistoryTest(unittest.TestCase):
    def run_client(self, boundaries):
        calls, requests = [], []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trace = root / 'output/operator-traces/history-test'
            collection = root / 'output/collections/history-test'
            class Simulator:
                def __init__(self, *args, **kwargs):
                    self.process = mock.Mock(pid=123)
                    self.process.poll.return_value = None
                    self.step = 0
                    score_dir = collection / 'evaluation/synthetic'
                    score_dir.mkdir(parents=True)
                    (score_dir / 'score_samples.jsonl').write_text(json.dumps({
                        'raw_points': 5, 'private': 'PRIVATE_SCORE_CANARY'}) + '\n')
                def receive(self):
                    return {'ready': True, 'observation': observation(0),
                            'public_interface': {'evaluation': 'PRIVATE_STATIC_CANARY'}}
                def dispatch(self, tool, arguments=None):
                    requests.append((self.step, tool, deepcopy(arguments)))
                    if tool == 'finish_episode':
                        (collection / 'capture.json').write_text(json.dumps({
                            'complete': True, 'steps': self.step,
                            'termination_reason': 'operator_finished'}))
                        return {'active': False}
                    self.step += arguments['steps'] if tool == 'act' else 1
                    return {'active': True, 'observation': observation(self.step)}
                def close(self):
                    return 0
            class Actor:
                def __init__(self, *args, **kwargs):
                    pass
                def invoke(self, prompt, images, schema):
                    calls.append({
                        'prompt': prompt, 'images': [str(p.relative_to(root)) for p in images],
                        'hashes': [hashlib.sha256(p.read_bytes()).hexdigest() for p in images],
                        'pixels': [Image.open(p).getpixel((0, 0)) for p in images],
                    })
                    return {'wall_s': .25, 'session_id': 'synthetic',
                            'usage': {'input_tokens': len(calls) * 100, 'output_tokens': len(calls) * 10},
                            'decision': {'tool': 'act' if len(calls) == 1 else 'finish_episode',
                                         'action': [[0.] * 9 for _ in range(2)], 'steps': 1,
                                         'stage': 'first_sleeve', 'visual_assessment': 'uncertain',
                                         'reason': 'Synthetic temporal input test.'}}
                def close(self):
                    pass
            prefix = SimpleNamespace(
                actions=np.zeros((700, 2, 9), np.float32),
                trusted_metadata={'reset_seed': 912345678, 'private': 'PRIVATE_TRUSTED_CANARY'},
                public_lineage={'source_group': 'PRIVATE_LINEAGE_CANARY', 'replay_steps': 700},
                initial_public_state={'simulation_time_s': np.asarray(2.5)},
                final_public_state={'simulation_time_s': np.asarray(37.5)},
            )
            argv = ['client', '--run-id', 'history-test', '--mode', 'dressing',
                    '--strategy', 'coordinated-sleeve', '--replay-prefix-run', 'synthetic-parent',
                    '--replay-prefix-steps', '700', '--max-steps', '720', '--decisions', '2',
                    '--review-points', '10']
            if boundaries is not None:
                argv += ['--replay-observe-steps', *map(str, boundaries)]
            with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                 mock.patch.object(codex_client, 'Simulator', Simulator), \
                 mock.patch.object(codex_actor, 'Actor', Actor), \
                 mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                 mock.patch('participant.collection.continuation.load_replay_prefix', return_value=prefix), \
                 mock.patch('participant.collection.milestones.write_index'), \
                 mock.patch.object(codex_client.signal, 'signal'), \
                 mock.patch.object(sys, 'argv', argv), mock.patch('builtins.print'):
                codex_client.main()
            attempt = json.loads((trace / 'attempt.json').read_text())
            current_payload = json.loads((root / 'output/actors/history-test/observations/00000/observation.json').read_text())
            captured = []
            if boundaries:
                for boundary in boundaries:
                    directory = trace / 'replay_observations' / f'{boundary:05d}'
                    with np.load(directory / 'public_depth.npz') as archive:
                        self.assertEqual(archive['depth'].shape, (5, 256, 256, 1))
                    captured.append(json.loads((directory / 'observation.json').read_text()))
                for entry in attempt['replay_visual_history']['captured']:
                    for record in entry['files']:
                        self.assertEqual(hashlib.sha256((trace / record['relative_file']).read_bytes()).hexdigest(),
                                         record['sha256'])
            return attempt, calls, requests, current_payload, captured

    def test_exact_new_episode_frames_current_first_history_only_first_call(self):
        attempt, calls, requests, current, captured = self.run_client([264, 320])
        self.assertEqual([len(call['images']) for call in calls], [15, 5])
        self.assertTrue(all(len(call['images']) <= 16 for call in calls))
        expected = [(step % 256, step // 256, camera)
                    for step in (700, 264, 320) for camera in range(5)]
        self.assertEqual(calls[0]['pixels'], expected)
        self.assertEqual(calls[1]['pixels'], [(701 % 256, 701 // 256, camera) for camera in range(5)])
        for boundary, payload in zip((264, 320), captured):
            self.assertEqual(payload['public_robot_observation']['joint_position'][0][0], boundary)
        first = attempt['replay_visual_history']['first_model_input']
        groups = first['image_context']['groups']
        self.assertEqual(first['image_context']['schema'], codex_client.REPLAY_IMAGE_SCHEMA)
        self.assertEqual([g['kind'] for g in groups], ['current', 'historical_same_episode', 'historical_same_episode'])
        self.assertEqual([g['image_indices'] for g in groups], [list(range(5)), list(range(5, 10)), list(range(10, 15))])
        self.assertEqual([g.get('replay_boundary') for g in groups], [None, 264, 320])
        self.assertEqual([g['simulation_time_s'] for g in groups], [37.5, 15.7, 18.5])
        for group in groups:
            self.assertEqual(group['camera_order'], CONTRACT['competition_access']['allowed_cameras'])
            self.assertFalse(set(group) - {'kind', 'image_indices', 'camera_order', 'replay_boundary', 'simulation_time_s'})
        # The payload sent beside the extra labels retains only CURRENT state and depth.
        pos = calls[0]['prompt'].index('{"public_robot_observation"')
        payload, _ = json.JSONDecoder().raw_decode(calls[0]['prompt'][pos:])
        self.assertEqual(payload, current)
        self.assertEqual(payload['public_robot_observation']['joint_position'][0][0], 700)
        for call in calls:
            for secret in ('PRIVATE_', '912345678', 'synthetic-parent', 'raw_points', 'source_group'):
                self.assertNotIn(secret, call['prompt'])
        self.assertNotIn(codex_client.REPLAY_IMAGE_SCHEMA, calls[1]['prompt'])
        self.assertEqual([record['relative_file'] for record in first['ordered_images']], calls[0]['images'])
        self.assertEqual([record['sha256'] for record in first['ordered_images']], calls[0]['hashes'])
        expected_hash = hashlib.sha256((calls[0]['prompt'] + json.dumps(calls[0]['hashes'])).encode()).hexdigest()
        self.assertEqual(first['input_sha256'], expected_hash)
        replay_requests = [(start, args['steps']) for start, tool, args in requests
                           if tool == 'act' and start < 700]
        self.assertEqual(sum(steps for _, steps in replay_requests), 700)
        self.assertTrue({264, 320}.issubset({start + steps for start, steps in replay_requests}))

    def test_one_history_group_and_no_flag_baseline(self):
        attempt, calls, _, _, _ = self.run_client([264])
        self.assertEqual([len(c['images']) for c in calls], [10, 5])
        self.assertEqual(attempt['replay_visual_history']['requested_boundaries'], [264])
        attempt, calls, _, _, _ = self.run_client(None)
        self.assertEqual([len(c['images']) for c in calls], [5, 5])
        self.assertNotIn('replay_visual_history', attempt)
        self.assertNotIn(codex_client.REPLAY_IMAGE_TASK, calls[0]['prompt'])
        self.assertEqual(attempt['input_profile'], 'five_public_RGB_images_all_public_state_and_16x16_depth_medians')

    def test_invalid_flags_rejected_before_files_simulator_or_model(self):
        cases = [([], ['1']), (['--replay-prefix-run', 'parent'], []),
                 (['--replay-prefix-run', 'parent'], ['0']),
                 (['--replay-prefix-run', 'parent'], ['1', '1']),
                 (['--replay-prefix-run', 'parent'], ['2', '1']),
                 (['--replay-prefix-run', 'parent'], ['1', '2', '3']),
                 (['--replay-prefix-run', 'parent'], ['true']),
                 (['--replay-prefix-run', 'parent', '--replay-prefix-steps', '10'], ['10']),
                 (['--replay-prefix-run', 'parent'], ['700'])]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for replay_flags, cuts in cases:
                argv = ['client', '--run-id', 'invalid', '--mode', 'dressing', *replay_flags,
                        '--replay-observe-steps', *cuts]
                with self.subTest(argv=argv), \
                     mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(codex_client, 'Simulator') as simulator, \
                     mock.patch.object(codex_actor, 'Actor') as actor, \
                     mock.patch('participant.collection.continuation.load_replay_prefix',
                                return_value=SimpleNamespace(actions=np.zeros((700, 2, 9)))) as loader, \
                     mock.patch.object(codex_client.signal, 'signal'), \
                     mock.patch.object(sys, 'argv', argv), mock.patch.object(sys, 'stderr', io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        codex_client.main()
                    self.assertEqual(error.exception.code, 2)
                    simulator.assert_not_called()
                    actor.assert_not_called()
                    if cuts != ['700']:
                        loader.assert_not_called()
                    self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
