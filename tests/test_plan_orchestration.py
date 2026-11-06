"""CPU main-loop checks for grouped plans and the trusted review boundary.

Only process/model/sensor boundaries are faked. The real client validates plans,
accounts usage, reads the separate score stream, and writes its attempt/events.
"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

import numpy as np

from participant.collection import codex_actor, codex_app_actor, codex_client


def three_segment_plan():
    def decision(tool, steps):
        return {
            'tool': tool, 'action': [[0.0] * 9 for _ in range(2)],
            'steps': steps, 'stage': 'preparation',
            'visual_assessment': 'uncertain', 'reason': 'Synthetic CPU wiring.',
        }
    move = decision('act', 2)
    for row in move['action']:
        row[3], row[8] = 0.03, -1.0
    return {'decisions': [move, decision('stop', 1), decision('finish_episode', 1)]}


class PlanOrchestrationTest(unittest.TestCase):
    def run_client(self, plan, *, backend='exec', mode='wiring', points_after_act=0,
                   expected_error=None, end_on_act=False, review_points=5, replay=False):
        calls, requests, observation_times, lifecycle = [], [], [], []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = root / 'synthetic-camera.png'
            image.write_bytes(b'synthetic-public-image')
            run_id = 'cpu-plan-test'
            collection = root / 'output/collections' / run_id
            scores = collection / 'evaluation/synthetic-episode/score_samples.jsonl'

            class FakeSimulator:
                def __init__(self, *args, **kwargs):
                    self.process = mock.Mock(pid=123)
                    self.process.poll.return_value = None
                    self.step = 0
                    scores.parent.mkdir(parents=True)
                    self.write_score(0)

                def write_score(self, points):
                    with scores.open('a') as stream:
                        stream.write(json.dumps({
                            'raw_points': points,
                            'private_marker': 'TRUSTED_SCORE_STREAM_ONLY',
                        }) + '\n')
                    with scores.with_name('score_events.jsonl').open('a') as stream:
                        stream.write(json.dumps({
                            'event': 'score_awarded' if points else 'evaluation_started',
                            'physics_tick': self.step * 12, 'evaluation_time_s': self.step / 20,
                            'raw_points': points, 'breakdown': {'pickup': points},
                        }) + '\n')

                def observation(self):
                    return {'simulation_time_s': self.step / 20}

                def finish_capture(self):
                    (collection / 'capture.json').write_text(json.dumps({
                        'complete': True, 'steps': self.step,
                        'termination_reason': 'step_budget' if end_on_act else 'operator_finished',
                    }))

                def receive(self):
                    return {
                        'ready': True, 'observation': self.observation(),
                        'public_interface': {
                            'action_scales': {'LIFT_RATE': 0.2},
                            'evaluation': 'FORBIDDEN_INTERFACE_EVALUATION',
                        },
                    }

                def dispatch(self, tool, arguments=None):
                    requests.append((tool, deepcopy(arguments)))
                    if tool == 'act':
                        self.step += arguments['steps']
                        self.write_score(points_after_act)
                        if end_on_act:
                            self.finish_capture()
                            return {'active': False, 'observation': self.observation()}
                    elif tool == 'stop':
                        self.step += 1
                    elif tool == 'finish_episode':
                        self.finish_capture()
                        return {'active': False}
                    else:
                        raise AssertionError('Unexpected simulator request: ' + tool)
                    return {'active': True, 'observation': self.observation()}

                def close(self):
                    lifecycle.append('simulator_closed')
                    return 0

            class FakeActor:
                last_call_timing = {'process_wall_s': 0.25, 'completed': True}

                def __init__(self, *args, **kwargs):
                    lifecycle.append('actor_created')

                def invoke(self, prompt, images, schema):
                    calls.append({'prompt': prompt, 'images': list(images),
                                  'schema': deepcopy(schema)})
                    if len(calls) > 1:
                        raise AssertionError('An already supplied plan caused another model call')
                    return {
                        'decision': deepcopy(plan), 'session_id': 'synthetic-thread',
                        'wall_s': 0.25, 'phase_wall_s': dict(self.last_call_timing),
                        'usage': {'input_tokens': 100, 'cached_input_tokens': 20,
                                  'cache_write_input_tokens': 0, 'output_tokens': 10,
                                  'reasoning_output_tokens': 2},
                    }

                def close(self):
                    lifecycle.append('actor_closed')

            def prepare_public_observation(obs, directory):
                observation_times.append(obs['simulation_time_s'])
                directory.mkdir(parents=True)
                payload = {'public_robot_observation': deepcopy(obs)}
                (directory / 'observation.json').write_text(json.dumps(payload))
                return payload, [image]

            selected_module = codex_app_actor if backend == 'app-server' else codex_actor
            selected_class = 'AppActor' if backend == 'app-server' else 'Actor'
            other_module = codex_actor if backend == 'app-server' else codex_app_actor
            other_class = 'Actor' if backend == 'app-server' else 'AppActor'
            argv = ['codex_client', '--run-id', run_id, '--mode', mode,
                    '--actor-backend', backend, '--plan-size', '3',
                    '--plan-step-budget', '3', '--decisions', '3',
                    '--review-points', str(review_points)]
            prefix = SimpleNamespace(
                actions=np.zeros((2, 2, 9), dtype=np.float32),
                trusted_metadata={'reset_seed': 892321},
                public_lineage={'source_group': 'synthetic-family', 'resume_kind': 'action_replay',
                                'replay_steps': 2, 'bitwise_physics_restored': False},
                initial_public_state={'simulation_time_s': np.asarray(0.)},
                final_public_state={'simulation_time_s': np.asarray(.1)},
            )
            if replay:
                argv += ['--replay-prefix-run', 'synthetic-parent']
            with mock.patch.object(codex_client, '__file__',
                                   str(root / 'participant/collection/client.py')), \
                 mock.patch.object(codex_client, 'Simulator', FakeSimulator), \
                 mock.patch.object(selected_module, selected_class, FakeActor), \
                 mock.patch.object(other_module, other_class,
                                   side_effect=AssertionError('Wrong actor backend selected')), \
                 mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                 mock.patch.object(codex_client, 'prepare_observation',
                                   side_effect=prepare_public_observation), \
                 mock.patch('participant.collection.continuation.load_replay_prefix',
                            return_value=prefix), \
                 mock.patch.object(codex_client.signal, 'signal'), \
                 mock.patch.object(sys, 'argv', argv), mock.patch('builtins.print'):
                if expected_error is None:
                    codex_client.main()
                else:
                    with self.assertRaises(expected_error):
                        codex_client.main()
            trace = root / 'output/operator-traces' / run_id
            result = {
                'manifest': json.loads((trace / 'attempt.json').read_text()),
                'events': [json.loads(line) for line in
                           (trace / 'decisions.jsonl').read_text().splitlines()],
                'gate': json.loads((trace / 'review_gate.json').read_text()),
                'calls': calls, 'requests': requests,
                'observation_times': observation_times, 'lifecycle': lifecycle,
            }
            # Keep only detached records; no later assertion relies on temp files.
            for call in calls:
                call['images'] = [path.name for path in call['images']]
            return result

    def assert_one_accounted_call(self, result):
        manifest = result['manifest']
        self.assertEqual(len(result['calls']), 1)
        self.assertEqual(manifest['actor_calls_attempted'], 1)
        self.assertEqual(manifest['actor_usage_accounting']['calls_recorded'], 1)
        self.assertTrue(manifest['actor_usage_accounting']['fully_known'])
        self.assertEqual(manifest['actor_usage']['input_tokens'], 100)
        self.assertEqual(manifest['actor_usage']['output_tokens'], 10)
        self.assertEqual(result['lifecycle'],
                         ['actor_created', 'simulator_closed', 'actor_closed'])

    def test_one_call_executes_three_segments_with_original_and_latest_clocks(self):
        for backend in ('exec', 'app-server'):
            with self.subTest(backend=backend):
                result = self.run_client(three_segment_plan(), backend=backend)
                self.assert_one_accounted_call(result)
                manifest = result['manifest']
                self.assertEqual(manifest['actor_backend'], backend)
                self.assertEqual(manifest['status'], 'completed')
                self.assertEqual(manifest['decisions_completed'], 3)
                self.assertEqual(manifest['actor_call_wall_s'], 0.25)
                self.assertEqual(manifest['simulation_steps'], 3)
                self.assertEqual(manifest['recorded_simulation_steps'], 3)
                self.assertEqual(manifest['simulation_time_s'], 0.15)
                self.assertTrue(manifest['finished'])
                self.assertEqual([r[0] for r in result['requests']],
                                 ['act', 'stop', 'finish_episode'])
                self.assertEqual(result['observation_times'], [0, 0.1, 0.15])

                events = result['events']
                decisions = [e for e in events if e['type'] == 'decision']
                applied = [e for e in events if e['type'] == 'applied_segment']
                self.assertEqual(len(decisions), 3)
                self.assertEqual(len(applied), 3)
                for records in (decisions, applied):
                    self.assertEqual([e['model_call_index'] for e in records], [0, 0, 0])
                    self.assertEqual([e['plan_segment_index'] for e in records], [0, 1, 2])
                    self.assertEqual([e['model_invoked'] for e in records], [True, False, False])
                    self.assertEqual([e['observation_simulation_time_s'] for e in records],
                                     [0, 0, 0])
                    self.assertEqual([e['latest_observation_simulation_time_s'] for e in records],
                                     [0, 0.1, 0.15])
                self.assertEqual([e['actual_steps'] for e in applied], [2, 1, 0])
                self.assertEqual([e['simulation_start_s'] for e in applied], [0, 0.1, 0.15])
                self.assertEqual([e['simulation_end_s'] for e in applied], [0.1, 0.15, 0.15])
                self.assertEqual([e['usage_scope'] for e in decisions],
                                 ['thread_cumulative', 'not_invoked', 'not_invoked'])
                self.assertEqual([e['usage'] for e in decisions[1:]], [{}, {}])
                self.assertEqual([e['usage_accounting'] for e in decisions[1:]], [None, None])
                self.assertEqual(len({e['input_sha256'] for e in decisions}), 1)
                self.assertEqual(len({e['latest_input_sha256'] for e in decisions}), 3)
                model_payload = json.loads(result['calls'][0]['prompt'].splitlines()[-1])
                self.assertEqual(model_payload['public_robot_observation']['simulation_time_s'], 0)
                self.assertFalse(any(e['type'] in ('supervisor_stop', 'plan_suffix_discarded')
                                     for e in events))
                self.assertEqual(result['gate']['status'], 'disabled_wiring')

    def test_invalid_suffix_rejects_valid_prefix_and_only_cleanup_runs(self):
        plan = three_segment_plan()
        plan['decisions'][1]['action'][0][0] = 1.01
        result = self.run_client(plan, expected_error=ValueError)
        self.assert_one_accounted_call(result)
        self.assertEqual(result['manifest']['status'], 'failed')
        self.assertEqual(result['manifest']['decisions_completed'], 0)
        self.assertEqual(result['manifest']['simulation_steps'], 1)
        self.assertTrue(result['manifest']['finished'])
        self.assertEqual([r[0] for r in result['requests']], ['stop', 'finish_episode'])
        self.assertFalse(any(e['type'] in ('decision', 'applied_segment') for e in result['events']))
        errors = [e for e in result['events'] if e['type'] == 'model_error']
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0]['usage_accounting']['call_failed'])
        cleanup = [e for e in result['events'] if e['type'] == 'supervisor_stop']
        self.assertEqual(len(cleanup), 1)
        self.assertEqual(cleanup[0]['neutral_steps'], 1)
        self.assertEqual(cleanup[0]['reason'], 'failed')

    def test_five_point_gate_discards_suffix_without_another_actor_call(self):
        result = self.run_client(three_segment_plan(), mode='pickup', points_after_act=5)
        self.assert_one_accounted_call(result)
        self.assertEqual(result['manifest']['status'], 'review_ready')
        self.assertEqual(result['manifest']['decisions_completed'], 1)
        self.assertEqual(result['manifest']['simulation_steps'], 3)
        self.assertTrue(result['manifest']['finished'])
        self.assertEqual(result['observation_times'], [0])
        self.assertEqual([r[0] for r in result['requests']], ['act', 'stop', 'finish_episode'])
        applied = [e for e in result['events'] if e['type'] == 'applied_segment']
        self.assertEqual(len(applied), 1)
        self.assertEqual(applied[0]['actual_steps'], 2)
        self.assertIsNone(applied[0]['official_score'])
        discarded = [e for e in result['events'] if e['type'] == 'plan_suffix_discarded']
        self.assertEqual(len(discarded), 1)
        self.assertEqual(discarded[0]['reason'], 'review_points')
        self.assertEqual([e['plan_segment_index'] for e in discarded[0]['segments']], [1, 2])
        cleanup = [e for e in result['events'] if e['type'] == 'supervisor_stop']
        self.assertEqual(len(cleanup), 1)
        self.assertEqual(cleanup[0]['reason'], 'review_points')
        self.assertEqual(result['gate']['status'], 'triggered')
        self.assertEqual(result['gate']['last_observed_raw_points'], 5)
        self.assertEqual(result['gate']['acknowledged_steps'], 2)
        self.assertFalse(result['gate']['policy_input_changed'])
        actor_input = json.dumps(result['calls'])
        for forbidden in ('TRUSTED_SCORE_STREAM_ONLY', 'FORBIDDEN_INTERFACE_EVALUATION',
                          'raw_points', 'score_samples.jsonl', 'last_observed_raw_points'):
            self.assertNotIn(forbidden, actor_input)

    def test_terminal_action_ack_still_records_five_point_review(self):
        result = self.run_client(three_segment_plan(), mode='pickup',
                                 points_after_act=5, end_on_act=True)
        self.assert_one_accounted_call(result)
        self.assertEqual(result['manifest']['status'], 'review_ready')
        self.assertTrue(result['manifest']['finished'])
        self.assertEqual(result['manifest']['simulation_steps'], 2)
        self.assertEqual(result['manifest']['decisions_completed'], 1)
        self.assertEqual([r[0] for r in result['requests']], ['act'])
        self.assertEqual(result['gate']['status'], 'triggered')
        self.assertEqual(result['gate']['last_observed_raw_points'], 5)
        self.assertFalse(any(e['type'] == 'supervisor_stop' for e in result['events']))
        discarded = [e for e in result['events'] if e['type'] == 'plan_suffix_discarded']
        self.assertEqual(len(discarded), 1)

        self.assertEqual([e['plan_segment_index'] for e in discarded[0]['segments']], [1, 2])

    def test_fifty_point_threshold_continues_past_five_without_actor_feedback(self):
        result = self.run_client(three_segment_plan(), mode='dressing',
                                 points_after_act=5, review_points=50)
        self.assert_one_accounted_call(result)
        self.assertEqual(result['manifest']['review_threshold_raw_points'], 50)
        self.assertEqual(result['manifest']['status'], 'completed')
        self.assertEqual(result['manifest']['decisions_completed'], 3)
        self.assertEqual(result['gate']['threshold_raw_points'], 50)
        self.assertEqual(result['gate']['status'], 'collector_ended_before_gate')
        self.assertEqual([r[0] for r in result['requests']], ['act', 'stop', 'finish_episode'])
        for forbidden in ('TRUSTED_SCORE_STREAM_ONLY', 'raw_points', 'score_segments'):
            self.assertNotIn(forbidden, json.dumps(result['calls']))

    def test_replay_records_parent_steps_then_starts_fresh_actor_with_new_observation(self):
        result = self.run_client(three_segment_plan(), mode='dressing', replay=True,
                                 points_after_act=5, review_points=50)
        self.assert_one_accounted_call(result)
        manifest = result['manifest']
        self.assertEqual(manifest['simulation_steps'], 5)
        self.assertEqual(manifest['replay_steps_completed'], 2)
        self.assertEqual(manifest['policy_suffix_start_step'], 2)
        self.assertEqual(manifest['new_recorded_suffix_steps'], 3)
        self.assertEqual(manifest['source_group'], 'synthetic-family')
        self.assertEqual(result['observation_times'], [.1, .2, .25])
        replayed = [e for e in result['events'] if e['type'] == 'replayed_segment']
        self.assertEqual(len(replayed), 1)
        self.assertFalse(replayed[0]['model_invoked'])
        self.assertEqual(replayed[0]['actual_steps'], 2)
        applied = [e for e in result['events'] if e['type'] == 'applied_segment']
        self.assertEqual(applied[0]['start_step'], 2)
        self.assertEqual(applied[0]['action_source'], 'model')
        self.assertNotIn('892321', json.dumps(result))
        self.assertNotIn('reset_seed', json.dumps(result))
        self.assertNotIn('TRUSTED_SCORE_STREAM_ONLY', json.dumps(result['calls']))

    def test_replay_score_gate_stops_without_creating_an_actor(self):
        result = self.run_client(three_segment_plan(), mode='pickup', replay=True,
                                 points_after_act=5, review_points=5)
        self.assertEqual(result['calls'], [])
        self.assertEqual(result['lifecycle'], ['simulator_closed'])
        self.assertEqual(result['manifest']['status'], 'review_ready')
        self.assertEqual(result['manifest']['actor_calls_attempted'], 0)
        self.assertEqual(result['manifest']['replay_steps_completed'], 2)
        self.assertEqual([r[0] for r in result['requests']], ['act', 'stop', 'finish_episode'])


if __name__ == '__main__':
    unittest.main()
