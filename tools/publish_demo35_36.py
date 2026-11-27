"""Publish the latest 400 transitions for Demos 35 and 36 in authenticated Jupyter."""

import argparse
import base64
import fcntl
from functools import lru_cache
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
import time

from tools.publish_demo_pair import END_HOLD_MS, ID, STRIDE, frame_block, newest_boundary


PAGE = "PhyRC-demo35-36.html"
WINDOW_STEPS = 400
PANELS = {
    35: ("바깥 밑단으로 팔꿈치 곡선 따라가기",
         "노란 몸통 밑단 바깥쪽을 잡고 전완을 따라 팔꿈치 방향으로 유도합니다."),
    36: ("소매 가까이에서 팔꿈치로 직접 유도하기",
         "실제 소매 출구 옆의 파란 천을 잡고 소매 끝을 팔꿈치 방향으로 직접 유도합니다."),
}
TEMPLATE = """<!doctype html>
<html lang="ko">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>PhyRC 시연 35·36 비교</title>
<style>
body { margin: 0; background: #141414; color: #f1f1f1; font: 16px system-ui, sans-serif; }
header { padding: 16px 22px 10px; }
h1, h2, p { margin: 0 0 6px; }
p { color: #c5c5c5; }
main { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; margin: 0 22px 22px; }
section { padding: 12px; background: #222; border-radius: 8px; }
img, .waiting { display: block; width: 100%; aspect-ratio: 640 / 345; }
.waiting { display: grid; place-items: center; background: #191919; }
@media (max-width: 720px) { main { grid-template-columns: 1fr; } }
</style>
<header><h1>PhyRC 시연 35·36 비교</h1><p>PLAYBACK_STATUS</p></header>
<main>PANELS</main>
<script>
window.addEventListener('load', async () => {
  if (!document.referrer) return;
  try {
    await Promise.all(Array.from(document.images, image => image.decode()));
  } catch {
    return;
  }
  const parentOrigin = new URL(document.referrer).origin;
  window.parent.postMessage({
    type: 'phyrc-comparison-ready', version: CLIP_VERSION, delayMs: REFRESH_MS
  }, parentOrigin);
});
</script>
</html>
"""


def frame_directories(pair_path):
    pair = json.loads(pair_path.read_text())
    root = pair_path.parents[3]
    runs = sorted(pair.get("runs", []), key=lambda run: run["demo"])
    if (pair.get("schema") != "phyrc-concurrent-pair-v1"
            or pair_path.parent.parent != root / "output" / "demo35-36"
            or [run["demo"] for run in runs] != list(PANELS)
            or len({run["run_id"] for run in runs}) != len(PANELS)):
        raise ValueError("Expected a launcher manifest for Demos 35 and 36")
    for run in runs:
        if Path(run["root"]).resolve() != root or not ID.fullmatch(run["run_id"]):
            raise ValueError("Invalid gallery run identity")
    return [root / "output" / "operator-traces" / run["run_id"] / "segment-frames" for run in runs]


@lru_cache(maxsize=160)
def encoded_frame(directory, step, duration, header):
    return b"".join(frame_block(directory, step, duration, header=header))


def clip(directory, end):
    start = max(0, end - WINDOW_STEPS)
    points = [start, *range((start // STRIDE + 1) * STRIDE, end, STRIDE)]
    if points[-1] != end:
        points.append(end)
    frames = []
    previous_time = 0
    for step, next_step in zip(points, points[1:]):
        timestamp = ((next_step - start) * 10 + STRIDE // 2) // STRIDE * 10
        frames.append(encoded_frame(directory, step, timestamp - previous_time, step == start))
        previous_time = timestamp
    frames.append(encoded_frame(directory, end, END_HOLD_MS, end == start))
    return start, base64.b64encode(b"".join(frames) + b";").decode("ascii")


def render_panel(demo, directory, end, finished):
    title, direction = PANELS[demo]
    header = f"<h2>시연 {demo} · {title}</h2><p>{direction}</p>"
    if end is None:
        status = "기록된 화면이 없습니다." if finished else "첫 화면을 기다리는 중입니다."
        return f'<section>{header}<p class="waiting">{status}</p></section>'
    start, encoded = clip(directory, end)
    return (
        f"<section>{header}<p>{start}–{end}전이 · 4배속</p>"
        f'<img alt="시연 {demo}의 5개 카메라 화면" src="data:image/gif;base64,{encoded}"></section>'
    )


def write_page(page, directories, ends, finished):
    status = "마지막 400전이 · 4배속" if finished else "최신 400전이 · 4배속 · 자동 갱신"
    panels = "".join(render_panel(demo, directory, end, finished)
                     for demo, directory, end in zip(PANELS, directories, ends))
    versions = [0 if end is None else end + 1 for end in ends]
    version = json.dumps(f"{versions[0]}-{versions[1]}-{int(finished)}")
    document = (TEMPLATE.replace("PLAYBACK_STATUS", status).replace("PANELS", panels)
                .replace("CLIP_VERSION", version).replace("REFRESH_MS", "null" if finished else "30000"))
    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=page.parent, delete=False) as stream:
        staged = Path(stream.name)
        try:
            stream.write(document)
            stream.flush()
            staged.replace(page)
        finally:
            staged.unlink(missing_ok=True)


def publish(pair_path, page, *, once):
    directories = frame_directories(pair_path)
    ends = (None, None)
    previous = None
    while True:
        ends = tuple(newest_boundary(directory, end) for directory, end in zip(directories, ends))
        finished = (pair_path.parent / "finished.json").is_file()
        current = (ends, finished)
        if current != previous:
            try:
                write_page(page, directories, ends, finished)
            except OSError as error:
                if once:
                    raise
                print(f"Gallery update deferred: {error}", flush=True)
            else:
                print(f"Demos 35/36 at {ends}, final={finished}", flush=True)
                previous = current
                if finished:
                    return
        if once:
            return
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", type=Path, required=True)
    parser.add_argument("--destination", type=Path, default=Path.home())
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    page = args.destination.resolve() / PAGE
    try:
        with page.with_name(f".{PAGE}.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            publish(args.pair.resolve(), page, once=args.once)
    except (OSError, KeyError, ValueError) as error:
        parser.exit(1, f"Gallery publisher failed: {error}\n")


if __name__ == "__main__":
    main()
