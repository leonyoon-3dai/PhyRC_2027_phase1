"""Event exporter: active-file rejection, boundary mapping, provenance and media."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import h5py
import numpy as np
from PIL import Image

from participant.collection.boundary import CONTRACT
from participant.collection.validate_capture import sha256, validate_capture
from Policy.training_dataset import DatasetWriter
from scripts.export_gallery_event import boundary_pixels, export_event, mosaic, DEFAULT_CAMERAS


class GalleryEventTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.capture = self.root / 'test-event'
        self.output = self.root / 'public-event'
        contract = copy.deepcopy(CONTRACT)
        contract['default_dimensions'].update(height=16, width=16)
        dims = contract['default_dimensions']
        action = np.zeros((2, 9), np.float32)
        def observation(step):
            obs = {k: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
                   for k, spec in contract['observations'].items()}
            obs['simulation_time_s'] = np.asarray(1.5 + step * .05, np.float64)
            for i in range(5):
                obs['rgb'][i, :, :, 0] = 20 + i
                obs['rgb'][i, :, :, 1] = step * 40
            return obs
        writer = DatasetWriter(self.capture, contract, {'raw_archive': False, 'private': 'private-canary'})
        writer.start_episode({'operator_source': 'integration_test'})
        for i in range(3):
            writer.append(observation(i), action, observation(i + 1), start_tick=i*12, end_tick=(i+1)*12, audit={})
        writer.finish_episode('test_done')
        writer.close()
        self.refresh_evidence()

    def refresh_evidence(self):
        hashes = {name: sha256(self.capture / name) for name in ('policy.hdf5', 'audit.hdf5')}
        (self.capture / 'capture.json').write_text(json.dumps({'complete': True, 'raw_archive': False,
            'steps': 3, 'files': hashes, 'private': 'private-canary'}))
        report = validate_capture(self.capture)
        self.assertTrue(report['quality_passed'])
        (self.capture / 'validation.json').write_text(json.dumps(report))

    def test_initial_internal_and_final_boundaries(self):
        with h5py.File(self.capture / 'policy.hdf5', 'r') as f:
            for boundary in range(4):
                pixels = boundary_pixels(f['data/demo_0'], 'robot_0_head', boundary, 3)
                self.assertTrue(np.all(pixels[..., 1] == boundary * 40))

    def test_active_manifest_rejected_before_hdf5_open(self):
        (self.capture / 'capture.json').write_text(json.dumps({'complete': False, 'raw_archive': False}))
        with patch('scripts.export_gallery_event.h5py.File') as opened:
            with self.assertRaisesRegex(ValueError, 'completed immediate capture'):
                export_event(self.capture, self.output, start=0, end=3)
            opened.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_stale_validation_rejected_before_hdf5_open(self):
        with h5py.File(self.capture / 'policy.hdf5', 'r+') as f:
            f['data/demo_0/obs/robot_0_head_rgb'][0, 0, 0, 0] = 99
        with patch('scripts.export_gallery_event.h5py.File') as opened:
            with self.assertRaisesRegex(ValueError, 'SHA'):
                export_event(self.capture, self.output, start=0, end=3)
            opened.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_boundary_continuity_checked(self):
        with h5py.File(self.capture / 'policy.hdf5', 'r+') as f:
            f['data/demo_0/obs/robot_0_head_rgb'][1, 0, 0, 0] = 99
            with self.assertRaisesRegex(ValueError, 'continuity'):
                boundary_pixels(f['data/demo_0'], 'robot_0_head', 1, 3)

    def test_mosaic_retains_each_view_and_labels_outside_camera_pixels(self):
        views = [np.full((16, 16, 3), i * 50, dtype=np.uint8) for i in range(4)]
        result = np.asarray(mosaic(views, DEFAULT_CAMERAS, 3, 128))
        self.assertEqual(result.shape, (332, 256, 3))
        for i in range(4):
            x, y = (i % 2) * 128, (i // 2) * 152 + 24
            self.assertTrue(np.all(result[y:y+128, x:x+128] == i * 50))

    def test_out_of_range_and_existing_output_rejected(self):
        with self.assertRaisesRegex(ValueError, 'exceeds'):
            export_event(self.capture, self.output, start=0, end=4)
        self.output.mkdir()
        keep = self.output / 'keep.txt'; keep.write_text('preserve')
        with self.assertRaisesRegex(ValueError, 'already exists'):
            export_event(self.capture, self.output, start=0, end=3)
        self.assertEqual(keep.read_text(), 'preserve')

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg/ffprobe unavailable')
    def test_real_media_export_includes_terminal_boundary_without_private_metadata(self):
        result = export_event(self.capture, self.output, start=0, end=3, tile_size=128)
        self.assertEqual(result['selection']['frame_count'], 4)
        self.assertTrue(result['selection']['contains_final_boundary'])
        self.assertEqual(result['selection']['sample_endpoint_span_s'], .15)
        self.assertEqual(result['playback']['duration_s'], .8)
        self.assertEqual(result['playback']['slowdown_factor'], 4)
        self.assertEqual(int(result['mp4']['stream']['nb_read_frames']), 4)
        with Image.open(self.output / 'preview.gif') as gif:
            self.assertEqual(gif.n_frames, 4)
            gif.seek(3)
            self.assertEqual(gif.info['duration'], 200)
        serialized = (self.output / 'provenance.json').read_text()
        self.assertNotIn(str(self.root), serialized)
        self.assertNotIn('private-canary', serialized)
        self.assertNotIn('source_group', serialized)
        self.assertEqual(result['source']['policy_sha256'], sha256(self.capture / 'policy.hdf5'))


if __name__ == '__main__':
    unittest.main()
