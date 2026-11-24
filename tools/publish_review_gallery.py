"""Append reviewed clips to the user's private, self-contained Jupyter gallery."""
import argparse
import base64
from contextlib import closing
import fcntl
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import tempfile
import time

if __package__:
    from .review_wide_media import wide_clip
else:
    from review_wide_media import wide_clip

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "PhyRC-review.html"
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,119}")
FIELDS = ("stage", "start_step", "end_step", "analysis", "next_prompt")


def json_block(kind, value):
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'<script type="application/json" data-{kind}>{encoded}</script>\n'.encode()


def append_cumulative(stream, group, segment, frames, end, previous, *, widescreen):
    if __package__:
        from .cumulative_gif import gif_delta, write_cumulative_gif
    else:
        from cumulative_gif import gif_delta, write_cumulative_gif

    last_id, last_end = previous if previous else (None, None)
    if last_id is not None and not ID.fullmatch(last_id):
        raise ValueError('Invalid previous GIF identifier')
    delta = gif_delta(frames, last_end, end, widescreen=widescreen)
    write_cumulative_gif(group / (segment + '.gif'), group / (last_id + '.gif') if last_id else None, delta)
    stream.write(b'<script type="application/octet-stream" data-gif-delta>')
    stream.write(base64.b64encode(delta))
    stream.write(b'!</script>\n')


def publish(review_dir, destination, template, retrospective, traces=None, *, widescreen=False):
    entry = destination / ENTRY
    checkpoint = destination / ".PhyRC-review-publisher.json"
    header = template.read_bytes()
    revision = hashlib.sha256(header + os.fsencode(traces or '') + (b'wide-v1' if widescreen else b'')).hexdigest()
    previous = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
    rebuild = (revision != previous.get("template") or not entry.exists()
               or entry.stat().st_size < previous.get("offset", 0))
    state = {} if rebuild else previous.copy()
    uri = (review_dir / "journal.sqlite3").resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        rows = db.execute("SELECT rowid,run,segment,payload FROM segments WHERE rowid>? ORDER BY rowid",
                          (state.get("rowid", 0),)).fetchall()
        has_controls = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='autonomous_runs'").fetchone()
        controls = dict(db.execute("SELECT run,status FROM autonomous_runs")) if has_controls else {}
    retro = json.loads(retrospective.read_text()) if retrospective.exists() else None
    extra = bytearray()
    for key, value in (("control", controls), ("retro", retro)):
        encoded = json_block(key, value)
        digest = hashlib.sha256(encoded).hexdigest()
        if digest != state.get(key):
            extra.extend(encoded)
            state[key] = digest
    if not rebuild and not rows and not extra and entry.stat().st_size == state["offset"]:
        return
    gallery = destination / "PhyRC-gallery"
    gallery.mkdir(mode=0o700, exist_ok=True)
    gifs = state.setdefault('gifs', {})
    staging = tempfile.NamedTemporaryFile(dir=destination, delete=False) if rebuild else None
    try:
        with (staging if rebuild else entry.open("r+b")) as stream:
            if rebuild:
                stream.write(header)
            else:
                # Resume from the last durable batch after an interrupted append.
                stream.seek(state["offset"])
                stream.truncate()
            stream.write(extra)
            for rowid, run, segment, raw in rows:
                if not ID.fullmatch(run) or not ID.fullmatch(segment):
                    raise ValueError("Invalid identifier in review journal")
                source = review_dir / "media" / run / (segment + ".mp4")
                if widescreen:
                    source = wide_clip(source, review_dir / 'wide-media' / run)
                clip = source.read_bytes()
                if clip[4:8] != b"ftyp":
                    raise ValueError(f"Missing MP4 header for {run}/{segment}")
                record = json.loads(raw)
                meta = {field: record[field] for field in FIELDS}
                meta.update(run=run, id=segment)
                if record.get('replay_prefix_steps') and record.get('parent_attempt'):
                    meta.update(replay_steps=record['replay_prefix_steps'], parent_run=record['parent_attempt'])
                group = gallery / run
                group.mkdir(mode=0o700, exist_ok=True)
                stream.write(json_block("record", meta))
                stream.write(b'<script type="application/octet-stream" data-video>')
                stream.write(base64.b64encode(clip))
                stream.write(b'!</script>\n')
                frames = traces / run / 'segment-frames' if traces is not None else None
                if frames is not None and (frames / '000000.jpg').is_file():
                    append_cumulative(stream, group, segment, frames, record['end_step'], gifs.get(run),
                                      widescreen=widescreen)
                    gifs[run] = [segment, record['end_step']]
                link = group / (segment + ".html")
                if not link.is_symlink():
                    link.symlink_to(Path("../..") / ENTRY)
                state["rowid"] = rowid
            state.update(offset=stream.tell(), template=revision)
            stream.flush()
            os.fsync(stream.fileno())
        if rebuild:
            os.replace(staging.name, entry)
        with tempfile.NamedTemporaryFile(mode="w", dir=destination, delete=False) as tmp:
            json.dump(state, tmp)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp.name, checkpoint)
    finally:
        if staging:
            Path(staging.name).unlink(missing_ok=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--review-dir", type=Path, default=ROOT / "output/segment-review")
    p.add_argument("--destination", type=Path, default=Path.home())
    p.add_argument("--traces", type=Path, help="Generate cumulative GIFs from recorded public frames in this directory")
    p.add_argument("--once", action="store_true")
    args = p.parse_args()
    args.destination.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (args.destination / ".PhyRC-review-publisher.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        while True:
            try:
                publish(args.review_dir, args.destination, ROOT / "tools/review_gallery.html",
                        ROOT / "docs/active/guided-retrospective.json", args.traces, widescreen=True)
            except (sqlite3.Error, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
                if args.once:
                    raise
                logging.warning("Gallery publication deferred: %s", exc)
            if args.once:
                return
            time.sleep(4)


if __name__ == "__main__":
    main()
