"""Offline motion diagnostics from public observation JSON and applied decisions.

Example (after collection stops)::

    python scripts/analyze_support_diagnostic.py \
      --observations output/actors/RUN/observations \
      --decisions output/operator-traces/RUN/decisions.jsonl \
      --public-interface public-interface.json --output support-report.json

The optional public interface is the actor's static joint_names/joint_units JSON,
not a simulator manifest. Alternatively supply --lift-joint-index explicitly.
Sparse observations often span model action PLUS controller settling. These are
reported together; neither zero commands nor closed fingers prove cloth support.
No audit, evaluation, raw state, image, or actor reasoning files are opened.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np


FIELDS = {
    'base_pose_world': (2, 7), 'grasp_pose_base': (2, 7),
    'fingertip_origin_distance': (2, 1), 'controller_target': (2, 9),
    'gripper_close_command': (2, 1),
}
TIME_TOLERANCE_S = 1e-6


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    def reject(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(Path(path).read_text(), parse_constant=reject)


def provenance(path):
    path = Path(path)
    return {'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def rotation(q):
    require(np.linalg.norm(q) > 1e-12, 'zero base quaternion')
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)],
                     [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)],
                     [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]])


def load_observations(directory):
    rows = []
    for path in sorted(Path(directory).glob('*/observation.json')):
        payload = read_json(path)
        state = payload['public_robot_observation']
        clean = {}
        for key, shape in FIELDS.items():
            value = np.asarray(state[key], dtype=float)
            require(value.shape == shape and np.isfinite(value).all(), 'invalid ' + key)
            clean[key] = value
        for key in ('joint_position', 'joint_velocity'):
            value = np.asarray(state[key], dtype=float)
            require(value.ndim == 2 and value.shape[0] == 2 and value.shape[1] > 0
                    and np.isfinite(value).all(), 'invalid ' + key)
            clean[key] = value
        require(clean['joint_position'].shape == clean['joint_velocity'].shape,
                'joint position/velocity layouts differ')
        require(np.isin(clean['gripper_close_command'], (0, 1)).all(), 'invalid grip intent')
        t = float(state['simulation_time_s'])
        require(math.isfinite(t), 'invalid simulation clock')
        world = []
        for robot in range(2):
            base = clean['base_pose_world'][robot]
            world.append(base[:3] + rotation(base[3:]) @ clean['grasp_pose_base'][robot, :3])
        clean['grasp_position_world'] = np.asarray(world)
        rows.append({'time': t, 'state': clean, 'source': provenance(path)})
    require(rows, 'no */observation.json files found')
    rows.sort(key=lambda row: row['time'])
    require(all(b['time'] > a['time'] for a, b in zip(rows, rows[1:])),
            'duplicate/nonincreasing observation times')
    require(all(row['state']['joint_position'].shape == rows[0]['state']['joint_position'].shape
                for row in rows), 'joint layout changed between observations')
    return rows


def joint_mapping(interface, count, lift_joint_index):
    if lift_joint_index is not None:
        require(type(lift_joint_index) is int and 0 <= lift_joint_index < count,
                'lift index outside observed joint layout')
    names = interface.get('joint_names') if interface else None
    units = interface.get('joint_units') if interface else None
    if names is not None:
        require(isinstance(names, list) and len(names) == 2
                and all(isinstance(row, list) and len(row) == count
                        and all(isinstance(n, str) for n in row) for row in names),
                'invalid public joint names')
    if units is not None:
        require(isinstance(units, list) and len(units) == 2
                and all(isinstance(row, list) and len(row) == count for row in units),
                'invalid public joint units')
    result = []
    for robot in range(2):
        row = names[robot] if names is not None else None
        lift = lift_joint_index
        source = 'explicit_cli_index' if lift is not None else 'unavailable'
        if lift is None and row is not None:
            matches = [i for i, n in enumerate(row) if n in ('joint_lift', 'lift_joint', 'lift')]
            require(len(matches) <= 1, 'ambiguous lift joint name')
            if matches:
                lift, source = matches[0], 'public_joint_name'
        if lift is not None and units is not None:
            require(units[robot][lift] == 'm', 'lift must use metres')
        fingers = [i for i, n in enumerate(row or []) if n in
                   ('gripper_finger_left_joint', 'gripper_finger_right_joint')]
        result.append({'lift_index': lift, 'source': source,
                       'lift_name': row[lift] if row is not None and lift is not None else None,
                       'finger_indices': fingers,
                       'finger_names': [row[i] for i in fingers]})
    return result


def load_segments(path):
    result = []
    for line_number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if value.get('type') != 'applied_segment':
            continue
        # Allowlist actual public actions and their observation boundaries only.
        row = {key: value[key] for key in ('decision_index', 'action_source', 'start_step',
               'end_step', 'simulation_start_s', 'simulation_end_s', 'applied_action')}
        row['line'] = line_number
        row['stage_intent'] = value.get('stage_intent')
        action = np.asarray(row['applied_action'], dtype=float)
        require(action.shape == (2, 9) and np.isfinite(action).all()
                and np.max(abs(action)) <= 1, 'invalid applied action')
        require(all(type(row[key]) is int and row[key] >= 0
                    for key in ('decision_index', 'start_step', 'end_step')), 'invalid boundary index')
        require(row['end_step'] >= row['start_step'], 'reversed step boundaries')
        require(all(type(row[key]) in (float, int) and math.isfinite(row[key])
                    for key in ('simulation_start_s', 'simulation_end_s')), 'invalid segment clock')
        require(abs((row['simulation_end_s'] - row['simulation_start_s'])
                    - .05 * (row['end_step'] - row['start_step'])) < TIME_TOLERANCE_S,
                'segment boundaries disagree with 20 Hz')
        result.append(row)
    require(result, 'no applied segments found')
    require(all(b['start_step'] == a['end_step'] and
                abs(b['simulation_start_s'] - a['simulation_end_s']) < TIME_TOLERANCE_S
                for a, b in zip(result, result[1:])), 'applied segments are not contiguous')
    return result


def endpoint(state, robot, mapping):
    lift = mapping['lift_index']
    target = float(state['controller_target'][robot, 0])
    actual = float(state['joint_position'][robot, lift]) if lift is not None else None
    return {
        'gripper_close_command': bool(state['gripper_close_command'][robot, 0]),
        'gripper_target': float(state['controller_target'][robot, 5]),
        'fingertip_origin_distance_m': float(state['fingertip_origin_distance'][robot, 0]),
        'finger_joint_positions': state['joint_position'][robot, mapping['finger_indices']].tolist(),
        'finger_joint_velocities': state['joint_velocity'][robot, mapping['finger_indices']].tolist(),
        'lift_target_m': target, 'lift_measured_m': actual,
        'lift_target_minus_measured_m': target - actual if actual is not None else None,
        'lift_velocity_m_s': float(state['joint_velocity'][robot, lift]) if lift is not None else None,
    }


def analyze(observations, decisions, *, public_interface=None, lift_joint_index=None):
    samples = load_observations(observations)
    segments = load_segments(decisions)
    interface = read_json(public_interface) if public_interface else {}
    mapping = joint_mapping(interface, samples[0]['state']['joint_position'].shape[1], lift_joint_index)
    intervals = []
    for segment in segments:
        if segment['action_source'] != 'model' or segment['start_step'] == segment['end_step']:
            continue
        action = np.asarray(segment['applied_action'])
        moving = np.any(action[:, :8] != 0, axis=1)
        record = {'decision_index': segment['decision_index'], 'stage_intent': segment['stage_intent'],
                  'model_segment': segment, 'commanded_motion_robots': np.flatnonzero(moving).tolist(),
                  'commanded_stationary_robots': np.flatnonzero(~moving).tolist(),
                  'single_robot_motion_command': bool(moving.sum() == 1),
                  'gripper_action': action[:, 8].tolist(), 'measurement_status': None}
        starts = [s for s in samples if abs(s['time'] - segment['simulation_start_s']) < TIME_TOLERANCE_S]
        ends = [s for s in samples if s['time'] >= segment['simulation_end_s'] - TIME_TOLERANCE_S]
        if not starts or not ends:
            record['measurement_status'] = 'missing_start_observation' if not starts else 'missing_end_observation'
            intervals.append(record)
            continue
        before, after = starts[0], ends[0]
        covered = [s for s in segments if s['simulation_start_s'] >= before['time'] - TIME_TOLERANCE_S
                   and s['simulation_end_s'] <= after['time'] + TIME_TOLERANCE_S
                   and s['end_step'] > s['start_step']]
        # Never attribute a later model decision to this model segment.
        if (not covered or covered[0] != segment
                or any(s['action_source'] != 'controller_settle'
                       or s['decision_index'] != segment['decision_index'] for s in covered[1:])
                or abs(covered[-1]['simulation_end_s'] - after['time']) >= TIME_TOLERANCE_S):
            record['measurement_status'] = 'end_observation_spans_other_or_unrecorded_actions'
            intervals.append(record)
            continue
        record.update(measurement_status='measured', start_observation=before['source'],
                      end_observation=after['source'], start_boundary=covered[0]['start_step'],
                      end_boundary=covered[-1]['end_step'], simulation_start_s=before['time'],
                      simulation_end_s=after['time'],
                      includes_controller_settle=bool(len(covered) > 1),
                      covered_segments=covered, robots=[])
        for robot in range(2):
            a, b = before['state'], after['state']
            delta = b['grasp_position_world'][robot] - a['grasp_position_world'][robot]
            record['robots'].append({
                'robot': robot, 'motion_command_zero': not bool(moving[robot]),
                'grasp_world_delta_m': delta.tolist(), 'grasp_world_displacement_m': float(np.linalg.norm(delta)),
                'base_world_delta_m': (b['base_pose_world'][robot, :3] - a['base_pose_world'][robot, :3]).tolist(),
                'grasp_base_delta_m': (b['grasp_pose_base'][robot, :3] - a['grasp_pose_base'][robot, :3]).tolist(),
                'before': endpoint(a, robot, mapping[robot]), 'after': endpoint(b, robot, mapping[robot]),
            })
        intervals.append(record)
    return {
        'schema': 'phyrc-public-support-diagnostic-v1',
        'scope': 'offline public robot kinematics; endpoint displacements, not path lengths',
        'support_confirmed': None, 'cloth_motion_measured': False,
        'limitations': [
            'Robot motion, close intent and finger spacing do not establish cloth support or attachment.',
            'Fingertip-origin distance is not the inner contact gap.',
            'A stationary command may retain targets; measured motion can continue.',
            'Sparse endpoint comparisons include explicitly listed controller-settle segments.',
            'Residuals and low velocity alone do not establish arrival or successful grasp.',
            'Lift residual is unavailable unless a joint name or explicit index maps measured lift.',
            'No evaluation, audit, raw simulator state, or images are read; visual review is still required.',
        ],
        'sources': {'decisions': provenance(decisions),
                    'observations': [s['source'] for s in samples],
                    'public_interface': provenance(public_interface) if public_interface else None},
        'joint_mapping': mapping,
        'summary': {'model_action_intervals': len(intervals),
                    'measured_intervals': sum(r['measurement_status'] == 'measured' for r in intervals),
                    'single_robot_motion_intervals': sum(r['single_robot_motion_command'] for r in intervals)},
        'intervals': intervals,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations', type=Path, required=True)
    parser.add_argument('--decisions', type=Path, required=True)
    parser.add_argument('--public-interface', type=Path)
    parser.add_argument('--lift-joint-index', type=int)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = analyze(args.observations, args.decisions, public_interface=args.public_interface,
                     lift_joint_index=args.lift_joint_index)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(report['summary']))


if __name__ == '__main__':
    main()
