"""Same-arm goal sequencing is prompt-only; fake actor/simulator, no performance claim."""
import ast
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest import mock

import numpy as np

from participant.collection import codex_client as client, named_actions as named
import test_depth_query as query
import test_support_diagnostic_strategy as diagnostic
from test_overhead_strategy import encode


ROOT = Path(__file__).resolve().parents[1]
BASE = '18f307dcadd7a323debb7fd26e99f6da6d4cc045'
BASE_SOURCE = subprocess.check_output(
    ['git', 'show', BASE + ':participant/collection/codex_client.py'], cwd=ROOT, text=True)
baseline = ModuleType('single_arm_progress_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(BASE_SOURCE, baseline.__file__, 'exec'), baseline.__dict__)
STRATEGY = 'coordinated-single-arm-progress'
OLD_STRATEGIES = ('general', 'coordinated', 'coordinated-sleeve', 'coordinated-hem-route',
    'coordinated-opening-first', 'coordinated-support-diagnostic', 'coordinated-regrasp-hem',
    'coordinated-support-guide', 'coordinated-neckline-first', 'coordinated-overhead-drape',
    'coordinated-entry-probe', 'coordinated-task-progress', 'coordinated-opposing-rim',
    'coordinated-leading-hand-swap')


class SingleArmProgressStrategyTest(unittest.TestCase):
    def prepare(self, **kwargs):
        return diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, **kwargs)

    def test_selection_adds_only_goal_continuity_to_existing_task_progress(self):
        result = self.prepare(replay=False)
        prompt = result['prompt']
        self.assertEqual(prompt, '\n\n'.join([baseline.TASK, baseline.COORDINATED_TASK,
            baseline.TASK_PROGRESS_TASK, client.SINGLE_ARM_PROGRESS_TASK,
            baseline.METHOD_SATURATION_TASK]))
        for competing in (client.SLEEVE_TASK, client.HEM_ROUTE_TASK, client.OVERHEAD_TASK,
                          client.NECKLINE_TASK, client.OPENING_FIRST_TASK,
                          client.REGRASP_HEM_TASK, client.SUPPORT_GUIDE_TASK,
                          client.SUPPORT_DIAGNOSTIC_TASK, client.ENTRY_PROBE_TASK,
                          client.OPPOSING_RIM_TASK, client.LEADING_HAND_SWAP_TASK):
            self.assertNotIn(competing, prompt)
        self.assertEqual(result['attempt']['strategy'], STRATEGY)
        self.assertEqual(result['attempt']['plan_execution'], 'single_decision')
        self.assertEqual(result['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())

    def test_old_constants_and_nonrouting_functions_match_fixed_public_source(self):
        def nodes(source):
            result = {}
            for node in ast.parse(source).body:
                if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                    result[node.name] = ast.dump(node)
                elif isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            result[target.id] = ast.dump(node)
            return result
        old, current = nodes(BASE_SOURCE), nodes(Path(client.__file__).read_text())
        self.assertEqual(set(current) - set(old), {'SINGLE_ARM_PROGRESS_TASK', 'SIDE_HEM_WRISTS_TASK'})
        for name, node in old.items():
            if name != 'main':
                with self.subTest(name=name):
                    self.assertEqual(current[name], node)

    def test_fourteen_old_routes_keep_prompt_schema_images_and_dispatch_in_56_configs(self):
        for strategy in OLD_STRATEGIES:
            for enabled in (False, True):
                for use_names in (False, True):
                    with self.subTest(strategy=strategy, query=enabled, named=use_names):
                        flags = dict(enabled=enabled, strategy=strategy, history=True, depth_panel=True,
                            extra_flags=['--named-actions'] if use_names else [],
                            response_transform=encode if use_names else None)
                        old = query.QueryTests().run_client(module=baseline, **flags)
                        new = query.QueryTests().run_client(**flags)
                        self.assertIsNone(old['error']); self.assertIsNone(new['error'])
                        for field in ('calls', 'requests', 'order', 'commands'):
                            self.assertEqual(old[field], new[field])
                        self.assertNotIn(client.SINGLE_ARM_PROGRESS_TASK, new['calls'][0]['prompt'])

    def test_goal_uncertainty_and_stage_names_do_not_create_runtime_gates(self):
        # The new instruction is not an inferred-contact classifier or a stage state machine.
        for use_names in (False, True):
            def uncertain_move(value, index, schema):
                value.update(tool='act', steps=8, stage='second_sleeve',
                    visual_assessment='uncertain',
                    reason='Selected arm identity unresolved after useful recovery; adjust approach without claiming passage.')
                value['action'][1][4] = .07
                return encode(value) if use_names else value
            with self.subTest(named=use_names):
                result = query.QueryTests().run_client(enabled=False, scenario='direct',
                    strategy=STRATEGY, extra_flags=['--named-actions'] if use_names else [],
                    response_transform=uncertain_move)
                self.assertIsNone(result['error'])
                self.assertEqual(result['attempt']['decisions_completed'], 1)
                acts = [args for tool, args in result['requests'] if tool == 'act']
                expected = np.zeros((2, 9), np.float32); expected[1, 4] = .07
                self.assertEqual(acts, [{'action': expected.tolist(), 'steps': 8}])
                self.assertEqual(result['calls'][0]['schema'],
                    named.response_schema(baseline.SCHEMA) if use_names else baseline.SCHEMA)
                self.assertNotIn('pixel_depth_query', result['attempt'])
                if not use_names:
                    self.assertNotIn('named_actions', result['attempt'])

    def test_query_freezes_16_images_and_full_length_act_has_separate_settle(self):
        for use_names in (False, True):
            def move(value, index, schema):
                if index == 1:
                    value.update(tool='act', steps=20, stage='first_sleeve',
                        reason='Continue the same observed forearm relationship; passage remains uncertain.')
                    value['action'][0][4] = .08
                return encode(value) if use_names else value
            with self.subTest(named=use_names):
                flags = ['--post-action-settle-steps', '6']
                if use_names: flags.append('--named-actions')
                result = query.QueryTests().run_client(strategy=STRATEGY, history=True,
                    depth_panel=True, extra_flags=flags, response_transform=move)
                self.assertIsNone(result['error'])
                self.assertEqual(result['order'][-6:],
                    ['call0', 'call1', 'act', 'act', 'stop', 'finish_episode'])
                first, followup = result['calls']
                self.assertEqual(len(first['images']), 16)
                self.assertEqual(first['images'], followup['images'])
                self.assertTrue(followup['prompt'].startswith(first['prompt']))
                self.assertIn(client.SINGLE_ARM_PROGRESS_TASK, first['prompt'])
                expected_schema = named.response_schema(baseline.SCHEMA) if use_names else baseline.SCHEMA
                self.assertEqual(followup['schema'], expected_schema)
                self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
                calls = [e for e in result['events'] if e['type'] == 'model_call']
                self.assertEqual(calls[0]['frozen_observation_id'], calls[1]['frozen_observation_id'])
                self.assertEqual(calls[0]['observation_simulation_time_s'],
                                 calls[1]['observation_simulation_time_s'])
                self.assertEqual(result['attempt']['pixel_depth_query']['queries_completed'], 1)
                # Query is physics-free: 3 replay + 20 act + 6 settle + 1 budget cleanup.
                self.assertEqual(result['attempt']['simulation_steps'], 30)
                acts = [args for tool, args in result['requests'] if tool == 'act']
                expected = np.zeros((2, 9), np.float32); expected[0, 4] = .08
                self.assertEqual(acts[-2], {'action': expected.tolist(), 'steps': 20})
                self.assertEqual(acts[-1], {'action': np.zeros((2, 9)).tolist(), 'steps': 6})
                for call in result['calls']:
                    for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                        self.assertNotIn(forbidden, call['prompt'])

    def test_invalid_or_interrupted_named_query_cycle_cannot_dispatch_model_act(self):
        for scenario, error in [('repeat_query', ValueError), ('invalid_second', ValueError),
                                ('nonzero_placeholder', ValueError),
                                ('interrupt_after_query', KeyboardInterrupt)]:
            with self.subTest(scenario=scenario):
                result = query.QueryTests().run_client(strategy=STRATEGY, scenario=scenario,
                    extra_flags=['--named-actions'], response_transform=encode)
                self.assertIsInstance(result['error'], error)
                self.assertEqual(result['attempt']['decisions_completed'], 0)
                self.assertEqual(result['requests'], [('stop', None), ('finish_episode', None)])

    def test_review_threshold_and_trusted_parent_data_do_not_change_actor_prompt(self):
        low = self.prepare(review_points=10, settle=6, depth=True)
        high = self.prepare(review_points=50, settle=6, depth=True)
        self.assertEqual(low['prompt'], high['prompt'])
        self.assertEqual(low['attempt']['review_threshold_raw_points'], 10)
        self.assertEqual(high['attempt']['review_threshold_raw_points'], 50)
        for forbidden in ('892321', 'private-parent', 'private-source-family',
                          'reset_seed', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])

    def test_other_modes_and_open_loop_plans_rejected_before_output_or_simulator(self):
        for mode, size in [('wiring', 1), ('pickup', 1), ('dressing', 2), ('dressing', 3)]:
            with self.subTest(mode=mode, size=size), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                argv = ['client', '--run-id', 'reject', '--mode', mode,
                        '--strategy', STRATEGY, '--plan-size', str(size)]
                with mock.patch.object(client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(client.signal, 'signal'), \
                     mock.patch.object(client, 'Simulator') as simulator, \
                     mock.patch.object(sys, 'argv', argv), mock.patch('sys.stderr'), \
                     self.assertRaises(SystemExit):
                    client.main()
                simulator.assert_not_called()
                self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
