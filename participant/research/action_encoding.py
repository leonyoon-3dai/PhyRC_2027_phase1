"""Offline named-channel encoding experiment; never dispatches robot actions.

Names describe normalized command channels, not measured velocities or angles.
No inference about a natural-language explanation, grasp state or action safety.
"""
import json
import math

import numpy as np


ROBOT_IDS = ('robot_0', 'robot_1')
CHANNELS = ('base_forward', 'base_left', 'base_CCW_yaw', 'lift', 'arm_extension',
            'wrist_yaw', 'wrist_pitch', 'wrist_roll', 'gripper')
OFFICIAL_FIELDS = ('base_forward_velocity', 'base_left_velocity', 'base_yaw_velocity',
                   'lift_velocity', 'arm_extension_velocity', 'wrist_yaw_velocity',
                   'wrist_pitch_velocity', 'wrist_roll_velocity', 'gripper_command')


def _keys(value, expected, context):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(f'{context} requires exactly the documented keys')


def _number(value):
    # Check range before isfinite: huge JSON integers must fail without overflow.
    if type(value) not in (int, float) or not -1 <= value <= 1 or not math.isfinite(value):
        raise ValueError('Action channels require finite JSON numbers in [-1,1]; bool is forbidden')
    return float(value)


def named_to_array(payload):
    """Validate explicit robot order and all nine names; return fresh float32(2,9).

    JSON shape: {"robots": [{"robot_id": "robot_0", "action": {all channels}},
                            {"robot_id": "robot_1", "action": {all channels}}]}.
    Channel object key order is irrelevant. Robot list order is mandatory.
    No defaults, clipping, units conversion or gripper-intent reinterpretation.
    """
    _keys(payload, ('robots',), 'Named action')
    robots = payload['robots']
    if type(robots) is not list or len(robots) != 2:
        raise ValueError('Expected exactly two robot entries')
    rows = []
    for robot, expected_id in zip(robots, ROBOT_IDS):
        _keys(robot, ('robot_id', 'action'), 'Robot entry')
        if type(robot['robot_id']) is not str or robot['robot_id'] != expected_id:
            raise ValueError('Robot order must be robot_0 then robot_1')
        _keys(robot['action'], CHANNELS, 'Channel object')
        rows.append([_number(robot['action'][name]) for name in CHANNELS])
    return np.asarray(rows, dtype=np.float32)


def array_to_named(action):
    """Display a normalized array using names, without correcting its values.

    Typed callers use the official float32(2,9) form; JSON callers use two lists
    of nine numbers. Boolean values are rejected before NumPy coercion.
    """
    if isinstance(action, np.ndarray):
        if action.shape != (2, 9) or action.dtype != np.float32:
            raise ValueError('Typed action must be float32 with shape (2,9)')
        values = action.tolist()
    else:
        values = action
    if type(values) is not list or len(values) != 2 or any(
            type(row) is not list or len(row) != 9 for row in values):
        raise ValueError('JSON action must have shape (2,9)')
    return {'robots': [
        {'robot_id': robot_id,
         'action': {name: _number(value) for name, value in zip(CHANNELS, row)}}
        for robot_id, row in zip(ROBOT_IDS, values)
    ]}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON object key')
        result[key] = value
    return result


def _invalid_constant(_value):
    raise ValueError('Non-finite JSON constant')


def named_json_to_array(text):
    """Parse raw JSON without duplicate keys or nonstandard NaN/Infinity."""
    if type(text) is not str:
        raise ValueError('Expected JSON text')
    payload = json.loads(text, object_pairs_hook=_unique_object,
                         parse_constant=_invalid_constant)
    return named_to_array(payload)
