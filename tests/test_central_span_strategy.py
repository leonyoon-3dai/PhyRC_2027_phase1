"""Opt-in routing/public contract tests; fake actors do not verify cloth behavior."""
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

from participant.collection import codex_client as client, named_actions
import test_depth_query as query
import test_support_diagnostic_strategy as diagnostic
from test_overhead_strategy import encode


ROOT = Path(__file__).resolve().parents[1]
BASE = 'db1ff08d2f60a4ae30688b24ed4931c6634da42c'
BASE_SOURCE = subprocess.check_output(
    ['git', 'show', BASE + ':participant/collection/codex_client.py'], cwd=ROOT, text=True)
baseline = ModuleType('central_span_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(BASE_SOURCE, baseline.__file__, 'exec'), baseline.__dict__)
STRATEGY = 'coordinated-central-span-entry'


class CentralSpanStrategyTest(unittest.TestCase):
    def test_route_composes_side_hem_without_forced_diagonal_and_keeps_selection_private(self):
        result = diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, replay=False)
        prompt = result['prompt']
        self.assertEqual(prompt, '\n\n'.join([client.TASK, client.COORDINATED_TASK,
            client.SIDE_HEM_WRISTS_TASK, client.CENTRAL_SPAN_ENTRY_TASK, client.METHOD_SATURATION_TASK]))
        self.assertNotIn(client.DIAGONAL_ENTRY_TASK, prompt)
        self.assertEqual(result['attempt']['strategy'], STRATEGY)
        self.assertEqual(result['attempt']['plan_execution'], 'single_decision')
        self.assertEqual(result['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())
        low = diagnostic.SupportDiagnosticStrategyTest().prepare(
            strategy=STRATEGY, review_points=10, settle=6, depth=True)
        high = diagnostic.SupportDiagnosticStrategyTest().prepare(
            strategy=STRATEGY, review_points=50, settle=6, depth=True)
        self.assertEqual(low['prompt'], high['prompt'])
        for forbidden in ('892321', 'private-parent', 'private-source-family',
                          'reset_seed', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])

    def test_all_previous_constants_and_nonrouting_code_match_fixed_public_source(self):
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
        old, new = nodes(BASE_SOURCE), nodes(Path(client.__file__).read_text())
        self.assertEqual(set(new) - set(old), {'CENTRAL_SPAN_ENTRY_TASK', 'MIDDLE_GRIP_DRAPE_TASK'})
        self.assertEqual(set(old) - set(new), set())
        for key in old:
            if key != 'main':
                with self.subTest(node=key):
                    self.assertEqual(old[key], new[key])

    def test_prior_recent_routes_and_omitted_default_match_fixed_behavior(self):
        # Older routes also retain the independent historical 56-configuration suite.
        for strategy in ('coordinated-side-hem-wrists', 'coordinated-diagonal-entry',
                         'coordinated-single-arm-progress'):
            for enabled in (False, True):
                for names in (False, True):
                    with self.subTest(strategy=strategy, query=enabled, named=names):
                        options = dict(strategy=strategy, enabled=enabled, history=True, depth_panel=True,
                            extra_flags=['--named-actions'] if names else [],
                            response_transform=encode if names else None)
                        old = query.QueryTests().run_client(module=baseline, **options)
                        new = query.QueryTests().run_client(**options)
                        self.assertIsNone(old['error']); self.assertIsNone(new['error'])
                        for field in ('calls', 'requests', 'order', 'commands'):
                            self.assertEqual(old[field], new[field])
                        self.assertNotIn(client.CENTRAL_SPAN_ENTRY_TASK, new['calls'][0]['prompt'])
        old = query.QueryTests().run_client(module=baseline, enabled=False, scenario='direct')
        new = query.QueryTests().run_client(enabled=False, scenario='direct')
        self.assertIsNone(new['error'])
        self.assertEqual(new['attempt']['strategy'], 'general')
        for field in ('calls', 'requests', 'order', 'commands'):
            self.assertEqual(old[field], new[field])

    def test_rejects_wrong_mode_backend_or_open_loop_before_outputs(self):
        for mode, size, backend in [('wiring', 1, 'exec'), ('pickup', 1, 'exec'),
                ('dressing', 2, 'exec'), ('dressing', 3, 'exec'), ('dressing', 1, 'app-server')]:
            with self.subTest(mode=mode, size=size, backend=backend), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                argv = ['client', '--run-id', 'reject', '--mode', mode, '--strategy', STRATEGY,
                        '--plan-size', str(size), '--actor-backend', backend]
                with mock.patch.object(client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(client.signal, 'signal'), \
                     mock.patch.object(client, 'Simulator') as simulator, \
                     mock.patch.object(sys, 'argv', argv), mock.patch('sys.stderr'), \
                     self.assertRaises(SystemExit):
                    client.main()
                simulator.assert_not_called()
                self.assertFalse((root / 'output').exists())

    def test_existing_xyz_query_named_mapping_and_motion_settle_are_unchanged(self):
        def move(value, index, schema):
            if index == 1:
                value.update(tool='act', steps=20, stage='first_sleeve',
                    visual_assessment='uncertain', reason='Compare the same hand with a supported free span.')
                value['action'][0][1] = .04
                value['action'][1][1] = .04
            return encode(value)
        result = query.QueryTests().run_client(strategy=STRATEGY, history=True, depth_panel=True,
            extra_flags=['--named-actions', '--post-action-settle-steps', '6'], response_transform=move)
        self.assertIsNone(result['error'])
        first, followup = result['calls']
        self.assertEqual(len(first['images']), 16)
        self.assertEqual(first['images'], followup['images'])
        self.assertEqual(followup['schema'], named_actions.response_schema(baseline.SCHEMA))
        self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
        queries = [e for e in result['events'] if e['type'] == 'depth_query_result']
        self.assertEqual(len(queries), 1)
        self.assertTrue(queries[0]['request']['include_camera_geometry'])
        self.assertEqual(queries[0]['response']['results'][0]['camera_xyz_m'], [0., 0., .75])
        self.assertFalse(queries[0]['executed'])
        calls = [e for e in result['events'] if e['type'] == 'model_call']
        self.assertEqual(calls[0]['frozen_observation_id'], calls[1]['frozen_observation_id'])
        self.assertEqual(calls[0]['observation_simulation_time_s'], calls[1]['observation_simulation_time_s'])
        expected = np.zeros((2, 9), np.float32); expected[:, 1] = .04
        acts = [args for tool, args in result['requests'] if tool == 'act']
        self.assertEqual(acts[-2], {'action': expected.tolist(), 'steps': 20})
        self.assertEqual(acts[-1], {'action': np.zeros((2, 9)).tolist(), 'steps': 6})
        self.assertEqual(result['attempt']['simulation_steps'], 30)  # 3 replay +20 act +6 settle +1 cleanup
        for call in result['calls']:
            for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                self.assertNotIn(forbidden, call['prompt'])

    def test_bad_query_cannot_dispatch_model_motion(self):
        for scenario, error in [('repeat_query', ValueError), ('invalid_second', ValueError),
                ('nonzero_placeholder', ValueError), ('interrupt_after_query', KeyboardInterrupt)]:
            with self.subTest(scenario=scenario):
                result = query.QueryTests().run_client(strategy=STRATEGY, scenario=scenario,
                    extra_flags=['--named-actions'], response_transform=encode)
                self.assertIsInstance(result['error'], error)
                self.assertEqual(result['attempt']['decisions_completed'], 0)
                self.assertEqual(result['requests'], [('stop', None), ('finish_episode', None)])

    def test_close_only_and_uncertain_stage_do_not_add_motion_or_runtime_gates(self):
        def close(value, index, schema):
            value.update(tool='act', steps=20, stage='preparation',
                visual_assessment='uncertain', reason='Observe fingers and cloth after closing.')
            value['action'][1][8] = 1.
            return value
        result = query.QueryTests().run_client(strategy=STRATEGY, enabled=False, scenario='direct',
            extra_flags=['--post-action-settle-steps', '6'], response_transform=close)
        self.assertIsNone(result['error'])
        acts = [args for tool, args in result['requests'] if tool == 'act']
        expected = np.zeros((2, 9), np.float32); expected[1, 8] = 1.
        self.assertEqual(acts, [{'action': expected.tolist(), 'steps': 20}])
        self.assertEqual(result['attempt']['decisions_completed'], 1)
        self.assertEqual(result['attempt']['simulation_steps'], 21)  # close +budget cleanup, no auto settle
        self.assertEqual(result['calls'][0]['schema'], baseline.SCHEMA)
        self.assertNotIn('pixel_depth_query', result['attempt'])


if __name__ == '__main__':
    unittest.main()
