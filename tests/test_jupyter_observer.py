"""CPU checks for bounded Jupyter observer publishing; no browser/GPU claims."""
import base64
import io
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image, PngImagePlugin

from participant.streaming.jupyter_observer import JupyterObserver


class ObserverTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'live.html'
        self.frame = np.zeros((16, 24, 3), dtype=np.uint8)

    def test_self_contained_escaping_and_live_status(self):
        observer = JupyterObserver(self.path, run_label='<img src=x onerror="bad()">')
        self.assertTrue(observer.write_frame(self.frame, simulation_time=1.25))
        page = self.path.read_text()
        self.assertIn('&lt;img src=x onerror=&quot;bad()&quot;&gt;', page)
        self.assertNotIn('<img src=x', page)
        self.assertIn('data-state="live"', page)
        # A /files page has an opaque sandbox origin; its own reload would 403.
        # The trusted notebook polls this snapshot from the JupyterLab origin.
        self.assertNotIn('http-equiv="refresh"', page)
        self.assertIn('Date.now()', page)
        self.assertIn('1.25초', page)
        self.assertRegex(page, r'촬영 시각 UTC: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ')
        self.assertNotIn(str(self.path), page)
        self.assertNotIn('fetch(', page)

    def test_source_metadata_removed_and_frame_resized(self):
        source = io.BytesIO()
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text('private_field', 'SENSITIVE_SOURCE_METADATA')
        Image.fromarray(self.frame).save(source, format='PNG', pnginfo=metadata)
        observer = JupyterObserver(self.path, run_label='test', max_size=(12, 8))
        observer.write_frame(source.getvalue())
        page = self.path.read_text()
        jpeg = base64.b64decode(re.search(r'data:image/jpeg;base64,([^"]+)', page).group(1))
        self.assertNotIn(b'SENSITIVE_SOURCE_METADATA', jpeg)
        with Image.open(io.BytesIO(jpeg)) as image:
            self.assertEqual(image.size, (12, 8))
            self.assertEqual(image.format, 'JPEG')

    def test_cadence_finish_and_no_file_accumulation(self):
        observer = JupyterObserver(self.path, run_label='test')
        with patch('participant.streaming.jupyter_observer.time.monotonic', return_value=100):
            self.assertTrue(observer.write_frame(self.frame))
            original = self.path.read_text()
            self.assertFalse(observer.write_frame(self.frame + 255))
            self.assertEqual(self.path.read_text(), original)
        with patch('participant.streaming.jupyter_observer.time.monotonic', return_value=102):
            self.assertTrue(observer.write_frame(self.frame + 255))
        observer.finish()
        page = self.path.read_text()
        self.assertIn('data-state="finished"', page)
        self.assertIn('data:image/jpeg;base64,', page)
        self.assertNotIn('http-equiv="refresh"', page)
        self.assertNotIn('setInterval', page)
        self.assertFalse(observer.write_frame(self.frame))
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_failed_atomic_replace_preserves_previous_frame(self):
        observer = JupyterObserver(self.path, run_label='test')
        observer.write_frame(self.frame)
        original = self.path.read_text()
        with patch('participant.streaming.jupyter_observer.os.replace', side_effect=OSError('test')):
            with self.assertRaises(OSError):
                observer.finish()
        self.assertEqual(self.path.read_text(), original)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])
        observer.finish(error=True)
        self.assertIn('data-state="error"', self.path.read_text())
        self.assertNotIn('http-equiv="refresh"', self.path.read_text())

    def test_invalid_frame_and_nonfinite_time_do_not_create_output(self):
        observer = JupyterObserver(self.path, run_label='test')
        for frame in [np.zeros((1, 1, 4), dtype=np.uint8), np.zeros((1, 1, 3))]:
            with self.assertRaises(ValueError):
                observer.write_frame(frame)
        for value in [float('nan'), float('inf'), -1, True]:
            with self.assertRaises(ValueError):
                observer.write_frame(self.frame, simulation_time=value)
        self.assertFalse(self.path.exists())


if __name__ == '__main__':
    unittest.main()
