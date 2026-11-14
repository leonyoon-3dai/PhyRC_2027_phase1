"""Prompt-only retention variant; these tests do not prove model adherence."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest import mock

from participant.collection import codex_client as client
import test_depth_query as query
import test_support_diagnostic_strategy as diagnostic
from test_overhead_strategy import encode


ROOT = Path(__file__).resolve().parents[1]
# Original source: 464203860304631d00a8acd6747b86c23cfded61:participant/collection/codex_client.py
# Pin content independently of commit metadata when identical trees are republished.
BASE_BLOB = 'a60253067fd10772000a4ee537cbb9bdb2521c72'
BASE_SOURCE_BYTES = subprocess.check_output(['git', 'cat-file', 'blob', BASE_BLOB], cwd=ROOT)
assert hashlib.sha256(BASE_SOURCE_BYTES).hexdigest() == 'e77f09589cd021a9ada5343a8a85e87d41f641cc546ea74ab4b5b20020082262'
BASE_SOURCE = BASE_SOURCE_BYTES.decode('utf-8')
baseline = ModuleType('retained_grip_baseline_client')
baseline.__file__ = str(ROOT / 'participant/collection/codex_client.py')
exec(compile(BASE_SOURCE, baseline.__file__, 'exec'), baseline.__dict__)
STRATEGY = 'coordinated-middle-grip-drape-retain'


class MiddleGripRetainStrategyTest(unittest.TestCase):
    def test_opt_in_retains_exact_method_then_appends_retention_instruction(self):
        result = diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, replay=False)
        prompt = result['prompt']
        base = '\n\n'.join([client.TASK, client.COORDINATED_TASK,
            client.SIDE_HEM_WRISTS_TASK, client.MIDDLE_GRIP_DRAPE_TASK, client.METHOD_SATURATION_TASK])
        self.assertEqual(prompt, base + '\n\n' + client.MIDDLE_GRIP_RETAIN_TASK)
        self.assertEqual(result['attempt']['strategy'], STRATEGY)
        self.assertEqual(result['attempt']['prompt_sha256'], hashlib.sha256(prompt.encode()).hexdigest())
        low = diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, review_points=10)
        high = diagnostic.SupportDiagnosticStrategyTest().prepare(strategy=STRATEGY, review_points=50)
        self.assertEqual(low['prompt'], high['prompt'])
        for forbidden in ('892321', 'private-parent', 'private-source-family', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, low['prompt'])

    def test_original_middle_grip_method_and_existing_routes_match_fixed_source(self):
        for strategy in ('coordinated-middle-grip-drape', 'coordinated-central-span-entry',
                         'coordinated-side-hem-wrists', 'coordinated-diagonal-entry'):
            for enabled in (False, True):
                with self.subTest(strategy=strategy, query=enabled):
                    options = dict(strategy=strategy, enabled=enabled, history=True, depth_panel=True,
                        extra_flags=['--named-actions'], response_transform=encode)
                    old = query.QueryTests().run_client(module=baseline, **options)
                    new = query.QueryTests().run_client(**options)
                    self.assertIsNone(old['error']); self.assertIsNone(new['error'])
                    for field in ('calls', 'requests', 'order', 'commands'):
                        self.assertEqual(old[field], new[field])

    def test_requires_single_decision_dressing_exec_before_outputs(self):
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

    def test_response_schema_and_dispatch_are_unchanged_not_a_runtime_retention_gate(self):
        # A synthetic actor may violate the prompt. Document that the shared
        # official action validator still accepts its otherwise valid action.
        def open_grip(value, index, schema):
            value.update(tool='act', steps=4, stage='recovery', visual_assessment='uncertain',
                         reason='Synthetic prompt-violation probe, not an approved manipulation.')
            value['action'][0][8] = -1.
            return encode(value)
        options = dict(enabled=False, scenario='direct', extra_flags=['--named-actions'],
                       response_transform=open_grip)
        old = query.QueryTests().run_client(module=baseline, strategy='coordinated-middle-grip-drape', **options)
        new = query.QueryTests().run_client(strategy=STRATEGY, **options)
        self.assertIsNone(new['error'])
        self.assertEqual(old['requests'], new['requests'])
        self.assertEqual(old['calls'][0]['schema'], new['calls'][0]['schema'])
        self.assertEqual(new['requests'][0][1]['action'][0][8], -1.)


if __name__ == '__main__':
    unittest.main()
