"""Publish a private Jupyter gallery with media served as separate files."""
import argparse
from contextlib import closing
import fcntl
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
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


def write_atomic(path, content):
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as staged:
        temp = Path(staged.name)
        try:
            staged.write(content)
            staged.close()
            temp.replace(path)
        finally:
            temp.unlink(missing_ok=True)


def publish_clip(source, target):
    if target.is_file():
        return
    with source.open('rb') as stream:
        if stream.read(8)[4:] != b'ftyp':
            raise ValueError(f"Missing MP4 header: {source}")
        stream.seek(0)
        with tempfile.TemporaryDirectory(dir=target.parent) as directory:
            staged = Path(directory) / target.name
            with staged.open('xb') as output:
                shutil.copyfileobj(stream, output)
            staged.replace(target)


def cumulative(group, segment, frames, end, previous, *, widescreen):
    if __package__:
        from .cumulative_gif import gif_delta, write_cumulative_gif
    else:
        from cumulative_gif import gif_delta, write_cumulative_gif

    target = group / (segment + '.gif')
    if target.is_file():
        return True
    if frames is None or not (frames / '000000.jpg').is_file():
        return False
    last_id, last_end = previous if previous else (None, None)
    delta = gif_delta(frames, last_end, end, widescreen=widescreen)
    write_cumulative_gif(target, group / (last_id + '.gif') if last_id else None, delta)
    return True


def publish(review_dir, destination, template, traces=None, *, widescreen=False):
    entry = destination / ENTRY
    checkpoint = destination / ".PhyRC-review-publisher.json"
    header = template.read_bytes()
    uri = (review_dir / "journal.sqlite3").resolve().as_uri() + "?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as db:
        db.create_function("gallery_run", 1, included_run, deterministic=True)
        rows = db.execute(
            "SELECT run,segment,payload FROM segments WHERE gallery_run(run) ORDER BY rowid"
        ).fetchall()
        has_controls = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='autonomous_runs'").fetchone()
        controls = dict(db.execute(
            "SELECT run,status FROM autonomous_runs WHERE gallery_run(run)"
        )) if has_controls else {}
    fingerprint = hashlib.sha256(header + json_block("state", [rows, controls])).hexdigest()
    stamp = {"catalog": fingerprint}
    if checkpoint.exists() and entry.exists() and json.loads(checkpoint.read_text()) == stamp:
        return

    gallery = destination / "PhyRC-gallery"
    gallery.mkdir(mode=0o700, exist_ok=True)
    records = []
    gifs = {}
    for run, segment, raw in rows:
        if not ID.fullmatch(run) or not ID.fullmatch(segment):
            raise ValueError("Invalid identifier in review journal")
        group = gallery / run
        group.mkdir(mode=0o700, exist_ok=True)
        target = group / (segment + ".mp4")
        if not target.is_file():
            source = review_dir / "media" / run / target.name
            if widescreen:
                source = wide_clip(source, review_dir / 'wide-media' / run)
            publish_clip(source, target)

        record = json.loads(raw)
        meta = {field: record[field] for field in FIELDS}
        meta.update(run=run, id=segment)
        if record.get('replay_prefix_steps') and record.get('parent_attempt'):
            meta.update(replay_steps=record['replay_prefix_steps'], parent_run=record['parent_attempt'])
        frames = traces / run / 'segment-frames' if traces is not None else None
        if cumulative(group, segment, frames, record['end_step'], gifs.get(run), widescreen=widescreen):
            meta['gif'] = True
            gifs[run] = (segment, record['end_step'])
        records.append(meta)

        for name in (segment + ".html", "index.html"):
            link = group / name
            if not link.is_symlink():
                link.symlink_to(Path("../..") / ENTRY)

    write_atomic(entry, header + json_block("catalog", {"clips": records, "controls": controls}))
    write_atomic(checkpoint, json.dumps(stamp).encode())


def included_run(run):
    match = re.search(r"(?:^|[-_])demo[-_]?(\d+)(?=$|[-_])", run, re.IGNORECASE)
    return match is not None and int(match[1]) >= 14


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
                        args.traces, widescreen=True)
            except (sqlite3.Error, OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
                if args.once:
                    raise
                logging.warning("Gallery publication deferred: %s", exc)
            if args.once:
                return
            time.sleep(4)


if __name__ == "__main__":
    main()
