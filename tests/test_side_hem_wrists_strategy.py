"""CPU routing and isolation checks; no claim about real grasp or dressing success."""
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


STRATEGY = 'coordinated-side-hem-wrists'


class SideHemWristsStrategyTest(unittest.TestCase):
    def prepare(self, **kwargs):
        return diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, **kwargs)

    def test_route_is_distinct_from_previous_fixed_grasp_and_neckline_objectives(self):
        result = self.prepare(replay=False)
        prompt = result['prompt']
        self.assertEqual(prompt, '\n\n'.join([client.TASK, client.COORDINATED_TASK,
            client.SIDE_HEM_WRISTS_TASK, client.METHOD_SATURATION_TASK]))
        for competing in (client.SINGLE_ARM_PROGRESS_TASK, client.TASK_PROGRESS_TASK,
                          client.NECKLINE_TASK, client.OVERHEAD_TASK, client.LEADING_HAND_SWAP_TASK,
                          client.OPPOSING_RIM_TASK, client.HEM_ROUTE_TASK):
            self.assertNotIn(competing, prompt)
        self.assertEqual(result['attempt']['strategy'], STRATEGY)
        self.assertEqual(result['attempt']['plan_execution'], 'single_decision')
        self.assertEqual(result['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())

    def test_replay_and_score_selection_do_not_supply_private_guidance(self):
        low = self.prepare(review_points=10, settle=6, depth=True)
        high = self.prepare(review_points=50, settle=6, depth=True)
        self.assertEqual(low['prompt'], high['prompt'])
        self.assertEqual(low['attempt']['review_threshold_raw_points'], 10)
        self.assertEqual(high['attempt']['review_threshold_raw_points'], 50)
        for forbidden in ('892321', 'private-parent', 'private-source-family',
                          'reset_seed', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])

    def test_named_depth_query_keeps_observation_frozen_and_actions_unmodified(self):
        def move(value, index, schema):
            if index == 1:
                value.update(tool='act', steps=4, stage='first_sleeve',
                    visual_assessment='uncertain',
                    reason='First wrist relation uncertain; r0 supports, r1 adjusts candidate opening.')
                value['action'][1][5] = .04
            return encode(value)
        result = query.QueryTests().run_client(strategy=STRATEGY, history=True,
            depth_panel=True, extra_flags=['--named-actions', '--post-action-settle-steps', '6'],
            response_transform=move)
        self.assertIsNone(result['error'])
        first, followup = result['calls']
        self.assertEqual(first['images'], followup['images'])
        self.assertEqual(followup['schema'], named_actions.response_schema(client.SCHEMA))
        self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
        calls = [event for event in result['events'] if event['type'] == 'model_call']
        self.assertEqual(calls[0]['frozen_observation_id'], calls[1]['frozen_observation_id'])
        acts = [args for tool, args in result['requests'] if tool == 'act']
        expected = np.zeros((2, 9), np.float32); expected[1, 5] = .04
        self.assertEqual(acts[-2], {'action': expected.tolist(), 'steps': 4})
        self.assertEqual(acts[-1], {'action': np.zeros((2, 9)).tolist(), 'steps': 6})
        # 3 replay, 4 model, 6 settle, 1 cleanup. Query itself adds no physics.
        self.assertEqual(result['attempt']['simulation_steps'], 14)
        for call in result['calls']:
            for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                self.assertNotIn(forbidden, call['prompt'])

    def test_invalid_query_cannot_create_a_manipulation_action(self):
        result = query.QueryTests().run_client(strategy=STRATEGY, scenario='repeat_query',
            extra_flags=['--named-actions'], response_transform=encode)
        self.assertIsInstance(result['error'], ValueError)
        self.assertEqual(result['attempt']['decisions_completed'], 0)
        self.assertEqual(result['requests'], [('stop', None), ('finish_episode', None)])

    def test_rejects_non_dressing_open_loop_or_alternate_backend_before_creating_outputs(self):
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


if __name__ == '__main__':
    unittest.main()
