"""Opt-in prompt routing and frozen public protocol; no model or physics."""
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
BASE = 'eea0546f23e240867caab37fdeef3077fe46e623'
BASE_SOURCE = subprocess.check_output(
    ['git', 'show', BASE + ':participant/collection/codex_client.py'], cwd=ROOT, text=True)
baseline = ModuleType('entry_probe_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(BASE_SOURCE, baseline.__file__, 'exec'), baseline.__dict__)
STRATEGY = 'coordinated-entry-probe'
OLD_STRATEGIES = ('general', 'coordinated', 'coordinated-sleeve', 'coordinated-hem-route',
    'coordinated-opening-first', 'coordinated-support-diagnostic', 'coordinated-regrasp-hem',
    'coordinated-support-guide', 'coordinated-neckline-first', 'coordinated-overhead-drape')


class EntryProbeStrategyTest(unittest.TestCase):
    def prepare(self, **kwargs):
        return diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, **kwargs)

    def test_selected_prompt_has_public_contract_without_competing_uncertainty_gates(self):
        result = self.prepare(replay=False)
        prompt = result['prompt']
        self.assertEqual(prompt, '\n\n'.join([baseline.TASK, baseline.COORDINATED_TASK,
            client.ENTRY_PROBE_TASK, baseline.METHOD_SATURATION_TASK]))
        for competing in (client.SLEEVE_TASK, client.HEM_ROUTE_TASK, client.OVERHEAD_TASK,
                          client.NECKLINE_TASK, client.OPENING_FIRST_TASK,
                          client.REGRASP_HEM_TASK, client.SUPPORT_GUIDE_TASK,
                          client.SUPPORT_DIAGNOSTIC_TASK):
            self.assertNotIn(competing, prompt)
        self.assertEqual(result['attempt']['strategy'], STRATEGY)
        self.assertEqual(result['attempt']['plan_execution'], 'single_decision')
        self.assertEqual(result['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())

    def test_existing_constants_and_nonrouting_functions_match_fixed_public_source(self):
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
        for name, node in old.items():
            if name != 'main':
                with self.subTest(name=name):
                    self.assertEqual(current[name], node)

    def test_ten_old_routes_keep_prompts_schemas_images_and_dispatch_with_both_options(self):
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
                        self.assertNotIn(client.ENTRY_PROBE_TASK, new['calls'][0]['prompt'])

    def test_optional_features_stay_off_and_public_action_range_is_not_restricted(self):
        result = query.QueryTests().run_client(enabled=False, scenario='direct', strategy=STRATEGY)
        self.assertIsNone(result['error'])
        self.assertEqual(result['order'], ['call0', 'finish_episode'])
        self.assertEqual(result['calls'][0]['schema'], baseline.SCHEMA)
        self.assertNotIn('named_actions', result['attempt'])
        self.assertNotIn('pixel_depth_query', result['attempt'])
        # 2-4 steps describes the information probe in the prompt, not a new
        # global actuator/schema limit for transport, recovery, stop or finish.
        self.assertEqual(result['calls'][0]['schema']['properties']['steps']['maximum'], 20)

    def test_query_freezes_16_images_then_probe_and_existing_settle_are_separate(self):
        for use_names in (False, True):
            def move(value, index, schema):
                if index == 1:
                    value.update(tool='act', steps=3)
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
                self.assertIn(client.ENTRY_PROBE_TASK, first['prompt'])
                expected_schema = named.response_schema(baseline.SCHEMA) if use_names else baseline.SCHEMA
                self.assertEqual(followup['schema'], expected_schema)
                self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
                calls = [e for e in result['events'] if e['type'] == 'model_call']
                self.assertEqual(calls[0]['frozen_observation_id'], calls[1]['frozen_observation_id'])
                self.assertEqual(calls[0]['observation_simulation_time_s'],
                                 calls[1]['observation_simulation_time_s'])
                self.assertEqual(result['attempt']['pixel_depth_query']['queries_completed'], 1)
                # 3 replay + 3 commanded probe + 6 neutral settling + 1 budget cleanup.
                self.assertEqual(result['attempt']['simulation_steps'], 13)
                acts = [args for tool, args in result['requests'] if tool == 'act']
                expected = np.zeros((2, 9), np.float32); expected[0, 4] = .08
                self.assertEqual(acts[-2]['steps'], 3)
                self.assertEqual(acts[-2]['action'], expected.tolist())
                self.assertEqual(acts[-1]['steps'], 6)
                self.assertEqual(acts[-1]['action'], np.zeros((2, 9)).tolist())
                for call in result['calls']:
                    for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                        self.assertNotIn(forbidden, call['prompt'])

    def test_trusted_threshold_and_parent_information_remain_outside_prompt(self):
        low = self.prepare(review_points=10, settle=6, depth=True)
        high = self.prepare(review_points=50, settle=6, depth=True)
        self.assertEqual(low['prompt'], high['prompt'])
        self.assertEqual(low['attempt']['review_threshold_raw_points'], 10)
        self.assertEqual(high['attempt']['review_threshold_raw_points'], 50)
        for forbidden in ('892321', 'private-parent', 'private-source-family',
                          'reset_seed', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])

    def test_wrong_mode_and_grouped_plans_fail_before_output_or_simulator(self):
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
