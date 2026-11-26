"""Publish two complete, incremental 4× practice GIFs through authenticated Jupyter."""
import argparse
from contextlib import ExitStack
import fcntl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import logging
import math
import os
from pathlib import Path
import shutil
import tempfile
from threading import Thread
import time
from urllib.parse import urlsplit

from PIL import GifImagePlugin, Image

if __package__:
    from .publish_review_gallery import ID, write_atomic
    from .review_wide_media import wide_panel
else:
    from publish_review_gallery import ID, write_atomic
    from review_wide_media import wide_panel


TEMPLATE = Path(__file__).with_name("review_gallery_compare.html")
PAGE, STATE = "PhyRC-compare.html", "PhyRC-compare.json"
MEDIA = "PhyRC-compare-media"
# 20 policy Hz × 4 = 80 steps per playback second. Show a real sample every 100ms.
STRIDE = 8
END_HOLD_MS = 100


def read_json(path):
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return {}


def save_changed(path, data):
    if not path.is_file() or path.read_bytes() != data:
        write_atomic(path, data)


def numeric(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def pair_runs(path):
    pair = read_json(path)
    if pair.get("schema") != "phyrc-concurrent-pair-v1":
        raise ValueError("expected the demo 33/34 launcher manifest")
    runs = pair.get("runs", [])
    if sorted(r["demo"] for r in runs) != [33, 34] or len({r["run_id"] for r in runs}) != 2:
        raise ValueError("expected two distinct runs for demos 33 and 34")
    for row in runs:
        if (not ID.fullmatch(row["run_id"]) or not Path(row["root"]).is_absolute()
                or type(row.get("source_step")) is not int or row["source_step"] < 0):
            raise ValueError("invalid demo pair entry")
    return sorted(runs, key=lambda r: r["demo"])


def frame_block(directory, step, duration, *, header=False):
    with Image.open(directory / f"{step:06d}.jpg") as original:
        panel = wide_panel(original).resize((640, 345), Image.Resampling.LANCZOS)
    frame = panel.quantize(colors=96, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
    if header:
        yield from GifImagePlugin.getheader(frame, info={"loop": 0})[0]
    yield from GifImagePlugin.getdata(frame, include_color_table=True, duration=duration, disposal=1)


def extend_gif(frames, end, target):
    """Copy finalized GIF blocks untouched; decode/quantize only new sampled boundaries."""
    cursor = target.with_suffix(".cursor.json")
    prior = read_json(cursor) if target.is_file() else {}
    if prior and prior["end_step"] > end:
        raise ValueError("the recorded timeline moved backwards")
    if prior.get("end_step") == end:
        return prior
    for step in range(prior.get("end_step", -1) + 1, end + 1):
        if not (frames / f"{step:06d}.jpg").is_file():
            raise ValueError(f"missing recorded boundary {step}")

    started = time.monotonic()
    cutoff = end - end % STRIDE
    next_step = prior.get("prefix_step", 0)
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as stream:
        partial = Path(stream.name)
        try:
            if next_step:
                # Earlier samples and their 100ms delays never change. Discard the previous
                # partial interval and its endpoint pause before adding the next boundaries.
                with target.open("rb") as previous:
                    remaining = prior["prefix_bytes"]
                    while remaining:
                        block = previous.read(min(remaining, 1024 * 1024))
                        if not block:
                            raise ValueError("truncated cumulative GIF")
                        stream.write(block)
                        remaining -= len(block)
            for step in range(next_step, cutoff, STRIDE):
                stream.writelines(frame_block(frames, step, 100, header=step == 0))
            prefix_bytes = stream.tell()
            # Time differences are in GIF centiseconds, rounded to the nearest 10ms.
            partial_ms = (end % STRIDE * 10 + 4) // 8 * 10
            if cutoff < end:
                stream.writelines(frame_block(frames, cutoff, partial_ms, header=cutoff == 0))
            stream.writelines(frame_block(frames, end, END_HOLD_MS, header=end == 0))
            stream.write(b";")
            stream.close()
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
    result = dict(end_step=end, prefix_step=cutoff, prefix_bytes=prefix_bytes,
                  duration_ms=cutoff // STRIDE * 100 + partial_ms + END_HOLD_MS,
                  publisher_wall_s=round(time.monotonic() - started, 4))
    write_atomic(cursor, json.dumps(result).encode())
    return result


def lifecycle(attempt, metrics):
    state = metrics.get("status", "")
    if attempt.get("status") == "failed" or state in ("failed", "interrupted", "error", "missing_attempt"):
        return "failed"
    if attempt.get("activity") == "closed" or state in ("completed", "closed", "review_ready"):
        return "closed"
    if attempt.get("status") == "held" or state in ("held", "holding"):
        return "held"
    return "running" if attempt or state == "collecting" else "waiting"


def newest_boundary(frames, current):
    """Discover atomically published frames without listing or rereading the whole run."""
    def present(step):
        return (frames / f"{step:06d}.jpg").is_file()

    if current is None or not present(current):
        if current is not None or not present(0):
            return current
        current = 0
    base, width = current, 1
    while present(base + width):
        current = base + width
        width *= 2
    upper = base + width
    while current + 1 < upper:
        middle = (current + upper) // 2
        if present(middle):
            current = middle
        else:
            upper = middle
    return current


def snapshot_run(run, destination, telemetry, launcher, *, force):
    run_id = run["run_id"]
    trace = Path(run["root"]) / "output/operator-traces" / run_id
    attempt = read_json(trace / "attempt.json")
    if attempt and attempt.get("run_id") != run_id:
        raise ValueError("attempt identity differs from selected run")
    metrics = next((r for r in telemetry if r.get("run_id") == run_id and r.get("demo") == run["demo"]), {})
    status = lifecycle(attempt, metrics)
    terminal = launcher.get("state") in ("finished", "failed", "interrupted")
    worker = next((r for r in launcher.get("runs", []) if r["run_id"] == run_id), {})
    code = worker.get("returncode")
    if type(code) is int:
        status = "closed" if code == 0 and attempt.get("activity") == "closed" else "failed"
    elif terminal and status not in ("closed", "failed"):
        status = "failed"
    frames = trace / "segment-frames"
    end = attempt.get("simulation_steps")
    if not (type(end) is int and end >= 0):
        end = None
    if end is None and (frames / "000000.jpg").is_file():
        end = 0
    if metrics.get("steps") is not None and type(metrics["steps"]) is int and metrics["steps"] >= 0:
        end = max(end or 0, metrics["steps"])
    media_path = f"{MEDIA}/{run_id}/full-4x.gif"
    target = destination / media_path
    prior = read_json(target.with_suffix(".cursor.json")) if target.is_file() else {}
    published_end = prior.get("end_step")
    if status not in ("closed", "failed") or end is None:
        end = newest_boundary(frames, max(end or 0, published_end or 0) if
                              end is not None or published_end is not None else None)
    local = dict(demo=run["demo"], run_id=run_id, source_step=run["source_step"], end_step=end,
                 status=status, gif_error=False)
    # A manifest may exist before the reset produces its first JPG.
    if end is not None and (end > 0 or (frames / "000000.jpg").is_file()):
        due = (published_end is None or force or status in ("closed", "failed") or
               (end > published_end and (end - published_end >= 80 or
                time.time() - target.stat().st_mtime >= 30)))
        if due:
            try:
                prior = extend_gif(frames, end, target)
            except (ValueError, OSError) as error:
                logging.warning("Demo %s GIF update deferred: %s", run["demo"], error)
                local["gif_error"] = True
    for public, key in (("transitions_per_minute", "transitions_per_min"), ("wall_s", "wall_s"),
                        ("actor_calls_attempted", "actor_calls_attempted")):
        val = metrics.get(key, attempt.get(key))
        local[public] = val if numeric(val) else None
    local.update(gif_end_step=prior.get("end_step"), gif_url=media_path if prior else None,
                 gif_duration_ms=prior.get("duration_ms"), publisher_wall_s=prior.get("publisher_wall_s"))
    return local


def publish_once(manifest, destination, *, force=False):
    runs = pair_runs(manifest)
    telemetry = read_json(manifest.with_name("telemetry.json"))
    if telemetry.get("schema") != "phyrc-pair-live-v1":
        telemetry = {}
    gpu = telemetry.get("gpu") or {}
    performance = dict(gpu={key: gpu.get(key) if numeric(gpu.get(key)) else None
                            for key in ("utilization_pct", "memory_used_mib", "memory_total_mib")})
    cpu = telemetry.get("cpu_utilization_pct")
    performance["cpu_utilization_pct"] = cpu if numeric(cpu) else None
    stamp = telemetry.get("sampled_at_utc")
    performance["sampled_at_utc"] = stamp if isinstance(stamp, str) and len(stamp) <= 40 else None
    launcher = read_json(manifest.with_name("finished.json")) or read_json(manifest.with_name("pair-state.json"))
    rows = [snapshot_run(run, destination, telemetry.get("runs", []), launcher, force=force)
            for run in runs]
    state = dict(schema="phyrc-demo-compare-v1", runs=rows, performance=performance)
    save_changed(destination / STATE, json.dumps(state, allow_nan=False).encode())
    save_changed(destination / PAGE, TEMPLATE.read_bytes())
    return state


class PairFiles(BaseHTTPRequestHandler):
    """Read-only gateway for the authenticated Jupyter server-proxy route."""
    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        route = urlsplit(self.path).path.lstrip("/")
        if not route:
            route = PAGE
        kind = self.server.routes.get(route)
        if not kind:
            self.send_error(404)
            return
        try:
            source = (self.server.destination / route).open("rb")
        except FileNotFoundError:
            self.send_error(404)
            return
        with source:
            self.send_response(200)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(os.fstat(source.fileno()).st_size))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            if self.command == "GET":
                try:
                    shutil.copyfileobj(source, self.wfile, 128 * 1024)
                except (ConnectionResetError, BrokenPipeError):
                    pass

    def log_message(self, format, *args):
        pass


def gateway(port, destination, runs):
    server = ThreadingHTTPServer(("127.0.0.1", port), PairFiles)
    server.destination = destination
    server.routes = {PAGE: "text/html; charset=utf-8", STATE: "application/json"}
    for run in runs:
        server.routes[f"{MEDIA}/{run['run_id']}/full-4x.gif"] = "image/gif"
    return server


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pair", type=Path, required=True, help="pair.json written by the dual-run launcher")
    p.add_argument("--destination", type=Path, default=Path.home())
    p.add_argument("--proxy-port", type=int, help="serve these four files on loopback for Jupyter Server Proxy")
    p.add_argument("--once", action="store_true", help="publish both GIFs to the latest recorded boundary and exit")
    args = p.parse_args()
    if args.proxy_port is not None and (args.once or not 0 < args.proxy_port <= 65535):
        p.error("choose a valid proxy port for continuous mode")
    runs = pair_runs(args.pair)
    args.destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    with ExitStack() as stack:
        lock = stack.enter_context((args.destination / ".PhyRC-compare.lock").open("a"))
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.proxy_port is not None:
            server = stack.enter_context(gateway(args.proxy_port, args.destination, runs))
            Thread(target=server.serve_forever, daemon=True).start()
            stack.callback(server.shutdown)
        while True:
            try:
                state = publish_once(args.pair, args.destination, force=args.once)
            except (OSError, ValueError) as exc:
                if args.once:
                    raise
                # Keep the previous complete snapshot online across temporary resource or I/O failures.
                logging.warning("Pair publication deferred: %s", exc)
                time.sleep(5)
                continue
            if args.once:
                if any(run["gif_error"] for run in state["runs"]):
                    p.exit(1, "One or more timelines have missing or unreadable source frames.\n")
                return
            time.sleep(5)


if __name__ == "__main__":
    main()
