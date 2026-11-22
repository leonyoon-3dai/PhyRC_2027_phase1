"""Exercise the public review path without a model, display server or simulator."""
from concurrent.futures import ThreadPoolExecutor
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Thread
import unittest
import zipfile

from tools import segment_review as review


class SegmentReviewTest(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "journal"
        self.clip = Path(temporary.name) / "fixture.mp4"
        # Container header + deterministic bytes, used solely for HTTP range tests.
        self.bytes = b"\x00\x00\x00\x18ftypisom" + bytes(range(200))
        self.clip.write_bytes(self.bytes)
        self.record = dict(run_id="run-a", segment_id="hold-01", parent=None, start_step=0,
                           end_step=4, stage="first_sleeve", prompt="Inspect the cuff.",
                           analysis="The wrist is occluded.", next_prompt="Raise the near edge.",
                           outcome="uncertain", labels=["occluded"], score_before=None,
                           score_after=None, score_source=None, physics_profile="official-test",
                           upstream_revision="abcdef0", reviewer_model="test-fixture",
                           review_frame_steps=[0, 2, 4], source_group="fixture")
        self.feedback = dict(run_id="run-a", segment_id="hold-01", id="operator-01",
                             action="revise", text="Lower the near edge.")

    def publish(self, **updates):
        return review.publish_segment(self.root, dict(self.record, **updates), self.clip)

    def test_concurrent_publish_and_retries(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            records = list(pool.map(lambda _: self.publish(), range(6)))
        self.assertTrue(all(r == records[0] for r in records))
        with self.assertRaises(review.Conflict):
            self.publish(labels=["slip"])
        self.clip.write_bytes(self.bytes + b"changed")
        with self.assertRaises(review.Conflict):
            self.publish()
        self.assertEqual((self.root / records[0]["clip_path"]).read_bytes(), self.bytes)
        self.assertEqual(len(review.export_rows(self.root, "run-a").splitlines()), 1)
        self.assertEqual(list(self.root.rglob("*.part")), [])

    def test_operator_claim_hold_retry_and_export(self):
        self.publish()
        hold = dict(self.feedback, id="wait", action="hold", text="")
        review.submit_feedback(self.root, hold)
        self.assertIsNone(review.claim_feedback(self.root, "run-a", "hold-01"))
        reply = review.submit_feedback(self.root, self.feedback)
        with ThreadPoolExecutor(max_workers=2) as pool:
            claims = list(pool.map(lambda _: review.claim_feedback(self.root, "run-a", "hold-01"), range(2)))
        self.assertEqual(claims, [reply, reply])
        self.assertEqual(review.submit_feedback(self.root, self.feedback), reply)
        with self.assertRaises(review.Conflict):
            review.submit_feedback(self.root, dict(self.feedback, id="late"))
        self.assertFalse(review.state(self.root)["can_feedback"])
        parent = dict(run_id="run-a", segment_id="hold-01")
        self.publish(segment_id="hold-02", parent=parent, start_step=4, end_step=8,
                     review_frame_steps=[4, 8], score_before=5, score_after=10,
                     score_source="evaluation/episode/score_samples.jsonl")
        self.assertEqual(review.state(self.root)["latest"]["segment_id"], "hold-02")
        self.assertFalse(review.state(self.root, "run-a", "hold-01")["can_feedback"])
        lines = [json.loads(line) for line in review.export_rows(self.root, "run-a").splitlines()]
        self.assertEqual(lines[0]["claimed_feedback_id"], self.feedback["id"])
        self.assertEqual(lines[1]["parent"], parent)
        self.assertEqual(len(lines[0]["feedback"]), 2)
        self.assertIsNone(lines[0]["score_after"])

    def test_scope_and_boundaries(self):
        self.assertEqual(review.state(self.root)["segments"], [])
        for changes in ({"run_id": "../escape"}, {"labels": []}, {"upstream_revision": "latest"},
                        {"score_after": 5}, {"score_after": float("nan")},
                        {"score_breakdown_after": {"first_sleeve": 5}}, {"review_frame_steps": [0, 5]},
                        {"parent": dict(run_id="missing", segment_id="parent")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.publish(**changes)
        self.publish(hold_reason="review_unavailable")
        with self.assertRaises(review.Conflict):
            review.submit_feedback(self.root, dict(self.feedback, action="accept"))
        with self.assertRaises(ValueError):
            review.submit_feedback(self.root, dict(self.feedback, text="raw_points = 10"))
        self.publish(run_id="run-b", hold_reason="hard_horizon", start_step=4, review_frame_steps=[4])
        self.assertEqual(review.state(self.root)["runs"], ["run-b", "run-a"])
        for action in ("revise", "accept"):
            with self.subTest(action=action), self.assertRaises(review.Conflict):
                review.submit_feedback(self.root, dict(self.feedback, run_id="run-b", action=action))
        review.submit_feedback(self.root, dict(self.feedback, run_id="run-b", action="finish", text=""))
        self.assertEqual(review.claim_feedback(self.root, "run-b", "hold-01")["action"], "finish")

    def test_portable_bundle_matches_metadata_and_refuses_overwrite_or_corruption(self):
        self.publish()
        self.publish(segment_id="hold-02", score_after=10, score_source="eval/fixture")
        self.publish(run_id="other")
        output = self.root.parent / "exports" / "run-a.zip"
        review.bundle_run(self.root, "run-a", output)
        with zipfile.ZipFile(output) as archive:
            rows = [json.loads(line) for line in archive.read("segments.jsonl").splitlines()]
            self.assertEqual([r["segment_id"] for r in rows], ["hold-01", "hold-02"])
            self.assertEqual(set(archive.namelist()), {"segments.jsonl", "run_outcome.json", *(r["clip_path"] for r in rows)})
            self.assertEqual(json.loads(archive.read("run_outcome.json"))["status"], "unfinalized")
            for row in rows:
                self.assertEqual(archive.read(row["clip_path"]), self.bytes)
        with self.assertRaises(FileExistsError):
            review.bundle_run(self.root, "run-a", output)
        (self.root / rows[0]["clip_path"]).write_bytes(b"corrupt")
        damaged = output.with_name("damaged.zip")
        with self.assertRaisesRegex(ValueError, "clip hash mismatch"):
            review.bundle_run(self.root, "run-a", damaged)
        self.assertFalse(damaged.exists())
        self.assertFalse(list(output.parent.glob("*.part")))

    def test_final_score_requires_matching_closed_reports(self):
        self.publish(evaluator_success_before=None, evaluator_success_after=False, score_after=5,
                     score_source="evaluation/episode/score_samples.jsonl")
        collection = self.root.parent / "collections" / "run-a"
        episode = collection / "evaluation" / "episode"
        episode.mkdir(parents=True)
        capture = dict(schema="participant-live-capture-v2", steps=4, complete=True,
                       evaluation_enabled=True, evaluation_valid=True)
        (collection / "capture.json").write_text(json.dumps(capture))
        rows = [self.record]
        self.assertEqual(review.final_outcome("run-a", rows, collection)["status"], "unfinalized")
        for valid, evaluated, success in ((True, True, True), (True, True, False),
                                          (True, False, None), (False, None, None)):
            with self.subTest(valid=valid, evaluated=evaluated, success=success):
                result = dict(success_evaluated=evaluated, success=bool(success), raw_points=5,
                              breakdown={"pickup": 5}, final_score=0.0, score_status="fixture")
                report = dict(valid=valid, result=result if valid else None,
                              metadata={"source_group": "fixture", "episode_seed": 17})
                summary = dict(evaluation_path="evaluation/episode", report=report)
                (collection / "capture.json").write_text(json.dumps(dict(capture, evaluation_valid=valid)))
                (collection / "evaluation_summary.json").write_text(json.dumps(summary))
                (episode / "result.json").write_text(json.dumps(report))
                out = self.root.parent / f"test-{valid}-{evaluated}-{success}.zip"
                review.bundle_run(self.root, "run-a", out, collection)
                with zipfile.ZipFile(out) as archive:
                    outcome = json.loads(archive.read("run_outcome.json"))
                self.assertEqual(outcome["status"], "finalized")
                self.assertEqual(outcome["valid"], valid)
                self.assertIs(outcome["success"], success)
                self.assertEqual(outcome["raw_points"], 5 if valid else None)
                self.assertNotIn("episode_seed", json.dumps(outcome))
        with self.assertRaisesRegex(ValueError, "source group"):
            review.final_outcome("run-a", [dict(self.record, source_group="wrong")], collection)
        with self.assertRaisesRegex(ValueError, "named for this run"):
            review.final_outcome("run-b", rows, collection)
        (episode / "result.json").write_text("{}")
        with self.assertRaisesRegex(ValueError, "disagree"):
            review.final_outcome("run-a", rows, collection)
        (collection / "capture.json").write_text(json.dumps(dict(capture, evaluation_enabled=False)))
        outcome = review.final_outcome("run-a", rows, collection)
        self.assertEqual(outcome["status"], "unevaluated")
        self.assertIsNone(outcome["success"])

    def test_verified_reset_in_offline_bundle_only_and_legacy_null(self):
        self.publish(physics_profile="shirt/manikin=0.35, gripper/cloth=unverified")
        collection = self.root.parent / "collections" / "run-a"
        collection.mkdir(parents=True)
        rows = [self.record]
        self.assertIsNone(review.final_outcome("run-a", rows, collection)["collection_start"])
        metadata_file = collection / "run_metadata.json"
        metadata = dict(schema="participant-collection-run-v1", source_group="fixture", episode_seed=43)
        metadata_file.write_text(json.dumps(metadata))
        self.assertIsNone(review.final_outcome("run-a", rows, collection)["collection_start"])
        receipt = dict(profile="fresh-nearest-table-cp2", start_step=0, requested_seed=42,
                       episode_seed=43, table_index=2, shirt_manikin_friction=0.35,
                       verified_after_reset=True)
        full = dict(receipt, table_center_world_m=[9, 8, 7], mean_base_distance_xy_m=[1, 2, 3, 4])
        metadata_file.write_text(json.dumps(dict(metadata, collection_start=full)))
        archive_file = self.root.parent / "fresh.zip"
        review.bundle_run(self.root, "run-a", archive_file, collection)
        with zipfile.ZipFile(archive_file) as archive:
            outcome = json.loads(archive.read("run_outcome.json"))
            self.assertEqual(outcome["collection_start"], receipt)
            self.assertIn("run_metadata.json", outcome["sources"])
            self.assertNotIn(b"episode_seed", archive.read("segments.jsonl"))
        self.assertNotIn("collection_start", review.state(self.root)["latest"])
        for changes in ({"verified_after_reset": False}, {"profile": "unknown"}, {"start_step": 5},
                        {"episode_seed": 41}, {"table_index": 1}, {"shirt_manikin_friction": 0}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                review.practice_start(dict(metadata, collection_start=dict(full, **changes)), rows)
        for changes in ({"source_group": "other"}, {"replay_prefix_steps": 3},
                        {"physics_profile": "shirt/manikin=0.0, gripper/cloth=1"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                review.practice_start(dict(metadata, collection_start=full), [dict(rows[0], **changes)])

    def test_http_export_media_ranges_and_stale_feedback(self):
        self.publish()
        with ThreadingHTTPServer(("127.0.0.1", 0), review.ReviewHandler) as server:
            server.root = self.root
            worker = Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                def request(method, path, headers=None, payload=None):
                    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                    try:
                        conn.request(method, path, body=payload, headers=headers or {})
                        response = conn.getresponse()
                        return response.status, dict(response.getheaders()), response.read()
                    finally:
                        conn.close()

                status, _, data = request("GET", "/api/state")
                self.assertEqual(status, 200)
                clip = json.loads(data)["latest"]["clip_url"]
                for byte_range, expected in (("bytes=4-7", self.bytes[4:8]),
                                             ("bytes=200-", self.bytes[200:]),
                                             ("bytes=-5", self.bytes[-5:])):
                    status, headers, data = request("GET", clip, {"Range": byte_range})
                    self.assertEqual((status, data), (206, expected))
                    self.assertIn("Content-Range", headers)
                self.assertEqual(request("HEAD", clip)[2], b"")
                self.assertEqual(request("GET", clip, {"Range": "bytes=99999-"})[0], 416)
                self.assertEqual(request("GET", clip, {"Range": "bytes=-0"})[0], 416)
                self.assertEqual(request("GET", "/api/export?run=run-a")[0], 200)
                headers = {"Content-Type": "application/json"}
                payload = json.dumps(self.feedback)
                self.assertEqual(request("POST", "/api/feedback", dict(headers, Origin="http://other.test"), payload)[0], 403)
                self.assertEqual(request("POST", "/api/feedback", headers, payload)[0], 200)
                self.publish(segment_id="hold-02")
                stale = json.dumps(dict(self.feedback, id="another"))
                self.assertEqual(request("POST", "/api/feedback", headers, stale)[0], 409)
                # A repeat of the already-persisted request is acknowledged, even after a new HOLD.
                self.assertEqual(request("POST", "/api/feedback", headers, payload)[0], 200)
            finally:
                server.shutdown()
                worker.join()


if __name__ == "__main__":
    unittest.main()
