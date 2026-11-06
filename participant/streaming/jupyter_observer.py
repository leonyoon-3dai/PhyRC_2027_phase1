"""Publish one bounded human-observer snapshot for an existing Jupyter notebook.

This utility opens no listener and has no simulator dependency. The trusted
runner supplies rendered pixels, a public run label and optional simulation
time. Never pass this human viewport to an action-generating policy session.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import html
import io
import json
import math
import os
from pathlib import Path
import tempfile
import time
from urllib.parse import quote


class JupyterObserver:
    """Atomically replace a self-contained page, at most once per interval.

    ``write_frame`` accepts an RGB uint8 array or JPEG/PNG bytes. ``finish``
    preserves the last image and tells the notebook to stop polling. The output
    is a preview, not a dataset or evidence that the task succeeded.
    """

    def __init__(self, output, *, run_label, interval_s=1.0, stale_after_s=10.0,
                 max_size=(1280, 720), jpeg_quality=75):
        self.output = Path(output)
        if self.output.suffix.lower() != '.html':
            raise ValueError('observer output must have an .html extension')
        if not isinstance(run_label, str) or not run_label or len(run_label) > 200:
            raise ValueError('run_label must contain 1 to 200 characters')
        if not math.isfinite(interval_s) or interval_s < 0.25:
            raise ValueError('interval_s must be finite and at least 0.25')
        if not math.isfinite(stale_after_s) or stale_after_s <= interval_s:
            raise ValueError('stale_after_s must exceed interval_s')
        if (len(max_size) != 2 or any(isinstance(x, bool) or not isinstance(x, int)
                                    or not 1 <= x <= 4096 for x in max_size)):
            raise ValueError('max_size must contain two integers in [1,4096]')
        if isinstance(jpeg_quality, bool) or not isinstance(jpeg_quality, int) or not 1 <= jpeg_quality <= 95:
            raise ValueError('jpeg_quality must be an integer in [1,95]')
        self.run_label = run_label
        self.interval_s = float(interval_s)
        self.stale_after_s = float(stale_after_s)
        self.max_size = tuple(max_size)
        self.jpeg_quality = jpeg_quality
        self._last_write = None
        self._image = None
        self._captured_at = None
        self._simulation_time = None
        self._finished = False

    def due(self):
        """Allow a runner to skip an expensive capture before the next interval."""
        return not self._finished and (self._last_write is None or
                                      time.monotonic() - self._last_write >= self.interval_s)

    def write_frame(self, rgb, *, simulation_time=None):
        """Return True when published, False when cadence/finished skips a frame."""
        if not self.due():
            return False
        if simulation_time is not None:
            if isinstance(simulation_time, bool):
                raise ValueError('simulation_time must be a finite nonnegative number')
            simulation_time = float(simulation_time)
            if not math.isfinite(simulation_time) or simulation_time < 0:
                raise ValueError('simulation_time must be a finite nonnegative number')
        image = self._encode(rgb)
        captured_at = datetime.now(timezone.utc)
        page = self._page(image, captured_at, simulation_time, 'live')
        self._replace(page)
        self._image, self._captured_at = image, captured_at
        self._simulation_time = simulation_time
        self._last_write = time.monotonic()
        return True

    def finish(self, *, error=False):
        """Stop refresh and label the final preview; error details stay in logs."""
        if not isinstance(error, bool):
            raise ValueError('error must be a boolean')
        if self._finished:
            return
        self._replace(self._page(self._image, self._captured_at,
                                self._simulation_time, 'error' if error else 'finished'))
        self._finished = True

    def _encode(self, rgb):
        import numpy as np
        from PIL import Image

        if isinstance(rgb, (bytes, bytearray)):
            if len(rgb) > 32 * 1024 * 1024:
                raise ValueError('encoded frame exceeds 32 MiB')
            with Image.open(io.BytesIO(rgb)) as source:
                if source.format not in ('PNG', 'JPEG'):
                    raise ValueError('encoded frame must be PNG or JPEG')
                if source.width * source.height > 16_777_216:
                    raise ValueError('frame exceeds 16 megapixels')
                image = source.convert('RGB')
        else:
            array = np.asarray(rgb)
            if (array.dtype != np.uint8 or array.ndim != 3 or array.shape[2] != 3
                    or not array.shape[0] or not array.shape[1]
                    or array.shape[0] * array.shape[1] > 16_777_216):
                raise ValueError('frame must be a nonempty RGB uint8 array up to 16 megapixels')
            image = Image.fromarray(array)
        image.thumbnail(self.max_size, Image.Resampling.LANCZOS)
        encoded = io.BytesIO()
        # Re-encode pixels only: EXIF, PNG text and other source metadata are omitted.
        image.save(encoded, format='JPEG', quality=self.jpeg_quality)
        return base64.b64encode(encoded.getvalue()).decode('ascii')

    def _replace(self, page):
        self.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8',
                                             dir=self.output.parent,
                                             prefix='.observer-', suffix='.tmp',
                                             delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(page)
                stream.flush()
                os.fchmod(stream.fileno(), 0o644)
            os.replace(temporary, self.output)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _page(self, image, captured_at, simulation_time, status):
        live = status == 'live'
        label = html.escape(self.run_label, quote=True)
        capture_text = captured_at.isoformat(timespec='seconds').replace('+00:00', 'Z') if captured_at else '아직 없음'
        capture_ms = int(captured_at.timestamp() * 1000) if captured_at else 0
        sim = f'{simulation_time:.2f}초' if simulation_time is not None else '미기록'
        status_text = {'live': '실행 중 · 최근 관찰 화면', 'finished': '실행 종료 · 마지막 관찰 화면',
                       'error': '영상 갱신 중단 · 마지막 관찰 화면'}[status]
        picture = (f'<img alt="시뮬레이션 관찰 화면" src="data:image/jpeg;base64,{image}">'
                   if image else '<p>저장된 관찰 화면이 없습니다.</p>')
        script = ''
        if live:
            script = f'''<script>
const capturedAt = {capture_ms};
const staleAfter = {self.stale_after_s * 1000:g};
function updateAge() {{
  const age = Math.max(0, Date.now() - capturedAt);
  document.getElementById('age').textContent = '마지막 화면: ' + (age / 1000).toFixed(1) + '초 전';
  if (age > staleAfter) {{
    document.getElementById('status').textContent = '화면 갱신 지연 · 현재 상태 확인 필요';
    document.getElementById('status').className = 'stale';
  }}
}}
updateAge(); setInterval(updateAge, 500);
</script>'''
        return f'''<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PhyRC 관찰 · {label}</title>
<style>
body{{margin:0;padding:16px;background:#101820;color:#edf3f8;font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1280px;margin:auto}}h1{{font-size:20px;margin:0 0 8px}}
img{{display:block;width:min(100%,768px);height:auto;margin:12px auto}}
.details{{color:#b9cad7;font-size:14px}}.stale{{color:#ffcf70}}
</style></head><body><main>
<h1>PhyRC 관찰 · {label}</h1>
<p id="status" data-state="{status}">{status_text}</p>
<div class="details" id="capture" data-captured-ms="{capture_ms}">촬영 시각 UTC: {capture_text} · 시뮬레이션 시간: {sim}</div>
<div class="details" id="age"></div>
{picture}
<p class="details">관찰용 미리보기 · 실시간 갱신은 관찰 notebook에서 확인합니다. 과제 점수와 성공 여부는 별도 평가 기록으로 확인합니다.</p>
</main>{script}</body></html>
'''


def create_notebook(output, *, observer_html, jupyter_root, run_label='PhyRC 실시간 관찰',
                    interval_s=1.0, stale_after_s=10.0, base_url='/'):
    """Create and trust our generated observer notebook using Jupyter's Python.

    Jupyter /files HTML uses an opaque sandbox origin, so its own reload may
    receive 403. This notebook's trusted output fetches the page from the Lab
    origin and copies only the JPEG and permitted status fields. No kernel
    execution or server configuration change is required to see saved output.
    nbformat is imported lazily and is normally available in Jupyter's Python.
    """
    import nbformat
    from nbformat.sign import NotebookNotary

    output, observer_html, jupyter_root = Path(output), Path(observer_html), Path(jupyter_root)
    if output.suffix != '.ipynb':
        raise ValueError('notebook output must end in .ipynb')
    # The mapping is generated by the trusted runner, never accepted over HTTP.
    relative_html = observer_html.resolve().relative_to(jupyter_root.resolve())
    output.resolve().relative_to(jupyter_root.resolve())
    if not base_url.startswith('/') or base_url.startswith('//') or '?' in base_url or '#' in base_url:
        raise ValueError('base_url must be an absolute URL path without query or fragment')
    if not isinstance(run_label, str) or not run_label or len(run_label) > 200:
        raise ValueError('run_label must contain 1 to 200 characters')
    if not math.isfinite(interval_s) or interval_s < .25:
        raise ValueError('interval_s must be at least 0.25')
    if not math.isfinite(stale_after_s) or stale_after_s <= interval_s:
        raise ValueError('stale_after_s must exceed interval_s')
    route = base_url.rstrip('/') + '/files/' + quote(relative_html.as_posix(), safe='/')
    # A constant generated widget ID is scoped to this output's script lookup.
    widget_id = 'phyrc-observer-' + os.urandom(8).hex()
    markup = f'''<section id="{widget_id}" style="max-width:900px;padding:16px;background:#101820;color:#edf3f8;font:16px/1.5 system-ui,sans-serif">
<h2 style="margin:0 0 8px">{html.escape(run_label, quote=True)}</h2>
<p data-status>관찰 화면 준비 중</p>
<p data-capture style="font-size:14px"></p><p data-age style="font-size:14px"></p>
<img data-frame alt="시뮬레이션 관찰 화면" style="display:none;width:min(100%,768px);height:auto">
<p style="font-size:13px">관찰용 미리보기 · 과제 점수와 성공 여부는 별도 평가 기록으로 확인합니다.</p>
</section><script>
(() => {{
 const root = document.getElementById({json.dumps(widget_id)});
 const route = {json.dumps(route)};
 let active = true, capturedAt = 0;
 const status = root.querySelector('[data-status]');
 const capture = root.querySelector('[data-capture]');
 const age = root.querySelector('[data-age]');
 const image = root.querySelector('[data-frame]');
 async function poll() {{
  if (!root.isConnected || !active) return;
  try {{
   const response = await fetch(route, {{credentials:'same-origin', cache:'no-store'}});
   if (!response.ok) throw new Error('preview unavailable');
   const doc = new DOMParser().parseFromString(await response.text(), 'text/html');
   const nextStatus = doc.getElementById('status');
   const nextCapture = doc.getElementById('capture');
   const nextImage = doc.querySelector('img');
   const state = nextStatus?.getAttribute('data-state');
   if (!['live','finished','error'].includes(state)) throw new Error('invalid preview');
   const src = nextImage?.getAttribute('src');
   if (src && src.startsWith('data:image/jpeg;base64,') && /^[A-Za-z0-9+/=]+$/.test(src.slice(23))) {{
    image.src = src; image.style.display = 'block';
   }}
   status.textContent = nextStatus.textContent;
   status.setAttribute('data-state', state);
   capture.textContent = nextCapture?.textContent || '';
   capturedAt = Number(nextCapture?.getAttribute('data-captured-ms')) || 0;
   active = state === 'live';
   if (!active) age.textContent = '';
  }} catch (_) {{ status.textContent = capturedAt ? '화면 갱신 지연 · 현재 상태 확인 필요' : '관찰 화면 준비 중'; }}
  if (active && capturedAt) {{
   const elapsed = Math.max(0,Date.now()-capturedAt);
   age.textContent = '마지막 화면: '+(elapsed/1000).toFixed(1)+'초 전';
   if (elapsed > {stale_after_s * 1000:g}) status.textContent = '화면 갱신 지연 · 현재 상태 확인 필요';
  }}
  if (active) setTimeout(poll, {interval_s * 1000:g});
 }}
 poll();
}})();
</script>'''
    source = 'from IPython.display import HTML, display\ndisplay(HTML(' + repr(markup) + '))'
    notebook = nbformat.v4.new_notebook(cells=[
        nbformat.v4.new_markdown_cell('실시간 관찰 화면입니다. 저장된 출력이 자동으로 갱신되며 종료 후 마지막 화면을 유지합니다.'),
        nbformat.v4.new_code_cell(source=source, execution_count=1,
                                  metadata={'trusted': True, 'jupyter': {'source_hidden': True}},
                                  outputs=[nbformat.v4.new_output('display_data', data={'text/html': markup})]),
    ])
    notebook.metadata['kernelspec'] = {'display_name':'Python 3', 'language':'python', 'name':'python3'}
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    # Sign the serialized representation. Notebook serialization can normalize
    # metadata, and signing the pre-write object may not match what Lab reads.
    NotebookNotary().sign(nbformat.read(output, as_version=4))
    return output


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='기존 Jupyter용 관찰 notebook 생성')
    parser.add_argument('--notebook', type=Path, required=True)
    parser.add_argument('--html', type=Path, required=True)
    parser.add_argument('--jupyter-root', type=Path, required=True)
    parser.add_argument('--run-label', default='PhyRC 실시간 관찰')
    parser.add_argument('--interval-s', type=float, default=1.0)
    parser.add_argument('--base-url', default='/')
    args = parser.parse_args()
    create_notebook(args.notebook, observer_html=args.html, jupyter_root=args.jupyter_root,
                    run_label=args.run_label, interval_s=args.interval_s, base_url=args.base_url)
    print('관찰 notebook 생성 및 서명 완료')
