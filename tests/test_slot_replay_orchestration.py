"""CPU integration: exact prefix boundary and public HOLD before actor calls."""
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
from participant.collection import codex_client as client, codex_actor, user_review
from test_user_review import observation


class SlotReplayOrchestrationTest(unittest.TestCase):
    def test_replayed_slot_prefix_holds_at_110_before_actor_and_keeps_origin_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            run = 'slot-prefix-110'
            slot = '/output/checkpoints/source/slot_SOURCE.npz'
            actions = np.zeros((110, 2, 9), np.float32)
            actions[:63, 0, 3] = .025
            actions[63:, 1, 1] = -.035
            prefix = SimpleNamespace(actions=actions,
                trusted_metadata={'reset_seed': 123, 'initial_slot': {'path': slot}},
                public_lineage={'source_group': 'source-group', 'replay_steps': 110,
                    'replay_initialization': 'approximate_slot', 'bitwise_physics_restored': False},
                initial_public_state={'simulation_time_s': np.asarray(1.5)},
                final_public_state={'simulation_time_s': np.asarray(7.)})
            calls, applied, commands, holds = [], [], [], []
            collection = root / 'output/collections' / run
            class Simulator:
                def __init__(self, command, *args, **kwargs):
                    commands.append(command)
                    self.process = SimpleNamespace(pid=123, poll=lambda: None)
                    self.pending_request = None
                    self.observation_step = 0
                    self.obs = observation()
                    self.obs['simulation_time_s'] = np.asarray(1.5)
                    self.held = False
                def receive(self):
                    return {'ready': True, 'observation': self.obs,
                            'public_interface': {'action_scales': {'LIFT_RATE': 1.}}}
                def dispatch(self, tool, arguments=None):
                    calls.append((tool, arguments))
                    if tool == 'act':
                        self.observation_step += arguments['steps']
                        applied.extend([arguments['action']] * arguments['steps'])
                        self.obs['simulation_time_s'] = np.asarray(1.5 + self.observation_step / 20)
                    elif tool == 'hold':
                        self.held = True
                    elif tool == 'finish_episode':
                        collection.mkdir(parents=True)
                        (collection / 'capture.json').write_text(json.dumps({
                            'complete': True, 'steps': self.observation_step,
                            'termination_reason': 'operator_finished'}))
                        return {'active': False}
                    else:
                        raise AssertionError('Unexpected motion/control: ' + tool)
                    return {'active': True, 'held': self.held, 'observation': self.obs}
                def close(self):
                    return 0
            real_guided = user_review.run_guided
            actor = mock.Mock()
            def wait(private, meta, sim, seen, event, **kwargs):
                actor.invoke.assert_not_called()
                self.assertTrue(sim.held)
                self.assertEqual(sim.observation_step, 110)
                self.assertEqual(meta['observation_step'], 110)
                self.assertEqual(meta['source_checkpoint']['replay_steps'], 110)
                holds.append(meta)
                return {'action': 'finish', 'text': 'Explicit test close after reviewing restored boundary.'}
            def guided(**kwargs):
                return real_guided(**kwargs, wait=wait, score_reader=lambda _: 0)
            argv = ['client', '--run-id', run, '--mode', 'dressing', '--user-guided',
                    '--initial-slot', slot, '--replay-prefix-run', 'closed-parent',
                    '--replay-prefix-steps', '110', '--max-steps', '240']
            with mock.patch.object(client, '__file__', str(root / 'participant/collection/client.py')), \
                 mock.patch.object(client, 'Simulator', Simulator), \
                 mock.patch.object(client, 'source_snapshot', return_value={}), \
                 mock.patch.object(client.signal, 'signal'), \
                 mock.patch('participant.collection.continuation.load_replay_prefix', return_value=prefix) as loader, \
                 mock.patch('participant.collection.milestones.write_index'), \
                 mock.patch.object(codex_actor, 'Actor', return_value=actor), \
                 mock.patch.object(user_review, 'run_guided', side_effect=guided), \
                 mock.patch.object(sys, 'argv', argv), mock.patch('builtins.print'):
                client.main()
            loader.assert_called_once_with(root, 'closed-parent', 110, initial_slot=slot)
            actor.invoke.assert_not_called()
            np.testing.assert_array_equal(np.asarray(applied, dtype=np.float32), actions)
            self.assertEqual([x[0] for x in calls][-2:], ['hold', 'finish_episode'])
            self.assertEqual(len(holds), 1)
            self.assertEqual(holds[0]['reason'], 'start_state_review')
            self.assertIn(slot, commands[0])
            self.assertIn('--reset-seed', commands[0])
            manifest = json.loads((root / 'output/operator-traces' / run / 'attempt.json').read_text())
            self.assertEqual(manifest['replay_steps_completed'], 110)
            self.assertEqual(manifest['policy_suffix_start_step'], 110)
            self.assertEqual(manifest['new_recorded_suffix_steps'], 0)
            for boundary in ('initial', 'final'):
                comparison = manifest['continuation'][boundary + '_public_state_comparison']
                self.assertEqual(comparison['fields']['simulation_time_s']['max_absolute_difference'], 0)

    def test_old_slot_validation_cannot_skip_postreplay_review(self):
        argv = ['client', '--run-id', 'rejected-skip', '--mode', 'dressing', '--user-guided',
                '--initial-slot', '/output/slot_SOURCE.npz', '--replay-prefix-run', 'closed-parent',
                '--start-state-validation', '/unread-old-validation.json']
        with mock.patch.object(client.signal, 'signal'), mock.patch.object(sys, 'argv', argv), \
             mock.patch.object(sys, 'stderr', io.StringIO()), \
             mock.patch('participant.collection.continuation.load_replay_prefix') as loader:
            with self.assertRaises(SystemExit) as caught:
                client.main()
            self.assertEqual(caught.exception.code, 2)
            loader.assert_not_called()


if __name__ == '__main__':
    unittest.main()
