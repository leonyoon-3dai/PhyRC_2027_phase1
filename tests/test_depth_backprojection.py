"""Offline geometry/uncertainty checks, including privileged-metadata canaries."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

from participant.research.depth_backprojection import (CAMERAS, analyze_pixel,
                                                       analyze_saved_observations)


class DepthGeometryTest(unittest.TestCase):
    def setUp(self):
        self.k = np.array([[4., 0., 2.], [0., 8., 2.], [0., 0., 1.]])
        self.depth = np.full((5, 5), 2., np.float32)
        self.mask = np.ones((5, 5), bool)

    def test_off_center_optical_z_and_axis_convention(self):
        result = analyze_pixel(self.depth, self.mask, self.k, [4, 0], patch_radius=0)
        np.testing.assert_allclose(result['camera_xyz_m'], [1., -.5, 2.])
        self.assertGreater(np.linalg.norm(result['camera_xyz_m']), result['depth_sample_m'])
        self.assertLess(result['reprojection_roundtrip_error_px'], 1e-12)
        self.assertFalse(result['roundtrip_is_accuracy_validation'])
        self.assertIsNone(result['world_xyz_m'])

    def test_skew_intrinsics_are_inverted_without_ignoring_cross_term(self):
        self.k[0, 1] = 2.
        result = analyze_pixel(self.depth, self.mask, self.k, [4, 4], patch_radius=0)
        np.testing.assert_allclose(result['camera_xyz_m'], [.75, .5, 2.])

    def test_invalid_center_is_not_replaced_with_valid_neighbors(self):
        self.mask[2, 2] = False
        result = analyze_pixel(self.depth, self.mask, self.k, [2, 2])
        self.assertEqual(result['status'], 'invalid')
        self.assertIsNone(result['camera_xyz_m'])
        self.assertFalse(result['neighbor_depth_substituted'])
        self.assertEqual(result['uncertainty']['median_depth_m'], 2.)
        self.assertEqual(result['uncertainty']['valid_pixels'], 24)
        self.assertIn('center_mask_invalid', result['uncertainty']['flags'])

    def test_depth_step_flags_boundary_and_preserves_center_value(self):
        self.depth[:, 3:] = 4.
        result = analyze_pixel(self.depth, self.mask, self.k, [2, 2])
        self.assertEqual(result['status'], 'review_required')
        self.assertEqual(result['camera_xyz_m'], [0., 0., 2.])
        stats = result['uncertainty']
        self.assertEqual(stats['median_depth_m'], 2.)
        self.assertEqual(stats['median_absolute_deviation_m'], 0.)
        self.assertEqual(stats['depth_range_m'], 2.)
        self.assertIn('patch_depth_range_exceeds_threshold', stats['flags'])

    def test_mad_and_low_valid_fraction_are_explicit(self):
        self.depth[:] = np.arange(1, 26, dtype=np.float32).reshape(5, 5)
        full = analyze_pixel(self.depth, self.mask, self.k, [2, 2])
        self.assertEqual(full['uncertainty']['median_depth_m'], 13.)
        self.assertEqual(full['uncertainty']['median_absolute_deviation_m'], 6.)
        self.mask[:] = False; self.mask[2, 2] = True
        sparse = analyze_pixel(self.depth, self.mask, self.k, [2, 2])
        self.assertEqual(sparse['uncertainty']['valid_fraction'], 1/25)
        self.assertIn('low_patch_valid_fraction', sparse['uncertainty']['flags'])
        self.assertTrue(sparse['center_valid'])

    def test_nonfinite_nonpositive_and_empty_patch_remain_json_safe(self):
        for bad in (float('nan'), float('inf'), 0., -1.):
            with self.subTest(depth=bad):
                self.depth[:] = bad
                result = analyze_pixel(self.depth, self.mask, self.k, [2, 2])
                self.assertEqual(result['status'], 'invalid')
                self.assertIsNone(result['camera_xyz_m'])
                self.assertIsNone(result['uncertainty']['median_depth_m'])
                self.assertEqual(result['uncertainty']['mask_numeric_inconsistency_count'], 25)
                json.dumps(result, allow_nan=False)

    def test_edge_patch_and_row_column_rgb_sampling(self):
        rgb = np.zeros((5, 5, 3), np.uint8); rgb[1, 4] = [11, 22, 33]
        result = analyze_pixel(self.depth, self.mask, self.k, [4, 1], rgb=rgb, patch_radius=2)
        self.assertEqual(result['rgb_uint8'], [11, 22, 33])
        self.assertEqual(result['uncertainty']['patch_bounds_xyxy_exclusive'], [2, 0, 5, 4])
        self.assertEqual(result['uncertainty']['patch_pixels'], 12)
        self.assertIn('patch_truncated_at_image_edge', result['uncertainty']['flags'])

    def test_bad_calibration_pixel_and_shape_rejected(self):
        for matrix in (np.zeros((3,3)), np.eye(4), [[1,0,0],[0,1,0],[0,1,1]]):
            with self.assertRaises(ValueError): analyze_pixel(self.depth, self.mask, matrix, [2,2])
        for pixel in ([-1,2], [5,2], [True,2], [1.5,2]):
            with self.assertRaises(ValueError): analyze_pixel(self.depth, self.mask, self.k, pixel)
        with self.assertRaises(ValueError): analyze_pixel(self.depth, self.mask[:, :3], self.k, [2,2])


class SavedDepthPilotTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.run = 'closed-public-fixture'
        self.capture = self.root/'output/collections'/self.run
        self.obs = self.root/'output/actors'/self.run/'observations/00000'
        self.capture.mkdir(parents=True); self.obs.mkdir(parents=True)
        self.write(self.capture/'capture.json', {'complete': True})
        k = [[4.,0.,3.],[0.,4.,2.],[0.,0.,1.]]
        self.metadata = {'episode_seed': 33221199667788, 'private_geometry': 'GEOMETRY_CANARY',
            'public_interface': {'camera_intrinsics': {c:k for c in CAMERAS},
            'camera_calibration': [{'id':c,'resolution_wh':[6,4],'intrinsics':k,
                                   'hidden_object_pose':'FORBIDDEN_CANARY'} for c in CAMERAS]}}
        self.write(self.capture/'run_metadata.json', self.metadata)
        self.write(self.obs/'observation.json', {'rgb_image_order':list(CAMERAS),
            'public_robot_observation':{'simulation_time_s':1.5},'unused':'PRIVATE_CANARY'})
        depth=np.ones((5,4,6,1),np.float32);valid=np.ones_like(depth,bool)
        valid[1,2,3,0]=False
        np.savez_compressed(self.obs/'public_depth.npz',depth=depth,depth_valid=valid)
        for camera in CAMERAS:Image.fromarray(np.zeros((4,6,3),np.uint8)).save(self.obs/(camera+'.png'))

    @staticmethod
    def write(path,value):path.write_text(json.dumps(value))

    def test_saved_public_inputs_only_and_unknown_semantics(self):
        result=analyze_saved_observations(self.root,self.run,[0],patch_radius=1)
        self.assertEqual(len(result['samples']),5)
        self.assertIsNone(result['samples'][1]['camera_xyz_m'])
        self.assertEqual(result['samples'][0]['pixel_uv'],[3,2])
        self.assertFalse(result['sent_to_actor']);self.assertFalse(result['pose_detector_used'])
        text=json.dumps(result,allow_nan=False)
        for bad in ('33221199667788','episode_seed','GEOMETRY_CANARY','FORBIDDEN_CANARY','PRIVATE_CANARY',str(self.root)):
            self.assertNotIn(bad,text)

    def test_mismatched_public_calibration_and_live_capture_rejected(self):
        self.metadata['public_interface']['camera_calibration'][0]['intrinsics'][0][0]=5.
        # Distinct matrices are needed because the fixture originally shares k.
        self.metadata['public_interface']['camera_intrinsics'][CAMERAS[0]]=[[4.,0.,3.],[0.,4.,2.],[0.,0.,1.]]
        self.write(self.capture/'run_metadata.json',self.metadata)
        with self.assertRaisesRegex(ValueError,'disagree'):analyze_saved_observations(self.root,self.run,[0])
        self.write(self.capture/'capture.json',{'complete':False})
        with self.assertRaisesRegex(ValueError,'closed'):analyze_saved_observations(self.root,self.run,[0])

    def test_cli_refuses_existing_output_before_analysis(self):
        output=self.root/'existing.json';output.write_text('keep original')
        result=subprocess.run([sys.executable,'-m','participant.research.depth_backprojection',
            '--root',str(self.root),'--run-id',self.run,'--output',str(output)],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(output.read_text(),'keep original')
        self.assertIn('already exists',result.stderr)


if __name__=='__main__':unittest.main()
