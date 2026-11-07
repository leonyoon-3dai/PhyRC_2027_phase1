"""Optional model-output representation; official actions remain float32 (2, 9).

Pack exact channel names without clipping, scaling, heuristic repair or physics.
Duplicate JSON keys are rejected earlier by the existing exec actor parser.
"""
from copy import deepcopy
import hashlib
import json
import math


SCHEMA_ID = 'phyrc-named-actions-v1'
ROBOTS = ('robot_0', 'robot_1')
CHANNELS = ('base_forward', 'base_left', 'base_CCW_yaw', 'lift', 'arm_extension',
            'wrist_yaw', 'wrist_pitch', 'wrist_roll', 'gripper')
MAPPING = {'schema': SCHEMA_ID, 'robot_order': list(ROBOTS), 'channel_order': list(CHANNELS),
           'official_dtype': 'float32', 'value_transform': 'none',
           'validation': 'existing_official_action_validator'}
MAPPING_SHA256 = hashlib.sha256(json.dumps(
    MAPPING, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
TASK = '''For this attempt, return action ONLY as an object with robot_0 and robot_1 objects. Each robot must contain every channel named in the response schema exactly once. Put each intended normalized command under its own channel name; set unused channels to zero. Object key order is irrelevant. In particular wrist_roll and gripper are separate commands: a close intent belongs only in gripper. Deliberate wrist_roll remains available when you intend roll. Do not return positional action arrays. The controller packs names into the unchanged official robot/channel order without changing values or inferring intent from your reason. Stop, finish_episode and any depth_query placeholder require all eighteen named values to be zero and steps=1.'''
POSITIONAL_DESCRIPTION = ('Each action has two rows in robot order 0,1; each row is '
    '[base_forward, base_left, base_CCW_yaw, lift, arm_extension, wrist_yaw, wrist_pitch, wrist_roll, gripper]. '
    'The first 8 are normalized VELOCITIES in [-1,1], not positions or deltas.')
NAMED_DESCRIPTION = ('Each action has exactly two objects named robot_0 and robot_1, each with '
    'base_forward, base_left, base_CCW_yaw, lift, arm_extension, wrist_yaw, wrist_pitch, wrist_roll, and gripper. '
    'The eight channels other than gripper are normalized VELOCITIES in [-1,1], not positions or deltas.')


def response_schema(base):
    result = deepcopy(base)
    robot = {'type': 'object', 'additionalProperties': False, 'required': list(CHANNELS),
             'properties': {name: {'type': 'number', 'minimum': -1, 'maximum': 1}
                            for name in CHANNELS}}
    result['properties']['action'] = {
        'type': 'object', 'additionalProperties': False, 'required': list(ROBOTS),
        'properties': {name: deepcopy(robot) for name in ROBOTS}}
    return result


def prompt(base):
    if base.count(POSITIONAL_DESCRIPTION) != 1:
        raise ValueError('named action prompt requires one known action contract')
    result = base.replace(POSITIONAL_DESCRIPTION, NAMED_DESCRIPTION)
    result = result.replace('an all-zero 2x9 action', 'an all-zero named action object')
    return result + '\n\n' + TASK


def pack(value):
    if type(value) is not dict or set(value) != set(ROBOTS):
        raise ValueError('named action requires exactly robot_0 and robot_1')
    rows = []
    for robot in ROBOTS:
        row = value[robot]
        if type(row) is not dict or set(row) != set(CHANNELS):
            raise ValueError('named action requires exactly nine known channels per robot')
        values = [row[channel] for channel in CHANNELS]
        if any(type(x) not in (int, float) or not -1 <= x <= 1 or not math.isfinite(x)
               for x in values):
            raise ValueError('named action values must be finite numbers in [-1,1]')
        rows.append(values)
    return rows


def normalize_result(result):
    """Keep raw intent beside canonical decision; existing validation runs next."""
    value = result['decision']
    if type(value) is not dict or 'action' not in value:
        raise ValueError('named action decision is missing action')
    raw = value['action']
    return dict(result, decision=dict(value, action=pack(raw)), named_action={
        'schema': SCHEMA_ID, 'mapping_sha256': MAPPING_SHA256,
        'raw_action': deepcopy(raw)})


def public_provenance(value, canonical=None):
    """Fail closed on extra metadata, altered mapping, or mismatched action."""
    if (type(value) is not dict or set(value) != {'schema', 'mapping_sha256', 'raw_action'}
            or value['schema'] != SCHEMA_ID or value['mapping_sha256'] != MAPPING_SHA256):
        raise ValueError('invalid named action mapping provenance')
    packed = pack(value['raw_action'])
    if canonical is not None and packed != canonical:
        raise ValueError('named action provenance disagrees with canonical decision')
    return deepcopy(value)


def public_mapping(value):
    if value != MAPPING:
        raise ValueError('unknown named action mapping')
    return deepcopy(MAPPING)
