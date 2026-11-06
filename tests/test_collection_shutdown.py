"""Real SIGTERM/pipe/recorder regression with CPU synthetic sensor data.

Uses the production orchestrator, JSON protocol, Operator and HDF5 writer. Only
the physics environment and restored parent input are synthetic; no actor runs.
"""
import json
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import h5py
import numpy as np

from participant.collection import codex_actor, codex_client
from participant.collection.validate_capture import validate_capture


COLLECTOR = '''
import os, signal, sys, time
from types import ModuleType
sys.path.insert(0, 'tests')
from test_collection_runtime import Env, collector

class InterruptedEnv(Env):
    def __init__(self, **kwargs):
        super().__init__()
        self.sent = False
    def step(self, action):
        if not self.sent:
            self.sent = True
            os.kill(os.getppid(), signal.SIGTERM)
            time.sleep(.05)  # The parent is awaiting this action's ACK.
        return super().step(action)
    def close(self):
        pass

module = ModuleType('Policy.environment')
module.DressingEnv = InterruptedEnv
sys.modules['Policy.environment'] = module
sys.argv = ['collect_operator', '--output', sys.argv[1],
            '--source', 'integration_test', '--source-group', 'cpu-shutdown',
            '--model-id', 'none', '--prompt', 'Synthetic shutdown regression.',
            '--max-steps', '40']
raise SystemExit(collector.main())
'''


class CollectionShutdownTest(unittest.TestCase):
    def test_sigterm_during_settle_ack_preserves_real_recorded_boundaries(self):
        repository = Path(__file__).resolve().parents[1]
        transport = codex_client.Simulator
        previous_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
        # The first model act lasts two steps; interrupt inside the following neutral act.
        collector = COLLECTOR.replace('if not self.sent:', 'if self.t >= .1 and not self.sent:')
        collector = collector.replace('super().__init__()',
            'super().__init__()\n        self.contract["default_dimensions"].update(height=256, width=256)')
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = 'cpu-settle-shutdown'
            collection = root / 'output/collections' / run_id

            class CPUSimulator(transport):
                def __init__(self, command, root, log):
                    super().__init__([sys.executable, '-c', collector, str(collection)],
                                     repository, log, timeout_s=15)

            action = np.zeros((2, 9), np.float32)
            action[:, 3], action[:, 8] = .03, 1
            result = {'decision': {'tool': 'act', 'action': action.tolist(), 'steps': 2,
                                  'stage': 'preparation', 'visual_assessment': 'uncertain',
                                  'reason': 'CPU synthetic movement before neutral wait.'},
                      'wall_s': .01, 'usage': {}, 'session_id': 'test'}
            argv = ['client', '--run-id', run_id, '--mode', 'dressing',
                    '--post-action-settle-steps', '6', '--max-steps', '40']
            try:
                with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(codex_client, 'Simulator', CPUSimulator), \
                     mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                     mock.patch.object(codex_client, 'official_review_points', return_value=0), \
                     mock.patch('participant.collection.milestones.write_index'), \
                     mock.patch.object(codex_actor, 'Actor') as actor, \
                     mock.patch.object(sys, 'argv', argv), mock.patch('builtins.print'):
                    actor.return_value.invoke.return_value = result
                    with self.assertRaisesRegex(KeyboardInterrupt, 'SIGTERM'):
                        codex_client.main()
                    actor.return_value.invoke.assert_called_once()
            finally:
                for sig, handler in previous_handlers.items():
                    signal.signal(sig, handler)

            trace = root / 'output/operator-traces' / run_id
            attempt = json.loads((trace / 'attempt.json').read_text())
            self.assertEqual(attempt['status'], 'interrupted')
            self.assertTrue(attempt['finished'])
            self.assertTrue(attempt['capture_complete'])
            self.assertNotIn('shutdown_error', attempt)
            self.assertEqual(attempt['post_action_settle']['simulation_steps'], 6)
            self.assertEqual(attempt['acknowledged_simulation_steps'], 9)
            self.assertEqual(attempt['recorded_simulation_steps'], 9)
            protocol = [json.loads(line) for line in (collection / 'operator.jsonl').read_text().splitlines()]
            accepted = [event['request'] for event in protocol if event['event'] == 'request_accepted']
            self.assertEqual([r['tool'] for r in accepted], ['act', 'act', 'stop', 'finish_episode'])
            self.assertEqual([r['observation_step'] for r in accepted], [0, 2, 8, 9])
            self.assertEqual(len({r['request_id'] for r in accepted}), 4)
            with h5py.File(collection / 'policy.hdf5') as stream:
                recorded = stream['data/demo_0/actions'][:].reshape(-1, 2, 9)
                np.testing.assert_array_equal(recorded[:2], np.repeat(action[None], 2, axis=0))
                np.testing.assert_array_equal(recorded[2:], np.zeros((7, 2, 9), np.float32))
            report = validate_capture(collection)
            self.assertTrue(report['quality_passed'], report)
            self.assertEqual(report['validated_transitions'], 9)

    def test_sigterm_while_waiting_for_replay_ack_finishes_real_files(self):
        repository = Path(__file__).resolve().parents[1]
        transport = codex_client.Simulator
        previous_handlers = {sig: signal.getsignal(sig) for sig in
                             (signal.SIGTERM, signal.SIGINT)}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = 'cpu-shutdown'
            collection = root / 'output/collections' / run_id
            class CPUSimulator(transport):
                def __init__(self, command, root, log):
                    super().__init__([sys.executable, '-c', COLLECTOR, str(collection)],
                                     repository, log, timeout_s=15)

            prefix = SimpleNamespace(
                actions=np.zeros((20, 2, 9), dtype=np.float32),
                trusted_metadata={'reset_seed': 1},
                public_lineage={'source_group': 'cpu-shutdown', 'resume_kind': 'action_replay',
                                'replay_steps': 20, 'bitwise_physics_restored': False},
                initial_public_state={'simulation_time_s': np.asarray(0.)},
                final_public_state={'simulation_time_s': np.asarray(1.)},
            )
            argv = ['codex_client', '--run-id', run_id, '--mode', 'dressing',
                    '--replay-prefix-run', 'synthetic-parent', '--max-steps', '40']
            try:
                with mock.patch.object(codex_client, '__file__',
                                       str(root / 'participant/collection/codex_client.py')), \
                     mock.patch.object(codex_client, 'Simulator', CPUSimulator), \
                     mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                     mock.patch('participant.collection.continuation.load_replay_prefix',
                                return_value=prefix), \
                     mock.patch.object(codex_actor, 'Actor') as actor, \
                     mock.patch.object(sys, 'argv', argv):
                    with self.assertRaisesRegex(KeyboardInterrupt, 'SIGTERM'):
                        codex_client.main()
                    actor.assert_not_called()
            finally:
                for sig, handler in previous_handlers.items():
                    signal.signal(sig, handler)

            trace = root / 'output/operator-traces' / run_id
            attempt = json.loads((trace / 'attempt.json').read_text())
            self.assertEqual(attempt['status'], 'interrupted')
            self.assertTrue(attempt['finished'])
            self.assertTrue(attempt['capture_complete'])
            self.assertNotIn('shutdown_error', attempt)
            self.assertEqual(attempt['simulator_returncode'], 0)
            self.assertEqual(attempt['actor_calls_attempted'], 0)
            self.assertEqual(attempt['replay_steps_completed'], 20)
            self.assertEqual(attempt['acknowledged_simulation_steps'], 21)
            self.assertEqual(attempt['recorded_simulation_steps'], 21)
            protocol = [json.loads(line) for line in
                        (collection / 'operator.jsonl').read_text().splitlines()]
            accepted = [e['request'] for e in protocol if e['event'] == 'request_accepted']
            self.assertEqual([r['tool'] for r in accepted], ['act', 'stop', 'finish_episode'])
            self.assertEqual([r['observation_step'] for r in accepted], [0, 20, 21])
            report = validate_capture(collection)
            self.assertTrue(report['quality_passed'], report)
            self.assertEqual(report['validated_transitions'], 21)


if __name__ == '__main__':
    unittest.main()
