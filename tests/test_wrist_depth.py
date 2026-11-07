"""Fixed optical-Z mapping, current-time labels, image budget and source capture."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

from participant.collection import codex_client
from participant.collection.wrist_depth import (
    ABOVE, BELOW, INVALID, CAMERAS, append_wrist_depth_panel, input_image_order, render_depth)


class WristDepthTest(unittest.TestCase):
    def obs(self):
        return {'depth': np.full((5, 256, 256, 1), .42, np.float32),
                'depth_valid': np.ones((5, 256, 256, 1), bool),
                'simulation_time_s': np.asarray(37.5), 'private': 'PRIVATE_CANARY'}

    def test_fixed_mapping_endpoints_and_sentinels(self):
        z = np.array([[.03, 1.20, .42, .02, 1.21, 0, -1, np.nan, np.inf, .5]], np.float32)
        valid = np.ones(z.shape, bool); valid[0, -1] = False
        rgb = render_depth(z, valid)[0]
        np.testing.assert_array_equal(rgb[:5], [[255]*3, [0]*3, [170]*3, BELOW, ABOVE])
        np.testing.assert_array_equal(rgb[5:], np.tile(INVALID, (5, 1)))
        changed = z.copy(); changed[0, 1] = 3
        self.assertEqual(render_depth(changed, valid)[0, 2].tolist(), [170]*3)

    def test_exact_pixels_outside_labels_current_time_and_no_private_metadata(self):
        obs = self.obs(); obs['depth'][1, 0, 0, 0] = .02; obs['depth_valid'][2, 255, 255, 0] = False
        images = [Path(f'{camera}.png') for camera in CAMERAS]
        with tempfile.TemporaryDirectory() as tmp:
            result, meta = append_wrist_depth_panel(obs, images, Path(tmp))
            self.assertEqual(result[:5], images)
            self.assertEqual(len(result), 6)
            self.assertEqual(meta['image_index'], 5)
            self.assertEqual(meta['simulation_time_s'], 37.5)
            self.assertAlmostEqual(meta['quantization_step_m'], 1.17 / 255)
            self.assertAlmostEqual(meta['maximum_rounding_error_m'], 1.17 / 510)
            self.assertTrue(np.isfinite(meta['quantization_step_m']))
            self.assertTrue(np.isfinite(meta['maximum_rounding_error_m']))
            self.assertEqual(meta['panels'][0]['pixel_counts'], {'effective_valid': 65536,
                'invalid': 0, 'below_range': 1, 'within_range': 65535, 'above_range': 0})
            self.assertEqual(meta['panels'][1]['pixel_counts'], {'effective_valid': 65535,
                'invalid': 1, 'below_range': 0, 'within_range': 65535, 'above_range': 0})
            self.assertEqual(meta['input_image_order'][-1]['simulation_time_s'], 37.5)
            self.assertEqual(hashlib.sha256(result[-1].read_bytes()).hexdigest(), meta['png_sha256'])
            pixels = np.asarray(Image.open(result[-1]))
            self.assertEqual(pixels.shape, (424, 512, 3))
            for panel, source_i in zip(meta['panels'], (1, 2)):
                x0, y0, x1, y1 = panel['pixel_rectangle_xyxy_exclusive']
                np.testing.assert_array_equal(pixels[y0:y1, x0:x1],
                    render_depth(obs['depth'][source_i, :, :, 0], obs['depth_valid'][source_i, :, :, 0]))
            self.assertNotIn('PRIVATE_CANARY', json.dumps(meta))
            self.assertNotIn(tmp, json.dumps(meta))
            self.assertEqual(json.loads((Path(tmp)/'current_wrist_depth.json').read_text()), meta)
            with self.assertRaisesRegex(ValueError, 'no previous panel'):
                append_wrist_depth_panel(obs, images, Path(tmp))

    def test_image_budget_and_temporal_labels_fail_closed(self):
        for count in (0, 4, 6, 16, 20):
            with self.subTest(count=count), self.assertRaisesRegex(ValueError, '16 total images'):
                input_image_order([Path('x')]*count, 10)
        with self.assertRaisesRegex(ValueError, 'require temporal context'):
            input_image_order([Path('x')]*15, 10)
        context = {'groups': [
            {'kind':'current','image_indices':list(range(5)), 'camera_order':list(CAMERAS), 'simulation_time_s':10},
            {'kind':'historical_same_episode','image_indices':list(range(5,10)), 'camera_order':list(CAMERAS), 'simulation_time_s':11},
        ]}
        with self.assertRaisesRegex(ValueError, 'current/past'):
            input_image_order([Path('x')]*10, 10, context)
        context['groups'][1]['simulation_time_s'] = 9
        context['groups'][0]['simulation_time_s'] = 9.9
        with self.assertRaisesRegex(ValueError, 'current/past'):
            input_image_order([Path('x')]*10, 10, context)

    def test_invalid_clock_rejected_before_writing(self):
        for t in (np.nan, np.inf, -1, True, [1]):
            obs = self.obs(); obs['simulation_time_s'] = t
            with tempfile.TemporaryDirectory() as tmp:
                with self.assertRaises(ValueError):
                    append_wrist_depth_panel(obs, [Path('x')]*5, Path(tmp))
                self.assertFalse(list(Path(tmp).iterdir()))

    def test_new_renderer_is_included_by_real_source_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); trace=root/'trace'; trace.mkdir()
            for name in ('run.sh','scripts/collect_operator.py','participant/streaming/collector_stream.py',
                         'config/policy_interface.json','config/assets.lock.json',
                         'participant/collection/wrist_depth.py',
                         'participant/collection/depth_query.py',
                         'participant/collection/named_actions.py',
                         'participant/research/depth_backprojection.py'):
                p=root/name; p.parent.mkdir(parents=True, exist_ok=True); p.write_text('fixed-source')
            with patch.object(codex_client.subprocess, 'check_output', side_effect=['a'*40, '']):
                snapshot=codex_client.source_snapshot(root,trace)
            self.assertIn('participant/collection/wrist_depth.py',snapshot['files_sha256'])
            self.assertIn('participant/collection/depth_query.py',snapshot['files_sha256'])
            self.assertIn('participant/collection/named_actions.py',snapshot['files_sha256'])
            self.assertIn('participant/research/depth_backprojection.py',snapshot['files_sha256'])
            copied=trace/'source_snapshot/participant/collection/wrist_depth.py'
            self.assertEqual(copied.read_text(),'fixed-source')
            self.assertEqual(hashlib.sha256(copied.read_bytes()).hexdigest(),
                             snapshot['files_sha256']['participant/collection/wrist_depth.py'])


if __name__ == '__main__':
    unittest.main()
