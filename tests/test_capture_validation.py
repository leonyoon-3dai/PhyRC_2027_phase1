"""Corruption injection tests for full capture QC; no GPU or model required."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import h5py
import numpy as np

from participant.collection.boundary import CONTRACT
from participant.collection.validate_capture import sha256, validate_capture
from Policy.training_dataset import DatasetWriter


def make_capture(path, *, result=None):
    contract = copy.deepcopy(CONTRACT)
    contract['default_dimensions'].update(height=16, width=16)
    dims = contract['default_dimensions']
    def observation(t, previous):
        values = {name: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
                  for name, spec in contract['observations'].items()}
        values['simulation_time_s'] = np.asarray(t, np.float64)
        values['previous_action'] = previous.copy()
        values['rgb'][0] = int(t * 100)
        return values
    action = np.zeros((2, 9), np.float32)
    writer = DatasetWriter(path, contract, {'source': 'integration_test', 'raw_archive': False})
    writer.start_episode({'operator_source': 'integration_test', 'source_group': 'qc_fixture', 'model_id': 'unit-test'})
    before = observation(0, action)
    for i in range(2):
        action = action.copy(); action[:, 3] += .01
        after = observation((i + 1) * .05, action)
        writer.append(before, action, after, start_tick=i * 12, end_tick=(i + 1) * 12, audit={})
        before = after
    writer.finish_episode('test_done', result=result)
    writer.close()
    update_checksums(path)


def update_checksums(path):
    (path / 'capture.json').write_text(json.dumps({'complete': True, 'raw_archive': False, 'episodes': 1,
                                                'files': {name: sha256(path / name) for name in ('policy.hdf5', 'audit.hdf5')}}))


class CaptureValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'capture'

    def test_full_capture_checks_across_batch_boundary(self):
        make_capture(self.path)
        report = validate_capture(self.path, batch_size=1)
        self.assertTrue(report['quality_passed'], report['errors'])
        self.assertEqual(report['total_transitions'], 2)
        episode = report['episodes'][0]
        self.assertEqual(episode['source']['source_group'], 'qc_fixture')
        self.assertEqual(episode['simulation_seconds'], .1)
        self.assertIsNone(episode['evaluation']['raw_points'])
        self.assertIsNone(episode['evaluation']['dressing_success'])
        self.assertFalse(episode['evaluation']['evaluated'])
        self.assertEqual(report['training_approval'], 'unreviewed')

    def test_valid_no_contact_and_invalid_evaluations_stay_distinct(self):
        for valid in (True, False):
            with self.subTest(valid=valid):
                path = self.path.with_name('capture_' + str(valid))
                result = {'valid': valid, 'reason': 'test', 'result': {
                    'raw_points': 0, 'success': False, 'success_evaluated': True,
                    'score_status': 'no_contact', 'final_score': None}}
                make_capture(path, result=result)
                report = validate_capture(path)
                self.assertTrue(report['quality_passed'], report['errors'])
                score = report['episodes'][0]['evaluation']
                self.assertTrue(score['evaluated'])
                self.assertEqual(score['valid'], valid)
                self.assertEqual(score['raw_points'], 0 if valid else None)
                self.assertEqual(score['dressing_success'], False if valid else None)
                self.assertIsNone(score['final_score_points_per_s'])

    def test_tamper_hash_is_detected_even_if_values_remain_valid(self):
        make_capture(self.path)
        with h5py.File(self.path / 'policy.hdf5', 'r+') as policy:
            policy.attrs['extra'] = 'changed'
        report = validate_capture(self.path)
        self.assertFalse(report['quality_passed'])
        self.assertIn('SHA256 mismatch: policy.hdf5', report['errors'])

    def test_corrupt_transition_fields_are_detected_after_rehash(self):
        mutations = [
            ('policy', 'data/demo_0/obs/joint_position', (1, 0), .5, 'continuity'),
            ('policy', 'data/demo_0/next_obs/previous_action', (1, 0), .2, 'previous_action'),
            ('policy', 'data/demo_0/next_obs/simulation_time_s', (1, 0), .101, 'duration'),
            ('policy', 'data/demo_0/actions', (1, 0), float('nan'), 'non-finite'),
            ('policy', 'data/demo_0/dones', (0,), 1, 'dones'),
            ('audit', 'demo_0/start_tick', (1,), 13, 'physics ticks'),
        ]
        for index, (file, field, position, value, message) in enumerate(mutations):
            with self.subTest(field=field):
                path = self.path.with_name('mutation_' + str(index)); make_capture(path)
                with h5py.File(path / (file + '.hdf5'), 'r+') as data:
                    data[field][position] = value
                update_checksums(path)
                report = validate_capture(path, batch_size=1)
                self.assertFalse(report['quality_passed'])
                self.assertTrue(any(message in error for error in report['errors']), report['errors'])
                self.assertEqual(report['total_transitions'], 2)
                self.assertEqual(report['validated_transitions'], 0)
                self.assertEqual(report['episodes'][0]['source']['source_group'], 'qc_fixture')

    def test_missing_camera_and_wrong_action_dtype_fail(self):
        for mutation in ('camera', 'dtype'):
            with self.subTest(mutation=mutation):
                path = self.path.with_name(mutation); make_capture(path)
                with h5py.File(path / 'policy.hdf5', 'r+') as data:
                    if mutation == 'camera':
                        del data['data/demo_0/obs/robot_1_head_rgb']
                    else:
                        values = data['data/demo_0/actions'][:].astype(np.float64)
                        del data['data/demo_0/actions']
                        data['data/demo_0'].create_dataset('actions', data=values)
                update_checksums(path)
                self.assertFalse(validate_capture(path)['quality_passed'])

    def test_incomplete_and_empty_evidence_are_not_approved(self):
        make_capture(self.path)
        with h5py.File(self.path / 'policy.hdf5', 'r+') as data:
            data.attrs['complete'] = False
            data['data/demo_0'].attrs['complete'] = False
        update_checksums(self.path)
        report = validate_capture(self.path)
        self.assertFalse(report['quality_passed'])
        self.assertTrue(any('incomplete' in error for error in report['errors']))
        missing = validate_capture(self.path / 'missing')
        self.assertFalse(missing['quality_passed'])


if __name__ == '__main__':
    unittest.main()
