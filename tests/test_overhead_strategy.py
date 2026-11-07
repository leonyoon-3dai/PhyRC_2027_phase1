"""CPU route/contract regressions; no model, physics or dressing-performance test."""
import ast
from copy import deepcopy
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


ROOT = Path(__file__).resolve().parents[1]
BASE = 'f9271fb3b7b968cb12a8391a2d30e4f67241a4ee'
BASE_SOURCE = subprocess.check_output(
    ['git', 'show', BASE + ':participant/collection/codex_client.py'], cwd=ROOT, text=True)
baseline = ModuleType('overhead_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(BASE_SOURCE, baseline.__file__, 'exec'), baseline.__dict__)
STRATEGY = 'coordinated-overhead-drape'
OLD_STRATEGIES = ('general', 'coordinated', 'coordinated-sleeve', 'coordinated-hem-route',
    'coordinated-opening-first', 'coordinated-support-diagnostic', 'coordinated-regrasp-hem',
    'coordinated-support-guide', 'coordinated-neckline-first')
CHANNELS = ('base_forward', 'base_left', 'base_CCW_yaw', 'lift', 'arm_extension',
            'wrist_yaw', 'wrist_pitch', 'wrist_roll', 'gripper')


def encode(value, _index=0, _schema=None):
    result = deepcopy(value)
    result['action'] = {f'robot_{i}': dict(zip(CHANNELS, row))
                        for i, row in enumerate(value['action'])}
    return result


class OverheadStrategyTest(unittest.TestCase):
    def prepare(self, **kwargs):
        return diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, **kwargs)

    def test_new_route_omits_competing_passage_order_and_keeps_action_contract(self):
        result = self.prepare(replay=False)
        prompt = result['prompt']
        self.assertEqual(prompt, '\n\n'.join([client.OVERHEAD_BASE_TASK,
            client.COORDINATED_TASK, client.OVERHEAD_TASK, client.METHOD_SATURATION_TASK]))
        self.assertNotIn('demonstration: thread both arms into the sleeves', prompt)
        self.assertNotIn('head passage through the neck opening before sleeve threading', prompt)
        for other in (client.NECKLINE_TASK, client.HEM_ROUTE_TASK, client.SLEEVE_TASK,
                      client.REGRASP_HEM_TASK, client.SUPPORT_GUIDE_TASK,
                      client.OPENING_FIRST_TASK, client.SUPPORT_DIAGNOSTIC_TASK):
            self.assertNotIn(other, prompt)
        self.assertEqual(client.OVERHEAD_BASE_TASK.split('\n\n')[1],
                         baseline.TASK.split('\n\n')[1])
        self.assertEqual(result['attempt']['strategy'], STRATEGY)
        self.assertEqual(result['attempt']['plan_execution'], 'single_decision')
        self.assertEqual(result['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())

    def test_existing_constants_and_all_nonrouting_functions_match_fixed_source(self):
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

    def test_nine_existing_routes_keep_prompt_schema_images_and_dispatch_bytes(self):
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

    def test_default_optional_features_stay_off_and_use_original_action_schema(self):
        result = query.QueryTests().run_client(enabled=False, scenario='direct', strategy=STRATEGY)
        self.assertIsNone(result['error'])
        self.assertEqual(result['order'], ['call0', 'finish_episode'])
        self.assertEqual(result['calls'][0]['schema'], baseline.SCHEMA)
        self.assertNotIn('named_actions', result['attempt'])
        self.assertNotIn('pixel_depth_query', result['attempt'])
        self.assertNotIn('frozen_public_depth_query_context:', result['calls'][0]['prompt'])

    def test_new_route_query_freezes_16_images_and_maps_followup_before_dispatch(self):
        for use_names in (False, True):
            def move(value, index, schema):
                if index == 1:
                    value.update(tool='act', steps=2)
                    value['action'][0][3] = value['action'][1][3] = .03
                return encode(value) if use_names else value
            with self.subTest(named=use_names):
                result = query.QueryTests().run_client(strategy=STRATEGY, history=True,
                    depth_panel=True, extra_flags=['--named-actions'] if use_names else [],
                    response_transform=move)
                self.assertIsNone(result['error'])
                # One-decision fixture exhausts its budget after act. The existing
                # supervisor then records a separate neutral cleanup transition.
                self.assertEqual(result['order'][-5:], ['call0', 'call1', 'act', 'stop', 'finish_episode'])
                first, followup = result['calls']
                self.assertEqual(len(first['images']), 16)
                self.assertEqual(first['images'], followup['images'])
                self.assertTrue(followup['prompt'].startswith(first['prompt']))
                self.assertIn(client.OVERHEAD_TASK, first['prompt'])
                expected_schema = named.response_schema(baseline.SCHEMA) if use_names else baseline.SCHEMA
                self.assertEqual(followup['schema'], expected_schema)
                self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
                calls = [e for e in result['events'] if e['type'] == 'model_call']
                self.assertEqual(calls[0]['frozen_observation_id'], calls[1]['frozen_observation_id'])
                self.assertEqual(calls[0]['observation_simulation_time_s'],
                                 calls[1]['observation_simulation_time_s'])
                self.assertEqual(result['attempt']['simulation_steps'], 6)  # 3 replay + 2 act + 1 cleanup
                self.assertEqual(result['attempt']['pixel_depth_query']['queries_completed'], 1)
                final_act = [args for tool, args in result['requests'] if tool == 'act'][-1]
                self.assertEqual(final_act['action'],
                    [[0., 0., 0., float(np.float32(.03)), 0., 0., 0., 0., 0.]] * 2)
                for call in result['calls']:
                    for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                        self.assertNotIn(forbidden, call['prompt'])

    def test_trusted_review_threshold_and_lineage_stay_outside_new_prompt(self):
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
