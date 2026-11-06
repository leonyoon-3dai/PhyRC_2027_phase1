"""B1: offline public optical-Z depth sanity, not a pose/keypoint detector.

Uses saved public RGB-D and saved public_interface intrinsics only. No Isaac,
HDF5, evaluator, scene geometry, actor session, world extrinsic or network input.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np
from PIL import Image


CAMERAS = ('overview', 'robot_0_wrist', 'robot_1_wrist', 'robot_0_head', 'robot_1_head')
RUN_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def intrinsics(value):
    matrix = np.asarray(value, np.float64)
    require(matrix.shape == (3, 3) and np.isfinite(matrix).all(), 'Invalid 3x3 intrinsics')
    require(matrix[0, 0] > 0 and matrix[1, 1] > 0
            and np.allclose(matrix[2], [0, 0, 1], atol=1e-12, rtol=0)
            and abs(matrix[1, 0]) <= 1e-12, 'Expected calibrated pinhole intrinsics')
    return matrix


def analyze_pixel(depth, depth_valid, matrix, pixel_uv, *, rgb=None, patch_radius=2,
                  min_valid_fraction=.8, depth_jump_m=.05, depth_jump_fraction=.05):
    """Backproject the CENTER sample; neighbor statistics never replace its Z.

    Returns a JSON-safe allowlist. Camera axes are X right, Y down, Z forward.
    Pixel coordinates are literal zero-based u/column, v/row; no implicit +0.5.
    Flags describe a heuristic local depth check, not accuracy or probability.
    """
    depth, mask, matrix = np.asarray(depth), np.asarray(depth_valid), intrinsics(matrix)
    require(depth.ndim == 2 and min(depth.shape) > 0 and depth.dtype.kind == 'f'
            and mask.shape == depth.shape and mask.dtype == bool, 'Expected HxW float depth and bool mask')
    require(len(pixel_uv) == 2 and all(type(x) is int for x in pixel_uv), 'Pixel must be integer (u,v)')
    u, v = pixel_uv
    height, width = depth.shape
    require(0 <= u < width and 0 <= v < height, 'Pixel lies outside image')
    require(type(patch_radius) is int and 0 <= patch_radius <= 32, 'Patch radius must be 0..32')
    require(all(np.isfinite(x) for x in (min_valid_fraction, depth_jump_m, depth_jump_fraction))
            and 0 <= min_valid_fraction <= 1 and depth_jump_m >= 0 and depth_jump_fraction >= 0,
            'Invalid uncertainty thresholds')
    color = None
    if rgb is not None:
        rgb = np.asarray(rgb)
        require(rgb.shape == (height, width, 3) and rgb.dtype == np.uint8, 'RGB and depth must align')
        color = rgb[v, u].tolist()
    x0, x1 = max(0, u-patch_radius), min(width, u+patch_radius+1)
    y0, y1 = max(0, v-patch_radius), min(height, v+patch_radius+1)
    patch, supplied = depth[y0:y1, x0:x1], mask[y0:y1, x0:x1]
    numeric_valid = np.isfinite(patch) & (patch > 0)
    effective = supplied & numeric_valid
    values = patch[effective].astype(np.float64)
    fraction = float(effective.sum() / effective.size)
    flags = []
    z = float(depth[v, u])
    if not bool(mask[v, u]):
        flags.append('center_mask_invalid')
    if not np.isfinite(z):
        flags.append('center_nonfinite')
    elif z <= 0:
        flags.append('center_nonpositive')
    center_valid = bool(mask[v, u]) and np.isfinite(z) and z > 0
    if patch.size != (2 * patch_radius + 1)**2:
        flags.append('patch_truncated_at_image_edge')
    if fraction < min_valid_fraction:
        flags.append('low_patch_valid_fraction')
    inconsistent = int(np.count_nonzero(supplied & ~numeric_valid))
    if inconsistent:
        flags.append('mask_marks_nonfinite_or_nonpositive_valid')
    median = mad = minimum = maximum = spread = center_deviation = threshold = None
    if len(values):
        median = float(np.median(values))
        mad = float(np.median(np.abs(values-median)))
        minimum, maximum = float(values.min()), float(values.max())
        spread = maximum-minimum
        threshold = max(float(depth_jump_m), float(depth_jump_fraction)*median)
        if spread > threshold:
            flags.append('patch_depth_range_exceeds_threshold')
        if center_valid:
            center_deviation = abs(z-median)
            if center_deviation > threshold:
                flags.append('center_differs_from_patch_median')
    else:
        flags.append('no_valid_patch_depth')
    xyz = residual = None
    if center_valid:
        ray = np.linalg.solve(matrix, np.array([u, v, 1.], np.float64))
        point = ray * (z / ray[2])  # optical Z, NOT Euclidean distance along the ray
        projected = matrix @ point
        uv_again = projected[:2] / projected[2]
        xyz = point.tolist()
        residual = float(np.linalg.norm(uv_again-[u, v]))
    return {
        'pixel_uv': [u, v], 'pixel_coordinate_convention': 'zero_based_column_row_no_half_pixel_offset',
        'rgb_uint8': color, 'depth_semantics': 'optical_axis_Z_metres_not_ray_range',
        'depth_sample_m': z if np.isfinite(z) else None,
        'center_valid': bool(center_valid), 'camera_xyz_m': xyz,
        'camera_axes': 'X_right_Y_down_Z_forward', 'world_xyz_m': None,
        'reprojection_roundtrip_error_px': residual,
        'roundtrip_is_accuracy_validation': False,
        'status': 'invalid' if not center_valid else 'review_required' if flags else 'valid_depth_sample',
        'uncertainty': {
            'kind': 'local_depth_heuristics_not_probability', 'flags': flags,
            'patch_radius_px': patch_radius, 'patch_bounds_xyxy_exclusive': [x0, y0, x1, y1],
            'patch_pixels': int(effective.size), 'valid_pixels': int(effective.sum()),
            'valid_fraction': fraction, 'mask_numeric_inconsistency_count': inconsistent,
            'median_depth_m': median, 'median_absolute_deviation_m': mad,
            'minimum_depth_m': minimum, 'maximum_depth_m': maximum, 'depth_range_m': spread,
            'center_minus_patch_median_abs_m': center_deviation,
            'applied_depth_jump_threshold_m': threshold,
            'parameters': {'min_valid_fraction': min_valid_fraction, 'depth_jump_m': depth_jump_m,
                           'depth_jump_fraction': depth_jump_fraction},
        },
        'neighbor_depth_substituted': False, 'semantic_keypoint_detected': False,
    }


def _json(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 2*1024*1024,
            'Missing, linked or oversized metadata')
    value = json.loads(path.read_text())
    require(isinstance(value, dict), 'Expected metadata object')
    return value


def _sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def analyze_saved_observations(root, run_id, observation_indices, *, patch_radius=2):
    """Center-pixel pilot on closed saved public observations; no semantic label."""
    started = time.perf_counter()
    root = Path(root).resolve()
    require(isinstance(run_id, str) and RUN_ID.fullmatch(run_id), 'Invalid run ID')
    require(observation_indices and len(set(observation_indices)) == len(observation_indices)
            and all(type(i) is int and 0 <= i <= 99999 for i in observation_indices),
            'Expected distinct nonnegative observation indices')
    capture = root/'output/collections'/run_id
    source = root/'output/actors'/run_id/'observations'
    require(capture.resolve().is_relative_to(root) and source.resolve().is_relative_to(root),
            'Source path escapes root')
    require(_json(capture/'capture.json').get('complete') is True, 'Only closed captures are permitted')
    metadata_path = capture/'run_metadata.json'
    public = _json(metadata_path)['public_interface']
    calibration = {item['id']: item for item in public['camera_calibration']}
    samples, sources = [], {'run_metadata.json': {'sha256': _sha(metadata_path),
        'fields_used': ['public_interface.camera_intrinsics',
                        'public_interface.camera_calibration.id',
                        'public_interface.camera_calibration.resolution_wh',
                        'public_interface.camera_calibration.intrinsics']}}
    for index in observation_indices:
        directory = source/f'{index:05d}'
        require(not directory.is_symlink(), 'Linked observation directory rejected')
        observation_path = directory/'observation.json'
        observation = _json(observation_path)
        order = observation['rgb_image_order']
        require(tuple(order) == CAMERAS, 'Saved RGB/depth camera order differs from the public contract')
        clock = observation['public_robot_observation']['simulation_time_s']
        require(type(clock) in (int, float) and np.isfinite(clock), 'Invalid public observation clock')
        archive = directory/'public_depth.npz'
        require(archive.is_file() and not archive.is_symlink(), 'Missing or linked public depth archive')
        with np.load(archive, allow_pickle=False) as arrays:
            require(set(arrays.files) == {'depth', 'depth_valid'}, 'Unexpected public depth archive fields')
            depth, valid = arrays['depth'], arrays['depth_valid']
        require(depth.ndim == 4 and depth.shape[0] == 5 and depth.shape[-1] == 1
                and depth.dtype == np.float32 and valid.dtype == bool and valid.shape == depth.shape,
                'Expected saved five-camera float32 depth and bool mask')
        sources[f'observations/{index:05d}/observation.json'] = {'sha256': _sha(observation_path)}
        sources[f'observations/{index:05d}/public_depth.npz'] = {'sha256': _sha(archive)}
        height, width = depth.shape[1:3]
        for camera_index, camera in enumerate(order):
            spec = calibration[camera]
            matrix = intrinsics(public['camera_intrinsics'][camera])
            require(spec['resolution_wh'] == [width, height]
                    and np.array_equal(matrix, intrinsics(spec['intrinsics'])),
                    'Saved public calibration sources disagree')
            rgb_path = directory/(camera+'.png')
            require(not rgb_path.is_symlink(), 'Linked RGB source rejected')
            with Image.open(rgb_path) as image:
                rgb = np.asarray(image)
            sample = analyze_pixel(depth[camera_index, ..., 0], valid[camera_index, ..., 0], matrix,
                                   [width//2, height//2], rgb=rgb, patch_radius=patch_radius)
            sample.update(observation_index=index, public_simulation_time_s=clock, camera=camera,
                          selection='image_center_calibration_probe_not_keypoint',
                          resolution_wh=[width, height], intrinsics=matrix.tolist(),
                          intrinsics_source='saved run_metadata.json public_interface.camera_intrinsics.'+camera)
            samples.append(sample)
            sources[f'observations/{index:05d}/{camera}.png'] = {'sha256': _sha(rgb_path)}
    return {'schema': 'phyrc-offline-depth-sanity-v1', 'baseline': 'B1', 'run_id': run_id,
            'created_at_utc': datetime.now(timezone.utc).isoformat(),
            'observation_indices': list(observation_indices), 'samples': samples,
            'source_files': sources, 'module_sha256': _sha(Path(__file__)),
            'cpu_wall_s': time.perf_counter()-started,
            'scope': 'public optical-Z to camera-XYZ connection and local depth heuristics only',
            'pose_detector_used': False, 'keypoint_accuracy_evaluated': False,
            'world_extrinsics_used': False, 'simulation_ground_truth_used': False,
            'hdf5_read': False, 'live_runtime_modified': False, 'sent_to_actor': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--observations', type=int, nargs='+', default=[0])
    parser.add_argument('--patch-radius', type=int, default=2)
    parser.add_argument('--output', type=Path, required=True, help='New JSON path; refuses overwrite')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('--output already exists')
    if not args.output.parent.is_dir():
        parser.error('--output parent must already exist')
    result = analyze_saved_observations(args.root, args.run_id, args.observations,
                                        patch_radius=args.patch_radius)
    with args.output.open('x') as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'baseline': 'B1', 'samples': len(result['samples']),
                      'valid_center_samples': sum(s['center_valid'] for s in result['samples']),
                      'cpu_wall_s': result['cpu_wall_s'], 'keypoints_detected': False}))


if __name__ == '__main__':
    main()
