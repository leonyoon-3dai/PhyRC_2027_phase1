import hashlib
import io
from pathlib import Path
import sqlite3
import tarfile
import tempfile
import unittest
import zipfile

from scripts.restore_review_gallery import restore, restore_frames


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

    def test_restore_frames_requires_a_safe_complete_sequence(self):
        frames = {f'{step:06d}.jpg': f'Frame {step}'.encode() for step in range(3)}
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            bundle = directory / 'frames.tar.gz'
            destination = directory / 'restored'

            def pack(contents, *, link=None):
                with tarfile.open(bundle, 'w:gz') as archive:
                    for name, data in contents.items():
                        member = tarfile.TarInfo(name)
                        member.size = len(data)
                        archive.addfile(member, io.BytesIO(data))
                    if link is not None:
                        member = tarfile.TarInfo(link)
                        member.type = tarfile.SYMTYPE
                        member.linkname = '000000.jpg'
                        archive.addfile(member)
                data = bundle.read_bytes()
                asset = dict(path=bundle.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
                return dict(runs=[dict(run_id='run-1', review_frame_count=len(frames), review_frames=asset)])

            incomplete = {name: data for name, data in frames.items() if name != '000001.jpg'}
            with self.assertRaisesRegex(ValueError, 'Incomplete review frame sequence'):
                restore_frames(pack(incomplete), directory, destination)
            self.assertFalse(destination.exists())

            with self.assertRaisesRegex(ValueError, 'Unexpected frame'):
                restore_frames(pack(incomplete, link='000001.jpg'), directory, destination)
            self.assertFalse(destination.exists())

            with self.assertRaisesRegex(ValueError, 'Unexpected frame'):
                restore_frames(pack({**frames, '../escaped.jpg': b'outside'}), directory, destination)
            self.assertFalse(destination.exists())
            self.assertFalse((directory / 'escaped.jpg').exists())

            restore_frames(pack(frames), directory, destination)
            folder = destination / 'run-1' / 'segment-frames'
            self.assertEqual({path.name: path.read_bytes() for path in folder.iterdir()}, frames)
