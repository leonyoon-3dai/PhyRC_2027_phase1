"""Dual-run private media checks, using synthetic five-camera frames and no simulator."""
import http.client
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest

from PIL import Image, ImageDraw

from tools import publish_demo_pair as publisher


class ComparePublisherTest(unittest.TestCase):
    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.out = self.root / "web"
        self.out.mkdir()
        self.manifest = self.root / "pair.json"
        self.runs = [dict(demo=33, run_id="fixture-demo33", root=str(self.root / "workerA"), source_step=1200),
                     dict(demo=34, run_id="fixture-demo34", root=str(self.root / "workerB"), source_step=2905)]
        self.manifest.write_text(json.dumps(dict(schema="phyrc-concurrent-pair-v1", runs=self.runs[::-1])))
        self.colors = ["red", "blue", "green", "yellow", "magenta"]

    def frames(self, index, end):
        run = self.runs[index]
        directory = Path(run["root"]) / "output/operator-traces" / run["run_id"] / "segment-frames"
        directory.mkdir(exist_ok=True, parents=True)
        positions = [(128, 20), (0, 296), (256, 296), (0, 572), (256, 572)]
        for step in range(end + 1):
            target = directory / f"{step:06d}.jpg"
            if not target.exists():
                panel = Image.new("RGB", (512, 828))
                draw = ImageDraw.Draw(panel)
                for (x, y), color in zip(positions, self.colors):
                    draw.rectangle((x, y, x + 255, y + 255), fill=color)
                draw.text((2, 4), f"Step {step}", fill="white")
                panel.save(target)
        (directory.parent / "attempt.json").write_text(json.dumps(
            dict(run_id=run["run_id"], simulation_steps=end, activity="collecting",
                 status="collecting", private_evaluator="PRIVATE")))
        return directory

    def publish(self, force=False):
        return publisher.publish_once(self.manifest, self.out, force=force)

    def test_full_4x_gif_incremental_equals_single_render(self):
        frames = self.frames(0, 0)
        initial = self.publish()
        self.assertEqual(initial["runs"][0]["gif_end_step"], 0)
        self.assertIsNone(initial["runs"][1]["gif_url"])
        target = self.out / initial["runs"][0]["gif_url"]
        for step in (3, 8, 9, 17, 24, 25):
            self.frames(0, step)
            result = self.publish(force=True)["runs"][0]
            direct = self.root / f"other-{step}.gif"
            publisher.extend_gif(frames, step, direct)
            self.assertEqual(target.read_bytes(), direct.read_bytes())
            with Image.open(target) as gif:
                self.assertEqual((gif.size, gif.info["loop"]), ((640, 345), 0))
                sampled = [*range(0, step, 8), step]
                self.assertEqual(gif.n_frames, len(sampled))
                total = 0
                for index in range(gif.n_frames):
                    gif.seek(index)
                    total += gif.info["duration"]
                self.assertEqual(total, result["gif_duration_ms"])
                self.assertLessEqual(abs(total - 100 - step * 12.5), 5)
                # Five synthetic tiles verify real display positions R1 left, R0 right.
                rgb = gif.convert("RGB")
                for (x, y), name in zip(((160, 180), (400, 90), (560, 90),
                                         (400, 260), (560, 260)), self.colors):
                    expected = Image.new("RGB", (1, 1), name).getpixel((0, 0))
                    self.assertLess(max(abs(a - b) for a, b in zip(rgb.getpixel((x, y)), expected)), 12)
        unchanged = target.stat().st_mtime_ns
        self.publish(force=True)
        self.assertEqual(unchanged, target.stat().st_mtime_ns)

    def test_missing_boundary_preserves_last_gif_and_other_run_advances(self):
        frames = self.frames(0, 9)
        self.frames(1, 8)
        self.publish(force=True)
        self.frames(0, 23)
        self.frames(1, 21)
        (frames / "000015.jpg").unlink()
        a, b = self.publish(force=True)["runs"]
        self.assertEqual((a["end_step"], a["gif_end_step"], a["gif_error"]), (23, 9, True))
        self.assertEqual((b["gif_end_step"], b["gif_error"]), (21, False))
        self.frames(0, 23)
        self.assertEqual(self.publish(force=True)["runs"][0]["gif_end_step"], 23)

    def test_terminal_state_finishes_gif_and_records_startup_failure_without_frames(self):
        frames = self.frames(0, 4)
        self.publish()
        self.frames(0, 11)
        manifest = frames.parent / "attempt.json"
        run = json.loads(manifest.read_text())
        manifest.write_text(json.dumps(dict(run, activity="closed", status="completed")))
        self.manifest.with_name("finished.json").write_text(json.dumps(dict(state="failed", runs=[
            dict(run_id=self.runs[0]["run_id"], returncode=0),
            dict(run_id=self.runs[1]["run_id"], returncode=None)])))
        a, b = self.publish()["runs"]
        self.assertEqual((a["status"], a["gif_end_step"]), ("closed", 11))
        self.assertEqual((b["status"], b["gif_url"]), ("failed", None))

    def test_telemetry_and_loopback_allowlist(self):
        self.frames(0, 1)
        metrics = dict(schema="phyrc-pair-live-v1", gpu={"utilization_pct": 71, "uuid": "PRIVATE"},
                       cpu_utilization_pct=13.5, runs=[dict(demo=33, run_id=self.runs[0]["run_id"],
                         actor_calls_attempted=3, wall_s=11, transitions_per_min=4.2, steps=1)])
        self.manifest.with_name("telemetry.json").write_text(json.dumps(metrics))
        state = self.publish(force=True)
        self.assertEqual([r["demo"] for r in state["runs"]], [33, 34])
        self.assertEqual(state["runs"][0]["transitions_per_minute"], 4.2)
        self.assertNotIn("PRIVATE", json.dumps(state))
        self.assertNotIn(str(self.root), json.dumps(state))
        with publisher.gateway(0, self.out, self.runs) as server:
            th = Thread(target=server.serve_forever, daemon=True)
            th.start()
            try:
                for route, status in (("/" + publisher.PAGE, 200), ("/" + publisher.STATE, 200),
                                      ("/" + state["runs"][0]["gif_url"] + "?step=1", 200),
                                      ("/pair.json", 404), ("/../pair.json", 404),
                                      ("/PhyRC-compare-media/other/full-4x.gif", 404)):
                    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=2)
                    try:
                        conn.request("GET", route)
                        response = conn.getresponse()
                        self.assertEqual(response.status, status, route)
                        response.read()
                    finally:
                        conn.close()
            finally:
                server.shutdown()
                th.join()


if __name__ == "__main__":
    unittest.main()
