"""CPU orchestration checks for bounded, explicitly attributed neutral actions."""
from copy import deepcopy
import json
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np

from participant.collection import codex_actor, codex_client


def decision(tool='act', *, motion=.03, grip=1., steps=2):
    action = [[0.] * 9 for _ in range(2)]
    if tool == 'act':
        for row in action:
            row[3], row[8] = motion, grip
    return dict(tool=tool, action=action, steps=steps if tool == 'act' else 1,
                stage='preparation', visual_assessment='uncertain', reason='CPU synthetic action.')


class PostActionSettleTest(unittest.TestCase):
    def run_client(self, decisions=None, *, settle=6, replay=False, max_steps=100,
                   points_on_act=None, horizon=False, interrupt_settle=False):
        decisions = decisions or [decision(), decision('finish_episode')]
        requests, calls, handlers = [], [], {}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            collection = root / 'output/collections/cpu-settle'
            scores = collection / 'evaluation/test/score_samples.jsonl'
            image = root / 'public.png'
            image.write_bytes(b'public-test-image')

            class FakeSimulator:
                def __init__(self, *_):
                    self.process = mock.Mock(pid=123)
                    self.process.poll.return_value = None
                    self.step = self.acts = 0
                    self.previous = [[0.] * 9 for _ in range(2)]
                    self.grips = [False, False]
                    scores.parent.mkdir(parents=True)
                    self.score(0)

                def score(self, points):
                    with scores.open('a') as stream:
                        stream.write(json.dumps({'raw_points': points, 'private': 'SCORE_NEVER_ACTOR'}) + '\n')
                    with scores.with_name('score_events.jsonl').open('a') as stream:
                        stream.write(json.dumps({'event': 'score_awarded' if points else 'evaluation_started',
                            'physics_tick': self.step * 12, 'evaluation_time_s': self.step / 20,
                            'raw_points': points, 'breakdown': {'pickup': points}}) + '\n')

                def observation(self):
                    return {'simulation_time_s': self.step / 20, 'previous_action': deepcopy(self.previous),
                            'gripper_close_command': [[value] for value in self.grips]}

                def capture(self):
                    (collection / 'capture.json').write_text(json.dumps({'complete': True, 'steps': self.step}))

                def receive(self):
                    return {'ready': True, 'observation': self.observation(), 'public_interface': {}}

                def dispatch(self, tool, arguments=None):
                    requests.append((tool, deepcopy(arguments)))
                    if tool == 'finish_episode':
                        self.capture()
                        return {'active': False}
                    action = arguments['action'] if tool == 'act' else [[0.] * 9 for _ in range(2)]
                    count = arguments['steps'] if tool == 'act' else 1
                    if horizon:
                        count = min(count, max_steps - self.step)
                    self.step += count
                    self.previous = deepcopy(action)
                    for i, row in enumerate(action):
                        if row[8] > .5:
                            self.grips[i] = True
                        elif row[8] < -.5:
                            self.grips[i] = False
                    if tool == 'act':
                        self.acts += 1
                        self.score(5 if points_on_act == self.acts else 0)
                        if interrupt_settle and self.acts == 2:
                            handlers[signal.SIGTERM](signal.SIGTERM, None)
                    active = not (horizon and self.step >= max_steps)
                    if not active:
                        self.capture()
                    return {'active': active, 'observation': self.observation()}

                def close(self):
                    return 0

            class FakeActor:
                def __init__(self, *_, **__):
                    pass

                def invoke(self, prompt, images, schema):
                    item = deepcopy(decisions[len(calls)])
                    calls.append({'prompt': prompt, 'images': [p.name for p in images]})
                    return {'decision': item, 'session_id': 'test', 'wall_s': .1,
                            'usage': {'input_tokens': 10 * len(calls), 'output_tokens': len(calls)}}

                def close(self):
                    pass

            def prepare(obs, directory):
                directory.mkdir(parents=True)
                payload = {'public_robot_observation': deepcopy(obs)}
                (directory / 'observation.json').write_text(json.dumps(payload))
                return payload, [image]

            argv = ['client', '--run-id', 'cpu-settle', '--mode', 'dressing',
                    '--decisions', str(len(decisions)), '--max-steps', str(max_steps)]
            if settle is not None:
                argv += ['--post-action-settle-steps', str(settle)]
            prefix_action = np.zeros((2, 2, 9), np.float32)
            prefix_action[:, :, 3] = .02
            prefix = SimpleNamespace(actions=prefix_action, trusted_metadata={'reset_seed': 12},
                public_lineage={'source_group': 'parent', 'replay_steps': 2},
                initial_public_state={'simulation_time_s': np.asarray(0.)},
                final_public_state={'simulation_time_s': np.asarray(.1)})
            if replay:
                argv += ['--replay-prefix-run', 'parent']
            with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                 mock.patch.object(codex_client, 'Simulator', FakeSimulator), \
                 mock.patch.object(codex_client, 'source_snapshot', return_value={}), \
                 mock.patch.object(codex_client, 'prepare_observation', side_effect=prepare), \
                 mock.patch.object(codex_actor, 'Actor', FakeActor), \
                 mock.patch('participant.collection.continuation.load_replay_prefix', return_value=prefix), \
                 mock.patch.object(codex_client.signal, 'signal',
                                   side_effect=lambda sig, handler: handlers.__setitem__(sig, handler)), \
                 mock.patch.object(sys, 'argv', argv), mock.patch('builtins.print'):
                if interrupt_settle:
                    with self.assertRaisesRegex(KeyboardInterrupt, 'SIGTERM'):
                        codex_client.main()
                else:
                    codex_client.main()
            trace = root / 'output/operator-traces/cpu-settle'
            return {'calls': calls, 'requests': requests,
                    'attempt': json.loads((trace / 'attempt.json').read_text()),
                    'events': [json.loads(x) for x in (trace / 'decisions.jsonl').read_text().splitlines()],
                    'observations': [json.loads(p.read_text())['public_robot_observation'] for p in
                        sorted((root / 'output/actors/cpu-settle/observations').glob('*/observation.json'))]}

    def test_motion_settles_before_next_actor_and_preserves_grip_intent(self):
        result = self.run_client()
        self.assertEqual([r[0] for r in result['requests']], ['act', 'act', 'finish_episode'])
        self.assertEqual(result['requests'][1][1], {'action': [[0.] * 9] * 2, 'steps': 6})
        attempt = result['attempt']
        self.assertEqual((attempt['decisions_completed'], attempt['actor_calls_attempted']), (2, 2))
        self.assertEqual(attempt['simulation_steps'], 8)
        settle = attempt['post_action_settle']
        self.assertEqual((settle['segments_completed'], settle['simulation_steps']), (1, 6))
        self.assertGreater(settle['environment_dispatch_wall_s'], 0)
        self.assertLessEqual(settle['environment_dispatch_wall_s'], attempt['environment_dispatch_wall_s'])
        obs = result['observations'][1]
        self.assertEqual(obs['simulation_time_s'], .4)
        self.assertEqual(obs['previous_action'], [[0.] * 9] * 2)
        self.assertEqual(obs['gripper_close_command'], [[True], [True]])
        applied = [e for e in result['events'] if e['type'] == 'applied_segment']
        self.assertEqual([(e['start_step'], e['end_step']) for e in applied], [(0, 2), (2, 8), (8, 8)])
        self.assertEqual(len({e['segment_id'] for e in applied}), 3)
        self.assertEqual(applied[1]['action_source'], 'controller_settle')
        self.assertFalse(applied[1]['model_invoked'])
        self.assertEqual(applied[1]['decision_index'], applied[0]['decision_index'])
        self.assertIn('does not guarantee', result['calls'][0]['prompt'])

    def test_default_and_explicit_zero_keep_prompt_requests_and_replay_unchanged(self):
        default = self.run_client(settle=None, replay=True)
        zero = self.run_client(settle=0, replay=True)
        enabled = self.run_client(settle=6, replay=True)
        self.assertEqual(default['requests'], zero['requests'])
        self.assertEqual(default['calls'], zero['calls'])
        self.assertNotIn('post_action_settle', default['attempt'])
        self.assertEqual(enabled['requests'][:2], default['requests'][:2])
        self.assertEqual(enabled['attempt']['replay_steps_completed'], 2)
        self.assertEqual(enabled['observations'][0]['simulation_time_s'], .1)
        self.assertEqual(enabled['attempt']['post_action_settle']['simulation_steps'], 6)

    def test_gripper_only_neutral_stop_and_finish_do_not_add_a_wait(self):
        decisions = [decision(motion=0, grip=1, steps=1), decision(motion=0, grip=0, steps=1),
                     decision('stop'), decision('finish_episode')]
        result = self.run_client(decisions)
        self.assertEqual([r[0] for r in result['requests']], ['act', 'act', 'stop', 'finish_episode'])
        self.assertEqual(result['attempt']['post_action_settle']['segments_completed'], 0)
        self.assertEqual(result['attempt']['simulation_steps'], 3)

    def test_review_gate_before_and_after_wait_prevents_another_model_call(self):
        for scoring_act, expected_waits, expected_steps in [(1, 0, 3), (2, 1, 9)]:
            with self.subTest(scoring_act=scoring_act):
                result = self.run_client(points_on_act=scoring_act)
                self.assertEqual(result['attempt']['status'], 'review_ready')
                self.assertEqual(result['attempt']['actor_calls_attempted'], 1)
                self.assertEqual(result['attempt']['post_action_settle']['segments_completed'], expected_waits)
                self.assertEqual(result['attempt']['simulation_steps'], expected_steps)
                self.assertNotIn('SCORE_NEVER_ACTOR', json.dumps(result['calls']))

    def test_remaining_budget_caps_wait_and_horizon_closes_without_extra_stop(self):
        result = self.run_client(max_steps=7, horizon=True)
        self.assertEqual([r[0] for r in result['requests']], ['act', 'act'])
        self.assertEqual(result['requests'][1][1]['steps'], 5)
        self.assertEqual(result['attempt']['simulation_steps'], 7)
        self.assertEqual(result['attempt']['post_action_settle']['budget_capped_segments'], 1)
        self.assertTrue(result['attempt']['finished'])

    def test_exhausted_budget_skips_wait_and_finishes_without_an_extra_step(self):
        result = self.run_client(max_steps=2)
        self.assertEqual([r[0] for r in result['requests']], ['act', 'finish_episode'])
        self.assertEqual(result['attempt']['simulation_steps'], 2)
        self.assertEqual(result['attempt']['post_action_settle']['budget_skipped_segments'], 1)

    def test_signal_during_wait_records_ack_before_cleanup(self):
        result = self.run_client(interrupt_settle=True)
        self.assertEqual([r[0] for r in result['requests']], ['act', 'act', 'stop', 'finish_episode'])
        self.assertEqual(result['attempt']['status'], 'interrupted')
        self.assertEqual(result['attempt']['post_action_settle']['simulation_steps'], 6)
        self.assertEqual(result['attempt']['simulation_steps'], 9)
        self.assertEqual(result['attempt']['actor_calls_attempted'], 1)
        self.assertTrue(result['attempt']['capture_complete'])

    def test_invalid_flags_reject_before_creating_output_or_starting_simulator(self):
        for extra in [('--post-action-settle-steps', '-1'), ('--post-action-settle-steps', '21'),
                      ('--post-action-settle-steps', '6', '--mode', 'wiring'),
                      ('--post-action-settle-steps', '6', '--plan-size', '2')]:
            with self.subTest(extra=extra), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                with mock.patch.object(codex_client, '__file__', str(root / 'participant/collection/client.py')), \
                     mock.patch.object(codex_client.signal, 'signal'), \
                     mock.patch.object(codex_client, 'Simulator') as simulator, \
                     mock.patch.object(sys, 'argv', ['client', '--run-id', 'invalid', '--mode', 'dressing', *extra]), \
                     mock.patch('sys.stderr'), self.assertRaises(SystemExit):
                    codex_client.main()
                simulator.assert_not_called()
                self.assertFalse((root / 'output').exists())


if __name__ == '__main__':
    unittest.main()
