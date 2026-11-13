"""Suffix plans fail closed against incomplete/tampered originals and preserve lineage."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from participant.collection.boundary import CONTRACT
from participant.collection.retry_plan import build_plan, write_plan
from participant.collection.validate_capture import validate_capture
from Policy.training_dataset import DatasetWriter


class RetryPlanTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.run = 'closed-parent'
        self.capture = self.root / 'output/collections' / self.run
        trace = self.root / 'output/operator-traces' / self.run
        trace.mkdir(parents=True)
        contract = copy.deepcopy(CONTRACT)
        contract['default_dimensions'].update(height=16, width=16)
        dims = contract['default_dimensions']
        def observation(t, action):
            values = {key: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
                      for key, spec in contract['observations'].items()}
            values['simulation_time_s'] = np.asarray(t, np.float64)
            values['previous_action'] = action.copy()
            return values
        writer = DatasetWriter(self.capture, contract, {'source': 'gpt', 'raw_archive': False})
        writer.start_episode({'operator_source': 'gpt', 'source_group': 'family'})
        action = np.zeros((2, 9), np.float32)
        for index in range(3):
            writer.append(observation(index * .05, action), action,
                          observation((index + 1) * .05, action),
                          start_tick=index * 12, end_tick=(index + 1) * 12, audit={})
        writer.finish_episode('fixture'); writer.close()
        (trace / 'attempt.json').write_text(json.dumps({
            'run_id': self.run, 'finished': True, 'capture_complete': True,
            'status': 'review_ready', 'simulation_steps': 3, 'source_group': 'family'}))
        (self.capture / 'capture.json').write_text(json.dumps({
            'complete': True, 'raw_archive': False, 'steps': 3, 'files': {
                name: hashlib.sha256((self.capture / name).read_bytes()).hexdigest()
                for name in ('policy.hdf5', 'audit.hdf5')}}))
        (self.capture / 'validation.json').write_text(json.dumps(validate_capture(self.capture)))
        (self.capture / 'run_metadata.json').write_text(json.dumps({
            'source_group': 'family', 'episode_seed': 8675309}))

    def plan(self):
        return build_plan(self.root, self.run, 2, reason='Keep support; change opening angle only')

    def test_boundary_lineage_and_seed_isolation(self):
        result = self.plan()
        self.assertEqual(result['boundary']['source_observation_index'], 1)
        self.assertEqual(result['boundary']['source_remaining_steps'], 1)
        self.assertEqual(result['lineage']['parent_attempt'], self.run)
        self.assertEqual(result['lineage']['source_group'], 'family')
        self.assertFalse(result['actor_receives_plan'])
        self.assertFalse(result['limitations']['bitwise_physics_restored'])
        self.assertNotIn('8675309', json.dumps(result))
        self.assertEqual(result['continuation_arguments'][0:4],
                         ['--replay-prefix-run', self.run, '--replay-prefix-steps', '2'])

    def test_no_source_mutation_and_immutable_output(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.capture.rglob('*') if p.is_file()}
        path = write_plan(self.root, 'new-branch', self.plan())
        self.assertEqual(path.parent, self.root / 'output/retry-plans')
        with self.assertRaises(FileExistsError):
            write_plan(self.root, 'new-branch', self.plan())
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before})
        with self.assertRaises(ValueError):
            write_plan(self.root, '../original', {})

    def test_incomplete_stale_hash_and_invalid_boundary_rejected(self):
        for boundary in (None, True, 0, -1, 4):
            with self.subTest(boundary=boundary), self.assertRaises(ValueError):
                build_plan(self.root, self.run, boundary, reason='review')
        path = self.capture / 'capture.json'
        original = path.read_text()
        value = json.loads(original); value['complete'] = False
        path.write_text(json.dumps(value))
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            self.plan()
        path.write_text(original)
        with (self.capture / 'policy.hdf5').open('ab') as stream:
            stream.write(b'tampered')
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            self.plan()

    def test_symlink_output_rejected(self):
        outside = self.root / 'elsewhere'; outside.mkdir()
        (self.root / 'output/retry-plans').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            write_plan(self.root, 'new-branch', self.plan())
        self.assertEqual(list(outside.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
