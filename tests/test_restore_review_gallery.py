import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile

from scripts.restore_review_gallery import restore


class ClosedGalleryRestoreTest(unittest.TestCase):
    def test_restore_checks_each_clip_before_publishing_directory(self):
        def receipt(path):
            data = path.read_bytes()
            return dict(path=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())

        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            db_path = directory / 'journal.sqlite3'
            clip = b'reviewed MP4'
            member = 'media/run-1/hold-0001.mp4'
            with sqlite3.connect(db_path) as db:
                db.execute('CREATE TABLE segments(run,segment,digest)')
                db.execute('INSERT INTO segments VALUES (?, ?, ?)',
                           ('run-1', 'hold-0001', hashlib.sha256(clip).hexdigest()))
            bundle = directory / 'run-1.zip'
            def pack(content):
                with zipfile.ZipFile(bundle, 'w') as archive:
                    archive.writestr(member, content)
                return dict(journal=receipt(db_path), runs=[dict(run_id='run-1', review_zip=receipt(bundle))])

            destination = directory / 'review'
            with self.assertRaisesRegex(ValueError, 'Clip differs'):
                restore(pack(b'other footage'), directory, destination)
            self.assertFalse(destination.exists())
            valid = pack(clip)
            self.assertEqual(restore(valid, directory, destination), 1)
            self.assertEqual((destination / member).read_bytes(), clip)
            self.assertEqual((destination / 'journal.sqlite3').read_bytes(), db_path.read_bytes())
            with self.assertRaises(FileExistsError):
                restore(valid, directory, destination)
