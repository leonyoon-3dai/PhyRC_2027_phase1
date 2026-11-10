"""Export a labelled four-camera event from a closed, validated collection.

Only public RGB datasets are read from policy.hdf5. The validation report must
already exist and match the complete capture's policy hash. No audit, score,
raw state, actor trace, or active collection is opened. Nothing is published.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import h5py
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from participant.collection.export_report import CAMERAS, identifier
from participant.collection.validate_capture import complete_flag, load_json, sha256

# Presentation order only; the public observation/action contract is unchanged.
DEFAULT_CAMERAS = ('robot_1_head', 'robot_0_head', 'robot_1_wrist', 'robot_0_wrist')
PLAYBACK_FPS = (1, 2, 4, 5, 10, 20)  # Exact integral GIF centisecond durations.


def require(condition, message):
    if not condition:
        raise ValueError(message)


def signature(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns


def check_capture(capture, validation, episode):
    """Reject active/incomplete manifests before opening any HDF5 file."""
    manifest_path = capture / 'capture.json'
    manifest = load_json(manifest_path.read_text())
    require(manifest.get('complete') is True and manifest.get('raw_archive') is False,
            'export requires a completed immediate capture; do not open an active run')
    report = load_json(validation.read_text())
    require(report.get('schema') == 'phyrc-capture-validation-v1'
            and report.get('quality_passed') is True and report.get('errors') == [],
            'export requires a passing full-capture validation report')
    require(type(report.get('validated_transitions')) is int
            and report['validated_transitions'] > 0
            and report['validated_transitions'] == report.get('total_transitions'),
            'validation must cover every transition')
    episodes = report.get('episodes', [])
    require(episodes and all(e.get('quality_passed') is True and e.get('complete') is True
                            for e in episodes), 'validation contains incomplete episodes')
    selected = [e for e in episodes if e.get('episode') == episode]
    require(len(selected) == 1, 'episode is missing or ambiguous in validation')
    count = selected[0].get('transitions')
    require(type(count) is int and count > 0, 'invalid episode transition count')
    policy_path = capture / 'policy.hdf5'
    before = signature(policy_path)
    actual = sha256(policy_path)
    require(before == signature(policy_path), 'policy changed while hashing')
    checksums = manifest.get('files', manifest.get('checksums', {}))
    require(actual == checksums.get('policy.hdf5') == report.get('sha256', {}).get('policy.hdf5'),
            'policy SHA does not match completed manifest and validation')
    return count, {'policy_sha256': actual, 'capture_sha256': sha256(manifest_path),
                   'validation_sha256': sha256(validation)}, before


def boundary_pixels(episode, camera, boundary, count):
    """Boundary 0 precedes action 0; boundary k follows action k-1, including N."""
    field = camera + '_rgb'
    if boundary == 0:
        return episode['obs'][field][0]
    pixels = episode['next_obs'][field][boundary - 1]
    if boundary < count:
        require(np.array_equal(pixels, episode['obs'][field][boundary]),
                'selected public RGB obs/next_obs boundary continuity differs')
    return pixels


def display_camera_order(cameras):
    """Keep robot_1 left and robot_0 right, regardless of selection order.

    An overview selection fills the slot of the single omitted robot camera.
    The source RGB/depth indexing and robot IDs are never changed.
    """
    require(len(cameras) == 4 and len(set(cameras)) == 4 and all(c in CAMERAS for c in cameras),
            'select four distinct designated public cameras')
    selected = set(cameras)
    return tuple(c if c in selected else 'overview' for c in DEFAULT_CAMERAS)


def mosaic(views, cameras, boundary, tile_size):
    # All pixels retained, aspect ratio preserved; labels occupy separate bands.
    label_h, footer_h = 24, 28
    canvas = Image.new('RGB', (2 * tile_size, 2 * (tile_size + label_h) + footer_h), '#111827')
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default(size=14)
    for i, (camera, pixels) in enumerate(zip(cameras, views)):
        x, y = (i % 2) * tile_size, (i // 2) * (tile_size + label_h)
        draw.text((x + 7, y + 4), camera, font=font, fill='white')
        h, w = pixels.shape[:2]
        scale = min(tile_size / w, tile_size / h)
        im = Image.fromarray(pixels).resize((round(w * scale), round(h * scale)), Image.Resampling.NEAREST)
        canvas.paste(im, (x + (tile_size - im.width) // 2,
                          y + label_h + (tile_size - im.height) // 2))
    draw.text((7, canvas.height - footer_h + 6),
              f'boundary {boundary}  |  episode {boundary / 20:.2f}s (20 Hz)', font=font, fill='white')
    return canvas


def probe_video(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,nb_read_frames,duration', '-of', 'json', str(path)],
        check=True, capture_output=True, text=True)
    return json.loads(result.stdout)['streams'][0]


def export_event(capture, output, *, start, end, run_id=None, validation=None,
                 episode='demo_0', cameras=DEFAULT_CAMERAS, fps=5, tile_size=256, colors=64):
    capture, output = Path(capture), Path(output)
    validation = Path(validation) if validation else capture / 'validation.json'
    run_id = identifier(run_id or capture.name)
    require(episode.startswith('demo_') and episode[5:].isdigit(), 'invalid episode name')
    require(type(start) is int and type(end) is int and 0 <= start < end,
            'specify increasing nonnegative inclusive boundaries')
    cameras = display_camera_order(cameras)
    require(fps in PLAYBACK_FPS and type(fps) is int, 'unsupported playback fps')
    require(type(tile_size) is int and 128 <= tile_size <= 512 and tile_size % 2 == 0,
            'tile size must be an even integer from 128 to 512')
    require(type(colors) is int and 16 <= colors <= 256, 'palette colors must be 16..256')
    require(not output.exists(), 'output already exists; use a new event directory')
    count, hashes, source_stat = check_capture(capture, validation, episode)
    require(end <= count, 'end boundary exceeds recorded transitions')
    require(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'ffmpeg and ffprobe are required')
    frame_count = end - start + 1
    policy_path = capture / 'policy.hdf5'
    with tempfile.TemporaryDirectory(prefix='phyrc-event-') as temp:
        temp = Path(temp)
        source_dimensions = {}
        with h5py.File(policy_path, 'r') as f:
            require(f.attrs.get('schema') == 'phyrc-policy-dataset-v1' and complete_flag(f.attrs),
                    'policy file is not complete')
            data = f['data'][episode]
            require(complete_flag(data.attrs) and int(data.attrs['num_samples']) == count,
                    'episode completion/count differs from validation')
            for camera in cameras:
                for group in ('obs', 'next_obs'):
                    ds = data[group][camera + '_rgb']
                    require(ds.dtype == np.uint8 and len(ds.shape) == 4 and ds.shape[0] == count
                            and ds.shape[-1] == 3, 'invalid public RGB shape or dtype')
                    require(ds.shape == data['obs'][camera + '_rgb'].shape,
                            'RGB before/after dimensions differ')
                source_dimensions[camera] = list(data['obs'][camera + '_rgb'].shape[1:3])
            for i, boundary in enumerate(range(start, end + 1)):
                views = [boundary_pixels(data, c, boundary, count) for c in cameras]
                mosaic(views, cameras, boundary, tile_size).save(temp / f'{i:06d}.png')
        require(signature(policy_path) == source_stat, 'policy changed during export')
        common = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-nostdin', '-n', '-threads', '2',
                  '-framerate', str(fps), '-i', str(temp / '%06d.png')]
        subprocess.run(common + ['-an', '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p',
                                  '-threads', '2', '-movflags', '+faststart', str(temp / 'event.mp4')], check=True)
        filters = (f'[0:v]split[a][b];[b]palettegen=max_colors={colors}:stats_mode=diff[p];'
                   '[a][p]paletteuse=dither=none:diff_mode=rectangle')
        subprocess.run(common + ['-filter_complex_threads', '2', '-filter_complex', filters,
                                  '-an', '-threads', '2', '-loop', '0', str(temp / 'preview.gif')], check=True)
        video = probe_video(temp / 'event.mp4')
        require(int(video['nb_read_frames']) == frame_count, 'MP4 frame count differs')
        with Image.open(temp / 'preview.gif') as gif:
            require(gif.n_frames == frame_count and gif.info.get('loop') == 0, 'GIF frame/loop count differs')
            durations = []
            for i in range(gif.n_frames):
                gif.seek(i)
                durations.append(gif.info['duration'])
            require(set(durations) == {1000 // fps}, 'GIF playback durations differ')
            gif_size = [gif.width, gif.height]
        require(signature(policy_path) == source_stat, 'policy changed during encoding')
        require(hashes['capture_sha256'] == sha256(capture / 'capture.json')
                and hashes['validation_sha256'] == sha256(validation), 'capture evidence changed during export')
        metadata = {
            'schema': 'phyrc-gallery-event-v1', 'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'run_id': run_id, 'source_episode': episode, 'source': hashes,
            'exporter_sha256': sha256(Path(__file__)),
            'validation': {'quality_passed': True, 'validated_episode_transitions': count,
                           'scope': 'preexisting full capture report, matched policy SHA; RGB continuity rechecked'},
            'selection': {'boundary_start_inclusive': start, 'boundary_end_inclusive': end,
                          'frame_count': frame_count, 'episode_time_start_s': start / 20,
                          'episode_time_end_s': end / 20, 'sample_endpoint_span_s': (end - start) / 20,
                          'mapping': 'boundary 0 = obs[0]; boundary k > 0 = next_obs[k-1]; '
                                     'for k < N also checked equal to obs[k]',
                          'contains_final_boundary': end == count, 'frames_omitted_within_interval': 0},
            'layout': {'columns': 2, 'rows': 2, 'cameras_row_major': list(cameras),
                       'robot_columns': {'left': 'robot_1', 'right': 'robot_0'},
                       'source_height_width': source_dimensions, 'tile_size_px': tile_size,
                       'labels': 'camera names and derived episode-relative boundary/time only',
                       'resize': 'nearest_neighbor with aspect-preserving letterbox', 'cropped': False},
            'playback': {'source_policy_hz': 20, 'fps': fps, 'slowdown_factor': 20 / fps,
                         'duration_s': frame_count / fps, 'includes_wall_time_waits': False,
                         'temporal_interpolation': False},
            'encoding': {'ffmpeg_threads': 2, 'filter_complex_threads': 2,
                         'gif_palette_colors': colors, 'gif_dither': 'none',
                         'mp4_codec': 'libx264', 'mp4_crf': 20, 'mp4_pixel_format': 'yuv420p'},
            'gif': {'file': 'preview.gif', 'bytes': (temp / 'preview.gif').stat().st_size,
                    'sha256': sha256(temp / 'preview.gif'), 'size_px': gif_size,
                    'frame_count': frame_count, 'loop': 0, 'frame_duration_ms': 1000 // fps},
            'mp4': {'file': 'event.mp4', 'bytes': (temp / 'event.mp4').stat().st_size,
                    'sha256': sha256(temp / 'event.mp4'), 'stream': video},
            'privacy': 'Only selected designated camera RGB and fixed labels exported; '
                       'no source filesystem paths, actor text, audit, geometry, seeds or evaluation copied.',
            'evaluation': 'Not inferred from video; consult separately reviewed run results.',
        }
        output.mkdir(parents=True, exist_ok=False)
        for name in ('preview.gif', 'event.mp4'):
            shutil.copyfile(temp / name, output / name)
        (output / 'provenance.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--start', type=int, required=True, help='First transition boundary, inclusive')
    parser.add_argument('--end', type=int, required=True, help='Last transition boundary, inclusive; N is allowed')
    parser.add_argument('--run-id')
    parser.add_argument('--validation', type=Path)
    parser.add_argument('--episode', default='demo_0')
    parser.add_argument('--cameras', nargs=4, choices=CAMERAS, default=DEFAULT_CAMERAS,
                        help='Select four cameras; displayed head row then wrist row, robot_1 left / robot_0 right')
    parser.add_argument('--fps', type=int, choices=PLAYBACK_FPS, default=5)
    parser.add_argument('--tile-size', type=int, default=256)
    parser.add_argument('--colors', type=int, default=64)
    args = parser.parse_args()
    result = export_event(**vars(args))
    print(json.dumps({'run_id': result['run_id'], 'frames': result['selection']['frame_count'],
                      'gif_bytes': result['gif']['bytes'], 'mp4_bytes': result['mp4']['bytes']}))


if __name__ == '__main__':
    main()
