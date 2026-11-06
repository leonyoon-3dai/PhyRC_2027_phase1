"""Bounded, prevalidated open-loop decision lists; no visual retry inference.

A plan groups already-supported decisions from one model response. It does not
claim to observe or recover between segments. The caller still records every
transition and may stop the unexecuted suffix at a trusted termination boundary.
"""
from copy import deepcopy

from participant.collection.codex_client import SCHEMA, validate_decision


def plan_schema(max_segments=3):
    if type(max_segments) is not int or not 1 <= max_segments <= 3:
        raise ValueError('max_segments must be 1..3')
    return {
        'type': 'object', 'additionalProperties': False,
        'required': ['decisions'],
        'properties': {'decisions': {
            'type': 'array', 'minItems': 1, 'maxItems': max_segments,
            'items': deepcopy(SCHEMA),
        }},
    }


def validate_plan(value, *, max_segments=3, max_total_steps=60, wiring=False):
    """Reject the entire list before any action, including a malformed suffix."""
    plan_schema(max_segments)
    if type(max_total_steps) is not int or not 1 <= max_total_steps <= 60:
        raise ValueError('plan step budget must be 1..60')
    if not isinstance(value, dict) or set(value) != {'decisions'}:
        raise ValueError('plan fields do not match schema')
    decisions = value['decisions']
    if not isinstance(decisions, list) or not 1 <= len(decisions) <= max_segments:
        raise ValueError('plan segment count out of bounds')
    actions, total = [], 0
    for index, decision in enumerate(decisions):
        action = validate_decision(decision, wiring=wiring)
        if decision['tool'] == 'finish_episode' and index != len(decisions) - 1:
            raise ValueError('finish_episode must be the final segment')
        total += (decision['steps'] if decision['tool'] == 'act'
                  else 1 if decision['tool'] == 'stop' else 0)
        actions.append(action)
    if total > max_total_steps:
        raise ValueError('plan exceeds total step budget')
    return actions


PLAN_TASK = '''Return one object with a decisions array. The list contains at most {max_segments} decisions and at most {max_total_steps} total control steps. Each decision follows the original action contract. All decisions are planned from THIS observation; you will not see new observations until this list ends. This is an open-loop list, not a conditional program: do not claim that future grasp success has already been checked. Use a single short decision near uncertain contact or when the next motion depends on its result. You may group predictable positioning or neutral holding steps. Never include another segment after finish_episode. The controller may stop a suffix before it is executed. Give each segment its own brief operational reason.'''


BATCH_WIRING_TASK = '''This is one model-call wiring test, not a dressing demonstration. In one decisions array return exactly these three segments: (1) act with lift +0.03 and gripper -1 for both robots, all other velocities zero, for 2 steps; (2) stop with all-zero action and steps=1; (3) finish_episode with all-zero action and steps=1. Label all segments preparation and uncertain. Do not attempt grasp or dressing.'''
