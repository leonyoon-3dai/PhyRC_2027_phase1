import base64
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest

from PIL import Image

from tools.publish_review_gallery import ENTRY, publish


class ReviewGalleryTest(unittest.TestCase):
    def test_cumulative_playback_starts_at_reset_and_preserves_previous_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = root / 'review'
            media = journal / 'media/run'
            media.mkdir(parents=True)
            traces = root / 'traces'
            frames = traces / 'run/segment-frames'
            frames.mkdir(parents=True)
            template = root / 'template'
            template.write_bytes(b'gallery header\n')
            destination = root / 'PhyRC-gallery/run'
            for step in (0, 8, 11, 16, 18):
                Image.new('RGB', (64, 64), (20 * step // 2, 0, 0)).save(frames / f'{step:06d}.jpg')

            with sqlite3.connect(journal / 'journal.sqlite3') as db:
                db.execute('CREATE TABLE segments(run,segment,payload)')
                for n, (start, end) in enumerate(((0, 0), (0, 11), (11, 18), (18, 18)), 1):
                    segment = f'hold-{n:04d}'
                    (media / (segment + '.mp4')).write_bytes(b'0000ftyp')
                    fields = dict(stage='setup', start_step=start, end_step=end, analysis='', next_prompt='')
                    db.execute('INSERT INTO segments VALUES (?,?,?)', ('run', segment, json.dumps(fields)))
                    db.commit()
                    publish(journal, root, template, root / 'missing.json', traces)

            page = (root / ENTRY).read_bytes()
            chunks = re.findall(rb'data-gif-delta>([A-Za-z0-9+/=]*)!</script>', page)
            self.assertEqual(len(chunks), 4)
            for i, count in enumerate((1, 3, 5, 5), 1):
                path = destination / f'hold-{i:04d}.gif'
                inline = b''.join(base64.b64decode(chunk) for chunk in chunks[:i]) + b'\x3b'
                self.assertEqual(inline, path.read_bytes())
                with Image.open(path) as gif:
                    self.assertEqual(gif.n_frames, count)
                    self.assertEqual(gif.info['loop'], 0)
                    self.assertEqual(gif.convert('RGB').getpixel((0, 0)), (0, 0, 0))
                    gif.seek(gif.n_frames - 1)
                    if i > 1:
                        self.assertGreater(gif.convert('RGB').getpixel((0, 0))[0], 100)

    def test_append_recovery_and_new_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = root / "review"
            journal.mkdir()
            template = root / "header"
            template.write_bytes(b"gallery header\n")
            retro = root / "retro.json"
            retro.write_text('{"title":"History"}')
            db = sqlite3.connect(journal / "journal.sqlite3")
            db.execute("CREATE TABLE segments(run,segment,payload)")

            def segment(run, index):
                name = f"hold-{index:04d}"
                media = journal / "media" / run
                media.mkdir(parents=True, exist_ok=True)
                (media / f"{name}.mp4").write_bytes(b"0000ftyp" + name.encode())
                fields = dict(stage="pickup", start_step=index, end_step=index + 1,
                              analysis="</script><iframe>", next_prompt="검토")
                db.execute("INSERT INTO segments VALUES (?,?,?)", (run, name, json.dumps(fields)))
                db.commit()

            for number in range(1, 78):
                segment("first", number)
            publish(journal, root, template, retro)
            entry = root / ENTRY
            before = entry.read_bytes()
            self.assertEqual(before.count(b" data-video>"), 77)
            self.assertNotIn(b"</script><iframe>", before)
            self.assertEqual((root / "PhyRC-gallery/first/hold-0039.html").resolve(), entry)
            stamp = entry.stat().st_mtime_ns
            publish(journal, root, template, retro)
            self.assertEqual(stamp, entry.stat().st_mtime_ns)

            # A crash after appending bytes but before replacing the checkpoint.
            with entry.open("ab") as out:
                out.write(b"partial write")
            segment("second", 1)
            publish(journal, root, template, retro)
            updated = entry.read_bytes()
            self.assertEqual(before, updated[:len(before)])
            self.assertNotIn(b"partial write", updated)
            self.assertEqual(updated.count(b" data-video>"), 78)
            self.assertEqual((root / "PhyRC-gallery/second/hold-0001.html").resolve(), entry)
            retro.write_text('{"title":"Updated"}')
            publish(journal, root, template, retro)
            self.assertEqual(entry.read_bytes().count(b" data-video>"), 78)
            self.assertIn(b'Updated', entry.read_bytes()[len(updated):])
            db.close()


if __name__ == "__main__":
    unittest.main()
