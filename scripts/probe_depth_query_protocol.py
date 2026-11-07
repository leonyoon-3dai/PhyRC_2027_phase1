#!/usr/bin/env python3
"""Two real isolated CLI calls on synthetic public inputs; no simulator or GPU.

This tests response schemas, 16-image resume, exact lookup and call accounting.
It does not test model-selected garment points or dressing performance.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import time

import numpy as np

from participant.collection.boundary import CONTRACT
from participant.collection.codex_actor import Actor
from participant.collection.codex_client import (
    SCHEMA, TokenUsageAccounting, dump, prepare_observation, replay_image_context,
    validate_decision,
)
from participant.collection import depth_query as dq
from participant.collection.wrist_depth import append_wrist_depth_panel


def synthetic_observation(tick):
    dims = CONTRACT['default_dimensions']
    obs = {key: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
           for key, spec in CONTRACT['observations'].items()}
    obs['simulation_time_s'] = np.asarray(tick / 20, np.float64)
    obs['depth'].fill(.75)
    obs['depth_valid'].fill(True)
    obs['depth_valid'][:, 0, 0, 0] = False
    obs['depth'][:, 0, 0, 0] = 0
    for i in range(5):
        obs['rgb'][i] = [30 + tick, 40 + i * 20, 90]
        obs['rgb'][i, 112:145, 112:145] = [220, 180, 40]
    return obs


def build_fixture(root):
    current = synthetic_observation(20)
    payload, images = prepare_observation(current, root / 'current')
    history = []
    for tick in (8, 14):
        _, old_images = prepare_observation(synthetic_observation(tick), root / f'history-{tick}')
        history.append({'replay_boundary': tick, 'simulation_time_s': tick / 20, 'images': old_images})
    images, context = replay_image_context(images, 1., history)
    (root / 'panel').mkdir()
    images, panel = append_wrist_depth_panel(current, images, root / 'panel', context)
    matrix = [[200., 0., 128.], [0., 200., 128.], [0., 0., 1.]]
    interface = {'camera_intrinsics': {c: deepcopy(matrix) for c in dq.CAMERAS},
                 'camera_calibration': [{'id': c, 'resolution_wh': [256, 256],
                                         'intrinsics': deepcopy(matrix)} for c in dq.CAMERAS]}
    paths = {'observation_json': root / 'current/observation.json',
             'public_depth_npz': root / 'current/public_depth.npz',
             **{c + '_rgb': root / 'current' / (c + '.png') for c in dq.CAMERAS}}
    frame = dq.freeze_public_frame(current, interface,
        {key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()},
        'synthetic-depth-protocol', 0)
    return payload, images, context, panel, frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model-timeout', type=float, default=180)
    parser.add_argument('--named-actions', action='store_true',
                        help='Test named zero query then a named advance/close action, without dispatch')
    args = parser.parse_args()
    if not np.isfinite(args.model_timeout) or not 10 <= args.model_timeout <= 180:
        parser.error('model-timeout must be 10..180 seconds')
    root = args.output.resolve()
    root.mkdir(parents=True, exist_ok=False, mode=0o700)
    payload, images, context, panel, frame = build_fixture(root)
    image_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in images]
    prompt = ('This is a synthetic protocol fixture, not a robot task or a real episode. '
              'The supplied historical groups are synthetic placeholders used only to test image ordering. '
              'Use no tools. On this first call, return tool=depth_query with an all-zero 2x9 action, '
              'steps=1, stage=preparation, visual_assessment=uncertain. Query exactly camera '
              'robot_0_wrist and pixels_uv [[128,128],[0,0]], with include_camera_geometry=true. '
              'Use the supplied observation ID and a brief fixture reason. Do not return an action yet.\n'
              + dq.TASK + '\n' + json.dumps(payload, allow_nan=False)
              + '\nImage temporal context: ' + json.dumps(context, allow_nan=False)
              + '\nCurrent wrist depth panel: ' + json.dumps(panel, allow_nan=False)
              + '\nfrozen_public_depth_query_context: ' + json.dumps(frame.context(), allow_nan=False))
    action_schema = SCHEMA
    if args.named_actions:
        from participant.collection import named_actions
        prompt = prompt.replace('an all-zero 2x9 action', 'an all-zero named action object')
        prompt += '\n' + named_actions.TASK
        action_schema = named_actions.response_schema(SCHEMA)
    first_schema = dq.response_schema(action_schema)
    usage = TokenUsageAccounting()
    report = {'schema': 'phyrc-synthetic-depth-query-probe-v1',
              'model': 'gpt-6-astra', 'effort': 'ultra', 'model_timeout_s': args.model_timeout,
              'max_model_calls': 2, 'model_calls_attempted': 0, 'calls_completed': 0,
              'physics_transitions': 0, 'simulator_created': False, 'gpu_calls': 0,
              'synthetic_only': True, 'dressing_or_semantic_selection_validated': False,
              'image_count': len(images), 'image_sha256': image_hashes,
              'frozen_observation_id': frame.observation_id, 'calls': [],
              'passed': False, 'cleanup_ok': False}
    if args.named_actions:
        report['named_actions'] = named_actions.public_mapping(named_actions.MAPPING)
    actor = None
    started = time.monotonic()
    try:
        actor = Actor(root / 'private-actor', model='gpt-6-astra', effort='ultra',
                      timeout_s=args.model_timeout)
        report['cli_version'] = actor.cli_version
        first_session = None
        for call_index in range(2):
            schema = first_schema if call_index == 0 else action_schema
            report['model_calls_attempted'] += 1
            dump(root / 'summary.json', report)
            result = actor.invoke(prompt, images, schema)
            if args.named_actions:
                result = named_actions.normalize_result(result)
            record = usage.record(call_index, result)
            report['calls_completed'] += 1
            report['calls'].append({'model_call_index': call_index,
                'schema_sha256': dq.sha(schema), 'prompt_sha256': result['prompt_sha256'],
                'wall_s': result['wall_s'], 'usage_accounting': record,
                'image_count': len(images), 'decision': result['decision']})
            if args.named_actions:
                report['calls'][-1]['named_action'] = named_actions.public_provenance(
                    result['named_action'], result['decision']['action'])
                report['calls'][-1]['frozen_observation_id'] = frame.observation_id
                report['calls'][-1]['observation_simulation_time_s'] = frame.timestamp_s
            if call_index == 0:
                first_session = result['session_id']
                ordinary, request = dq.route_initial(result['decision'], SCHEMA, validate_decision)
                if ordinary is not None or request is None:
                    raise ValueError('expected fixture query')
                if (request['camera'] != 'robot_0_wrist' or request['pixels_uv'] != [[128,128],[0,0]]
                        or request['include_camera_geometry'] is not True):
                    raise ValueError('unexpected fixture points')
                response = dq.lookup(frame, request)
                if (response['results'][0]['optical_z_m'] != .75
                        or response['results'][1]['optical_z_m'] is not None):
                    raise ValueError('incorrect exact fixture lookup')
                report['query_result'] = response
                prompt = ('Same synthetic frozen observation and same 16 images; no physics has run. '
                          'The query budget is exhausted. Return the ORIGINAL action schema without '
                          'a depth_query field: tool=finish_episode, all-zero 2x9 action, steps=1, '
                          'stage=preparation, visual_assessment=uncertain, brief fixture reason. '
                          'Use no tools. This response is validated only and will not be dispatched.\n'
                          'depth_query_result: ' + json.dumps(response, allow_nan=False))
                if args.named_actions:
                    prompt = ('Same synthetic frozen observation and same 16 images; no physics has run. '
                              'The query budget is exhausted. Return the named action-only schema without '
                              'a depth_query field: tool=act, steps=2, stage=preparation, '
                              'visual_assessment=uncertain. Set robot_1 base_forward=0.35 and gripper=1; '
                              'every other named channel of both robots must be zero, including wrist_roll. '
                              'Use a brief fixture reason and no tools. This response is validated only '
                              'and will not be dispatched.\n' + named_actions.TASK + '\n'
                              'depth_query_result: ' + json.dumps(response, allow_nan=False))
            else:
                action = validate_decision(result['decision'])
                if args.named_actions:
                    expected = np.zeros((2, 9), np.float32)
                    expected[1, 0], expected[1, 8] = .35, 1
                    if (result['decision']['tool'] != 'act' or result['decision']['steps'] != 2
                            or not np.array_equal(action, expected)):
                        raise ValueError('expected named advance/close without roll')
                    report['validated_float32_action'] = action.tolist()
                    staged = [[hashlib.sha256((actor.public / f'{turn:06d}' /
                               f'camera-{i:02d}.png').read_bytes()).hexdigest()
                               for i in range(len(images))] for turn in range(2)]
                    report['staged_image_sha256'] = staged
                    report['same_staged_image_bytes'] = staged[0] == staged[1]
                    if not report['same_staged_image_bytes']:
                        raise ValueError('staged image mismatch')
                elif result['decision']['tool'] != 'finish_episode':
                    raise ValueError('expected fixture finish')
                report['same_session_resumed'] = result['session_id'] == first_session
                if not report['same_session_resumed']:
                    raise ValueError('session mismatch')
            if image_hashes != [hashlib.sha256(p.read_bytes()).hexdigest() for p in images]:
                raise ValueError('fixture images changed')
            dump(root / 'summary.json', report)
        report['passed'] = True
    except BaseException as error:
        # Never publish private CLI logs, session identifiers or error messages.
        report['error_type'] = type(error).__name__
        raise
    finally:
        try:
            if actor is not None:
                actor.close()
            report['cleanup_ok'] = True
        finally:
            report['wall_s'] = time.monotonic() - started
            report['usage_accounting'] = usage.summary()
            dump(root / 'summary.json', report)
            print(json.dumps({k: report[k] for k in ('passed', 'calls_completed', 'physics_transitions',
                                                   'image_count', 'cleanup_ok', 'wall_s')}))


if __name__ == '__main__':
    main()
