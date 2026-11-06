"""CPU strategy selection, provenance separation and optional-input checks."""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from participant.collection import codex_client
import test_plan_orchestration as orchestration


class OpeningFirstStrategyTest(unittest.TestCase):
    def test_selects_opening_check_and_hem_route_without_cuff_requirement(self):
        result = orchestration.PlanOrchestrationTest().run_client(orchestration.three_segment_plan(), mode='dressing',
                    strategy='coordinated-opening-first', review_points=50)
        prompt = result['calls'][0]['prompt']
        self.assertIn(codex_client.COORDINATED_TASK, prompt)
        self.assertIn(codex_client.HEM_ROUTE_TASK, prompt)
        self.assertIn(codex_client.OPENING_FIRST_TASK, prompt)
        self.assertNotIn(codex_client.SLEEVE_TASK, prompt)
        self.assertEqual(result['manifest']['strategy'], 'coordinated-opening-first')
        self.assertEqual(result['manifest']['actor_calls_attempted'], 1)
        self.assertEqual([r[0] for r in result['requests']], ['act', 'stop', 'finish_episode'])

    def test_replayed_current_input_does_not_implicitly_add_history_or_scores(self):
        for points, completed in [(5, 3), (10, 1)]:
            with self.subTest(points=points):
                result = orchestration.PlanOrchestrationTest().run_client(orchestration.three_segment_plan(), mode='dressing',
                    strategy='coordinated-opening-first', replay=True,
                    points_after_act=points, review_points=10)
                if points == 10:
                    # The trusted replay boundary itself can stop the run before actor creation.
                    self.assertEqual(result['calls'], [])
                    self.assertEqual(result['manifest']['actor_calls_attempted'], 0)
                else:
                    self.assertEqual(result['manifest']['decisions_completed'], completed)
                    self.assertEqual(result['calls'][0]['images'], ['synthetic-camera.png'])
                    self.assertNotIn('Image temporal context', result['calls'][0]['prompt'])
                self.assertNotIn('replay_visual_history', result['manifest'])
                for forbidden in ('TRUSTED_SCORE_STREAM_ONLY', 'raw_points', 'score_segments'):
                    self.assertNotIn(forbidden, json.dumps(result['calls']))

    def test_non_dressing_modes_reject_before_creating_output(self):
        for mode in ('wiring', 'pickup'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(codex_client.signal, 'signal'), \
                     mock.patch.object(codex_client, 'Simulator') as simulator, \
                     mock.patch.object(sys, 'argv', ['client', '--run-id', 'reject', '--mode', mode,
                         '--strategy', 'coordinated-opening-first']), \
                     mock.patch('sys.stderr'), self.assertRaises(SystemExit):
                    codex_client.main()
                simulator.assert_not_called()
                self.assertFalse((root / 'output').exists())

    def test_early264_configuration_keeps_depth_and_settling_optional(self):
        class SelectionProbeFinished(Exception):
            pass
        for settle, depth in [(0, False), (6, True)]:
            with self.subTest(settle=settle, depth=depth), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                argv = ['client', '--run-id', 'selection', '--mode', 'dressing',
                    '--strategy', 'coordinated-opening-first', '--plan-size', '1',
                    '--replay-prefix-run', 'synthetic-parent', '--replay-prefix-steps', '264',
                    '--post-action-settle-steps', str(settle)]
                if depth:
                    argv += ['--wrist-depth-panel']
                prefix = SimpleNamespace(actions=np.zeros((264, 2, 9), np.float32),
                    trusted_metadata={'reset_seed': 123},
                    public_lineage={'source_group': 'synthetic-family', 'replay_steps': 264})
                with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(codex_client.signal, 'signal'), \
                     mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                     mock.patch('participant.collection.continuation.load_replay_prefix', return_value=prefix), \
                     mock.patch.object(codex_client, 'Simulator', side_effect=SelectionProbeFinished), \
                     mock.patch.object(sys, 'argv', argv), self.assertRaises(SelectionProbeFinished):
                    codex_client.main()
                trace = root / 'output/operator-traces/selection'
                attempt = json.loads((trace / 'attempt.json').read_text())
                prompt = (trace / 'prompt.txt').read_text()
                self.assertEqual(attempt['continuation']['replay_steps'], 264)
                self.assertNotIn('replay_visual_history', attempt)
                self.assertEqual('post_action_settle' in attempt, bool(settle))
                self.assertEqual('wrist_depth_panel' in attempt, depth)
                self.assertIn(codex_client.OPENING_FIRST_TASK, prompt)
                self.assertNotIn('synthetic-family', prompt)
                self.assertNotIn('reset_seed', prompt)


if __name__ == '__main__':
    unittest.main()
