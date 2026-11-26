import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from participant.ops import pair_performance as perf


def moment(second):
    return f"2026-11-26T12:{second // 60:02d}:{second % 60:02d}+00:00"


class PairPerformanceTests(unittest.TestCase):
    def test_overlapping_and_solo_windows_use_only_steps_inside_observed_windows(self):
        rows = [{"run_id": "A", "started_at_utc": moment(0), "ended_at_utc": moment(40)},
                {"run_id": "B", "started_at_utc": moment(12), "ended_at_utc": moment(90)}]
        samples = [{"sampled_at_utc": moment(t), "interval_s": 5, "runs": [
                        {"run_id": "A", "steps": a}, {"run_id": "B", "steps": b}],
                    "gpu": {"utilization_pct": 84}, "cpu_utilization_pct": None}
                   for t, a, b in [(0, 0, None), (5, 3, None), (10, 5, None),
                                   (15, 9, 1), (20, 12, 8), (25, 12, 11),
                                   (43, 14, 18), (48, 14, 20), (85, 14, 30)]]
        result = perf.window_report(samples, rows)
        self.assertEqual(result["collector_wall_overlap_s"], 28)
        shared = result["windows"]["overlap"]
        self.assertEqual(shared["transitions"], {"A": 3, "B": 10})
        self.assertEqual(shared["combined_transitions_per_min"], 78)
        self.assertEqual(shared["hardware"]["gpu_utilization_pct"]["samples"], 2)
        self.assertEqual(result["windows"]["solo_A"]["combined_transitions_per_min"], 30)
        self.assertEqual(result["windows"]["solo_B"]["combined_transitions_per_min"], 24)

    def test_phase_overlap_counts_partial_overlaps_and_excludes_touching_endpoints(self):
        self.assertEqual(perf.phase_overlap([(1, 4), (8, 12)], [(2.5, 3), (3.5, 8), (9, 11)]), 3)
        self.assertEqual(perf.phase_overlap([(1, 2)], [(2, 3)]), 0)
        self.assertIsNone(perf.phase_overlap([], [(2, 3)]))

    def test_no_baseline_or_end_marks_stay_unknown(self):
        rows = [{"run_id": "A", "started_at_utc": moment(0), "ended_at_utc": None},
                {"run_id": "B", "started_at_utc": None, "ended_at_utc": None}]
        result = perf.window_report([], rows)
        self.assertIsNone(result["collector_wall_overlap_s"])
        self.assertIsNone(result["windows"]["overlap"]["combined_transitions_per_min"])

    def test_sampler_reads_flushed_recorder_and_finishes_without_gpu(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            runs = [{"demo": i, "run_id": f"d{i}", "root": str(root / f"checkout{i}")}
                    for i in (33, 34)]
            (root / "pair.json").write_text(json.dumps({"gpu_uuid": None, "runs": runs}))
            (root / "finished.json").write_text(json.dumps({"state": "failed", "runs": [
                {"demo": 33, "run_id": "d33", "returncode": 0},
                {"demo": 34, "run_id": "d34", "returncode": 1}]}))
            trace, collection = perf.output_paths(runs[0])
            trace.mkdir(parents=True)
            collection.mkdir(parents=True)
            (trace / "attempt.json").write_text(json.dumps({"status": "completed", "simulation_steps": 3,
                "started_at_utc": moment(0), "ended_at_utc": moment(20), "wall_s": 20,
                "actor_calls_attempted": 2, "actor_call_wall_s": 5}))
            other_trace, _ = perf.output_paths(runs[1])
            other_trace.mkdir(parents=True)
            (other_trace / "decisions.jsonl").write_text(
                '{"type":"decision","actor_started_monotonic_s":10,"actor_ended_monotonic_s":12}\n')
            (trace / "decisions.jsonl").write_text(
                '{"type":"decision","wall_s":3.2,"actor_started_monotonic_s":9,"actor_ended_monotonic_s":12.2}\n'
                '{"type":"model_error"}\n{"type":"applied_segment","environment_dispatch_wall_s":0.9}\n')
            (collection / "step_timings.jsonl").write_text('{"step_index":0,"environment_step_wall_s":0.2}\n'
                '{"step_index":1,"environment_step_wall_s":0.4}\n{"step_index":2')
            (root / "samples.jsonl").write_bytes(b'{"incomplete":')
            with patch.object(perf.signal, "signal"):
                perf.main(["sample", "--pair", str(root / "pair.json")])
            self.assertEqual(len(list(perf.records(root / "samples.jsonl"))), 1)
            live = perf.read_json(root / "telemetry.json")
            self.assertEqual(live["runs"][0]["steps"], 2)
            self.assertEqual(live["runs"][0]["transitions_per_min"], 6)
            self.assertEqual(live["runs"][1]["status"], "failed")
            self.assertIsNone(live["gpu"]["utilization_pct"])
            perf.main(["report", "--pair", str(root / "pair.json")])
            report = perf.read_json(root / "performance.json")
            overlaps = {(r["first_phase"], r["second_phase"]): r["overlap_s"] for r in report["host_phase_overlaps"]}
            self.assertEqual(overlaps["actor", "actor"], 2)
            self.assertIsNone(overlaps["dispatch", "dispatch"])
            data = report["runs"][0]
            self.assertEqual((data["manifest_steps"], data["timing_rows"]), (3, 2))
            self.assertEqual(data["step_wall_s"]["samples"], 2)
            self.assertAlmostEqual(data["step_wall_s"]["p50"], 0.3)
            self.assertEqual(data["actor_failed_calls"], 1)
            self.assertEqual(data["actor_successful_call_wall_s"]["mean"], 3.2)
            self.assertEqual(data["act_dispatch_wall_s"]["max"], 0.9)

    def test_gpu_checks_selected_device_and_retains_missing_metrics(self):
        with patch.object(perf.subprocess, "run") as run:
            run.return_value.stdout = "GPU-one, 84, [N/A], 24576\n"
            row = perf.read_gpu("GPU-one")
            self.assertEqual(row["utilization_pct"], 84)
            self.assertEqual(row["memory_total_mib"], 24576)
            self.assertIsNone(row["memory_used_mib"])
            self.assertIn("--id=GPU-one", run.call_args.args[0])
            self.assertIsNone(perf.read_gpu("GPU-two")["utilization_pct"])
        self.assertIsNone(perf.cpu_pct(None, (100, 30)))
        self.assertEqual(perf.cpu_pct((100, 30), (200, 50)), 80)


if __name__ == "__main__":
    unittest.main()
