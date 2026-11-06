"""Four fresh isolated CLI turns, ABBA encoding only; never runs a simulator.

Default is a plan-only print. --execute creates new private runtime storage.
The unchanged Actor requires an image, so all turns use the same blank fixture.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import time
import traceback

import numpy as np
from PIL import Image

from participant.collection.boundary import validate_action
from participant.collection.codex_actor import Actor
from participant.research.action_encoding import (
    CHANNELS, ROBOT_IDS, array_to_named, named_to_array)


ORDER = ('array', 'named', 'named', 'array')
MODEL, EFFORT, TIMEOUT_S = 'gpt-6-astra', 'ultra', 90
EXPECTED = np.array([[-.65, 0, 0, 0, 0, 0, 0, 0, 1]] * 2, np.float32)
BASE_PROMPT = """This is an encoding-only connection test, not robot task planning.
Encode this explicit command for BOTH robot_0 and robot_1:
base_forward = -0.65; base_left = 0; base_CCW_yaw = 0; lift = 0;
arm_extension = 0; wrist_yaw = 0; wrist_pitch = 0; wrist_roll = 0; gripper = 1.
These are normalized command values, not physical angles or velocities.
Do not infer, improve, execute, or correct the command. Use no tools.
The attached constant gray image is an information-free transport fixture.
It contains no scene or task evidence and must be ignored.
Return only the JSON object required by the response schema.
"""


def schema_for(encoding):
    number = {'type': 'number', 'minimum': -1, 'maximum': 1}
    if encoding == 'array':
        return {'type': 'object', 'properties': {'action': {
            'type': 'array', 'minItems': 2, 'maxItems': 2, 'items': {
                'type': 'array', 'minItems': 9, 'maxItems': 9, 'items': number}}},
            'required': ['action'], 'additionalProperties': False}
    if encoding != 'named':
        raise ValueError('Unknown encoding')
    channels = {'type': 'object', 'properties': {name: dict(number) for name in CHANNELS},
                'required': list(CHANNELS), 'additionalProperties': False}
    return {'type': 'object', 'properties': {'robots': {
        'type': 'array', 'minItems': 2, 'maxItems': 2, 'items': {
            'type': 'object', 'properties': {
                'robot_id': {'type': 'string', 'enum': list(ROBOT_IDS)}, 'action': channels},
            'required': ['robot_id', 'action'], 'additionalProperties': False}}},
        'required': ['robots'], 'additionalProperties': False}


def prompt_for(encoding):
    if encoding == 'array':
        return BASE_PROMPT + ('Use {"action": [[nine numbers for robot_0], '
            '[nine numbers for robot_1]]}. The nine columns, in order, are: '
            + ', '.join(CHANNELS) + '.\n')
    if encoding == 'named':
        return BASE_PROMPT + ('Use {"robots": [{"robot_id": "robot_0", "action": '
            '{all nine named channels}}, {"robot_id": "robot_1", "action": '
            '{all nine named channels}}]}. Preserve this robot list order.\n')
    raise ValueError('Unknown encoding')


def validate_response(encoding, response):
    if encoding == 'array':
        if type(response) is not dict or set(response) != {'action'}:
            raise ValueError('Array response keys differ from schema')
        array_to_named(response['action'])  # strict numeric checks before coercion
        action = validate_action(response['action'], 1)
    elif encoding == 'named':
        action = validate_action(named_to_array(response), 1)
    else:
        raise ValueError('Unknown encoding')
    return action, bool(np.array_equal(action, EXPECTED))


def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _write(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def event_counts(path):
    """Count event types without exporting raw reasoning, messages or thread IDs."""
    if not path.is_file():
        return {'available': False, 'sha256': None}
    counts = {'available': True, 'thread_started': 0, 'turn_completed': 0,
              'tool_or_unsupported_items': 0, 'malformed_lines': 0, 'sha256': _sha(path)}
    with path.open() as stream:
        for line in stream:
            try:
                event = json.loads(line)
                if not isinstance(event, dict): raise ValueError('non-object event')
            except (ValueError, json.JSONDecodeError):
                counts['malformed_lines'] += 1
                continue
            kind = event.get('type')
            if kind == 'thread.started': counts['thread_started'] += 1
            if kind == 'turn.completed': counts['turn_completed'] += 1
            if kind in ('item.started', 'item.updated', 'item.completed'):
                if event.get('item', {}).get('type') not in ('agent_message', 'reasoning', 'error'):
                    counts['tool_or_unsupported_items'] += 1
    return counts


def plan():
    return {'order': list(ORDER), 'model': MODEL, 'effort': EFFORT, 'timeout_s': TIMEOUT_S,
            'fresh_actor_per_call': True, 'maximum_invoke_attempts': 4,
            'blank_image_required_by_unchanged_actor': True,
            'simulation_action_dispatch': False, 'gpu_execution': False,
            'same_target': EXPECTED.tolist(), 'response_schemas': {
                name: schema_for(name) for name in ('array', 'named')}}


def run_probe(output, *, actor_factory=Actor):
    output = Path(output)
    if output.exists():
        raise ValueError('New output directory required; never overwrite a probe')
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    _write(output/'plan.json', plan())
    image = output/'constant-gray.png'
    Image.new('RGB', (16, 16), (128, 128, 128)).save(image)
    summary = {'schema': 'phyrc-action-encoding-cli-probe-v1', 'started_at_utc': _now(),
        'model': MODEL, 'effort': EFFORT, 'timeout_s': TIMEOUT_S, 'order': list(ORDER),
        'image': {'role': 'information_free_transport_fixture_not_observation',
                  'size_wh': [16, 16], 'rgb': [128, 128, 128], 'sha256': _sha(image)},
        'concurrent_E07_workload': 'May overlap; model-service load is not isolated or measured',
        'usage_scope': 'One completed turn per fresh thread; no cross-thread cumulative subtraction',
        'simulation_executed': False, 'actions_dispatched': 0, 'gpu_requested': False,
        'interpretation': 'Encoding-only CLI connection check, not robot demonstrations or a performance comparison',
        'calls': []}
    root = Path(__file__).resolve().parents[1]
    snapshot = output/'source_snapshot'; snapshot.mkdir()
    summary['source_sha256'] = {}
    for relative in ('scripts/probe_action_encoding.py', 'participant/collection/codex_actor.py',
                     'participant/collection/boundary.py', 'participant/research/action_encoding.py',
                     'config/policy_interface.json'):
        source = root/relative; destination = snapshot/relative
        destination.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(source, destination)
        summary['source_sha256'][relative] = _sha(destination)
    private_sessions = []
    interrupted = False
    for index, encoding in enumerate(ORDER):
        folder = output/f'call-{index:02d}-{encoding}'; folder.mkdir(mode=0o700)
        prompt, schema = prompt_for(encoding), schema_for(encoding)
        (folder/'prompt.txt').write_text(prompt)
        _write(folder/'schema.json', schema)
        record = {'index': index, 'encoding': encoding, 'started_at_utc': _now(),
                  'prompt_sha256': _sha(folder/'prompt.txt'), 'schema_sha256': _sha(folder/'schema.json'),
                  'image_sha256': _sha(image), 'invoke_attempted': False, 'response_valid': False,
                  'exact_expected_action': False, 'error_code': None, 'cleanup_ok': False}
        actor = None; started = time.perf_counter(); setup_started = started
        try:
            actor = actor_factory(folder/'actor', model=MODEL, effort=EFFORT, timeout_s=TIMEOUT_S)
            record['setup_wall_s'] = time.perf_counter()-setup_started
            if actor.session_id is not None or actor.calls != 0:
                raise ValueError('Actor did not start fresh')
            record['invoke_attempted'] = True
            returned = actor.invoke(prompt, [image], schema)
            _write(folder/'private-returned.json', returned)
            private_sessions.append(returned['session_id'])
            record['actor_wall_s'] = returned['wall_s']
            record['phase_wall_s'] = returned.get('phase_wall_s', {})
            record['cli_version'] = returned.get('cli_version')
            record['usage'] = {key: value for key, value in returned.get('usage', {}).items()
                               if key in ('input_tokens', 'cached_input_tokens', 'output_tokens',
                                          'total_tokens', 'reasoning_output_tokens')}
            action, matched = validate_response(encoding, returned['decision'])
            record['response_valid'] = True
            record['response'] = returned['decision']
            record['normalized_action_float32'] = action.tolist()
            record['exact_expected_action'] = matched
            if not matched: record['error_code'] = 'valid_encoding_wrong_target'
        except BaseException as error:
            (folder/'private-error.txt').write_text(traceback.format_exc())
            record['error_code'] = type(error).__name__
            record['actor_wall_s'] = time.perf_counter()-started-record.get('setup_wall_s', 0)
            if actor is not None: record['phase_wall_s'] = getattr(actor, 'last_call_timing', {})
            if isinstance(error, (KeyboardInterrupt, SystemExit)): interrupted = True
        finally:
            cleanup_started = time.perf_counter()
            if actor is not None:
                try:
                    actor.close()
                    record['cleanup_ok'] = bool(actor._closed and not actor._network_created
                        and not actor._proxy_created and actor._active_container is None
                        and not (actor.codex_home/'auth.json').exists())
                except Exception:
                    (folder/'private-cleanup-error.txt').write_text(traceback.format_exc())
                    record['cleanup_ok'] = False
            record['cleanup_wall_s'] = time.perf_counter()-cleanup_started
            record['slot_wall_s'] = time.perf_counter()-started
            record['finished_at_utc'] = _now()
            record['events'] = event_counts(folder/'actor/actor_events/000000.jsonl')
            response = folder/'actor/codex_home/decision-000000.json'
            record['response_file_sha256'] = _sha(response) if response.is_file() else None
            record['private_error_present'] = (folder/'private-error.txt').exists()
            _write(folder/'public-record.json', record)
            summary['calls'].append(record)
            temp = output/'summary.tmp'
            temp.write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
            temp.replace(output/'summary.json')
            print(json.dumps({'call': index, 'encoding': encoding,
                'response_valid': record['response_valid'], 'exact_expected_action': record['exact_expected_action'],
                'actor_wall_s': record.get('actor_wall_s'), 'cleanup_ok': record['cleanup_ok'],
                'error_code': record['error_code']}), flush=True)
        if interrupted or not record['cleanup_ok']:
            break  # no additional model attempt while cleanup is uncertain
    summary.update(finished_at_utc=_now(), invoke_attempts=sum(r['invoke_attempted'] for r in summary['calls']),
        accepted_responses=sum(r['response_valid'] for r in summary['calls']),
        exact_matches=sum(r['exact_expected_action'] for r in summary['calls']),
        completed_thread_count=len(private_sessions),
        distinct_completed_threads=(len(private_sessions) == len(set(private_sessions))) if private_sessions else None,
        all_four_slots_recorded=len(summary['calls']) == 4,
        cleanup_all_ok=all(r['cleanup_ok'] for r in summary['calls']))
    _write(output/'final-summary.json', summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(plan(), ensure_ascii=False, indent=2)); return
    if args.output is None: parser.error('--execute requires a new --output directory')
    def interrupted(_signum, _frame):
        raise KeyboardInterrupt('Probe interrupted')
    signal.signal(signal.SIGTERM, interrupted)
    result = run_probe(args.output)
    raise SystemExit(0 if result['exact_matches'] == 4 and result['cleanup_all_ok'] else 1)


if __name__ == '__main__':
    main()
