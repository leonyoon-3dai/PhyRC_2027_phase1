"""Serve the spectator UI and a bounded, allowlisted collection status API.

No simulator commands, arbitrary file access, HDF5 reads, or actor input paths
are exposed. Browser metrics are explicitly client-reported observations.
"""
import argparse
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
import time
from urllib.parse import urlsplit

from participant.collection.export_report import (action, boolean, identifier, integer, number,
    public_attempt, public_review_gate, public_score, select, text)

RUN_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}')
TERMINAL = {'completed', 'review_ready', 'failed', 'interrupted'}
STATUSES = TERMINAL | {'starting', 'collecting', 'replaying_prefix'}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def bounded_json(path, limit=262144):
    if path.is_symlink():
        raise ValueError('symlink status file rejected')
    if not path.is_file():
        return None
    if path.stat().st_size > limit:
        raise ValueError('status file exceeds limit')
    return json.loads(path.read_text())


def completed_tail(path, limit=262144):
    """Read only complete lines, dropping a partial first/last record."""
    if path.is_symlink():
        raise ValueError('symlink event file rejected')
    if not path.is_file():
        return []
    with path.open('rb') as stream:
        size = path.stat().st_size
        start = max(0, size - limit)
        stream.seek(start)
        data = stream.read(limit)
    lines = data.split(b'\n')[:-1]
    if start and lines:
        lines = lines[1:]
    return [json.loads(line) for line in lines if line.strip()]


class ProgressStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.lock = threading.RLock()
        self.cache_at = 0
        self.cache = None
        self.metrics = None

    def inside(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError('outside status root')
        return path

    def latest(self):
        choices = []
        parent = self.inside('output/operator-traces')
        if not parent.is_dir():
            return None
        for directory in parent.iterdir():
            if not RUN_ID.fullmatch(directory.name) or directory.is_symlink():
                continue
            path = directory / 'attempt.json'
            try:
                value = bounded_json(path)
                if (not isinstance(value, dict) or value.get('run_id') != directory.name
                        or value.get('status') not in STATUSES):
                    continue
                started = datetime.fromisoformat(value['started_at_utc'].replace('Z', '+00:00'))
                if started.tzinfo is None:
                    continue
                choices.append((started.timestamp(), value['status'] not in TERMINAL, value))
            except (OSError, ValueError, KeyError, TypeError):
                continue
        return max(choices, key=lambda item: item[:2])[2] if choices else None

    def snapshot(self, *, refresh=False):
        with self.lock:
            now = time.monotonic()
            if refresh or self.cache is None or now - self.cache_at >= .5:
                self.cache = self._snapshot()
                self.cache_at = now
            result = json.loads(json.dumps(self.cache))
            metric = self.metrics
            if metric and metric['run_id'] == result.get('run_id'):
                result['viewer_metrics'] = {k: v for k, v in metric.items() if k != 'received_monotonic'}
                result['viewer_metrics']['last_seen_seconds'] = max(0, now - metric['received_monotonic'])
            else:
                result['viewer_metrics'] = None
            return result

    def _snapshot(self):
        raw = self.latest()
        result = {'schema': 'phyrc-spectator-progress-v1', 'observed_at_utc': utc_now(),
                  'control_mode': 'observer_only', 'available': raw is not None,
                  'sent_to_actor': False, 'run_id': None,
                  'run_scope': 'latest_model_collection', 'same_as_video_run_verified': False}
        if raw is None:
            return result
        run = raw['run_id']
        trace = self.inside('output/operator-traces/' + run)
        capture = self.inside('output/collections/' + run)
        attempt = public_attempt(raw)
        result.update(run_id=run, attempt=attempt)
        started = datetime.fromisoformat(raw['started_at_utc'].replace('Z', '+00:00'))
        result['elapsed_wall_s'] = (attempt.get('wall_s') if raw['status'] in TERMINAL
                                   else max(0, time.time() - started.timestamp()))
        result['elapsed_wall_is_live_estimate'] = raw['status'] not in TERMINAL
        prompt = trace / 'prompt.txt'
        result['prompt'] = None
        result['prompt_scope'] = 'initial_task_prompt_only'
        if not prompt.is_symlink() and prompt.is_file() and prompt.stat().st_size <= 262144:
            try:
                result['prompt'] = text(prompt.read_text(), max_length=262144)
            except ValueError:
                result['prompt_redacted'] = True
        timeline = []
        for event in completed_tail(trace / 'decisions.jsonl'):
            if event.get('type') == 'decision':
                row = select(event, {'decision_index': integer, 'model_call_index': integer,
                    'plan_segment_index': integer, 'plan_segment_count': integer, 'model_invoked': boolean,
                    'observation_simulation_time_s': number, 'latest_observation_simulation_time_s': number,
                    'wall_s': number})
                row['response'] = select(event['decision'], {'tool': identifier, 'action': action,
                    'steps': integer, 'stage': identifier, 'visual_assessment': identifier,
                    'reason': partial(text, max_length=8000)})
                row['execution'] = None
                timeline.append(row)
            elif event.get('type') == 'applied_segment':
                for row in reversed(timeline):
                    if row['decision_index'] == event.get('decision_index'):
                        row['execution'] = select(event, {'start_step': integer, 'end_step': integer,
                            'actual_steps': integer, 'simulation_start_s': number, 'simulation_end_s': number,
                            'environment_dispatch_wall_s': number})
                        break
        result['recent_decisions'] = timeline[-6:]
        evaluation = bounded_json(capture / 'evaluation_summary.json')
        if isinstance(evaluation, dict):
            result['evaluation'] = public_score(evaluation.get('report'))
            result['evaluation']['source'] = 'final_official_report'
        else:
            result['evaluation'] = {'source': 'no_measurement', 'raw_points': None, 'success': None,
                                    'final_score': None, 'score_status': None}
            candidates = sorted((capture / 'evaluation').glob('*/score_samples.jsonl'))
            if candidates:
                sample_path = candidates[-1]
                if not sample_path.resolve().is_relative_to(self.root):
                    raise ValueError('outside score root')
                samples = completed_tail(sample_path)
                if samples:
                    result['evaluation'] = select(samples[-1], {'raw_points': number, 'success': boolean,
                        'success_evaluated': boolean, 'score_status': identifier, 'final_score': number,
                        'evaluation_time_s': number, 'physics_tick': integer})
                    result['evaluation']['source'] = 'live_official_score_sample'
        result['review_gate'] = public_review_gate(bounded_json(trace / 'review_gate.json'))
        result['files'] = []
        for role, parent, names in [('trace', trace, ('attempt.json', 'decisions.jsonl', 'prompt.txt')),
                                   ('capture', capture, ('policy.hdf5', 'audit.hdf5', 'capture.json', 'validation.json'))]:
            for name in names:
                path = parent / name
                if not path.is_symlink() and path.is_file():
                    result['files'].append({'path': role + '/' + name, 'bytes': path.stat().st_size})
        return result

    def report_metrics(self, value):
        fields = {'run_id', 'sdk_connected', 'total_video_frames', 'video_width', 'video_height', 'page_visible'}
        if not isinstance(value, dict) or set(value) != fields:
            raise ValueError('invalid metrics fields')
        run = value['run_id']
        if not isinstance(run, str) or not RUN_ID.fullmatch(run):
            raise ValueError('invalid run label')
        for key in ('sdk_connected', 'page_visible'):
            boolean(value[key])
        for key in ('video_width', 'video_height'):
            if integer(value[key]) > 8192:
                raise ValueError('invalid dimensions')
        count = value['total_video_frames']
        if count is not None and integer(count) > 2**53 - 1:
            raise ValueError('invalid frame count')
        with self.lock:
            if self.snapshot().get('run_id') != run:
                raise ValueError('stale run label')
            prior = self.metrics
            increased = bool(prior and prior['run_id'] == run and count is not None
                             and prior['total_video_frames'] is not None
                             and count > prior['total_video_frames'])
            record = dict(value, received_at_utc=utc_now(), client_reported=True,
                          frame_count_increased=increased,
                          run_label_scope='latest_model_collection', same_as_video_run_verified=False)
            folder = self.inside('output/viewer-metrics')
            folder.mkdir(parents=True, exist_ok=True)
            path = self.inside('output/viewer-metrics/' + run + '.jsonl')
            with path.open('a') as stream:
                stream.write(json.dumps(record, allow_nan=False) + '\n')
            self.metrics = dict(record, received_monotonic=time.monotonic())
            return {'ok': True, 'client_reported': True}


def make_handler(store, dist):
    dist = Path(dist).resolve()
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dist), **kwargs)

        def log_message(self, *_):
            pass

        def json_response(self, status, value):
            payload = json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(payload)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(payload)

        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path == '/api/progress' and not parsed.query:
                try:
                    self.json_response(200, store.snapshot())
                except (ValueError, OSError, KeyError, TypeError):
                    self.json_response(503, {'error': 'status_temporarily_unavailable'})
            elif parsed.path.startswith('/api/'):
                self.json_response(404, {'error': 'not_found'})
            else:
                super().do_GET()

        def do_POST(self):
            if self.path != '/api/viewer-metrics':
                self.json_response(404, {'error': 'not_found'})
                return
            origin = self.headers.get('Origin')
            if origin and urlsplit(origin).netloc != self.headers.get('Host'):
                self.json_response(403, {'error': 'origin_rejected'})
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size <= 2048:
                    raise ValueError('invalid payload length')
                result = store.report_metrics(json.loads(self.rfile.read(size)))
                self.json_response(200, result)
            except (ValueError, OSError, TypeError):
                self.json_response(400, {'error': 'invalid_metrics'})

        def send_head(self):
            path = Path(self.translate_path(self.path)).resolve()
            if not path.is_relative_to(dist):
                self.send_error(403)
                return None
            return super().send_head()

        def list_directory(self, _):
            self.send_error(404)
            return None
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--dist', type=Path)
    parser.add_argument('--bind', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8210)
    args = parser.parse_args()
    dist = args.dist or args.root / 'output/webrtc/viewer/dist'
    server = ThreadingHTTPServer((args.bind, args.port), make_handler(ProgressStore(args.root), dist))
    server.daemon_threads = True
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
