"""CPU routing/protocol checks, not a test of model adherence or physical entry."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np

from participant.collection import codex_client as client, named_actions
import test_depth_query as query
import test_support_diagnostic_strategy as diagnostic
from test_overhead_strategy import encode


STRATEGY = 'coordinated-diagonal-entry'


class DiagonalEntryStrategyTest(unittest.TestCase):
    def prepare(self, **kwargs):
        return diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, **kwargs)

    def test_new_route_adds_only_entry_comparison_and_excludes_trusted_selection_data(self):
        plain = self.prepare(replay=False)
        prompt = plain['prompt']
        self.assertEqual(prompt, '\n\n'.join([client.TASK, client.COORDINATED_TASK,
            client.SIDE_HEM_WRISTS_TASK, client.DIAGONAL_ENTRY_TASK, client.METHOD_SATURATION_TASK]))
        self.assertEqual(plain['attempt']['strategy'], STRATEGY)
        self.assertEqual(plain['attempt']['plan_execution'], 'single_decision')
        self.assertEqual(plain['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())
        low = self.prepare(review_points=10, settle=6, depth=True)
        high = self.prepare(review_points=50, settle=6, depth=True)
        self.assertEqual(low['prompt'], high['prompt'])
        for forbidden in ('892321', 'private-parent', 'private-source-family',
                          'reset_seed', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])

    def test_existing_side_hem_route_and_omitted_strategy_default_remain_opt_out(self):
        old = diagnostic.SupportDiagnosticStrategyTest().prepare(
            strategy='coordinated-side-hem-wrists', replay=False)
        self.assertEqual(old['prompt'], '\n\n'.join([client.TASK, client.COORDINATED_TASK,
            client.SIDE_HEM_WRISTS_TASK, client.METHOD_SATURATION_TASK]))
        # This helper omits --strategy for general without replay history.
        default = query.QueryTests().run_client(enabled=False, scenario='direct')
        self.assertIsNone(default['error'])
        self.assertEqual(default['attempt']['strategy'], 'general')
        for call in default['calls']:
            self.assertNotIn(client.DIAGONAL_ENTRY_TASK, call['prompt'])

    def test_requires_closed_loop_dressing_exec_before_output_or_simulator(self):
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

    def test_named_query_preserves_frozen_observation_mapping_and_settle_contract(self):
        def move(value, index, schema):
            if index == 1:
                value.update(tool='act', steps=4, stage='first_sleeve',
                    visual_assessment='uncertain', reason='Inspect the same hand and supported lip relation.')
                value['action'][0][7] = -.03
                value['action'][1][3] = .04
            return encode(value)
        result = query.QueryTests().run_client(strategy=STRATEGY, history=True,
            depth_panel=True, extra_flags=['--named-actions', '--post-action-settle-steps', '6'],
            response_transform=move)
        self.assertIsNone(result['error'])
        first, followup = result['calls']
        self.assertEqual(first['images'], followup['images'])
        self.assertEqual(followup['schema'], named_actions.response_schema(client.SCHEMA))
        self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
        events = [event for event in result['events'] if event['type'] == 'model_call']
        self.assertEqual(events[0]['frozen_observation_id'], events[1]['frozen_observation_id'])
        expected = np.zeros((2, 9), np.float32)
        expected[0, 7] = -.03
        expected[1, 3] = .04
        acts = [args for tool, args in result['requests'] if tool == 'act']
        self.assertEqual(acts[-2], {'action': expected.tolist(), 'steps': 4})
        self.assertEqual(acts[-1], {'action': np.zeros((2, 9)).tolist(), 'steps': 6})
        # Three replay, four model, six settle, one cleanup; query adds no physics.
        self.assertEqual(result['attempt']['simulation_steps'], 14)
        for call in result['calls']:
            for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                self.assertNotIn(forbidden, call['prompt'])


if __name__ == '__main__':
    unittest.main()
