"""Endpoint attribution and geometry tests; no model or simulator required."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from scripts.analyze_support_diagnostic import analyze


def observation(t):
    return {'simulation_time_s': t,
            'joint_position': [[0., .4, .02, -.02], [0., .4, .02, -.02]],
            'joint_velocity': [[0.] * 4, [0.] * 4],
            'base_pose_world': [[0., 0., 0., 1., 0., 0., 0.] for _ in range(2)],
            'grasp_pose_base': [[1., 0., .5, 1., 0., 0., 0.] for _ in range(2)],
            'fingertip_origin_distance': [[.04], [.04]],
            'controller_target': [[.4, 0., 0., 0., 0., .01, 0., 0., 0.] for _ in range(2)],
            'gripper_close_command': [[True], [True]],
            'cloth_world_positions': 'MUST_NOT_APPEAR'}


def segment(start, end, *, decision=0, source='model', motion=True):
    action = [[0.] * 9, [0.] * 9]
    if motion:
        action[0][3] = .2
    return {'type': 'applied_segment', 'decision_index': decision, 'action_source': source,
            'start_step': start, 'end_step': end, 'simulation_start_s': start / 20,
            'simulation_end_s': end / 20, 'applied_action': action,
            'stage_intent': 'lift', 'official_score': 'MUST_NOT_APPEAR'}


class SupportDiagnosticTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.obs = self.root / 'observations'
        self.obs.mkdir()
        self.decisions = self.root / 'decisions.jsonl'
        self.interface = self.root / 'interface.json'
        names = ['wheel', 'lift_joint', 'gripper_finger_left_joint', 'gripper_finger_right_joint']
        self.interface.write_text(json.dumps({'joint_names': [names, names],
                                             'joint_units': [['rad', 'm', 'rad', 'rad']] * 2}))
        # Invalid unrelated files prove the analyzer does not enumerate/read them.
        (self.root / 'audit.hdf5').write_text('not HDF5')
        (self.root / 'evaluation.json').write_text('not JSON')

    def save_obs(self, index, state):
        folder = self.obs / f'{index:05d}'
        folder.mkdir()
        (folder / 'observation.json').write_text(json.dumps({'public_robot_observation': state}))

    def run_report(self, segments, **kwargs):
        self.decisions.write_text('\n'.join(json.dumps(s) for s in segments) + '\n')
        return analyze(self.obs, self.decisions, **kwargs)

    def test_stationary_partner_drift_residual_and_settle_are_separate(self):
        a, b = observation(0.), copy.deepcopy(observation(.5))
        b['grasp_pose_base'][0][2] += .03
        b['base_pose_world'][1][0] = .002
        b['joint_position'][0][1] = .43
        b['controller_target'][0][0] = .45
        self.save_obs(0, a)
        self.save_obs(1, b)
        report = self.run_report([segment(0, 4), segment(4, 10, source='controller_settle', motion=False)],
                                 public_interface=self.interface)
        row = report['intervals'][0]
        self.assertTrue(row['includes_controller_settle'])
        self.assertEqual((row['start_boundary'], row['end_boundary']), (0, 10))
        self.assertEqual(row['commanded_stationary_robots'], [1])
        self.assertAlmostEqual(row['robots'][1]['base_world_delta_m'][0], .002)
        self.assertAlmostEqual(row['robots'][0]['after']['lift_target_minus_measured_m'], .02)
        self.assertIsNone(report['support_confirmed'])
        self.assertFalse(report['cloth_motion_measured'])
        self.assertNotIn('MUST_NOT_APPEAR', json.dumps(report))
        self.assertEqual(len(report['sources']['observations'][0]['sha256']), 64)

    def test_world_motion_accounts_for_base_rotation(self):
        a, b = observation(0.), copy.deepcopy(observation(.2))
        b['base_pose_world'][0] = [0., 0., 0., np.sqrt(.5), 0., 0., np.sqrt(.5)]
        self.save_obs(0, a)
        self.save_obs(1, b)
        row = self.run_report([segment(0, 4)])['intervals'][0]['robots'][0]
        np.testing.assert_allclose(row['grasp_world_delta_m'], [-1., 1., 0.], atol=1e-12)
        np.testing.assert_allclose(row['grasp_base_delta_m'], [0., 0., 0.])
        self.assertIsNone(row['after']['lift_measured_m'])

    def test_missing_final_snapshot_is_unknown_not_zero_motion(self):
        self.save_obs(0, observation(0.))
        report = self.run_report([segment(0, 4)])
        self.assertEqual(report['intervals'][0]['measurement_status'], 'missing_end_observation')
        self.assertNotIn('robots', report['intervals'][0])
        self.assertEqual(report['summary']['measured_intervals'], 0)

    def test_does_not_attribute_second_model_action_to_first(self):
        self.save_obs(0, observation(0.))
        self.save_obs(2, observation(.4))
        report = self.run_report([segment(0, 4), segment(4, 8, decision=1)])
        self.assertEqual(report['intervals'][0]['measurement_status'],
                         'end_observation_spans_other_or_unrecorded_actions')
        self.assertEqual(report['intervals'][1]['measurement_status'], 'missing_start_observation')

    def test_explicit_index_and_invalid_unit_or_quaternion(self):
        self.save_obs(0, observation(0.))
        self.save_obs(1, observation(.2))
        report = self.run_report([segment(0, 4)], lift_joint_index=1)
        self.assertEqual(report['joint_mapping'][0]['source'], 'explicit_cli_index')
        self.assertAlmostEqual(report['intervals'][0]['robots'][0]['after']['lift_measured_m'], .4)
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.run_report([segment(0, 4)], lift_joint_index=8)
        interface = json.loads(self.interface.read_text())
        interface['joint_units'][0][1] = 'rad'
        self.interface.write_text(json.dumps(interface))
        with self.assertRaisesRegex(ValueError, 'metres'):
            self.run_report([segment(0, 4)], public_interface=self.interface)
        path = self.obs / '00001/observation.json'
        data = json.loads(path.read_text())
        data['public_robot_observation']['base_pose_world'][0][3:] = [0.] * 4
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'zero base quaternion'):
            self.run_report([segment(0, 4)])

    def test_rejects_boundary_time_mismatch_and_discontinuous_segments(self):
        self.save_obs(0, observation(0.))
        self.save_obs(1, observation(.5))
        bad = segment(0, 4)
        bad['simulation_end_s'] = .9
        with self.assertRaisesRegex(ValueError, '20 Hz'):
            self.run_report([bad])
        with self.assertRaisesRegex(ValueError, 'not contiguous'):
            self.run_report([segment(0, 4), segment(5, 10, decision=1)])


if __name__ == '__main__':
    unittest.main()
