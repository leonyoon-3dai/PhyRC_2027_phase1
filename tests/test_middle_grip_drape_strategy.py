"""Opt-in/contract regression checks; fake actors do not validate cloth outcomes."""
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
BASE = '112cc5145dda4203ddce478473ddd70e7f17b3bb'
BASE_SOURCE = subprocess.check_output(
    ['git', 'show', BASE + ':participant/collection/codex_client.py'], cwd=ROOT, text=True)
baseline = ModuleType('middle_grip_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(BASE_SOURCE, baseline.__file__, 'exec'), baseline.__dict__)
STRATEGY = 'coordinated-middle-grip-drape'


class MiddleGripDrapeStrategyTest(unittest.TestCase):
    def test_opt_in_route_and_provenance_exclude_private_review_and_replay_metadata(self):
        result = diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, replay=False)
        prompt = result['prompt']
        self.assertEqual(prompt, '\n\n'.join([client.TASK, client.COORDINATED_TASK,
            client.SIDE_HEM_WRISTS_TASK, client.MIDDLE_GRIP_DRAPE_TASK, client.METHOD_SATURATION_TASK]))
        self.assertNotIn(client.CENTRAL_SPAN_ENTRY_TASK, prompt)
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

    def test_existing_constants_and_nonrouting_code_match_fixed_source(self):
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
        self.assertEqual(set(new) - set(old), {'MIDDLE_GRIP_DRAPE_TASK'})
        self.assertEqual(set(old) - set(new), set())
        for key in old:
            if key != 'main':
                with self.subTest(node=key):
                    self.assertEqual(old[key], new[key])

    def test_previous_routes_retain_prompt_actions_images_schema_and_default(self):
        for strategy in ('coordinated-central-span-entry', 'coordinated-side-hem-wrists',
                         'coordinated-diagonal-entry', 'coordinated-single-arm-progress'):
            for enabled in (False, True):
                for named in (False, True):
                    with self.subTest(strategy=strategy, query=enabled, named=named):
                        options = dict(strategy=strategy, enabled=enabled, history=True, depth_panel=True,
                            extra_flags=['--named-actions'] if named else [],
                            response_transform=encode if named else None)
                        old = query.QueryTests().run_client(module=baseline, **options)
                        new = query.QueryTests().run_client(**options)
                        self.assertIsNone(old['error']); self.assertIsNone(new['error'])
                        for field in ('calls', 'requests', 'order', 'commands'):
                            self.assertEqual(old[field], new[field])
        old = query.QueryTests().run_client(module=baseline, enabled=False, scenario='direct')
        new = query.QueryTests().run_client(enabled=False, scenario='direct')
        self.assertIsNone(new['error'])
        self.assertEqual(new['attempt']['strategy'], 'general')
        for field in ('calls', 'requests', 'order', 'commands'):
            self.assertEqual(old[field], new[field])

    def test_rejects_non_dressing_open_loop_and_alternate_backend_before_outputs(self):
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

    def test_frozen_public_query_named_motion_and_settle_contract(self):
        def move(value, index, schema):
            if index == 1:
                value.update(tool='act', steps=4, stage='first_sleeve',
                    visual_assessment='uncertain', reason='Inspect the selected hand after a supported descent.')
                value['action'][1][3] = -.04
            return encode(value)
        result = query.QueryTests().run_client(strategy=STRATEGY, history=True, depth_panel=True,
            extra_flags=['--named-actions', '--post-action-settle-steps', '6'], response_transform=move)
        self.assertIsNone(result['error'])
        first, followup = result['calls']
        self.assertEqual(first['images'], followup['images'])
        self.assertEqual(followup['schema'], named_actions.response_schema(baseline.SCHEMA))
        self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
        calls = [e for e in result['events'] if e['type'] == 'model_call']
        self.assertEqual(calls[0]['frozen_observation_id'], calls[1]['frozen_observation_id'])
        self.assertEqual(calls[0]['observation_simulation_time_s'], calls[1]['observation_simulation_time_s'])
        expected = np.zeros((2, 9), np.float32); expected[1, 3] = -.04
        acts = [args for tool, args in result['requests'] if tool == 'act']
        self.assertEqual(acts[-2], {'action': expected.tolist(), 'steps': 4})
        self.assertEqual(acts[-1], {'action': np.zeros((2, 9)).tolist(), 'steps': 6})
        self.assertEqual(result['attempt']['simulation_steps'], 14)  # 3 replay +4 act +6 settle +1 cleanup
        for call in result['calls']:
            for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                self.assertNotIn(forbidden, call['prompt'])

    def test_invalid_query_never_dispatches_model_motion(self):
        for scenario, error in [('repeat_query', ValueError), ('invalid_second', ValueError),
                ('nonzero_placeholder', ValueError), ('interrupt_after_query', KeyboardInterrupt)]:
            with self.subTest(scenario=scenario):
                result = query.QueryTests().run_client(strategy=STRATEGY, scenario=scenario,
                    extra_flags=['--named-actions'], response_transform=encode)
                self.assertIsInstance(result['error'], error)
                self.assertEqual(result['attempt']['decisions_completed'], 0)
                self.assertEqual(result['requests'], [('stop', None), ('finish_episode', None)])


if __name__ == '__main__':
    unittest.main()
