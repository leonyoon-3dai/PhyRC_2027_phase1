"""Measure a pair of collectors sharing one GPU. Reads supervisor artifacts only."""

import argparse
import csv
from datetime import datetime, timezone
import fcntl
import json
import math
from pathlib import Path
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time


def read_json(path):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_json(path, value):
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                     prefix=path.name + ".", delete=False) as temp:
        json.dump(value, temp, indent=2, allow_nan=False)
        temp.write("\n")
    Path(temp.name).replace(path)


def records(path):
    if not path.is_file():
        return
    with path.open("rb") as stream:
        for line in stream:
            # An interrupted writer may leave an uncommitted final row.
            if not line.endswith(b"\n"):
                break
            value = json.loads(line)
            if isinstance(value, dict):
                yield value


def number(value):
    return type(value) in (float, int) and math.isfinite(value)


def timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        moment = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return moment.timestamp() if moment.tzinfo else None
    except ValueError:
        return None


def stats(values):
    values = sorted(x for x in values if number(x))
    if not values:
        return {"samples": 0, "mean": None, "p50": None, "p95": None, "max": None}

    def percentile(frac):
        position = (len(values) - 1) * frac
        index = int(position)
        return values[index] + (values[math.ceil(position)] - values[index]) * (position - index)

    return {"samples": len(values), "mean": statistics.fmean(values),
            "p50": percentile(0.5), "p95": percentile(0.95), "max": values[-1]}


def cpu_ticks():
    try:
        values = Path("/proc/stat").read_text().splitlines()[0].split()
        if values[0] != "cpu":
            return None
        # guest and guest_nice are already included in user and nice.
        times = [int(v) for v in values[1:9]]
        return sum(times), sum(times[3:5])
    except (OSError, IndexError, ValueError):
        return None


def cpu_pct(previous, current):
    if previous and current and current[0] > previous[0]:
        busy = 1 - (current[1] - previous[1]) / (current[0] - previous[0])
        return round(100 * max(0, min(1, busy)), 2)
    return None


def read_gpu(uuid):
    data = {"uuid": uuid, "utilization_pct": None, "memory_used_mib": None, "memory_total_mib": None}
    if not uuid:
        return data
    try:
        command = ["nvidia-smi", "--id=" + uuid,
                   "--query-gpu=uuid,utilization.gpu,memory.used,memory.total",
                   "--format=csv,noheader,nounits"]
        result = subprocess.run(command, check=True, capture_output=True, text=True, timeout=3)
        row, = csv.reader(result.stdout.splitlines(), skipinitialspace=True)
        if len(row) == 4 and row[0].strip() == uuid:
            for key, cell in zip(list(data)[1:], row[1:]):
                try:
                    value = float(cell)
                    if math.isfinite(value) and value >= 0:
                        data[key] = value
                except ValueError:
                    continue
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return data


def recorded_steps(path):
    """Read the last flushed transition, skipping a partially written final line."""
    try:
        with path.open("rb") as stream:
            size = stream.seek(0, 2)
            stream.seek(max(0, size - 65536))
            tail = stream.read()
    except OSError:
        return None
    complete = tail.split(b"\n")[:-1]
    if size > 65536:
        complete = complete[1:]
    for line in reversed(complete):
        try:
            index = json.loads(line)["step_index"]
            if type(index) is int and index >= 0:
                return index + 1
        except (TypeError, ValueError, KeyError):
            continue
    return 0 if size == 0 else None


def output_paths(run):
    output = Path(run["root"]) / "output"
    return (output / "operator-traces" / run["run_id"], output / "collections" / run["run_id"])


def launcher_state(directory):
    return read_json(directory / "finished.json") or read_json(directory / "pair-state.json")


def snapshot(run, now, launcher):
    trace, collection = output_paths(run)
    attempt = read_json(trace / "attempt.json")
    start, end = (timestamp(attempt.get(k)) for k in ("started_at_utc", "ended_at_utc"))
    wall = attempt.get("wall_s") if end is not None else None
    if not number(wall) and start is not None:
        wall = max(0.0, (end if end is not None else now) - start)
    steps = recorded_steps(collection / "step_timings.jsonl")
    source = "step_timings" if steps is not None else "attempt"
    if steps is None:
        steps = attempt.get("simulation_steps")
    rate = steps / wall if number(steps) and number(wall) and wall > 0 else None
    exit_code = next((item.get("returncode") for item in launcher.get("runs", [])
                      if item.get("run_id") == run["run_id"]), None)
    status = attempt.get("status", "starting")
    if isinstance(exit_code, int) and exit_code != 0:
        status = "failed" if launcher.get("state") != "interrupted" else "interrupted"
    elif not attempt and launcher.get("state") in {"finished", "failed", "interrupted"}:
        status = "missing_attempt"
    return {"demo": run["demo"], "run_id": run["run_id"], "status": status, "launcher_returncode": exit_code,
            "activity": attempt.get("activity"), "started_at_utc": attempt.get("started_at_utc"),
            "ended_at_utc": attempt.get("ended_at_utc"), "steps": steps,
            "step_source": source if steps is not None else None, "wall_s": wall,
            "transitions_per_s": rate, "transitions_per_min": rate * 60 if rate is not None else None,
            "actor_calls_attempted": attempt.get("actor_calls_attempted")}


def load_pair(path):
    pair = read_json(path)
    runs = pair.get("runs")
    if (not isinstance(runs, list) or len(runs) != 2
            or any(not isinstance(run, dict) or any(not run.get(k) for k in ("root", "demo", "run_id"))
                   for run in runs)
            or len({run["run_id"] for run in runs}) != 2):
        raise ValueError("pair.json must identify two distinct runs with demo, root and run_id")
    return pair


def phase_overlap(first, second):
    """Intersection of two sorted non-overlapping time series on the common host clock."""
    if not first or not second:
        return None
    left = right = 0
    seconds = 0.0
    while left < len(first) and right < len(second):
        a, b = first[left], second[right]
        seconds += max(0, min(a[1], b[1]) - max(a[0], b[0]))
        if a[1] < b[1]:
            left += 1
        else:
            right += 1
    return seconds


def run_report(run, launcher):
    trace, collection = output_paths(run)
    attempt = read_json(trace / "attempt.json")
    successfully_returned, errors, dispatch = [], 0, []
    intervals = {"actor": [], "dispatch": []}
    for event in records(trace / "decisions.jsonl"):
        phase = {"decision": "actor", "model_error": "actor", "applied_segment": "dispatch"}.get(event.get("type"))
        if phase:
            start = event.get(phase + "_started_monotonic_s")
            end = event.get(phase + "_ended_monotonic_s")
            if number(start) and number(end) and start <= end:
                intervals[phase].append((start, end))
        if event.get("type") == "decision":
            successfully_returned.append(event.get("wall_s"))
        if event.get("type") == "model_error":
            errors += 1
        if event.get("type") == "applied_segment":
            dispatch.append(event.get("environment_dispatch_wall_s"))
    simulator_s, write_s = [], []
    for row in records(collection / "step_timings.jsonl"):
        simulator_s.append(row.get("environment_step_wall_s"))
        write_s.append(row.get("dataset_write_wall_s"))
    return {**snapshot(run, time.time(), launcher),
            "manifest_steps": attempt.get("simulation_steps"), "timing_rows": len(simulator_s),
            "actor_wall_s_total": attempt.get("actor_call_wall_s"),
            "actor_timing_scope": attempt.get("actor_call_timing_scope"),
            "actor_successful_calls": len(successfully_returned), "actor_failed_calls": errors,
            "actor_successful_call_wall_s": stats(successfully_returned),
            "dispatch_wall_s_total": attempt.get("environment_dispatch_wall_s"),
            "act_dispatch_wall_s": stats(dispatch), "step_wall_s": stats(simulator_s),
            "dataset_write_wall_s": stats(write_s),
            "phase_intervals_logged": {key: len(spans) for key, spans in intervals.items()}}, intervals


def window_report(samples, run_rows):
    ids = [row["run_id"] for row in run_rows]
    lifetimes = [(timestamp(row["started_at_utc"]), timestamp(row["ended_at_utc"])) for row in run_rows]
    closed = all(start is not None and end is not None and end >= start for start, end in lifetimes)
    overlap = max(0, min(end for _, end in lifetimes) - max(start for start, _ in lifetimes)) if closed else None
    buckets = {"overlap": ids, **{"solo_" + run_id: [run_id] for run_id in ids}}
    result = {key: {"observed_wall_s": 0.0, "sample_windows": 0, "transitions": dict.fromkeys(members, 0)}
              for key, members in buckets.items()}
    hw = {key: {"gpu_utilization_pct": [], "gpu_memory_used_mib": [], "host_cpu_utilization_pct": []}
          for key in buckets}
    for prev, curr in zip(samples, samples[1:]):
        left, right = timestamp(prev.get("sampled_at_utc")), timestamp(curr.get("sampled_at_utc"))
        if left is None or right is None or left >= right:
            continue
        elapsed = right - left
        cadence = curr.get("interval_s")
        if not number(cadence) or elapsed > 2 * cadence + 3:
            continue
        active = []
        mixed = False
        for run_id, (start, end) in zip(ids, lifetimes):
            if start is None:
                mixed = True
                break
            if start <= left and (end is None or right <= end):
                active.append(run_id)
            elif not (right <= start or (end is not None and end <= left)):
                mixed = True
        if mixed or not active:
            continue
        key = "overlap" if len(active) == 2 else "solo_" + active[0]
        before = {r["run_id"]: r for r in prev["runs"]}
        after = {r["run_id"]: r for r in curr["runs"]}
        changes = {}
        for run_id in active:
            a, b = before.get(run_id, {}).get("steps"), after.get(run_id, {}).get("steps")
            if type(a) is not int or type(b) is not int or b < a:
                break
            changes[run_id] = b - a
        if len(changes) != len(active):
            continue
        bucket = result[key]
        bucket["observed_wall_s"] += elapsed
        bucket["sample_windows"] += 1
        hw[key]["gpu_utilization_pct"].append(curr["gpu"].get("utilization_pct"))
        hw[key]["gpu_memory_used_mib"].append(curr["gpu"].get("memory_used_mib"))
        hw[key]["host_cpu_utilization_pct"].append(curr.get("cpu_utilization_pct"))
        for run_id, n in changes.items():
            bucket["transitions"][run_id] += n
    for key, bucket in result.items():
        bucket["hardware"] = {name: stats(values) for name, values in hw[key].items()}
        wall = bucket["observed_wall_s"]
        bucket["transitions_per_min"] = {run_id: count * 60 / wall if wall else None
                                         for run_id, count in bucket["transitions"].items()}
        bucket["combined_transitions_per_min"] = sum(bucket["transitions"].values()) * 60 / wall if wall else None
    return {"collector_wall_overlap_s": overlap, "windows": result}


def make_report(pair, directory):
    samples = list(records(directory / "samples.jsonl"))
    launcher = launcher_state(directory)
    runs, intervals = zip(*(run_report(run, launcher) for run in pair["runs"]))
    phase_pairs = [{"first_demo": runs[0]["demo"], "first_phase": a, "second_demo": runs[1]["demo"],
                    "second_phase": b, "overlap_s": phase_overlap(intervals[0][a], intervals[1][b])}
                   for a in ("actor", "dispatch") for b in ("actor", "dispatch")]
    result = {"schema": "phyrc-pair-performance-v1", "gpu_uuid": pair.get("gpu_uuid"), "runs": runs,
              **window_report(samples, runs), "host_phase_overlaps": phase_pairs, "hardware_sample_count": len(samples),
              "gpu_utilization_pct": stats(s["gpu"].get("utilization_pct") for s in samples),
              "gpu_memory_used_mib": stats(s["gpu"].get("memory_used_mib") for s in samples),
              "host_cpu_utilization_pct": stats(s.get("cpu_utilization_pct") for s in samples),
              "measurement_scope": (
                  "Overlap uses both attempt UTC lifetimes (second resolution, includes HOLD, model calls and startup). "
                  "Rates use complete, regularly sampled windows within overlap or a single collector lifetime; mixed "
                  "boundary windows and sampling gaps are excluded. Hardware counters cover the device or host. "
                  "Host phase overlaps intersect instrumented actor and action RPC intervals; missing phases are null. "
                  "Observed solo slices may cover different actions; no independent matched solo baseline is inferred.")}
    write_json(directory / "performance.json", result)
    return result


def discard_unfinished_sample(log):
    end = log.seek(0, 2)
    cursor = end
    while cursor:
        start = max(0, cursor - 4096)
        log.seek(start)
        chunk = log.read(cursor - start)
        final_newline = chunk.rfind(b"\n")
        if final_newline >= 0:
            log.truncate(start + final_newline + 1)
            return
        cursor = start
    log.truncate(0)


def sample(pair, directory, interval):
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    previous = None
    with (directory / "samples.jsonl").open("a+b") as log:
        fcntl.flock(log.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        discard_unfinished_sample(log)
        while True:
            started = time.monotonic()
            gpu = read_gpu(pair.get("gpu_uuid"))
            current = cpu_ticks()
            now = datetime.now(timezone.utc)
            launcher = launcher_state(directory)
            live = {"schema": "phyrc-pair-live-v1", "sampled_at_utc": now.isoformat(), "interval_s": interval,
                    "gpu": gpu, "cpu_utilization_pct": cpu_pct(previous, current),
                    "runs": [snapshot(run, now.timestamp(), launcher) for run in pair["runs"]]}
            previous = current
            log.write((json.dumps(live, allow_nan=False) + "\n").encode())
            log.flush()
            write_json(directory / "telemetry.json", live)
            if (directory / "finished.json").is_file() or stop.is_set():
                break
            stop.wait(max(0, interval - (time.monotonic() - started)))
        make_report(pair, directory)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("sample", "report"))
    parser.add_argument("--pair", required=True, type=Path)
    parser.add_argument("--interval", type=float, default=5.0, help="sample cadence in seconds (default 5)")
    args = parser.parse_args(argv)
    if not math.isfinite(args.interval) or args.interval < 1:
        parser.error("--interval must be finite and at least one second")
    pair = load_pair(args.pair)
    if args.command == "sample":
        sample(pair, args.pair.parent, args.interval)
    else:
        make_report(pair, args.pair.parent)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as error:
        sys.exit(str(error))
