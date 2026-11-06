#!/usr/bin/env python3
"""Model-free real-collector wiring: one query, two lift steps, one stop, finish.

Running this driver starts the simulator/GPU through the normal collector.
It never instantiates the real Actor or calls a model. The deterministic fixture
reads only the supplied public prompt and query result, not simulator internals.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
import time
from unittest import mock

import numpy as np

from participant.collection import codex_actor, codex_client
from participant.collection import depth_query as dq


MODEL_ID = 'synthetic-depth-query-wiring-fixture'


def public_clock(prompt):
    for line in prompt.splitlines():
        if line.startswith('{"public_robot_observation":'):
            value = json.loads(line)['public_robot_observation']['simulation_time_s']
            if type(value) not in (int, float) or not np.isfinite(value):
                raise ValueError('invalid public fixture clock')
            return float(value)
    raise ValueError('missing public fixture clock')


def prefixed_json(prompt, prefix):
    values = [json.loads(line[len(prefix):]) for line in prompt.splitlines() if line.startswith(prefix)]
    if len(values) != 1:
        raise ValueError('expected one public query payload')
    return values[0]


class WiringFixtureActor:
    """Four deterministic responses; only public prompt data enters decisions."""
    def __init__(self, *_, model, effort, timeout_s):
        if model != MODEL_ID or effort != 'none' or timeout_s != 180:
            raise ValueError('unexpected fixture configuration')
        self.calls = []
        self.query_id = None
        self.query_clock = None
        self.closed = False

    def invoke(self, prompt, images, schema):
        if self.closed or len(self.calls) >= 4:
            raise ValueError('fixture invocation budget exhausted')
        started = time.monotonic()
        index = len(self.calls)
        clock = public_clock(prompt)
        expected_schema = codex_client.SCHEMA if index == 1 else dq.response_schema(codex_client.SCHEMA)
        if schema != expected_schema:
            raise ValueError('unexpected fixture response schema')
        value = {'tool': 'finish_episode', 'action': [[0.] * 9 for _ in range(2)],
                 'steps': 1, 'stage': 'preparation', 'visual_assessment': 'uncertain',
                 'reason': 'Deterministic public-input recorder wiring; no model or dressing attempt.'}
        if index != 1:
            value['depth_query'] = None
        if index == 0:
            context = prefixed_json(prompt, 'frozen_public_depth_query_context: ')
            if context['simulation_time_s'] != clock:
                raise ValueError('query context clock mismatch')
            self.query_id, self.query_clock = context['frozen_observation_id'], clock
            value.update(tool='depth_query', depth_query={
                'kind': 'depth_query', 'observation_id': self.query_id,
                'camera': 'robot_0_wrist', 'pixels_uv': [[128,128],[0,0]],
                'include_camera_geometry': True})
        elif index == 1:
            result = prefixed_json(prompt, 'depth_query_result: ')
            if (clock != self.query_clock or result['simulation_time_s'] != clock
                    or result['observation_id'] != self.query_id
                    or result['camera'] != 'robot_0_wrist'
                    or [point['pixel_uv'] for point in result['results']] != [[128,128],[0,0]]):
                raise ValueError('query follow-up is not the same public observation')
            for point in result['results']:
                z = point['optical_z_m']
                if z is not None and (type(z) not in (int,float) or not np.isfinite(z) or z <= 0):
                    raise ValueError('invalid public depth response')
            value.update(tool='act', steps=2)
            for row in value['action']:
                row[3], row[8] = .03, -1.
        elif index == 2:
            value['tool'] = 'stop'
        self.calls.append({'call_index': index, 'public_clock_s': clock,
                           'tool': value['tool'], 'image_count': len(images)})
        # These are fixture invocation counters with known zero model usage.
        return {'decision': value, 'session_id': 'synthetic-fixture-session',
                'wall_s': time.monotonic() - started,
                'model': MODEL_ID, 'effort': 'none', 'cli_version': 'not_invoked',
                'usage': dict.fromkeys(codex_client.USAGE_FIELDS, 0)}

    def close(self):
        self.closed = True


def run_probe(run_id, report_path=None):
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,119}', run_id):
        raise ValueError('run-id must be a safe unique name')
    root = Path(codex_client.__file__).resolve().parents[2]
    report_path = Path(report_path) if report_path else root / 'output/sessions' / (run_id + '-probe.json')
    if report_path.exists():
        raise ValueError('probe report already exists')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {'schema': 'phyrc-model-free-depth-query-wiring-v1', 'run_id': run_id,
              'source': 'integration_test', 'source_group': 'integration-depth-query-wiring-' + run_id,
              'model_id': MODEL_ID, 'real_model_calls': 0, 'expected_physics_transitions': 3,
              'expected_query_physics_transitions': 0, 'passed': False,
              'gpu_execution': 'requested_real_collector',
              'driver_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'quality_status': 'pipeline_wiring_only_not_dressing_or_training_approval'}
    instances = []

    def factory(*args, **kwargs):
        fixture = WiringFixtureActor(*args, **kwargs)
        instances.append(fixture)
        return fixture

    argv = ['codex_client', '--run-id', run_id, '--mode', 'wiring', '--actor-backend', 'exec',
            '--source-group', report['source_group'], '--model', MODEL_ID, '--effort', 'none',
            '--pixel-depth-query', '--plan-size', '1', '--decisions', '3',
            '--max-steps', '4', '--model-timeout', '180']
    # Four is a hard episode guard, leaving room for explicit finish after the
    # intended three transitions. No query placeholder is sent as a fourth step.
    started = time.monotonic()
    try:
        with mock.patch.object(codex_actor, 'Actor', side_effect=factory), \
             mock.patch.object(sys, 'argv', argv):
            codex_client.main()
        if len(instances) != 1:
            raise ValueError('expected exactly one fixture actor')
        fixture = instances[0]
        trace = root / 'output/operator-traces' / run_id
        attempt = json.loads((trace / 'attempt.json').read_text())
        events = [json.loads(line) for line in (trace / 'decisions.jsonl').read_text().splitlines()]
        calls = [row for row in events if row['type'] == 'model_call']
        queries = [row for row in events if row['type'] == 'depth_query_result']
        segments = [row for row in events if row['type'] == 'applied_segment']
        expected_tools = ['depth_query','act','stop','finish_episode']
        if ([row['tool'] for row in fixture.calls] != expected_tools
                or len(calls) != 4 or len(queries) != 1 or queries[0]['executed'] is not False
                or calls[0]['observation_simulation_time_s'] != calls[1]['observation_simulation_time_s']
                or calls[0]['frozen_observation_id'] != calls[1]['frozen_observation_id']):
            raise ValueError('query/call sequence mismatch')
        call_positions = [i for i,e in enumerate(events) if e['type'] == 'model_call']
        if any(e['type'] in ('applied_segment','supervisor_stop','replayed_segment')
               for e in events[call_positions[0]+1:call_positions[1]]):
            raise ValueError('unexpected physical segment during query')
        if ([row['actual_steps'] for row in segments] != [2,1,0]
                or attempt['simulation_steps'] != 3 or attempt['acknowledged_simulation_steps'] != 3
                or attempt['recorded_simulation_steps'] != 3 or not attempt['capture_complete']
                or attempt['status'] != 'completed' or attempt['source'] != 'integration_test'
                or attempt['source_group'] != report['source_group']
                or attempt['actor_calls_attempted'] != 4 or not fixture.closed):
            raise ValueError('wiring transition/provenance check failed')
        report.update(passed=True, actual_physics_transitions=3, query_physics_transitions=0,
                      client_actor_invocations=4, fixture_calls=fixture.calls,
                      query_followup_same_clock=True, actor_cleanup_ok=fixture.closed,
                      attempt_sha256=hashlib.sha256((trace / 'attempt.json').read_bytes()).hexdigest(),
                      decisions_sha256=hashlib.sha256((trace / 'decisions.jsonl').read_bytes()).hexdigest())
    except BaseException as error:
        report['error_type'] = type(error).__name__
        raise
    finally:
        report['wall_s'] = time.monotonic() - started
        report['fixture_calls'] = [deepcopy(call) for actor in instances for call in actor.calls]
        codex_client.dump(report_path, report)
        print(json.dumps({k: report.get(k) for k in ('run_id','passed','real_model_calls',
                         'actual_physics_transitions','query_physics_transitions')}))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    run_probe(args.run_id, args.report)


if __name__ == '__main__':
    main()
