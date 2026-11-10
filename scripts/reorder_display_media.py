"""Rebuild the 2026-11-10 R1-left/R0-right presentation media from a fixed Git revision.

CPU-only relocation of existing labelled tiles. No mirroring, resampling, new
simulation, or changes to recorded policy inputs. The fixed source prevents a
second invocation from swapping the already corrected media back again.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, GifImagePlugin

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '3a255108a1c8e65428f19fa7caebb4b4684bc50f'
DISPLAY_FOLDER = 'docs/gallery/assets/robot-layout-20261110'
RECEIPT = ROOT / DISPLAY_FOLDER / 'provenance.json'


def original(path):
    return subprocess.check_output(['git', 'show', f'{SOURCE}:{path}'], cwd=ROOT)


def source_provenances():
    """Read the pinned tree, including on a later checkout with new receipts."""
    paths = subprocess.check_output(
        ['git', 'ls-tree', '-r', '--name-only', SOURCE, 'docs/gallery/assets'],
        cwd=ROOT, text=True).splitlines()
    return [ROOT / path for path in paths if path.endswith('/provenance.json')]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def move_tiles(image, kind):
    result = image.copy()
    w, h = image.size
    if kind == 'four':
        assert (w, h) == (512, 588)
        result.paste(image.crop((256, 0, 512, 560)), (0, 0))
        result.paste(image.crop((0, 0, 256, 560)), (256, 0))
    elif kind == 'five':
        # The 1024px preview has rounded 204/205px tiles. Move every source
        # pixel exactly once, retaining those widths rather than resampling.
        edges = [round(w * i / 5) for i in range(6)]
        target = 0
        for source in (0, 2, 1, 4, 3):
            result.paste(image.crop((edges[source], 0, edges[source + 1], h)), (target, 0))
            target += edges[source + 1] - edges[source]
    elif kind == 'depth':
        assert (w, h) == (512, 424)
        result.paste(image.crop((256, 44, 512, 324)), (0, 44))
        result.paste(image.crop((0, 44, 256, 324)), (256, 44))
    elif kind == 'review':
        assert (w, h) == (870, 708)
        result = Image.new('RGB', (870, 996), '#17202a')
        result.paste(image.crop((0, 0, 870, 80)), (0, 0))
        # Each complete 256px image and its original camera/type label move together.
        for column, source_row in enumerate((1, 0)):
            for row, source_x in enumerate((15, 302, 589)):
                source_y = 84 + source_row * 288
                result.paste(image.crop((source_x, source_y, source_x + 272, source_y + 280)),
                             (15 + column * 435, 84 + row * 288))
        result.paste(image.crop((0, 672, 870, 708)), (0, 960))
    else:
        raise ValueError(kind)
    return result


def exact_palette(image):
    rgb = np.asarray(image.convert('RGB'))
    values = rgb.astype('uint32')
    packed = (values[..., 0] << 16) | (values[..., 1] << 8) | values[..., 2]
    colors, indices = np.unique(packed, return_inverse=True)
    assert len(colors) <= 256, 'GIF frame unexpectedly exceeds 256 colors'
    indexed = Image.fromarray(indices.reshape(rgb.shape[:2]).astype('uint8'))
    palette = np.stack((colors >> 16, (colors >> 8) & 255, colors & 255), axis=1).astype('uint8')
    indexed.putpalette(palette.reshape(-1).tolist() + [0] * (768 - palette.size))
    return indexed


def check_images(old, new, kind):
    count = getattr(old, 'n_frames', 1)
    assert getattr(new, 'n_frames', 1) == count
    if old.format == 'GIF':
        assert old.info.get('loop') == new.info.get('loop')
    for index in range(count):
        old.seek(index)
        new.seek(index)
        assert np.array_equal(np.asarray(move_tiles(old.convert('RGB'), kind)), np.asarray(new.convert('RGB')))
        if old.format == 'GIF':
            assert new.info.get('duration', 0) == old.info.get('duration', 0)
    return count, list(new.size)


def convert_image(path, target, kind):
    source = original(path)
    output = ROOT / target
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        try:
            with Image.open(BytesIO(source)) as old, Image.open(output) as new:
                count, size = check_images(old, new, kind)
            return {'path': target, 'source_path': path, 'source_sha256': digest(source),
                    'sha256': digest(output.read_bytes()), 'bytes': output.stat().st_size,
                    'transform': kind, 'size_px': size, 'frames': count,
                    'verification': 'all decoded RGB pixels equal relocated source tiles; all frame durations preserved'}
        except (AssertionError, OSError):
            pass  # Rebuild an unconverted/partial output from the fixed source.
    with Image.open(BytesIO(source)) as old:
        count = getattr(old, 'n_frames', 1)
        durations = []
        if old.format == 'GIF':
            # Write each original frame explicitly, without frame coalescing or
            # RGB quantization. Local palettes represent all original colors exactly.
            with output.open('wb') as stream:
                for index in range(count):
                    old.seek(index)
                    frame = exact_palette(move_tiles(old.convert('RGB'), kind))
                    duration = old.info.get('duration', 0)
                    durations.append(duration)
                    if index == 0:
                        for block in GifImagePlugin.getheader(frame, info={'loop': old.info.get('loop', 0)})[0]:
                            stream.write(block)
                    for block in GifImagePlugin.getdata(frame, duration=duration, disposal=2,
                                                       include_color_table=True):
                        stream.write(block)
                stream.write(b';')
        else:
            move_tiles(old.convert('RGB'), kind).save(output)
        with Image.open(output) as new:
            count, size = check_images(old, new, kind)
    return {'path': target, 'source_path': path, 'source_sha256': digest(source),
            'sha256': digest(output.read_bytes()), 'bytes': output.stat().st_size,
            'transform': kind, 'size_px': size, 'frames': count,
            'verification': 'all decoded RGB pixels equal relocated source tiles; all frame durations preserved'}


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,nb_frames,r_frame_rate:format=duration', '-of', 'json', str(path)]))


def video_filter(kind):
    if kind == 'four':
        return ('[0:v]split=3[a][b][c];[a]crop=256:560:256:0[r];'
                '[b]crop=256:560:0:0[l];[c]crop=512:28:0:560[f];'
                '[r][l]hstack=inputs=2[t];[t][f]vstack=inputs=2[out]')
    return ('[0:v]split=5[a][b][c][d][e];[a]crop=256:288:0:0[o];'
            '[b]crop=256:288:512:0[rw];[c]crop=256:288:256:0[lw];'
            '[d]crop=256:288:1024:0[rh];[e]crop=256:288:768:0[lh];'
            '[o][rw][lw][rh][lh]hstack=inputs=5[out]')


def decoded_yuv(path):
    data = subprocess.check_output(['ffmpeg', '-v', 'error', '-threads', '1', '-i', str(path),
                                   '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'])
    info = probe(path)['streams'][0]
    w, h = info['width'], info['height']
    stride = w * h * 3 // 2
    assert len(data) % stride == 0
    frames = np.frombuffer(data, dtype=np.uint8).reshape(-1, stride)
    return frames, w, h


def convert_video(path, kind):
    source = original(path)
    output = ROOT / path
    with tempfile.TemporaryDirectory(prefix='phyrc-layout-') as temporary:
        old = Path(temporary) / 'source.mp4'
        new = Path(temporary) / 'reordered.mp4'
        old.write_bytes(source)
        before = probe(old)
        # Successful prior runs can be reverified without recompressing media.
        profile = None
        if output.exists():
            profile = json.loads(subprocess.check_output(['ffprobe', '-v', 'error',
                '-select_streams', 'v:0', '-show_entries', 'stream=profile', '-of', 'json',
                str(output)]))['streams'][0].get('profile')
        if output.exists() and output.read_bytes() != source and profile == 'High':
            new.write_bytes(output.read_bytes())
        else:
            subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-threads', '1', '-i', str(old),
                '-filter_complex_threads', '1', '-filter_complex', video_filter(kind), '-map', '[out]',
                '-an', '-c:v', 'libx264', '-profile:v', 'high', '-crf', '18',
                '-preset', 'medium', '-pix_fmt', 'yuv420p',
                '-threads', '1', '-movflags', '+faststart', str(new)], check=True)
        after = probe(new)
        assert before == after, 'video dimensions, fps, count or duration changed'
        a, w, h = decoded_yuv(old)
        b, _, _ = decoded_yuv(new)
        assert a.shape == b.shape
        # Compare every frame against the intended tile relocation. Standard
        # H.264 High (4:2:0) supports browser playback; CRF18 adds small display
        # compression error, so require >=38 dB PSNR in every decoded frame.
        squared_error = np.zeros(len(a), dtype=np.float64)
        for start, pw, ph in ((0, w, h), (w*h, w//2, h//2), (w*h+w*h//4, w//2, h//2)):
            original_plane = a[:, start:start+pw*ph].reshape(-1, ph, pw)
            expected = original_plane.copy()
            if kind == 'four':
                area = 560 * ph // h
                expected[:, :area, :pw//2] = original_plane[:, :area, pw//2:]
                expected[:, :area, pw//2:] = original_plane[:, :area, :pw//2]
            else:
                tile = pw//5
                for target, index in enumerate((0, 2, 1, 4, 3)):
                    expected[:, :, target*tile:(target+1)*tile] = original_plane[:, :, index*tile:(index+1)*tile]
            delta = expected.reshape(len(a), -1).astype(np.float32) - b[:, start:start+pw*ph]
            squared_error += np.square(delta).sum(axis=1, dtype=np.float64)
        mse = squared_error / a.shape[1]
        worst_mse = float(mse.max())
        minimum_psnr = float(10 * np.log10(255**2 / max(worst_mse, 1e-12)))
        assert minimum_psnr >= 38, f'unexpected display compression error: {minimum_psnr}'
        output.write_bytes(new.read_bytes())
    return {'path': path, 'source_path': path, 'source_sha256': digest(source),
            'sha256': digest(output.read_bytes()), 'bytes': output.stat().st_size,
            'transform': kind, 'stream': after['streams'][0],
            'minimum_frame_psnr_db': round(minimum_psnr, 3),
            'encoding': 'H.264 High, yuv420p, CRF18, faststart',
            'verification': 'every decoded frame compared with relocated original at >=38dB PSNR; dimensions, fps, frames and duration unchanged'}


def main():
    jobs = []
    for path in source_provenances():
        meta = json.loads(original(str(path.relative_to(ROOT))))
        if meta.get('layout', {}).get('cameras_row_major') == ['robot_0_head', 'robot_1_head', 'robot_0_wrist', 'robot_1_wrist']:
            parent = str(path.parent.relative_to(ROOT))
            jobs.extend([(parent+'/preview.gif', parent+'/preview.gif', 'four'),
                         (parent+'/event.mp4', parent+'/event.mp4', 'four')])
    assert len(jobs) == 68
    for stem in ('rgb', 'depth'):
        jobs.extend([(f'docs/videos/sample_cameras_{stem}.gif', f'docs/videos/sample_cameras_{stem}.gif', 'five'),
                     (f'docs/videos/sample_all_cameras_{stem}.mp4', f'docs/videos/sample_all_cameras_{stem}.mp4', 'five'),
                     (f'docs/examples/teleop/preview_{stem}.png', f'docs/examples/teleop/preview_{stem}.png', 'five')])
    for run, name, display in [('20261106-astra-hem-settle-001', '15-current_wrist_depth', 'e14-current-wrist-depth'),
                               ('20261106-astra-opening264-001', '05-current_wrist_depth', 'e15-current-wrist-depth'),
                               ('20261106-astra-hem-depth-001', '15-current_wrist_depth', 'e13-current-wrist-depth')]:
        base = f'docs/collection/attempts/{run}/first-call/{name}'
        jobs.append((base+'.png', DISPLAY_FOLDER+'/'+display+'.png', 'depth'))
    base = 'docs/collection/assets/20261106-wrist-depth-input/e11-00000-wrists'
    jobs.append((base+'.png', DISPLAY_FOLDER+'/e11-00000-wrists.png', 'review'))
    def convert(job):
        path, target, kind = job
        result = convert_video(path, kind) if path.endswith('.mp4') else convert_image(path, target, kind)
        print(f'verified {target}', flush=True)
        return result
    with ThreadPoolExecutor(max_workers=3) as pool:
        records = list(pool.map(convert, jobs))
    by_path = {r['path']: r for r in records}
    for path in source_provenances():
        relative = str(path.relative_to(ROOT))
        meta = json.loads(original(relative))
        parent = str(path.parent.relative_to(ROOT))
        if parent+'/event.mp4' not in by_path:
            continue
        meta['layout']['cameras_row_major'] = ['robot_1_head', 'robot_0_head', 'robot_1_wrist', 'robot_0_wrist']
        meta['layout']['screen_left_robot'] = 'robot_1'
        meta['layout']['screen_right_robot'] = 'robot_0'
        meta['display_derivation'] = {'source_git_commit': SOURCE, 'source_provenance_sha256': digest(original(relative)),
            'script': 'scripts/reorder_display_media.py', 'raw_capture_unchanged': True,
            'operation': 'Move labelled camera tiles; footer and frame timing unchanged; no mirror or interpolation',
            'source_gif_sha256': meta['gif']['sha256'], 'source_mp4_sha256': meta['mp4']['sha256']}
        for media, name in [('gif', 'preview.gif'), ('mp4', 'event.mp4')]:
            result = by_path[parent+'/'+name]
            meta[media].update({key: result[key] for key in ('sha256', 'bytes')})
        meta['encoding']['mp4_crf'] = 18
        meta['encoding']['mp4_profile'] = 'High'
        meta['encoding']['ffmpeg_threads'] = 1
        meta['encoding']['filter_complex_threads'] = 1
        meta['encoding']['gif_encoder'] = 'Pillow exact per-frame palettes; no quantization or frame coalescing'
        meta['exporter_sha256_scope'] = 'Original export, before the separately recorded display derivation'
        path.write_text(json.dumps(meta, ensure_ascii=False, indent=2)+'\n')
    receipt = {'schema': 'phyrc-display-layout-v1', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_git_commit': SOURCE, 'screen_left': 'robot_1', 'screen_right': 'robot_0',
        'script_sha256': digest(Path(__file__).read_bytes()), 'media_count': len(records),
        'preserved': 'Raw actor input PNG/JSON, recordings, policy arrays, robot IDs, action order and temporal order',
        'verification_scope': 'Every GIF/image RGB pixel compared exactly; every MP4 frame compared with tile relocation at >=38dB PSNR',
        'files': records}
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(f'Completed {len(records)} verified media files', flush=True)


if __name__ == '__main__':
    main()
