"""B1b RGB-only candidate selection, abstention and depth uncertainty tests."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from participant.research.color_depth_roi import (ColorRules, color_candidates,
                                                 analyze_rgbd, export_saved_pilot)
from participant.research.depth_backprojection import CAMERAS


def image_fixture():
    rgb=np.full((48,64,3),210,np.uint8)
    rgb[10:35,10:50]=[15,20,230]
    rgb[30:35,10:50]=[240,230,20]
    return rgb


class ColorDepthTest(unittest.TestCase):
    def setUp(self):
        self.rgb=image_fixture()
        self.depth=np.ones((48,64),np.float32)
        self.valid=np.ones((48,64),bool)
        self.k=[[40,0,32],[0,40,24],[0,0,1]]

    def test_original_yellow_candidates_are_distinct_and_ordered(self):
        result=color_candidates(self.rgb)
        self.assertEqual(result['status'],'two_color_candidates')
        left,right=result['candidates']
        self.assertLess(left['pixel_uv'][0],right['pixel_uv'][0])
        for candidate in result['candidates']:
            u,v=candidate['pixel_uv']
            np.testing.assert_array_equal(self.rgb[v,u],[240,230,20])
            self.assertEqual(candidate['yellow_3x3_support_pixels'],9)
            self.assertFalse(candidate['grasp_point_validated'])
        self.assertFalse(result['two_gripper_grasp_success_evaluated'])

    def test_larger_yellow_only_distractor_is_not_eligible(self):
        rgb=np.full((90,120,3),210,np.uint8)
        rgb[10:35,10:50]=[15,20,230];rgb[30:35,10:50]=[240,230,20]
        rgb[10:80,70:115]=[240,230,20]
        result=color_candidates(rgb)
        self.assertEqual(result['eligible_components'],1)
        self.assertLess(result['selected_component']['bbox_xyxy_exclusive'][2],70)

    def test_missing_colors_and_tiny_noise_abstain(self):
        gray=np.full_like(self.rgb,200)
        self.assertEqual(color_candidates(gray)['status'],'no_supported_color_component')
        gray[1:3,1:3]=[15,20,230]
        self.assertEqual(color_candidates(gray)['status'],'no_supported_color_component')
        blue=self.rgb.copy();blue[30:35,10:50]=[15,20,230]
        self.assertEqual(color_candidates(blue)['status'],'insufficient_yellow_pixels')

    def test_uint8_channel_subtraction_does_not_wrap_into_false_blue(self):
        red=np.zeros_like(self.rgb);red[:]=[250,0,130]
        self.assertEqual(color_candidates(red)['status'],'no_supported_color_component')

    def test_linked_roi_never_selects_dilated_background_pixels(self):
        rgb=self.rgb.copy();rgb[29]=[210,210,210]
        result=color_candidates(rgb)
        self.assertEqual(result['status'],'two_color_candidates')
        for candidate in result['candidates']:
            u,v=candidate['pixel_uv'];np.testing.assert_array_equal(rgb[v,u],[240,230,20])

    def test_narrow_yellow_patch_does_not_invent_two_sides(self):
        rgb=self.rgb.copy();rgb[30:35,10:50]=[15,20,230];rgb[15:30,20:22]=[240,230,20]
        result=color_candidates(rgb)
        self.assertEqual(result['status'],'insufficient_horizontal_separation')
        self.assertEqual(result['candidates'],[])

    def test_occlusion_can_leave_both_candidates_on_one_fragment(self):
        rgb=self.rgb.copy();rgb[:,30:35]=[210,210,210]
        result=color_candidates(rgb)
        self.assertEqual(result['eligible_components'],2)
        self.assertTrue(all(c['pixel_uv'][0] < 30 for c in result['candidates']))
        self.assertFalse(result['physical_edge_validated'])
        self.assertFalse(result['two_gripper_grasp_success_evaluated'])

    def test_depth_does_not_change_rgb_selection_and_invalid_is_null(self):
        before=color_candidates(self.rgb)
        u,v=before['candidates'][0]['pixel_uv'];self.valid[v,u]=False
        self.depth[:]=2.
        after=analyze_rgbd(self.rgb,self.depth,self.valid,self.k)
        self.assertEqual([c['pixel_uv'] for c in before['candidates']],
                         [c['pixel_uv'] for c in after['candidates']])
        self.assertIsNone(after['candidates'][0]['depth_probe']['camera_xyz_m'])
        self.assertFalse(after['candidates'][0]['depth_probe']['neighbor_depth_substituted'])
        self.assertIsNotNone(after['candidates'][1]['depth_probe']['camera_xyz_m'])

    def test_depth_discontinuity_remains_flagged_at_selected_color_point(self):
        selected=color_candidates(self.rgb)['candidates'][0]['pixel_uv'];u,v=selected
        self.depth[v-2:v+3,u+1:u+3]=2.
        result=analyze_rgbd(self.rgb,self.depth,self.valid,self.k)
        probe=result['candidates'][0]['depth_probe']
        self.assertIn('patch_depth_range_exceeds_threshold',probe['uncertainty']['flags'])
        self.assertEqual(probe['status'],'review_required')
        self.assertFalse(result['cross_frame_correspondence_established'])


class ColorDepthExportTest(unittest.TestCase):
    def test_malformed_clock_is_rejected_without_exporting_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);run='malformed-clock-fixture';capture=root/'output/collections'/run
            obs=root/'output/actors'/run/'observations/00000';capture.mkdir(parents=True);obs.mkdir(parents=True)
            write=lambda p,v:p.write_text(json.dumps(v))
            write(capture/'capture.json',{'complete':True})
            k=[[40,0,32],[0,40,24],[0,0,1]]
            write(capture/'run_metadata.json',{'public_interface':{'camera_intrinsics':{c:k for c in CAMERAS},
                'camera_calibration':[{'id':c,'intrinsics':k,'resolution_wh':[64,48]} for c in CAMERAS]}})
            depth=np.ones((5,48,64,1),np.float32)
            np.savez_compressed(obs/'public_depth.npz',depth=depth,depth_valid=np.ones_like(depth,bool))
            Image.fromarray(image_fixture()).save(obs/'robot_0_head.png')
            bad_clocks=({'unexpected_payload':'CLOCK_CANARY'},['CLOCK_CANARY'],'CLOCK_CANARY',
                        True,None,float('nan'),float('inf'))
            for index,clock in enumerate(bad_clocks):
                with self.subTest(clock=repr(clock)):
                    write(obs/'observation.json',{'rgb_image_order':list(CAMERAS),
                        'public_robot_observation':{'simulation_time_s':clock}})
                    output=root/f'rejected-{index}'
                    with self.assertRaisesRegex(ValueError,'Invalid public observation clock'):
                        export_saved_pilot(root,run,[(0,'robot_0_head')],output)
                    self.assertFalse(output.exists())

    def test_saved_export_uses_only_public_fields_and_preserves_original_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);run='closed-color-fixture';capture=root/'output/collections'/run
            obs=root/'output/actors'/run/'observations/00000';capture.mkdir(parents=True);obs.mkdir(parents=True)
            write=lambda p,v:p.write_text(json.dumps(v))
            write(capture/'capture.json',{'complete':True})
            k=[[40,0,32],[0,40,24],[0,0,1]]
            write(capture/'run_metadata.json',{'episode_seed':33221199667788,'geometry':'FORBIDDEN_GEOMETRY',
                'public_interface':{'camera_intrinsics':{c:k for c in CAMERAS},
                    'camera_calibration':[{'id':c,'intrinsics':k,'resolution_wh':[64,48]} for c in CAMERAS]}})
            write(obs/'observation.json',{'rgb_image_order':list(CAMERAS),'public_robot_observation':{'simulation_time_s':1.5}})
            depth=np.ones((5,48,64,1),np.float32);np.savez_compressed(obs/'public_depth.npz',depth=depth,depth_valid=np.ones_like(depth,bool))
            image=obs/'robot_0_head.png';Image.fromarray(image_fixture()).save(image)
            output=root/'new-result';report=export_saved_pilot(root,run,[(0,'robot_0_head')],output)
            self.assertEqual((output/'obs00000-robot_0_head.png').read_bytes(),image.read_bytes())
            svg=(output/'obs00000-robot_0_head-annotation.svg').read_text()
            self.assertIn('data:image/png;base64,',svg)
            self.assertIn('Not verified edges, grasps or tracked points',svg)
            text=json.dumps(report,allow_nan=False)
            for bad in ('episode_seed','33221199667788','FORBIDDEN_GEOMETRY',str(root)):
                self.assertNotIn(bad,text)
            self.assertEqual(report['model_calls'],0)
            self.assertFalse(report['sent_to_actor'])
            with self.assertRaisesRegex(ValueError,'already exists'):
                export_saved_pilot(root,run,[(0,'robot_0_head')],output)


if __name__=='__main__':unittest.main()
