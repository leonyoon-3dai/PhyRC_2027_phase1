import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.publish_review_gallery import ENTRY, publish


class ReviewGalleryTest(unittest.TestCase):
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
