"""CPU routing/isolation regressions; no model adherence or dressing claim."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from participant.collection import codex_client as client
import test_depth_query as query
import test_support_diagnostic_strategy as diagnostic


# Generated from the public base 75492d7, independently of candidate constants.
BASE_PROMPT_SHA256 = {
    'general': 'ac89970d66c078519983057b04fc363bdfd72171d48c332df591c8013a0c6959',
    'coordinated': '1610f3c580383a6ed6b913f6bfaf69c9ce7887634b0c97002a98620a4ddb1aaa',
    'coordinated-sleeve': '8961c76a7e13b4f8a308c5c48e906bdacdc0839a42e58560e0fd73912c4dc622',
    'coordinated-hem-route': '853322660db461c80ef9fa9c36651a92a22cd37b1045a25674d2c8d9038b66bf',
    'coordinated-opening-first': '926fde1951603e81fcdeb04994dc8422f6e3c21eacafb00a87d2a1928348817a',
    'coordinated-support-diagnostic': 'e5521061fb3dcbdefa1f2f2fb5188fc1bbaa5dbb7c432ea1e8292835aead9f37',
    'coordinated-regrasp-hem': '4feb53baf36138ba8e785c9b89b1719762783c34109d95585b66285d4d7af1f9',
    'coordinated-support-guide': '1e0ef33ff79ab76ccaf944297e8a63c7fde64cfacd3bd58842fc8cae790534ca',
}
STRATEGY = 'coordinated-neckline-first'


class NecklineStrategyTest(unittest.TestCase):
    def prepare(self, **kwargs):
        return diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, **kwargs)

    def test_new_route_has_head_first_objective_and_original_action_contract(self):
        result = self.prepare(replay=False)
        prompt = result['prompt']
        self.assertTrue(prompt.startswith(client.NECKLINE_BASE_TASK + '\n\n'))
        self.assertIn('head passage through the neck opening before sleeve threading', prompt)
        self.assertNotIn('demonstration: thread both arms into the sleeves', prompt)
        self.assertIn(client.COORDINATED_TASK, prompt)
        self.assertIn(client.NECKLINE_TASK, prompt)
        self.assertIn(client.METHOD_SATURATION_TASK, prompt)
        for previous in (client.SLEEVE_TASK, client.HEM_ROUTE_TASK, client.OPENING_FIRST_TASK,
                         client.SUPPORT_DIAGNOSTIC_TASK, client.REGRASP_HEM_TASK,
                         client.SUPPORT_GUIDE_TASK):
            self.assertNotIn(previous, prompt)
        # The complete action/schema paragraph must survive objective replacement.
        self.assertEqual(client.NECKLINE_BASE_TASK.split('\n\n')[1],
                         client.TASK.split('\n\n')[1])
        self.assertEqual(result['attempt']['strategy'], STRATEGY)
        self.assertEqual(result['attempt']['plan_execution'], 'single_decision')
        self.assertEqual(result['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())

    def test_all_eight_existing_prompt_bytes_match_fixed_public_base(self):
        for strategy, digest in BASE_PROMPT_SHA256.items():
            with self.subTest(strategy=strategy):
                result = diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=strategy, replay=False)
                self.assertEqual(hashlib.sha256(result['prompt'].encode()).hexdigest(), digest)

    def test_replay_seed_lineage_and_score_threshold_do_not_enter_new_prompt(self):
        low = self.prepare(review_points=10, settle=6, depth=True)
        high = self.prepare(review_points=50, settle=6, depth=True)
        self.assertEqual(low['prompt'], high['prompt'])
        self.assertEqual(low['attempt']['review_threshold_raw_points'], 10)
        self.assertEqual(high['attempt']['review_threshold_raw_points'], 50)
        self.assertEqual(low['attempt']['continuation']['replay_steps'], 264)
        for forbidden in ('892321', 'private-parent', 'private-source-family',
                          'reset_seed', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])

    def test_query_default_off_preserves_one_call_and_action_schema(self):
        result = query.QueryTests().run_client(enabled=False, scenario='direct', strategy=STRATEGY)
        self.assertIsNone(result['error'])
        self.assertEqual(result['order'], ['call0', 'finish_episode'])
        self.assertEqual(result['calls'][0]['schema'], client.SCHEMA)
        self.assertNotIn('pixel_depth_query', result['attempt'])
        self.assertNotIn('frozen_public_depth_query_context:', result['calls'][0]['prompt'])

    def test_query_followup_retains_new_route_and_16_frozen_public_images(self):
        result = query.QueryTests().run_client(strategy=STRATEGY, history=True, depth_panel=True)
        self.assertIsNone(result['error'])
        self.assertEqual(result['order'][-3:], ['call0', 'call1', 'finish_episode'])
        self.assertEqual(len(result['calls']), 2)
        first, followup = result['calls']
        self.assertEqual(len(first['images']), 16)
        self.assertEqual(first['images'], followup['images'])
        self.assertTrue(followup['prompt'].startswith(first['prompt']))
        self.assertIn(client.NECKLINE_TASK, first['prompt'])
        self.assertNotIn(client.HEM_ROUTE_TASK, first['prompt'])
        self.assertEqual(followup['schema'], client.SCHEMA)
        self.assertEqual(result['attempt']['pixel_depth_query']['queries_completed'], 1)
        self.assertEqual([first['timeout'], followup['timeout']], [180, 180])
        for call in (first, followup):
            for forbidden in ('NEVER_ACTOR', 'PRIVATE_LINEAGE', '123987', 'PRIVATE_SESSION_CANARY'):
                self.assertNotIn(forbidden, call['prompt'])

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
