"""CPU prompt/contract regressions; no model adherence or cloth outcome claim."""
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
# Original source: 7bdd82c0abf0d719257eaa5fced3090ba8f01068:participant/collection/codex_client.py
# Pin content independently of commit metadata when identical trees are republished.
BASE_BLOB = 'd256e8d205a1352b7294de5b299441804dc3ce70'
BASE_SOURCE_BYTES = subprocess.check_output(['git', 'cat-file', 'blob', BASE_BLOB], cwd=ROOT)
assert hashlib.sha256(BASE_SOURCE_BYTES).hexdigest() == 'f44474d5b273a6bf1cc84662c63799f15be52bd77be2371b83de9dbc2451cfd0'
BASE_SOURCE = BASE_SOURCE_BYTES.decode('utf-8')
baseline = ModuleType('wide_hem_side_entry_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(BASE_SOURCE, baseline.__file__, 'exec'), baseline.__dict__)
STRATEGY = 'coordinated-wide-hem-side-entry'


def strategy_choices(source):
    call = next(node for node in ast.walk(ast.parse(source))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'add_argument' and node.args
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == '--strategy')
    return ast.literal_eval(next(item.value for item in call.keywords if item.arg == 'choices'))


class WideHemSideEntryStrategyTest(unittest.TestCase):
    def test_opt_in_composition_and_public_provenance(self):
        result = diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, replay=False)
        prompt = result['prompt']
        self.assertEqual(prompt, '\n\n'.join([baseline.TASK, baseline.COORDINATED_TASK,
            baseline.SIDE_HEM_WRISTS_TASK, baseline.METHOD_SATURATION_TASK,
            client.WIDE_HEM_SIDE_ENTRY_TASK]))
        for competing in (client.MIDDLE_GRIP_DRAPE_TASK, client.MIDDLE_GRIP_RETAIN_TASK,
                          client.CENTRAL_SPAN_ENTRY_TASK, client.DIAGONAL_ENTRY_TASK):
            self.assertNotIn(competing, prompt)
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

    def test_only_one_strategy_and_constant_added_with_existing_nonrouting_code_unchanged(self):
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
        current_source = Path(client.__file__).read_text()
        old, new = nodes(BASE_SOURCE), nodes(current_source)
        self.assertEqual(set(new) - set(old), {'WIDE_HEM_SIDE_ENTRY_TASK', 'WRIST_BODY_ENTRY_TASK'})
        self.assertEqual(set(old) - set(new), set())
        for name in old:
            if name != 'main':
                with self.subTest(node=name):
                    self.assertEqual(old[name], new[name])
        self.assertEqual(strategy_choices(current_source),
                         strategy_choices(BASE_SOURCE) + [STRATEGY, 'coordinated-wrist-body-entry'])

    def test_every_previous_strategy_keeps_prompt_schema_images_and_dispatch(self):
        for strategy in strategy_choices(BASE_SOURCE):
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

    def test_omitted_strategy_keeps_default_behavior(self):
        old = query.QueryTests().run_client(module=baseline, enabled=False, scenario='direct')
        new = query.QueryTests().run_client(enabled=False, scenario='direct')
        self.assertIsNone(new['error'])
        self.assertEqual(new['attempt']['strategy'], 'general')
        for field in ('calls', 'requests', 'order', 'commands'):
            self.assertEqual(old[field], new[field])

    def test_rejects_non_dressing_grouped_or_alternate_backend_before_outputs(self):
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

    def test_frozen_public_query_named_lateral_motion_and_settle_keep_shared_contract(self):
        def move(value, index, schema):
            if index == 1:
                value.update(tool='act', steps=4, stage='first_sleeve', visual_assessment='uncertain',
                             reason='CPU fixture: inspect the same-hand relation after lateral motion.')
                value['action'][0][1] = .04
                value['action'][1][1] = -.03
                value['action'][0][8] = value['action'][1][8] = 1.
            return encode(value)
        result = query.QueryTests().run_client(strategy=STRATEGY, history=True, depth_panel=True,
            extra_flags=['--named-actions', '--post-action-settle-steps', '6'], response_transform=move)
        self.assertIsNone(result['error'])
        first, followup = result['calls']
        self.assertEqual(first['images'], followup['images'])
        self.assertEqual(followup['schema'], named_actions.response_schema(baseline.SCHEMA))
        self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
        calls = [event for event in result['events'] if event['type'] == 'model_call']
        self.assertEqual(calls[0]['frozen_observation_id'], calls[1]['frozen_observation_id'])
        self.assertEqual(calls[0]['observation_simulation_time_s'], calls[1]['observation_simulation_time_s'])
        expected = np.zeros((2, 9), np.float32)
        expected[0, 1], expected[1, 1] = .04, -.03
        expected[:, 8] = 1.
        acts = [args for tool, args in result['requests'] if tool == 'act']
        self.assertEqual(acts[-2], {'action': expected.tolist(), 'steps': 4})
        self.assertEqual(acts[-1], {'action': np.zeros((2, 9)).tolist(), 'steps': 6})
        self.assertEqual(result['attempt']['simulation_steps'], 14)  # 3 replay +4 act +6 settle +1 cleanup
        for call in result['calls']:
            for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                self.assertNotIn(forbidden, call['prompt'])

    def test_prompt_retention_does_not_add_an_action_gate(self):
        def open_grip(value, index, schema):
            value.update(tool='act', steps=4, stage='recovery', visual_assessment='uncertain',
                         reason='Synthetic prompt violation; not an approved manipulation.')
            value['action'][0][8] = -1.
            return encode(value)
        options = dict(enabled=False, scenario='direct', extra_flags=['--named-actions'],
                       response_transform=open_grip)
        old = query.QueryTests().run_client(module=baseline, strategy='coordinated-side-hem-wrists', **options)
        new = query.QueryTests().run_client(strategy=STRATEGY, **options)
        self.assertIsNone(new['error'])
        self.assertEqual(old['requests'], new['requests'])
        self.assertEqual(old['calls'][0]['schema'], new['calls'][0]['schema'])
        self.assertEqual(new['requests'][0][1]['action'][0][8], -1.)

    def test_invalid_query_never_dispatches_model_motion(self):
        for scenario, error in [('stale', ValueError), ('repeat_query', ValueError),
                ('invalid_second', ValueError), ('nonzero_placeholder', ValueError),
                ('interrupt_after_query', KeyboardInterrupt)]:
            with self.subTest(scenario=scenario):
                result = query.QueryTests().run_client(strategy=STRATEGY, scenario=scenario,
                    extra_flags=['--named-actions'], response_transform=encode)
                self.assertIsInstance(result['error'], error)
                self.assertEqual(result['attempt']['decisions_completed'], 0)
                self.assertEqual(result['requests'], [('stop', None), ('finish_episode', None)])


if __name__ == '__main__':
    unittest.main()
