import json
from pathlib import Path
import re
import sqlite3
import tempfile
import unittest

from PIL import Image

from tools.publish_review_gallery import ENTRY, publish


def read_catalog(page):
    return json.loads(re.search(rb'data-catalog>(.*?)</script>', page).group(1))


class ReviewGalleryTest(unittest.TestCase):
    def test_cumulative_playback_starts_at_reset_and_preserves_previous_snapshots(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = root / 'review'
            media = journal / 'media/demo14'
            media.mkdir(parents=True)
            traces = root / 'traces'
            frames = traces / 'demo14/segment-frames'
            frames.mkdir(parents=True)
            template = root / 'template'
            template.write_bytes(b'gallery header\n')
            destination = root / 'PhyRC-gallery/demo14'
            for step in (0, 8, 11, 16, 18):
                Image.new('RGB', (64, 64), (20 * step // 2, 0, 0)).save(frames / f'{step:06d}.jpg')

            with sqlite3.connect(journal / 'journal.sqlite3') as db:
                db.execute('CREATE TABLE segments(run,segment,payload)')
                for n, (start, end) in enumerate(((0, 0), (0, 11), (11, 18), (18, 18)), 1):
                    segment = f'hold-{n:04d}'
                    (media / (segment + '.mp4')).write_bytes(b'0000ftyp')
                    fields = dict(stage='setup', start_step=start, end_step=end, analysis='', next_prompt='')
                    db.execute('INSERT INTO segments VALUES (?,?,?)', ('demo14', segment, json.dumps(fields)))
                    db.commit()
                    publish(journal, root, template, traces)

            page = (root / ENTRY).read_bytes()
            catalog = read_catalog(page)
            self.assertEqual([clip['gif'] for clip in catalog['clips']], [True] * 4)
            self.assertNotIn(b'data-gif-delta', page)
            for i, count in enumerate((1, 3, 5, 5), 1):
                path = destination / f'hold-{i:04d}.gif'
                with Image.open(path) as gif:
                    self.assertEqual(gif.n_frames, count)
                    self.assertEqual(gif.info['loop'], 0)
                    self.assertEqual(gif.convert('RGB').getpixel((0, 0)), (0, 0, 0))
                    gif.seek(gif.n_frames - 1)
                    if i > 1:
                        self.assertGreater(gif.convert('RGB').getpixel((0, 0))[0], 100)

    def test_small_catalog_excludes_old_runs_and_updates_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            journal = root / "review"
            journal.mkdir()
            template = root / "header"
            template.write_bytes(b"gallery header\n")
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

            segment("trial-demo13-sol", 1)
            for number in range(1, 78):
                segment("trial-demo14-sol", number)
            publish(journal, root, template)
            entry = root / ENTRY
            before = entry.read_bytes()
            self.assertEqual(len(read_catalog(before)["clips"]), 77)
            self.assertNotIn(b"demo13", before)
            self.assertNotIn(b"0000ftyp", before)
            self.assertNotIn(b"</script><iframe>", before)
            group = root / "PhyRC-gallery/trial-demo14-sol"
            self.assertEqual((group / "hold-0039.html").resolve(), entry)
            self.assertEqual((group / "index.html").resolve(), entry)
            self.assertEqual((group / "hold-0039.mp4").read_bytes(), b"0000ftyphold-0039")
            stamp = entry.stat().st_mtime_ns
            publish(journal, root, template)
            self.assertEqual(stamp, entry.stat().st_mtime_ns)

            segment("trial-demo15-sol", 1)
            publish(journal, root, template)
            updated = read_catalog(entry.read_bytes())
            self.assertEqual(len(updated["clips"]), 78)
            self.assertEqual(updated["clips"][-1]["run"], "trial-demo15-sol")
            self.assertEqual((root / "PhyRC-gallery/trial-demo15-sol/hold-0001.html").resolve(), entry)
            db.close()


if __name__ == "__main__":
    unittest.main()
