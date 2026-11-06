"""Trusted prefix validation and action-order preservation without a simulator."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import h5py
import numpy as np

from participant.collection.boundary import CONTRACT
from participant.collection.continuation import load_replay_prefix, iter_action_chunks
from participant.collection.validate_capture import validate_capture
from Policy.training_dataset import DatasetWriter


class ContinuationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.run = 'source-fixture'
        self.capture = self.root / 'output/collections' / self.run
        self.trace = self.root / 'output/operator-traces' / self.run
        self.trace.mkdir(parents=True)
        self.group = 'same-source-group'
        self.seed = 12345
        contract = copy.deepcopy(CONTRACT)
        contract['default_dimensions'].update(height=16, width=16)
        dims = contract['default_dimensions']
        def observation(t, action):
            value = {k: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
                     for k, spec in contract['observations'].items()}
            value['simulation_time_s'] = np.asarray(t, np.float64)
            value['previous_action'] = action.copy()
            value['joint_position'][:, 3] = t
            return value
        writer = DatasetWriter(self.capture, contract, {'source': 'gpt', 'raw_archive': False})
        writer.start_episode({'operator_source': 'gpt', 'source_group': self.group})
        a = np.zeros((2, 9), np.float32)
        before = observation(0, a)
        self.actions = []
        for i in range(3):
            a = a.copy(); a[0, 3] = .1 * (i + 1)
            after = observation((i + 1) * .05, a)
            writer.append(before, a, after, start_tick=i*12, end_tick=(i+1)*12, audit={})
            self.actions.append(a)
            before = after
        writer.finish_episode('fixture_finished'); writer.close()
        self.actions = np.asarray(self.actions)
        self.write(self.trace/'attempt.json', {'run_id': self.run, 'finished': True,
            'capture_complete': True, 'status': 'review_ready', 'simulation_steps': 3,
            'source_group': self.group})
        self.write(self.capture/'capture.json', {'complete': True, 'raw_archive': False, 'steps': 3, 'files': {
            name: self.hash(self.capture/name) for name in ('policy.hdf5', 'audit.hdf5')}})
        self.write(self.capture/'validation.json', validate_capture(self.capture))
        self.write(self.capture/'run_metadata.json', {'source_group': self.group})
        folder = self.capture/'evaluation'/'fixture'; folder.mkdir(parents=True)
        report = {'metadata': {'episode_seed': self.seed, 'source_group': self.group,
                              'internal_geometry': 'PRIVATE_GEOMETRY_CANARY'}}
        self.write(folder/'result.json', report)
        self.write(self.capture/'evaluation_summary.json', {'evaluation_path': 'evaluation/fixture', 'report': report})

    @staticmethod
    def hash(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value))

    def edit(self, relative, update):
        path = self.capture / relative
        value = json.loads(path.read_text()); update(value); self.write(path, value)

    def rehash_policy(self):
        digest = self.hash(self.capture/'policy.hdf5')
        self.edit('capture.json', lambda v: v['files'].update({'policy.hdf5': digest}))
        self.edit('validation.json', lambda v: v['sha256'].update({'policy.hdf5': digest}))

    def test_prefix_reads_only_policy_and_returns_selected_public_state(self):
        real_file = h5py.File
        opened = []
        def checked_file(path, *args, **kwargs):
            opened.append(Path(path).name)
            self.assertEqual(Path(path).name, 'policy.hdf5')
            self.assertEqual(args, ('r',))
            return real_file(path, *args, **kwargs)
        with patch('participant.collection.continuation.h5py.File', side_effect=checked_file):
            result = load_replay_prefix(self.root, self.run, steps=2)
        self.assertEqual(opened, ['policy.hdf5'])
        np.testing.assert_array_equal(result.actions, self.actions[:2])
        self.assertEqual(result.actions.dtype, np.float32)
        self.assertFalse(result.actions.flags.writeable)
        self.assertEqual(result.final_public_state['joint_position'].shape, (2, 13))
        self.assertAlmostEqual(float(result.final_public_state['simulation_time_s']), .1)
        self.assertEqual(result.trusted_metadata['reset_seed'], self.seed)
        self.assertEqual(result.trusted_metadata['seed_source']['json_field'], 'metadata.episode_seed')
        self.assertEqual(result.public_lineage['source_steps'], 3)
        self.assertEqual(result.public_lineage['source_end_step_exclusive'], 2)
        self.assertFalse(result.public_lineage['bitwise_physics_restored'])
        public = json.dumps(result.public_lineage) + repr(result)
        for excluded in ('12345', 'episode_seed', str(self.root), 'PRIVATE_GEOMETRY_CANARY'):
            self.assertNotIn(excluded, public)

    def test_default_includes_all_steps_and_existing_run_metadata_seed(self):
        self.edit('run_metadata.json', lambda v: v.update(episode_seed=self.seed))
        result = load_replay_prefix(self.root, self.run)
        np.testing.assert_array_equal(result.actions, self.actions)
        self.assertEqual(result.trusted_metadata['seed_source']['json_field'], 'episode_seed')

    def test_requires_completed_full_quality_validation(self):
        for field, value in [('quality_passed', False), ('validated_transitions', 2),
                             ('errors', ['continuity failure'])]:
            with self.subTest(field=field):
                original = (self.capture/'validation.json').read_text()
                self.edit('validation.json', lambda v: v.update({field: value}))
                with self.assertRaises(ValueError): load_replay_prefix(self.root, self.run)
                (self.capture/'validation.json').write_text(original)
        self.edit('capture.json', lambda v: v.update(complete=False))
        with self.assertRaisesRegex(ValueError, 'incomplete'): load_replay_prefix(self.root, self.run)

    def test_running_attempt_is_rejected_before_policy_open(self):
        self.write(self.trace/'attempt.json', {'run_id': self.run, 'finished': False,
                                              'capture_complete': False, 'status': 'collecting'})
        with patch('participant.collection.continuation.h5py.File') as opened:
            with self.assertRaisesRegex(ValueError, 'not finished'): load_replay_prefix(self.root, self.run)
            opened.assert_not_called()

    def test_tampered_policy_and_stale_validation_hash_are_rejected(self):
        with h5py.File(self.capture/'policy.hdf5', 'r+') as h: h.attrs['changed'] = True
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'): load_replay_prefix(self.root, self.run)
        digest = self.hash(self.capture/'policy.hdf5')
        self.edit('capture.json', lambda v: v['files'].update({'policy.hdf5': digest}))
        with self.assertRaisesRegex(ValueError, 'Validation policy checksum'): load_replay_prefix(self.root, self.run)

    def test_source_group_and_seed_reference_must_agree(self):
        self.edit('run_metadata.json', lambda v: v.update(source_group='different-group'))
        with self.assertRaisesRegex(ValueError, 'group'): load_replay_prefix(self.root, self.run)
        self.edit('run_metadata.json', lambda v: v.update(source_group=self.group))
        self.edit('evaluation_summary.json', lambda v: v['report']['metadata'].update(episode_seed=54321))
        with self.assertRaisesRegex(ValueError, 'disagrees'): load_replay_prefix(self.root, self.run)

    def test_run_seed_cannot_disagree_with_existing_evaluation(self):
        self.edit('run_metadata.json', lambda v: v.update(episode_seed=self.seed + 1))
        with self.assertRaisesRegex(ValueError, 'Run seed disagrees'):
            load_replay_prefix(self.root, self.run)

    def test_path_traversal_symlink_and_invalid_prefix_are_rejected(self):
        for run in ('../source-fixture', '/source-fixture', '..'):
            with self.assertRaises(ValueError): load_replay_prefix(self.root, run)
        for steps in (0, -1, True, 1.5, 4):
            with self.assertRaises(ValueError): load_replay_prefix(self.root, self.run, steps)
        self.edit('evaluation_summary.json', lambda v: v.update(evaluation_path='evaluation/../../outside'))
        with self.assertRaises(ValueError): load_replay_prefix(self.root, self.run)
        policy = self.capture/'policy.hdf5'
        moved = self.root/'moved-policy.hdf5'; policy.rename(moved); policy.symlink_to(moved)
        with self.assertRaisesRegex(ValueError, 'Symlink'): load_replay_prefix(self.root, self.run)

    def test_incomplete_policy_and_wrong_action_dtype_fail_even_with_updated_hash(self):
        with h5py.File(self.capture/'policy.hdf5', 'r+') as h: h.attrs['complete'] = False
        self.rehash_policy()
        with self.assertRaisesRegex(ValueError, 'incomplete'): load_replay_prefix(self.root, self.run)
        with h5py.File(self.capture/'policy.hdf5', 'r+') as h:
            h.attrs['complete'] = True
            e = h['data/demo_0']; values = e['actions'][:].astype(np.float64)
            del e['actions']; e.create_dataset('actions', data=values)
        self.rehash_policy()
        with self.assertRaisesRegex(ValueError, 'float32'): load_replay_prefix(self.root, self.run)

    def test_chunks_preserve_every_original_float_and_boundary(self):
        a = np.zeros((45, 2, 9), np.float32)
        a[22:44, 0, 3] = .125
        a[44, 1, 8] = -1
        chunks = list(iter_action_chunks(a))
        self.assertEqual([(c.start_step, c.end_step) for c in chunks], [(0,20),(20,22),(22,42),(42,44),(44,45)])
        rebuilt = np.concatenate([np.repeat(c.action[None], c.steps, axis=0) for c in chunks])
        self.assertEqual(rebuilt.tobytes(), a.tobytes())
        for value in (0,21,True):
            with self.assertRaises(ValueError): list(iter_action_chunks(a, value))
        a[0, 0, 0] = np.nan
        with self.assertRaises(ValueError): list(iter_action_chunks(a))


if __name__ == '__main__':
    unittest.main()
