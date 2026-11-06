"""B1c pair placement and explicit abstention; no cloth/grasp ground truth."""
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image

from participant.research.color_depth_roi import analyze_rgbd
from participant.research.color_pair_comparison import compare_methods, export_comparison
from participant.research.depth_backprojection import CAMERAS


def fixture():
    rgb=np.full((48,64,3),210,np.uint8)
    rgb[10:35,10:50]=[15,20,230];rgb[30:35,10:50]=[240,230,20]
    return rgb,np.ones((48,64),np.float32),np.ones((48,64),bool),[[40,0,32],[0,40,24],[0,0,1]]


class PairComparisonTest(unittest.TestCase):
    def test_A_keeps_original_candidate_and_depth_outputs(self):
        rgb,depth,valid,k=fixture()
        expected=analyze_rgbd(rgb,depth,valid,k)
        actual=compare_methods(rgb,depth,valid,k)
        self.assertEqual(actual['methods']['A']['proposed_candidates'],expected['candidates'])

    def test_split_fragment_regression_B_spreads_C_abstains(self):
        rgb,depth,valid,k=fixture();rgb[:,30:35]=210
        result=compare_methods(rgb,depth,valid,k);a,b,c=[result['methods'][key]for key in 'ABC']
        self.assertEqual(len(result['context']['components']),2)
        self.assertTrue(a['diagnostics']['both_on_one_fragment_while_other_components_exist'])
        self.assertTrue(all(p['pixel_uv'][0]<30 for p in a['emitted_candidates']))
        self.assertTrue(b['emits_pair'])
        self.assertLess(b['emitted_candidates'][0]['pixel_uv'][0],30)
        self.assertGreaterEqual(b['emitted_candidates'][1]['pixel_uv'][0],35)
        self.assertFalse(c['emits_pair']);self.assertEqual(c['emitted_candidates'],[])
        self.assertEqual(len(c['proposed_candidates']),2)
        self.assertIn('multiple_color_components_semantically_ambiguous',c['abstention_reasons'])

    def test_one_component_good_depth_emits_candidates_without_grasp_approval(self):
        result=compare_methods(*fixture())
        for method in result['methods'].values():
            self.assertTrue(method['emits_pair'])
            self.assertFalse(method['cloth_edge_or_grasp_approved'])
        self.assertFalse(result['cross_frame_correspondence_established'])

    def test_blue_only_other_fragment_cannot_be_ignored_for_pair_coverage(self):
        rgb,depth,valid,k=fixture();rgb[:,30:35]=210;rgb[30:35,35:50]=[15,20,230]
        result=compare_methods(rgb,depth,valid,k)
        c=result['methods']['C']
        self.assertIn('both_candidates_on_same_fragment_with_other_components_present',c['abstention_reasons'])
        self.assertIn('insufficient_image_horizontal_separation',c['abstention_reasons'])
        self.assertEqual(c['emitted_candidates'],[])

    def test_depth_edge_blocks_C_but_does_not_move_RGB_candidates(self):
        rgb,depth,valid,k=fixture();before=compare_methods(rgb,depth,valid,k)
        u,v=before['methods']['B']['proposed_candidates'][0]['pixel_uv']
        depth[v-2:v+3,u+1:u+3]=2.
        result=compare_methods(rgb,depth,valid,k)
        self.assertTrue(result['methods']['B']['emits_pair'])
        self.assertEqual([c['pixel_uv']for c in before['methods']['B']['proposed_candidates']],
                         [c['pixel_uv']for c in result['methods']['B']['proposed_candidates']])
        self.assertFalse(result['methods']['C']['emits_pair'])
        self.assertIn('image_left_depth_patch_requires_review',result['methods']['C']['abstention_reasons'])

    def test_invalid_depth_is_preserved_and_C_emits_no_pair(self):
        rgb,depth,valid,k=fixture();before=compare_methods(rgb,depth,valid,k)
        u,v=before['methods']['B']['proposed_candidates'][1]['pixel_uv'];valid[v,u]=False
        result=compare_methods(rgb,depth,valid,k);c=result['methods']['C']
        self.assertIsNone(c['proposed_candidates'][1]['depth_probe']['camera_xyz_m'])
        self.assertEqual(c['emitted_candidates'],[])
        self.assertIn('image_right_depth_invalid',c['abstention_reasons'])

    def test_empty_color_image_abstains_for_every_method(self):
        rgb,depth,valid,k=fixture();rgb[:]=210
        result=compare_methods(rgb,depth,valid,k)
        self.assertTrue(all(not method['emits_pair']for method in result['methods'].values()))

    def test_malformed_clock_is_rejected_without_exporting_payload(self):
        rgb,depth,valid,k=fixture()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);run='malformed-clock-fixture';cap=root/'output/collections'/run;cap.mkdir(parents=True)
            obs=root/'output/actors'/run/'observations/00000';obs.mkdir(parents=True)
            write=lambda p,v:p.write_text(json.dumps(v))
            write(cap/'capture.json',{'complete':True})
            write(cap/'run_metadata.json',{'public_interface':{'camera_intrinsics':{c:k for c in CAMERAS},
                'camera_calibration':[{'id':c,'resolution_wh':[64,48],'intrinsics':k}for c in CAMERAS]}})
            Image.fromarray(rgb).save(obs/'robot_0_head.png')
            np.savez_compressed(obs/'public_depth.npz',depth=np.repeat(depth[None,...,None],5,axis=0),
                                depth_valid=np.repeat(valid[None,...,None],5,axis=0))
            bad_clocks=({'unexpected_payload':'CLOCK_CANARY'},['CLOCK_CANARY'],'CLOCK_CANARY',
                        True,None,float('nan'),float('inf'))
            for index,clock in enumerate(bad_clocks):
                with self.subTest(clock=repr(clock)):
                    write(obs/'observation.json',{'rgb_image_order':list(CAMERAS),
                        'public_robot_observation':{'simulation_time_s':clock}})
                    output=root/f'rejected-{index}'
                    with self.assertRaisesRegex(ValueError,'Invalid public observation clock'):
                        export_comparison(root,run,[(0,'robot_0_head')],output)
                    self.assertFalse(output.exists())

    def test_export_preserves_original_and_has_no_privileged_payload(self):
        rgb,depth,valid,k=fixture()
        with tempfile.TemporaryDirectory()as temp:
            root=Path(temp);run='closed-pair-fixture';cap=root/'output/collections'/run;cap.mkdir(parents=True)
            obs=root/'output/actors'/run/'observations/00000';obs.mkdir(parents=True)
            write=lambda p,v:p.write_text(json.dumps(v))
            write(cap/'capture.json',{'complete':True})
            write(cap/'run_metadata.json',{'episode_seed':33221199667788,'geometry':'FORBIDDEN_GEOMETRY',
                'public_interface':{'camera_intrinsics':{c:k for c in CAMERAS},'camera_calibration':[
                    {'id':c,'resolution_wh':[64,48],'intrinsics':k}for c in CAMERAS]}})
            write(obs/'observation.json',{'rgb_image_order':list(CAMERAS),'public_robot_observation':{'simulation_time_s':1.5}})
            source=obs/'robot_0_head.png';Image.fromarray(rgb).save(source)
            np.savez_compressed(obs/'public_depth.npz',depth=np.repeat(depth[None,...,None],5,axis=0),
                                depth_valid=np.repeat(valid[None,...,None],5,axis=0))
            output=root/'comparison';report=export_comparison(root,run,[(0,'robot_0_head')],output)
            self.assertEqual(source.read_bytes(),(output/'obs00000-robot_0_head.png').read_bytes())
            text=json.dumps(report,allow_nan=False)
            for bad in ('33221199667788','episode_seed','FORBIDDEN_GEOMETRY',str(root)):self.assertNotIn(bad,text)
            self.assertFalse(report['sent_to_actor']);self.assertEqual(report['model_calls'],0)
            with self.assertRaisesRegex(ValueError,'already exists'):
                export_comparison(root,run,[(0,'robot_0_head')],output)


if __name__=='__main__':unittest.main()
