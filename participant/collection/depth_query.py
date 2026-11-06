"""Optional pure lookup of selected pixels in one frozen public observation.

No simulator, model, runtime directory discovery, scene state or world transforms.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json

import numpy as np

from participant.research.depth_backprojection import analyze_pixel, intrinsics, require


CAMERAS = ('overview', 'robot_0_wrist', 'robot_1_wrist', 'robot_0_head', 'robot_1_head')
MAX_POINTS = 8
REQUEST_FIELDS = {'kind', 'observation_id', 'camera', 'pixels_uv', 'include_camera_geometry'}
REQUEST_SCHEMA = {
    'type': 'object', 'additionalProperties': False, 'required': sorted(REQUEST_FIELDS),
    'properties': {
        'kind': {'type': 'string', 'enum': ['depth_query']},
        'observation_id': {'type': 'string', 'pattern': '^[0-9a-f]{64}$'},
        'camera': {'type': 'string', 'enum': list(CAMERAS)},
        'pixels_uv': {'type': 'array', 'minItems': 1, 'maxItems': MAX_POINTS,
                      'items': {'type': 'array', 'minItems': 2, 'maxItems': 2,
                                'items': {'type': 'integer', 'minimum': -4096, 'maximum': 4096}}},
        'include_camera_geometry': {'type': 'boolean'},
    },
}
TASK = '''You may optionally request one exact current public depth lookup before choosing an action. In the initial response use tool=depth_query, an all-zero 2x9 action, steps=1 and the depth_query object; this placeholder is NOT executed. Choose one current designated RGB camera and at most eight integer [u=column,v=row] pixels in its native 256x256 image, using the supplied frozen_observation_id. Do not use historical images or the appended depth panel as coordinate canvases. State the selected visible surface candidates briefly; hand, near/far rim and fingertip identities may remain uncertain. Invalid depth is not free space. The result gives optical-axis Z in metres and optionally camera XYZ/range, not hidden surfaces, object pose or passage evidence. Only compare points in the same camera/time. After a query you receive one action-only follow-up on the SAME frozen public observation and same attached images; no physics progresses between these calls, and a second query is forbidden. For an immediate ordinary action, set depth_query=null. Querying incurs an additional model call and may slow collection; use it only when selected visible points address a specific depth ambiguity.'''


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


@dataclass(frozen=True)
class FrozenPublicFrame:
    observation_id: str
    timestamp_s: float
    depth: np.ndarray
    valid: np.ndarray
    camera_intrinsics: dict
    source_sha256: dict

    def context(self):
        return {'frozen_observation_id': self.observation_id,
                'simulation_time_s': self.timestamp_s, 'query_budget': 1,
                'max_points': MAX_POINTS, 'rgb_image_order': list(CAMERAS),
                'current_rgb_image_indices': list(range(5)), 'resolution_wh': [256, 256]}


def freeze_public_frame(obs, interface, source_sha256, run_id, decision_index):
    """Copy only acknowledged public arrays and already filtered public K."""
    depth = np.array(obs['depth'], dtype=np.float32, copy=True)
    valid = np.array(obs['depth_valid'], dtype=bool, copy=True)
    require(depth.shape == (5, 256, 256, 1) and valid.shape == depth.shape,
            'Invalid public depth shape')
    timestamp = float(np.asarray(obs['simulation_time_s']).item())
    require(np.isfinite(timestamp), 'Invalid public observation clock')
    fields = {'observation_json', 'public_depth_npz', *[camera + '_rgb' for camera in CAMERAS]}
    require(set(source_sha256) == fields and all(isinstance(v, str) and len(v) == 64
            and all(c in '0123456789abcdef' for c in v) for v in source_sha256.values()),
            'Invalid public source digests')
    calibration = {row['id']: row for row in interface['camera_calibration']}
    matrices = {}
    for camera in CAMERAS:
        matrix = intrinsics(interface['camera_intrinsics'][camera]).copy()
        require(calibration[camera]['resolution_wh'] == [256, 256]
                and np.array_equal(matrix, intrinsics(calibration[camera]['intrinsics'])),
                'Public camera calibration disagrees')
        matrix.setflags(write=False)
        matrices[camera] = matrix
    identity = {'run_id': run_id, 'logical_decision_index': decision_index,
                'simulation_time_s': timestamp, 'camera_order': list(CAMERAS),
                'source_sha256': dict(source_sha256),
                'intrinsics_sha256': sha({k: v.tolist() for k, v in matrices.items()})}
    depth.setflags(write=False)
    valid.setflags(write=False)
    return FrozenPublicFrame(sha(identity), timestamp, depth, valid, matrices, dict(source_sha256))


def response_schema(action_schema):
    result = deepcopy(action_schema)
    result['required'].append('depth_query')
    result['properties']['tool']['enum'].append('depth_query')
    result['properties']['depth_query'] = {'anyOf': [deepcopy(REQUEST_SCHEMA), {'type': 'null'}]}
    return result


def route_initial(value, action_schema, validate_decision, *, wiring=False):
    require(isinstance(value, dict) and set(value) == set(action_schema['required']) | {'depth_query'},
            'Invalid optional-depth response fields')
    ordinary = {key: value[key] for key in action_schema['required']}
    if value['tool'] == 'depth_query':
        require(isinstance(value['depth_query'], dict), 'Missing depth request')
        # Reuse exact original zero/steps/stage/reason validation, then intercept.
        ordinary['tool'] = 'stop'
        validate_decision(ordinary, wiring=wiring)
        return None, value['depth_query']
    require(value['depth_query'] is None, 'Action and query cannot be mixed')
    validate_decision(ordinary, wiring=wiring)
    return ordinary, None


def lookup(frame, request):
    require(isinstance(request, dict) and set(request) == REQUEST_FIELDS, 'Unexpected query fields')
    require(len(canonical(request)) <= 4096, 'Oversized query')
    require(request['kind'] == 'depth_query' and request['observation_id'] == frame.observation_id,
            'Stale observation or wrong query kind')
    camera, points, geometry = request['camera'], request['pixels_uv'], request['include_camera_geometry']
    require(type(camera) is str and camera in CAMERAS, 'Unknown current RGB camera')
    require(type(geometry) is bool, 'Camera geometry flag must be boolean')
    require(type(points) is list and 1 <= len(points) <= MAX_POINTS, 'Point budget exceeded')
    require(all(type(uv) is list and len(uv) == 2
                and all(type(v) is int and -4096 <= v <= 4096 for v in uv) for uv in points),
            'Expected bounded integer [u,v] pixels')
    index = CAMERAS.index(camera)
    depth, valid = frame.depth[index, ..., 0], frame.valid[index, ..., 0]
    results = []
    for u, v in points:
        row = {'pixel_uv': [u, v], 'status': 'out_of_bounds', 'optical_z_m': None,
               'invalid_reasons': ['out_of_bounds']}
        xyz = None
        if 0 <= u < 256 and 0 <= v < 256:
            sample = analyze_pixel(depth, valid, frame.camera_intrinsics[camera], [u, v], patch_radius=0)
            okay = sample['center_valid']
            row.update(status='valid' if okay else 'invalid',
                       optical_z_m=float(depth[v, u]) if okay else None,
                       invalid_reasons=[] if okay else [f for f in sample['uncertainty']['flags']
                                                       if f.startswith('center_')])
            xyz = sample['camera_xyz_m'] if okay else None
        if geometry:
            row.update(camera_xyz_m=xyz, camera_range_m=float(np.linalg.norm(xyz)) if xyz is not None else None)
        results.append(row)
    response = {'kind': 'depth_query_result', 'observation_id': frame.observation_id,
                'camera': camera, 'camera_index': index, 'rgb_image_order': list(CAMERAS),
                'simulation_time_s': frame.timestamp_s, 'resolution_wh': [256, 256],
                'depth_semantics': 'optical_Z_metres_not_ray_range',
                'geometry_semantics': 'camera_X_right_Y_down_Z_forward' if geometry else None,
                'source_sha256': dict(frame.source_sha256),
                'intrinsics_sha256': sha(frame.camera_intrinsics[camera].tolist()),
                'request_sha256': sha(request), 'results': results,
                'neighbor_depth_substituted': False, 'hidden_surfaces_estimated': False,
                'object_pose_or_contact_inferred': False}
    canonical(response)
    return response
