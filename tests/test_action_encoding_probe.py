"""CPU-only probe contract tests. Real Actor/model creation is never needed."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from participant.research.action_encoding import array_to_named

SOURCE = Path(__file__).resolve().parents[1]/'scripts/probe_action_encoding.py'
SPEC = importlib.util.spec_from_file_location('probe_action_encoding', SOURCE)
probe = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(probe)


class ProbeTest(unittest.TestCase):
    def test_fixed_four_slots_model_and_timeout(self):
        plan = probe.plan()
        self.assertEqual(plan['order'], ['array', 'named', 'named', 'array'])
        self.assertEqual((plan['model'], plan['effort'], plan['timeout_s']), ('gpt-6-astra', 'ultra', 90))
        self.assertEqual(plan['maximum_invoke_attempts'], 4)
        self.assertFalse(plan['simulation_action_dispatch'])

    def test_both_schemas_are_closed_and_have_exact_array_lengths(self):
        for encoding in ('array', 'named'):
            schema = probe.schema_for(encoding)
            self.assertFalse(schema['additionalProperties'])
            self.assertEqual(set(schema['required']), set(schema['properties']))
            values = next(iter(schema['properties'].values()))
            self.assertEqual((values['minItems'], values['maxItems']), (2, 2))
        named = probe.schema_for('named')['properties']['robots']['items']
        self.assertFalse(named['additionalProperties'])
        self.assertEqual(len(named['properties']['action']['required']), 9)
        self.assertFalse(named['properties']['action']['additionalProperties'])

    def test_expected_responses_pass_and_wrong_roll_is_not_corrected(self):
        action = probe.EXPECTED.tolist()
        self.assertTrue(probe.validate_response('array', {'action': action})[1])
        self.assertTrue(probe.validate_response('named', array_to_named(action))[1])
        action[1][7] = 1
        observed, matched = probe.validate_response('array', {'action': action})
        self.assertFalse(matched); self.assertEqual(observed[1, 7], 1)
        with self.assertRaises(ValueError): probe.validate_response('array', {'action': action, 'reason': 'extra'})
        action[0][0] = True
        with self.assertRaises(ValueError): probe.validate_response('array', {'action': action})

    def test_four_fresh_actors_cleanup_and_no_retry_for_wrong_response(self):
        created = []
        class FakeActor:
            def __init__(self, root, **kwargs):
                self.root = root; self.codex_home = root/'codex_home'; self.codex_home.mkdir(parents=True)
                (self.codex_home/'auth.json').write_text('synthetic credential fixture')
                self.session_id = None; self.calls = 0; self._closed = False
                self._network_created = True; self._proxy_created = True; self._active_container = None
                self.index = len(created); created.append(self)
            def invoke(self, prompt, images, schema):
                self.calls += 1; self.session_id = f'synthetic-thread-{self.index}'
                self.image_bytes = images[0].read_bytes()
                action = probe.EXPECTED.tolist()
                if self.index == 1: action[1][7] = 1
                decision = {'action': action} if 'action' in schema['properties'] else array_to_named(action)
                return {'decision': decision, 'session_id': self.session_id, 'wall_s': .1,
                        'usage': {'input_tokens': 1, 'output_tokens': 1}, 'cli_version': 'synthetic'}
            def close(self):
                (self.codex_home/'auth.json').unlink(); self._closed = True
                self._network_created = self._proxy_created = False
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp)/'probe'
            result = probe.run_probe(output, actor_factory=FakeActor)
            self.assertEqual(result['invoke_attempts'], 4)
            self.assertEqual(result['exact_matches'], 3)
            self.assertEqual(len({a.root for a in created}), 4)
            self.assertTrue(all(a.calls == 1 and a._closed for a in created))
            self.assertTrue(all(a.image_bytes == created[0].image_bytes for a in created))
            self.assertTrue(result['distinct_completed_threads'])
            self.assertNotIn('synthetic-thread-', json.dumps(result))
            self.assertEqual(result['actions_dispatched'], 0)
            with self.assertRaises(ValueError): probe.run_probe(output, actor_factory=FakeActor)


if __name__ == '__main__':
    unittest.main()
