"""CPU prompt routing, provenance and observation cadence for regrasp options.

No test here claims that a model regrasped cloth or improved dressing scores.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from participant.collection import codex_client
import test_support_diagnostic_strategy as diagnostic


class RegraspStrategiesTest(unittest.TestCase):
    def prepare(self, **kwargs):
        return diagnostic.SupportDiagnosticStrategyTest().prepare(**kwargs)

    def test_each_new_strategy_selects_only_its_own_method_and_common_analysis(self):
        pairs = [('coordinated-regrasp-hem', codex_client.REGRASP_HEM_TASK,
                  codex_client.SUPPORT_GUIDE_TASK),
                 ('coordinated-support-guide', codex_client.SUPPORT_GUIDE_TASK,
                  codex_client.REGRASP_HEM_TASK)]
        for strategy, selected, other in pairs:
            with self.subTest(strategy=strategy):
                result = self.prepare(strategy=strategy, replay=False)
                expected = '\n\n'.join([codex_client.TASK, codex_client.COORDINATED_TASK,
                    codex_client.HEM_ROUTE_TASK, selected, codex_client.METHOD_SATURATION_TASK])
                self.assertEqual(result['prompt'], expected)
                self.assertNotIn(other, result['prompt'])
                self.assertEqual(result['attempt']['strategy'], strategy)
                self.assertEqual(result['attempt']['plan_execution'], 'single_decision')
                self.assertEqual(result['attempt']['prompt_sha256'],
                                 hashlib.sha256(expected.encode()).hexdigest())

    def test_all_existing_strategy_prompts_remain_exactly_the_same(self):
        strategy_suffixes = {
            'general': [],
            'coordinated': [codex_client.COORDINATED_TASK],
            'coordinated-sleeve': [codex_client.COORDINATED_TASK, codex_client.SLEEVE_TASK],
            'coordinated-hem-route': [codex_client.COORDINATED_TASK, codex_client.HEM_ROUTE_TASK],
            'coordinated-opening-first': [codex_client.COORDINATED_TASK,
                codex_client.HEM_ROUTE_TASK, codex_client.OPENING_FIRST_TASK],
            'coordinated-support-diagnostic': [codex_client.COORDINATED_TASK,
                codex_client.HEM_ROUTE_TASK, codex_client.SUPPORT_DIAGNOSTIC_TASK],
        }
        for strategy, suffix in strategy_suffixes.items():
            with self.subTest(strategy=strategy):
                result = self.prepare(strategy=strategy, replay=False)
                self.assertEqual(result['prompt'], '\n\n'.join([codex_client.TASK, *suffix]))

    def test_replay_configuration_and_review_results_remain_outside_actor_prompt(self):
        for strategy in ('coordinated-regrasp-hem', 'coordinated-support-guide'):
            with self.subTest(strategy=strategy):
                low = self.prepare(strategy=strategy, review_points=10, settle=6, depth=True)
                high = self.prepare(strategy=strategy, review_points=50, settle=6, depth=True)
                self.assertEqual(low['prompt'], high['prompt'])
                self.assertEqual(low['attempt']['review_threshold_raw_points'], 10)
                self.assertEqual(high['attempt']['review_threshold_raw_points'], 50)
                self.assertEqual(low['attempt']['continuation']['replay_steps'], 264)
                self.assertIn('--reset-seed', low['command'])
                self.assertIn('post_action_settle', low['attempt'])
                self.assertIn('wrist_depth_panel', low['attempt'])
                for forbidden in ('892321', 'private-parent', 'private-source-family',
                                  'reset_seed', 'raw_points', 'score_segments'):
                    self.assertNotIn(forbidden, low['prompt'])

    def test_rejects_other_modes_and_open_loop_plans_before_starting(self):
        for strategy in ('coordinated-regrasp-hem', 'coordinated-support-guide'):
            for mode, size in [('wiring', 1), ('pickup', 1), ('dressing', 2), ('dressing', 3)]:
                with self.subTest(strategy=strategy, mode=mode, size=size), \
                     tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    argv = ['client', '--run-id', 'reject', '--mode', mode,
                            '--strategy', strategy, '--plan-size', str(size)]
                    with mock.patch.object(codex_client, '__file__',
                                           str(root / 'participant/collection/client.py')), \
                         mock.patch.object(codex_client.signal, 'signal'), \
                         mock.patch.object(codex_client, 'Simulator') as simulator, \
                         mock.patch.object(sys, 'argv', argv), mock.patch('sys.stderr'), \
                         self.assertRaises(SystemExit):
                        codex_client.main()
                    simulator.assert_not_called()
                    self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
