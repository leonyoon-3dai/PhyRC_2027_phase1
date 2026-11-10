"""Optional current wrist-depth image, derived only from public depth and mask.

Fixed optical-axis Z mapping matches the offline depth review. No file lookup,
semantic segmentation, object pose, completion label or hidden state is used.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from participant.collection.boundary import CONTRACT

SCHEMA = 'phyrc-current-wrist-depth-panel-v1'
CAMERAS = tuple(CONTRACT['competition_access']['allowed_cameras'])
# Screen columns follow the physical view; the public camera/data order stays fixed.
WRISTS = ('robot_1_wrist', 'robot_0_wrist')
LOW, HIGH = .03, 1.20
INVALID, BELOW, ABOVE = (255, 0, 255), (0, 255, 255), (255, 128, 0)
MAX_IMAGES = 16
TASK = '''An optional CURRENT wrist-depth panel is appended LAST after the RGB images (including any historical RGB groups). Its exact zero-based index, current simulation time and pixel rectangles are supplied in current_wrist_depth_panel. The RGB images at indices 0..4 remain CURRENT. Screen left is robot_1_wrist and screen right is robot_0_wrist. Each wrist depth pane is native 256x256, matching that CURRENT wrist RGB, without interpolation. Depth is optical-axis Z in metres, not ray range: fixed 0.03m WHITE to 1.20m BLACK, with magenta invalid/missing (also nonfinite or nonpositive), cyan valid below0.03m, orange valid above1.20m. These colors encode range/validity, not hand/cloth labels. Out-of-range colors do not encode the exact distance. Missing pixels do not prove an opening or free space; the panel does not reveal hidden surfaces, object poses, contact or passage. Compare it with CURRENT RGB and the numeric public depth summaries, keeping occlusion and topology uncertain where unsupported.'''


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _time(value):
    a = np.asarray(value)
    _require(a.ndim == 0 and a.dtype.kind in 'fiu', 'depth panel needs a scalar public time')
    result = float(a)
    _require(math.isfinite(result) and result >= 0, 'depth panel needs finite nonnegative public time')
    return result


def render_depth(depth, mask):
    """Near white, far black; invalid wins over clipping colors, no auto contrast."""
    z = np.asarray(depth, dtype=np.float32)
    valid = np.asarray(mask)
    _require(z.ndim == 2 and valid.shape == z.shape and valid.dtype == np.bool_,
             'depth and boolean mask must be matching 2D arrays')
    effective = valid & np.isfinite(z) & (z > 0)
    q = np.zeros(z.shape, np.uint8)
    q[effective] = np.rint(np.clip((z[effective] - LOW) / (HIGH - LOW), 0, 1) * 255).astype(np.uint8)
    rgb = np.repeat((255 - q)[..., None], 3, axis=-1)
    rgb[~effective] = INVALID
    rgb[effective & (z < LOW)] = BELOW
    rgb[effective & (z > HIGH)] = ABOVE
    return rgb


def input_image_order(images, current_time, history_context=None):
    """Allowlist only temporal camera labels. Never copy arbitrary context fields."""
    _require(len(images) in (5, 10, 15) and len(images) + 1 <= MAX_IMAGES,
             'wrist panel requires complete RGB groups and at most 16 total images')
    groups = (history_context or {}).get('groups')
    if groups is None:
        _require(len(images) == 5, 'historical RGB images require temporal context')
        groups = [{'kind': 'current', 'image_indices': list(range(5)),
                   'camera_order': list(CAMERAS), 'simulation_time_s': current_time}]
    _require(isinstance(groups, list) and len(groups) * 5 == len(images), 'image context group count differs')
    order = []
    for group_index, group in enumerate(groups):
        offset = 5 * group_index
        expected_kind = 'current' if group_index == 0 else 'historical_same_episode'
        t = _time(group['simulation_time_s'])
        _require(group.get('kind') == expected_kind
                 and group.get('image_indices') == list(range(offset, offset + 5))
                 and group.get('camera_order') == list(CAMERAS), 'invalid RGB temporal ordering')
        _require(t == current_time if group_index == 0 else t < current_time,
                 'RGB context time does not match current/past ordering')
        for i, camera in enumerate(CAMERAS):
            order.append({'image_index': offset + i, 'kind': expected_kind,
                          'representation': 'RGB', 'camera': camera, 'simulation_time_s': t})
    order.append({'image_index': len(images), 'kind': 'current',
                  'representation': 'wrist_depth_panel', 'cameras': list(WRISTS),
                  'simulation_time_s': current_time})
    return order


def append_wrist_depth_panel(obs, images, directory, history_context=None):
    """Append one current-only panel; preserve every earlier image/index unchanged."""
    current_time = _time(obs['simulation_time_s'])
    order = input_image_order(images, current_time, history_context)
    depth = np.asarray(obs['depth'], dtype=np.float32)
    valid = np.asarray(obs['depth_valid'])
    _require(depth.shape == valid.shape == (5, 256, 256, 1) and valid.dtype == np.bool_,
             'unexpected public depth/mask shape or dtype')
    directory = Path(directory)
    png = directory / 'current_wrist_depth.png'
    sidecar = directory / 'current_wrist_depth.json'
    _require(directory.is_dir() and not png.exists() and not sidecar.exists(),
             'panel output directory must exist with no previous panel')
    image = Image.new('RGB', (512, 424), '#17202a')
    draw, font = ImageDraw.Draw(image), ImageFont.load_default(size=12)
    draw.text((7, 6), f'CURRENT wrist depth | optical Z metres | t={current_time:.6f}s', font=font, fill='white')
    draw.text((7, 25), 'Fixed: 0.03m WHITE -> 1.20m BLACK | native 256x256', font=font, fill='white')
    panels = []
    for column, camera in enumerate(WRISTS):
        i = CAMERAS.index(camera)
        x, y = column * 256, 68
        draw.text((x + 7, 48), camera + ' CURRENT', font=font, fill='white')
        z, mask = depth[i, :, :, 0], valid[i, :, :, 0]
        effective = mask & np.isfinite(z) & (z > 0)
        below, above = effective & (z < LOW), effective & (z > HIGH)
        counts = {'effective_valid': int(effective.sum()), 'invalid': int((~effective).sum()),
                  'below_range': int(below.sum()), 'within_range': int((effective & ~below & ~above).sum()),
                  'above_range': int(above.sum())}
        image.paste(Image.fromarray(render_depth(z, mask)), (x, y))
        panels.append({'camera': camera, 'matching_current_rgb_image_index': i, 'pixel_counts': counts,
                       'pixel_rectangle_xyxy_exclusive': [x, y, x + 256, y + 256],
                       'depth_float32_sha256': hashlib.sha256(depth[i].tobytes()).hexdigest(),
                       'depth_valid_bool_sha256': hashlib.sha256(valid[i].tobytes()).hexdigest()})
    for y, color, label in ((334, INVALID, 'MAGENTA: invalid, missing, nonfinite or Z<=0'),
                            (355, BELOW, 'CYAN: valid Z<0.03m (out of range)'),
                            (376, ABOVE, 'ORANGE: valid Z>1.20m (out of range)')):
        draw.rectangle((7, y, 19, y + 12), fill=color)
        draw.text((26, y), label, font=font, fill='white')
    draw.text((7, 404), 'No interpolation; no hidden surfaces, object pose or contact labels.', font=font, fill='white')
    image.save(png)
    metadata = {'schema': SCHEMA, 'image_index': len(images), 'kind': 'current',
                'simulation_time_s': current_time, 'input_image_order': order,
                'depth_semantics': 'optical_axis_Z_metres_not_ray_range', 'range_m': [LOW, HIGH],
                'inside_range': 'q=rint(255*(Z-0.03)/(1.20-0.03)); gray=255-q',
                'quantization_step_m': (HIGH - LOW) / 255,
                'maximum_rounding_error_m': (HIGH - LOW) / 510,
                'invalid_rule': 'not depth_valid OR nonfinite OR Z<=0',
                'invalid_rgb': list(INVALID), 'below_range_rgb': list(BELOW), 'above_range_rgb': list(ABOVE),
                'spatial_interpolation': 'none', 'auto_contrast': False,
                'range_categories_not_exact_out_of_range_distance': True,
                'source': 'current_public_depth_and_depth_valid', 'panels': panels,
                'file': png.name, 'png_sha256': hashlib.sha256(png.read_bytes()).hexdigest(),
                'interpretation': 'Depth validity/range only; not semantics, free space, contact, '
                                  'object pose, hidden surfaces, hand entry or sleeve passage.'}
    sidecar.write_text(json.dumps(metadata, allow_nan=False, indent=2) + '\n')
    return [*images, png], deepcopy(metadata)
