"""Trusted-side segment journal and loopback video review. Python standard library."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
from urllib.parse import parse_qs, urlsplit
import zipfile


ID = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.-]{0,119}\Z")
ACTIONS = ("accept", "revise", "hold", "finish")
OUTCOMES = ("success", "partial", "failure", "uncertain")
SCHEMA = """
CREATE TABLE IF NOT EXISTS segments (
  run TEXT NOT NULL, segment TEXT NOT NULL, payload TEXT NOT NULL,
  digest TEXT NOT NULL, created TEXT NOT NULL, claimed TEXT,
  PRIMARY KEY (run, segment)
);
CREATE TABLE IF NOT EXISTS feedback (
  run TEXT NOT NULL, segment TEXT NOT NULL, id TEXT NOT NULL,
  action TEXT NOT NULL, text TEXT NOT NULL, created_at TEXT NOT NULL,
  PRIMARY KEY (run, segment, id),
  FOREIGN KEY (run, segment) REFERENCES segments(run, segment)
);
"""


AUTONOMY_SCHEMA = """
CREATE TABLE IF NOT EXISTS autonomous_runs (
  run TEXT PRIMARY KEY, status TEXT NOT NULL, held_segment TEXT
);
CREATE TABLE IF NOT EXISTS interventions (
  run TEXT NOT NULL REFERENCES autonomous_runs(run), id TEXT NOT NULL, created TEXT NOT NULL,
  PRIMARY KEY(run,id)
);
"""


class Conflict(ValueError):
    """A different decision or publication already owns this identifier."""


def timestamp():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def json_text(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True)


def identifier(value, field):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise ValueError(f"invalid {field} identifier")
    return value


def required_text(value, field, limit=12000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{field} must contain 1–{limit} characters")
    return value.strip()


def validate_record(value):
    if not isinstance(value, dict):
        raise ValueError("record must be an object")
    required = {"run_id", "segment_id", "stage", "start_step", "end_step", "parent",
                "prompt", "analysis", "next_prompt", "labels", "outcome", "score_before",
                "score_after", "score_source", "physics_profile", "upstream_revision"}
    optional = {"observation_id", "evidence", "hold_reason", "source_group", "parent_attempt",
                "replay_prefix_steps", "initial_slot", "reviewer_model", "review_frame_steps",
                "score_breakdown_before", "score_breakdown_after",
                "evaluator_success_before", "evaluator_success_after", "review_source"}
    if value.get("review_source", "action_actor") not in ("action_actor", "unassessed"):
        raise ValueError("invalid review source")
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing or unknown:
        raise ValueError(f"missing fields {sorted(missing)}, unknown fields {sorted(unknown)}")
    record = dict(value)
    for field in ("run_id", "segment_id", "stage"):
        identifier(record[field], field)
    for field in ("prompt", "analysis", "next_prompt", "physics_profile"):
        record[field] = required_text(record[field], field)
    if (not isinstance(record["upstream_revision"], str) or
            not re.fullmatch("[a-fA-F0-9]{7,40}", record["upstream_revision"])):
        raise ValueError("upstream_revision must be a Git commit hash")
    record["upstream_revision"] = record["upstream_revision"].lower()
    if record["outcome"] not in OUTCOMES:
        raise ValueError(f"outcome must be one of {OUTCOMES}")
    labels = record["labels"]
    if not isinstance(labels, list) or not 1 <= len(labels) <= 64:
        raise ValueError("labels must contain 1–64 semantic tags")
    for label in labels:
        identifier(label, "label")
    if len(set(labels)) != len(labels):
        raise ValueError("duplicate semantic labels")
    start, end = record["start_step"], record["end_step"]
    if type(start) is not int or type(end) is not int or not 0 <= start <= end:
        raise ValueError("expected 0 <= start_step <= end_step (half-open transition range)")
    for field in ("score_before", "score_after"):
        score = record[field]
        if score is not None and (type(score) not in (int, float) or not 0 <= score <= 50):
            raise ValueError(f"{field} must be a raw evaluator score in [0,50] or null")
    if any(record[k] is not None for k in ("score_before", "score_after", "score_source")):
        record["score_source"] = required_text(record["score_source"], "score_source", 2000)
    parent = record["parent"]
    if parent is not None:
        if not isinstance(parent, dict) or set(parent) != {"run_id", "segment_id"}:
            raise ValueError("parent must be null or contain run_id and segment_id")
        for field in parent:
            identifier(parent[field], "parent." + field)
    for field in ("observation_id", "hold_reason", "source_group", "reviewer_model"):
        if field in record:
            record[field] = required_text(record[field], field, 512)
    for field in ("parent_attempt", "initial_slot"):
        if record.get(field) is not None:
            record[field] = required_text(record[field], field, 1000)
    prefix = record.get("replay_prefix_steps", 0)
    if type(prefix) is not int or prefix < 0:
        raise ValueError("replay_prefix_steps must be a nonnegative integer")
    frames = record.get("review_frame_steps", [])
    if not isinstance(frames, list) or any(type(step) is not int or not start <= step <= end
                                           for step in frames) or frames != sorted(set(frames)):
        raise ValueError("review_frame_steps must be unique ordered observation steps within the clip")
    for field in ("evaluator_success_before", "evaluator_success_after"):
        if record.get(field) is not None:
            if type(record[field]) is not bool or not record["score_source"]:
                raise ValueError(f"{field} requires a boolean and score_source, or null")
    for field in ("score_breakdown_before", "score_breakdown_after"):
        breakdown = record.get(field)
        if breakdown is not None:
            if not isinstance(breakdown, dict) or not record["score_source"]:
                raise ValueError(f"{field} requires component points and score_source")
            for component, points in breakdown.items():
                identifier(component, "score component")
                if type(points) not in (float, int) or not 0 <= points <= 50:
                    raise ValueError("invalid component points")
    evidence = record.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) > 100:
        raise ValueError("evidence must be an array of up to 100 references")
    for item in evidence:
        required_text(item, "evidence reference", 2000)
    return record


@contextmanager
def journal(root, write=False):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "journal.sqlite3", timeout=15)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA foreign_keys = ON")
        if db.execute("PRAGMA user_version").fetchone()[0] < 2:
            db.executescript("BEGIN IMMEDIATE;\n" + SCHEMA + AUTONOMY_SCHEMA + "PRAGMA user_version=2; COMMIT;")
        db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield db
        db.commit()
    finally:
        db.close()


def register_autonomy(root, run_id):
    with journal(root, write=True) as db:
        db.execute("INSERT INTO autonomous_runs VALUES (?, 'running', NULL)", (identifier(run_id, "run"),))


def control_state(root, run_id):
    with journal(root) as db:
        row = db.execute("SELECT status FROM autonomous_runs WHERE run=?", (run_id,)).fetchone()
        return row["status"] if row else None


def request_intervention(root, value):
    if not isinstance(value, dict) or set(value) != {"run_id", "id"}:
        raise ValueError("expected run_id and id")
    run, key = identifier(value["run_id"], "run"), identifier(value["id"], "intervention")
    with journal(root, write=True) as db:
        row = db.execute("SELECT status FROM autonomous_runs WHERE run=?", (run,)).fetchone()
        if not row:
            raise Conflict("this run does not use autonomous control")
        existing = db.execute("SELECT created FROM interventions WHERE run=? AND id=?", (run, key)).fetchone()
        if existing:
            return dict(run_id=run, id=key, created_at=existing["created"], control_state=row["status"])
        if row["status"] not in ("running", "pause_requested", "held"):
            raise Conflict("controller is closing or unavailable")
        created = timestamp()
        db.execute("INSERT INTO interventions VALUES (?,?,?)", (run, key, created))
        status = "held" if row["status"] == "held" else "pause_requested"
        db.execute("UPDATE autonomous_runs SET status=? WHERE run=?", (status, run))
        return dict(run_id=run, id=key, created_at=created, control_state=status)


def decide_boundary(root, run, segment, terminal, *, require_feedback=False):
    """Serialize a published boundary decision against new operator requests."""
    with journal(root, write=True) as db:
        row = db.execute("SELECT status FROM autonomous_runs WHERE run=?", (run,)).fetchone()
        if require_feedback or row["status"] == "pause_requested":
            status = "held"
        else:
            status = "closing" if terminal else "running"
        db.execute("UPDATE autonomous_runs SET status=?, held_segment=? WHERE run=?",
                   (status, segment if status == "held" else None, run))
        return status


def set_control_state(root, run, status):
    with journal(root, write=True) as db:
        db.execute("UPDATE autonomous_runs SET status=?, held_segment=NULL WHERE run=?", (status, run))


def select_row(db, run=None, segment=None):
    if segment is not None and run is None:
        raise ValueError("segment requires run")
    filters, params = [], []
    for key, item in (("run", run), ("segment", segment)):
        if item is not None:
            filters.append(key + " = ?")
            params.append(identifier(item, key))
    where = " WHERE " + " AND ".join(filters) if filters else ""
    return db.execute("SELECT * FROM segments" + where + " ORDER BY rowid DESC LIMIT 1", params).fetchone()


def hydrate(db, row):
    rec = json.loads(row["payload"])
    run, seg = row["run"], row["segment"]
    media = f"media/{run}/{seg}.mp4"
    replies = db.execute("SELECT id, action, text, created_at FROM feedback "
                         "WHERE run=? AND segment=? ORDER BY rowid", (run, seg))
    rec.update(schema="phyrc-segment-v1", created_at=row["created"], clip_url="/" + media,
               clip_path=media, clip_sha256=row["digest"], claimed_feedback_id=row["claimed"],
               feedback=[dict(reply) for reply in replies])
    control = db.execute("SELECT status FROM autonomous_runs WHERE run=?", (run,)).fetchone()
    if control:
        rec.update(control_mode="gpt_only", control_state=control["status"])
    return rec


def get_segment(root, run_id=None, segment_id=None):
    with journal(root) as db:
        row = select_row(db, run_id, segment_id)
        return hydrate(db, row) if row else None


def publish_segment(root, record, clip):
    """Atomically publish immutable metadata + MP4; identical retries return the original."""
    record = validate_record(record)
    run, seg, parent = record["run_id"], record["segment_id"], record["parent"]
    payload = json_text(record)
    directory = Path(root) / "media" / run
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (seg + ".mp4")
    temporary = None
    try:
        with Path(clip).open("rb") as source, tempfile.NamedTemporaryFile(
                dir=directory, suffix=".part", delete=False) as copy:
            temporary = Path(copy.name)
            header = source.read(12)
            if len(header) < 12 or header[4:8] != b"ftyp":
                raise ValueError("expected an MP4 clip with an ftyp header")
            digest = hashlib.sha256(header)
            copy.write(header)
            while chunk := source.read(1024 * 1024):
                copy.write(chunk)
                digest.update(chunk)
            copy.flush()
            os.fsync(copy.fileno())
        sha = digest.hexdigest()
        with journal(root, write=True) as db:
            old = select_row(db, run, seg)
            if old and (old["payload"] != payload or old["digest"] != sha):
                raise Conflict("segment ID already published with different content")
            if not old:
                if parent and not select_row(db, parent["run_id"], parent["segment_id"]):
                    raise ValueError("parent segment has not been published")
                db.execute("INSERT INTO segments(run,segment,payload,digest,created) "
                           "VALUES (?,?,?,?,?)", (run, seg, payload, sha, timestamp()))
                old = select_row(db, run, seg)
            # Readers see the file only via its committed database entry. An interrupted
            # new publish can leave an unreferenced file, replaced by a later retry.
            os.replace(temporary, path)
            return hydrate(db, old)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def state(root, run=None, segment=None):
    with journal(root) as db:
        row = select_row(db, run, segment)
        if (run or segment) and not row:
            raise KeyError("unknown run or segment")
        runs = [r["run"] for r in db.execute("SELECT run FROM segments GROUP BY run "
                                             "ORDER BY MAX(rowid) DESC")]
        if not row:
            return dict(latest=None, segments=[], runs=runs, can_feedback=False)
        history = db.execute("SELECT segment, json_extract(payload,'$.stage') AS stage, "
                             "json_extract(payload,'$.outcome') AS outcome "
                             "FROM segments WHERE run=? ORDER BY rowid DESC", (row["run"],))
        segments = [dict(run_id=row["run"], segment_id=s["segment"],
                         stage=s["stage"], outcome=s["outcome"]) for s in history]
        latest = hydrate(db, row)
        control = db.execute("SELECT held_segment FROM autonomous_runs WHERE run=?", (row["run"],)).fetchone()
        return dict(latest=latest, segments=segments, runs=runs,
                    can_feedback=row["claimed"] is None and row["segment"] == segments[0]["segment_id"]
                    and (control is None or control["held_segment"] == row["segment"]))


def submit_feedback(root, value):
    if not isinstance(value, dict) or set(value) != {"run_id", "segment_id", "id", "action", "text"}:
        raise ValueError("expected run_id, segment_id, id, action and text")
    run, seg, key = [identifier(value[field], field) for field in ("run_id", "segment_id", "id")]
    action, message = value["action"], value["text"]
    if action not in ACTIONS or not isinstance(message, str) or len(message) > 4000:
        raise ValueError("invalid feedback action or text")
    message = message.strip()
    if action == "revise" and not message:
        raise ValueError("enter a replacement instruction")
    if action == "revise":
        # Catch accidental inclusion of commonly copied evaluator/debug fields.
        # The collector separately limits model inputs to public observations.
        if re.search(r"\b(raw_points|score_breakdown|score_samples|audit|ground[_ -]?truth|"
                     r"seed|privileged[_ -]?state)\b|\bscore\s*[:=]|점수\s*[:=]|[+−-]\s*\d+\s*점",
                     message, re.IGNORECASE):
            raise ValueError("describe the next action using public camera observations")
    with journal(root, write=True) as db:
        row = select_row(db, run, seg)
        if not row:
            raise KeyError("unknown run or segment")
        prior = db.execute("SELECT id,action,text,created_at FROM feedback "
                           "WHERE run=? AND segment=? AND id=?", (run, seg, key)).fetchone()
        if prior:
            if prior["action"] == action and prior["text"] == message:
                return dict(prior)
            raise Conflict("feedback ID already used with different content")
        if row["claimed"] or select_row(db, run)["segment"] != seg:
            raise Conflict("review has moved on; refresh the segment")
        control = db.execute("SELECT held_segment FROM autonomous_runs WHERE run=?", (run,)).fetchone()
        if control and control["held_segment"] != seg:
            raise Conflict("request intervention and wait for its held segment")
        reason = json.loads(row["payload"]).get("hold_reason")
        if reason == "hard_horizon" and action not in ("hold", "finish"):
            raise Conflict("at the hard horizon only hold or finish is available")
        if reason == "review_unavailable" and action == "accept":
            raise Conflict("review unavailable; provide a public-view instruction, hold or finish")
        created = timestamp()
        db.execute("INSERT INTO feedback VALUES (?,?,?,?,?,?)", (run, seg, key, action, message, created))
        return dict(id=key, action=action, text=message, created_at=created)


def claim_feedback(root, run_id, segment_id):
    """Seal a runnable reply before applying it. Re-reading returns the same receipt."""
    with journal(root, write=True) as db:
        row = select_row(db, run_id, segment_id)
        if not row:
            raise KeyError("unknown run or segment")
        if row["segment"] != select_row(db, run_id)["segment"]:
            raise Conflict("only the active segment can supply a new instruction")
        reply = db.execute("SELECT id,action,text,created_at FROM feedback "
                           "WHERE run=? AND segment=? ORDER BY rowid DESC LIMIT 1",
                           (run_id, segment_id)).fetchone()
        if not reply or reply["action"] == "hold":
            return None
        if not row["claimed"]:
            db.execute("UPDATE segments SET claimed=? WHERE run=? AND segment=?",
                       (reply["id"], run_id, segment_id))
        return dict(reply)


def export_rows(root, run):
    identifier(run, "run")
    with journal(root) as db:
        rows = list(db.execute("SELECT * FROM segments WHERE run=? ORDER BY rowid", (run,)))
        if not rows:
            raise KeyError("unknown run")
        return "".join(json_text(hydrate(db, row)) + "\n" for row in rows)


def practice_start(metadata, rows):
    """Keep just the measured reset receipt; seeds stay in the offline supervisor bundle."""
    profile = metadata.get("collection_start")
    if profile is None:
        return None
    if (not isinstance(profile, dict) or metadata.get("schema") != "participant-collection-run-v1"
            or profile.get("profile") != "fresh-nearest-table-cp2"
            or profile.get("verified_after_reset") is not True):
        raise ValueError("unexpected or unverified collection_start profile")
    expected = {"start_step": 0, "table_index": 2}
    if any(type(profile.get(key)) is not int or profile[key] != value for key, value in expected.items()):
        raise ValueError("fresh start requires step zero and the fixed nearest table (index 2)")
    for key in ("requested_seed", "episode_seed"):
        if type(profile.get(key)) is not int or not 0 <= profile[key] < 2**63:
            raise ValueError(f"invalid practice {key}")
    if type(metadata.get("episode_seed")) is not int or metadata["episode_seed"] != profile["episode_seed"]:
        raise ValueError("run seed disagrees with verified collection_start")
    friction = profile.get("shirt_manikin_friction")
    if type(friction) not in (float, int) or not abs(friction - 0.35) <= 1e-6:
        raise ValueError("practice receipt disagrees with checkpoint-2 shirt/manikin friction")
    for row in rows:
        if (row.get("source_group") and row["source_group"] != metadata.get("source_group")
                or row.get("initial_slot") or row.get("replay_prefix_steps", 0)):
            raise ValueError("practice receipt disagrees with segment lineage")
        measured = re.search(r"(?:^|,\s*)shirt/manikin=([0-9.]+)(?:,|$)", row["physics_profile"])
        if measured and not abs(float(measured[1]) - friction) <= 1e-6:
            raise ValueError("segment friction disagrees with collection_start")
    fields = ("profile", "start_step", "requested_seed", "episode_seed", "table_index",
              "shirt_manikin_friction", "verified_after_reset")
    return {key: profile[key] for key in fields}


def final_outcome(run, rows, collection=None):
    """Read the closed recorder's official report and retain only public outcome fields."""
    outcome = dict(schema="phyrc-run-outcome-v1", run_id=run, status="unfinalized",
                   capture_complete=None, valid=None, success_evaluated=None, success=None,
                   raw_points=None, breakdown=None, final_score=None, score_status=None,
                   collection_start=None, sources={})
    if collection is None:
        return outcome
    collection = Path(collection).resolve()
    if not collection.is_dir() or collection.name != run:
        raise ValueError("--collection must be the capture directory named for this run")

    def read_source(name):
        data = (collection / name).read_bytes()
        outcome["sources"][str(name)] = hashlib.sha256(data).hexdigest()
        return json.loads(data)

    if (collection / "run_metadata.json").is_file():
        outcome["collection_start"] = practice_start(read_source("run_metadata.json"), rows)
    if not (collection / "capture.json").exists():
        return outcome
    capture = read_source("capture.json")
    if (capture.get("schema") != "participant-live-capture-v2"
            or type(capture.get("complete")) is not bool
            or type(capture.get("evaluation_enabled")) is not bool
            or type(capture.get("steps")) is not int
            or max(row["end_step"] for row in rows) > capture["steps"]):
        raise ValueError("capture identity, version or step count disagrees with the segment journal")
    outcome["capture_complete"] = capture["complete"]
    if not capture["evaluation_enabled"]:
        outcome["status"] = "unevaluated"
        return outcome
    if not (collection / "evaluation_summary.json").is_file():
        return outcome
    summary = read_source("evaluation_summary.json")
    path = Path(required_text(summary.get("evaluation_path"), "evaluation_path"))
    if (len(path.parts) != 2 or path.parts[0] != "evaluation" or not ID.fullmatch(path.parts[1])
            or not (collection / path / "result.json").resolve().is_relative_to(collection)):
        raise ValueError("unexpected evaluator result path")
    report = read_source(path / "result.json")
    valid = report.get("valid")
    if (report != summary.get("report") or type(valid) is not bool
            or capture.get("evaluation_valid") is not valid):
        raise ValueError("capture, evaluation summary and official result disagree")
    groups = {row["source_group"] for row in rows if row.get("source_group")}
    metadata = report.get("metadata", {})
    if groups and groups != {metadata.get("source_group")}:
        raise ValueError("evaluation source group disagrees with the segment journal")
    start = outcome["collection_start"]
    if start and "episode_seed" in metadata and (type(metadata["episode_seed"]) is not int
                                                or metadata["episode_seed"] != start["episode_seed"]):
        raise ValueError("evaluator seed disagrees with verified collection_start")
    outcome.update(status="finalized", valid=valid)
    if not valid:
        return outcome
    result = report.get("result")
    if not isinstance(result, dict):
        raise ValueError("valid report missing final result")
    raw, breakdown = result.get("raw_points"), result.get("breakdown")
    if type(raw) not in (int, float) or not 0 <= raw <= 50 or not isinstance(breakdown, dict):
        raise ValueError("invalid final raw score or component breakdown")
    for name, points in breakdown.items():
        identifier(name, "score component")
        if type(points) not in (int, float) or not 0 <= points <= 50:
            raise ValueError("invalid final component score")
    evaluated = result.get("success_evaluated")
    if evaluated is not None and type(evaluated) is not bool:
        raise ValueError("invalid final success_evaluated")
    if evaluated is True and type(result.get("success")) is not bool:
        raise ValueError("evaluated report missing final success")
    outcome.update(raw_points=raw, breakdown=breakdown, success_evaluated=evaluated,
                   success=result.get("success") if evaluated else None,
                   final_score=result.get("final_score"), score_status=result.get("score_status"))
    return outcome


def bundle_run(root, run, output, collection=None):
    """Package one metadata snapshot with its verified clips, leaving collection originals in place."""
    dataset = export_rows(root, run)
    rows = [json.loads(line) for line in dataset.splitlines()]
    outcome = final_outcome(run, rows, collection)
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix=".part", delete=False) as temp:
        temporary = Path(temp.name)
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            archive.writestr("segments.jsonl", dataset.encode(), compress_type=zipfile.ZIP_DEFLATED)
            archive.writestr("run_outcome.json", (json_text(outcome) + "\n").encode(),
                             compress_type=zipfile.ZIP_DEFLATED)
            for row in rows:
                media = row["clip_path"]
                digest = hashlib.sha256()
                with (Path(root) / media).open("rb") as clip, archive.open(
                        media, "w", force_zip64=True) as target:
                    while block := clip.read(1024 * 1024):
                        target.write(block)
                        digest.update(block)
                if digest.hexdigest() != row["clip_sha256"]:
                    raise ValueError(f"clip hash mismatch: {media}")
        # Publish only a finished ZIP. link() also excludes a concurrent writer at output.
        os.link(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return output



def byte_range(header, size):
    if not header:
        return 0, size - 1
    m = re.fullmatch(r"bytes=(\d*)-(\d*)", header)
    if not m or not any(m.groups()):
        raise ValueError("invalid range")
    start, end = m.groups()
    if start:
        start = int(start)
        end = min(int(end), size - 1) if end else size - 1
    else:
        start, end = max(0, size - int(end)), size - 1
    if start > end:
        raise ValueError("range outside clip")
    return start, end


class ReviewHandler(BaseHTTPRequestHandler):
    def send_bytes(self, data, content_type, status=200, download=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if download:
            self.send_header("Content-Disposition", f'attachment; filename="{download}"')
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def json(self, value, status=200):
        self.send_bytes(json_text(value).encode(), "application/json; charset=utf-8", status)

    def stream_clip(self, run, segment):
        with journal(self.server.root) as db:
            if not select_row(db, run, segment):
                raise KeyError("unknown clip")
        with (self.server.root / "media" / run / (segment + ".mp4")).open("rb") as clip:
            size = os.fstat(clip.fileno()).st_size
            requested = self.headers.get("Range")
            try:
                start, end = byte_range(requested, size)
            except ValueError:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(206 if requested else 200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(end - start + 1))
            if requested:
                self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.end_headers()
            if self.command == "HEAD":
                return
            clip.seek(start)
            remaining = end - start + 1
            while remaining:
                block = clip.read(min(remaining, 65536))
                if not block:
                    break
                self.wfile.write(block)
                remaining -= len(block)

    def dispatch(self):
        host = self.headers.get("Host", "")
        if not re.fullmatch(r"(localhost|127\.0\.0\.1|\[::1\])(:[0-9]+)?", host, re.I):
            self.json({"error": "use a localhost connection or an SSH port forward"}, 403)
            return
        url = urlsplit(self.path)
        query = parse_qs(url.query, keep_blank_values=True)
        run = query.get("run", [None])[0]
        segment = query.get("segment", [None])[0]
        root = self.server.root
        if self.command == "POST":
            if url.path not in ("/api/feedback", "/api/intervene"):
                raise KeyError("unknown route")
            origin = self.headers.get("Origin")
            if origin and origin not in ("http://" + host, "https://" + host):
                self.json({"error": "feedback requires the same origin"}, 403)
                return
            if self.headers.get_content_type() != "application/json":
                self.json({"error": "expected application/json"}, 415)
                return
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 32768:
                raise ValueError("invalid feedback size")
            handler = request_intervention if url.path == "/api/intervene" else submit_feedback
            self.json(handler(root, json.loads(self.rfile.read(size))))
        elif url.path == "/":
            self.send_bytes(Path(__file__).with_suffix(".html").read_bytes(), "text/html; charset=utf-8")
        elif url.path == "/api/state":
            self.json(state(root, run, segment))
        elif url.path == "/api/export":
            self.send_bytes(export_rows(root, run).encode(), "application/x-ndjson; charset=utf-8",
                            download=f"{run}.jsonl")
        else:
            media = re.fullmatch(r"/media/([^/]+)/([^/]+)\.mp4", url.path)
            if not media:
                raise KeyError("unknown route")
            self.stream_clip(*media.groups())

    def handle_request(self):
        try:
            self.dispatch()
        except Conflict as exc:
            self.json({"error": str(exc)}, 409)
        except (KeyError, FileNotFoundError) as exc:
            self.json({"error": str(exc)}, 404)
        except (ValueError, UnicodeError) as exc:
            self.json({"error": str(exc)}, 400)
        except (BrokenPipeError, ConnectionResetError):
            pass  # Browsers cancel old byte-range requests when seeking.

    do_GET = do_HEAD = do_POST = handle_request


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("output/segment-review"),
                        help="private directory shared with the collector (default: %(default)s)")
    commands = parser.add_subparsers(dest="command", required=True)
    serve = commands.add_parser("serve", help="open the review page on loopback")
    serve.add_argument("--port", type=int, default=8765)
    publish = commands.add_parser("publish", help="publish a completed segment and its clip")
    publish.add_argument("--record", required=True, type=Path)
    publish.add_argument("--clip", required=True, type=Path)
    bundle = commands.add_parser("bundle", help="archive one run's JSONL and hash-verified clips")
    bundle.add_argument("--run", required=True)
    bundle.add_argument("--collection", type=Path,
                        help="optional closed output/collections/RUN for verified final evaluation")
    bundle.add_argument("--out", required=True, type=Path, help="new ZIP file outside the capture directory")
    intervene = commands.add_parser("intervene", help="request human review at the next GPT-only action boundary")
    intervene.add_argument("--run", required=True)
    intervene.add_argument("--id", required=True, help="unique request ID, reused on retry")
    for command in ("latest", "export", "claim"):
        sub = commands.add_parser(command)
        sub.add_argument("--run", required=command != "latest")
        if command == "claim":
            sub.add_argument("--segment", required=True)
    args = parser.parse_args(argv)
    if args.command == "serve":
        with ThreadingHTTPServer(("127.0.0.1", args.port), ReviewHandler) as server:
            server.root = args.root.resolve()
            print(f"Review http://127.0.0.1:{server.server_port}/", flush=True)
            server.serve_forever()
    elif args.command == "publish":
        print(json_text(publish_segment(args.root, json.loads(args.record.read_text()), args.clip)))
    elif args.command == "export":
        sys.stdout.write(export_rows(args.root, args.run))
    elif args.command == "bundle":
        print(bundle_run(args.root, args.run, args.out, args.collection))
    elif args.command == "intervene":
        print(json_text(request_intervention(args.root, dict(run_id=args.run, id=args.id))))
    elif args.command == "latest":
        print(json_text(get_segment(args.root, args.run)))
    elif args.command == "claim":
        print(json_text(claim_feedback(args.root, args.run, args.segment)))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, sqlite3.Error) as error:
        sys.exit(str(error))
