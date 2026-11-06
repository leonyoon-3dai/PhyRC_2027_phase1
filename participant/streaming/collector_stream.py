"""Optional WebRTC spectator for the trusted collection process.

No robot-control callbacks are registered. The actor only receives the public
camera observations from DressingEnv, never this freely moved viewport.
"""
import ipaddress
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit


def observer_response():
    return {'ok': True, 'control_mode': 'observer_only', 'controls_enabled': False,
            'message': '관찰 전용 · 로봇 입력은 적용하지 않습니다.',
            'guidance': {'robots': [], 'stream_size': [1280, 720]},
            'server_keys': [], 'applied_keys': []}


def make_handler(origin):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def _headers(self, status):
            self.send_response(status)
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()

        def do_OPTIONS(self):
            if self.headers.get('Origin') != origin:
                self.send_error(403)
                return
            self.send_response(204)
            self.send_header('Access-Control-Allow-Origin', origin)
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

        def do_POST(self):
            if self.path != '/keys' or self.headers.get('Origin') != origin:
                self.send_error(403)
                return
            try:
                size = int(self.headers.get('Content-Length', '0'))
                if not 0 < size < 4096:
                    raise ValueError()
                request = json.loads(self.rfile.read(size))
                if not isinstance(request, dict):
                    raise ValueError()
            except (ValueError, TypeError):
                self._headers(400)
                self.wfile.write(b'{"ok":false,"error":"invalid_request"}')
                return
            # All key payloads are deliberately ignored; no queue or controller.
            self._headers(200)
            self.wfile.write(json.dumps(observer_response(), ensure_ascii=False).encode())
    return Handler


class CollectorStream:
    def __init__(self, host, origin, *, keyboard_port=8211):
        ipaddress.IPv4Address(host)
        parsed = urlsplit(origin)
        if parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
            raise ValueError('viewer origin must be a plain HTTP(S) origin')
        self.host, self.origin = host, origin.rstrip('/')
        self.keyboard_port = keyboard_port
        self.server = None
        self.thread = None
        self.original = None

    @classmethod
    def from_environment(cls):
        host = os.environ['STRETCH4_STREAM_HOST']
        return cls(host, os.environ.get('STRETCH4_VIEWER_ORIGIN', 'http://' + host + ':8210'))

    def install(self):
        import isaacsim
        self.original = isaacsim.SimulationApp
        def start(config, *args, **kwargs):
            app = self.original(dict(config, headless=True, hide_ui=False, width=1280, height=720), *args, **kwargs)
            app.set_setting('/exts/omni.kit.livestream.app/primaryStream/publicIp', self.host)
            app.set_setting('/exts/omni.kit.livestream.app/primaryStream/signalPort', 49100)
            app.set_setting('/exts/omni.kit.livestream.app/primaryStream/streamPort', 47998)
            from isaacsim.core.experimental.utils.app import enable_extension
            enable_extension('omni.kit.livestream.app')
            self.server = ThreadingHTTPServer(('0.0.0.0', self.keyboard_port), make_handler(self.origin))
            self.server.daemon_threads = True
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            print('[Collection stream] 관찰 전용 · 브라우저 로봇 입력 미적용', flush=True)
            return app
        isaacsim.SimulationApp = start

    def close(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.original:
            import isaacsim
            isaacsim.SimulationApp = self.original


def render_without_physics(env, evaluation=None):
    """Pump viewer events using Isaac's render-only path and verify its clock."""
    before = float(env.world.current_time)
    tick = evaluation.ticks if evaluation else None
    env.world.render()
    after = float(env.world.current_time)
    if abs(after - before) > 1e-9 or (evaluation and evaluation.ticks != tick):
        raise RuntimeError('observer_render_advanced_physics')
