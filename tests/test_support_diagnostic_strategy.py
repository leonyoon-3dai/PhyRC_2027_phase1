"""CPU selection and public/trusted separation for sequential support checks.

These checks validate orchestration, not the model's adherence or cloth support.
"""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from participant.collection import codex_client


class SupportDiagnosticStrategyTest(unittest.TestCase):
    def prepare(self, *, strategy='coordinated-support-diagnostic', replay=True,
                settle=0, depth=False, review_points=10):
        class SelectionFinished(Exception):
            pass

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            argv = ['client', '--run-id', 'selection', '--mode', 'dressing',
                    '--strategy', strategy, '--plan-size', '1',
                    '--review-points', str(review_points),
                    '--post-action-settle-steps', str(settle)]
            if replay:
                argv += ['--replay-prefix-run', 'private-parent', '--replay-prefix-steps', '264']
            if depth:
                argv += ['--wrist-depth-panel']
            prefix = SimpleNamespace(actions=np.zeros((264, 2, 9), np.float32),
                trusted_metadata={'reset_seed': 892321},
                public_lineage={'source_group': 'private-source-family', 'replay_steps': 264})
            with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                 mock.patch.object(codex_client.signal, 'signal'), \
                 mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                 mock.patch('participant.collection.continuation.load_replay_prefix', return_value=prefix), \
                 mock.patch.object(codex_client, 'Simulator', side_effect=SelectionFinished) as simulator, \
                 mock.patch.object(sys, 'argv', argv), self.assertRaises(SelectionFinished):
                codex_client.main()
            trace = root / 'output/operator-traces/selection'
            return {'prompt': (trace / 'prompt.txt').read_text(),
                    'attempt': json.loads((trace / 'attempt.json').read_text()),
                    'command': simulator.call_args.args[0]}

    def test_support_diagnostic_is_selected_without_other_strategies(self):
        result = self.prepare()
        prompt = result['prompt']
        self.assertIn(codex_client.COORDINATED_TASK, prompt)
        self.assertIn(codex_client.HEM_ROUTE_TASK, prompt)
        self.assertIn(codex_client.SUPPORT_DIAGNOSTIC_TASK, prompt)
        self.assertNotIn(codex_client.OPENING_FIRST_TASK, prompt)
        self.assertNotIn(codex_client.SLEEVE_TASK, prompt)
        self.assertEqual(result['attempt']['strategy'], 'coordinated-support-diagnostic')
        self.assertEqual(result['attempt']['plan_execution'], 'single_decision')

    def test_trusted_seed_lineage_and_review_threshold_stay_out_of_prompt(self):
        low, high = self.prepare(review_points=10), self.prepare(review_points=50)
        self.assertEqual(low['prompt'], high['prompt'])
        self.assertEqual(low['attempt']['review_threshold_raw_points'], 10)
        self.assertEqual(high['attempt']['review_threshold_raw_points'], 50)
        self.assertEqual(low['attempt']['continuation']['replay_steps'], 264)
        self.assertIn('--reset-seed', low['command'])
        for forbidden in ('892321', 'private-source-family', 'private-parent',
                          'reset_seed', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])
        self.assertNotIn('replay_visual_history', low['attempt'])

    def test_optional_inputs_remain_optional_and_existing_strategy_is_unchanged(self):
        for settle, depth in [(0, False), (6, True)]:
            with self.subTest(settle=settle, depth=depth):
                result = self.prepare(replay=False, settle=settle, depth=depth)
                self.assertEqual('post_action_settle' in result['attempt'], bool(settle))
                self.assertEqual('wrist_depth_panel' in result['attempt'], depth)
                self.assertNotIn('continuation', result['attempt'])
        original = self.prepare(strategy='coordinated-opening-first', replay=False)
        self.assertIn(codex_client.OPENING_FIRST_TASK, original['prompt'])
        self.assertNotIn(codex_client.SUPPORT_DIAGNOSTIC_TASK, original['prompt'])

    def test_rejects_non_dressing_or_grouped_actions_before_output_or_simulator(self):
        for mode, size in [('wiring', 1), ('pickup', 1), ('dressing', 2), ('dressing', 3)]:
            with self.subTest(mode=mode, size=size), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                argv = ['client', '--run-id', 'reject', '--mode', mode,
                        '--strategy', 'coordinated-support-diagnostic', '--plan-size', str(size)]
                with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(codex_client.signal, 'signal'), \
                     mock.patch.object(codex_client, 'Simulator') as simulator, \
                     mock.patch.object(sys, 'argv', argv), mock.patch('sys.stderr'), \
                     self.assertRaises(SystemExit):
                    codex_client.main()
                simulator.assert_not_called()
                self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
