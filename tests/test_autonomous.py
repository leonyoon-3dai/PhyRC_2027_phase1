"""Exercise the autonomous controller and the same intervention journal used by the browser."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from participant.collection import codex_client
from participant.collection.autonomous import CAMERA_BRIEFING, bound_gentle_action, run_autonomous
from participant.collection.segment_bridge import SegmentBridge
from tools import segment_review as journal
from test_user_review import Simulator, decision


def proposal(tool='act', steps=12):
    summary = dict(stage='pickup', outcome='partial', labels=['edge_visible'],
                   analysis='현재 영상에 옷단이 보인다.', next_prompt='양쪽을 이동한다.')
    return dict(decision=dict(decision(tool, steps), observation_review=summary), usage={})


class AutonomousTests(unittest.TestCase):
    def execute(self, responses, interrupt=False, segment_decisions=2, report_stall=False,
                max_steps=90, settle=0, scores=False, end_at_horizon=False, supervised_close=False,
                feedback_on_error=False, camera_briefing=False, gentle_wrist_dressing=False, events=None):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        trace = root / 'trace'
        trace.mkdir()
        (trace / 'simulator.log').touch()
        (root / 'config').mkdir()
        (root / 'config/execution_lock.json').write_text('{"official_upstream_commit":"acbd000"}')
        path = root / 'journal'
        sim, actor = Simulator(), Mock()
        sim.obs['base_pose_world'][:, 3] = 1
        args = SimpleNamespace(run_id='test-auto', gpt_only=True, model='gpt', max_steps=max_steps,
                               segment_steps=60, segment_decisions=segment_decisions, wrist_depth_panel=False,
                               post_action_settle_steps=settle, initial_slot=None, named_actions=False,
                               save_checkpoint_on_start=False, until_full_score_or_feedback=supervised_close,
                               camera_briefing=camera_briefing, gentle_wrist_dressing=gentle_wrist_dressing)
        web = SegmentBridge(root=root, trace=trace, journal=path, args=args, actor_factory=Mock())
        if scores:
            evaluation = root / 'output/collections' / args.run_id / 'evaluation/fixture'
            evaluation.mkdir(parents=True)
            values = [dict(physics_tick=i*12, raw_points=min(i, 50), breakdown={}, success=True, success_evaluated=True)
                      for i in range(max_steps + 1)]
            (evaluation / 'score_samples.jsonl').write_text(''.join(json.dumps(v) + '\n' for v in values))
        if end_at_horizon:
            dispatch = sim.dispatch
            def finish_at_limit(tool, arguments=None):
                result = dispatch(tool, arguments)
                if tool == 'act' and sim.observation_step == max_steps:
                    result['active'] = False
                return result
            sim.dispatch = finish_at_limit
        manifest = dict(simulation_steps=0, environment_dispatch_wall_s=0, decisions_completed=0,
                        actor_calls_attempted=0, actor_call_wall_s=0, source_group='test', replay_steps_completed=0)
        if events is None:
            events = []

        def reply(prompt, images, schema):
            initial = journal.get_segment(path, args.run_id)
            self.assertIsNotNone(initial)
            self.assertIn('observation_review', schema['required'])
            if supervised_close:
                self.assertEqual(schema['properties']['tool']['enum'], ['act'])
            for field in ('raw_points', 'evaluator_milestone', 'score_breakdown'):
                self.assertNotIn(field, prompt)
            if interrupt and sim.observation_step == 0 and actor.invoke.call_count == 1:
                req = dict(run_id=args.run_id, id='pause-01')
                self.assertEqual(journal.request_intervention(path, req), journal.request_intervention(path, req))
                self.assertFalse(journal.state(path, args.run_id)['can_feedback'])
            value = responses.pop(0)
            if isinstance(value, Exception):
                raise value
            if report_stall:
                value['decision']['observation_review'].update(outcome='failure', labels=['no_progress'])
            return value

        actor.invoke.side_effect = reply

        def handle_request():
            if (interrupt or feedback_on_error) and journal.control_state(path, args.run_id) == 'held':
                if feedback_on_error:
                    self.assertFalse(manifest['human_intervention'])
                state = journal.state(path, args.run_id)
                self.assertTrue(state['can_feedback'])
                journal.submit_feedback(path, dict(run_id=args.run_id, segment_id=state['latest']['segment_id'],
                                        id='correction', action='revise', text='오른쪽 가장자리를 확인한다.'))

        def encode(frames, start, end, dest):
            dest.write_bytes(b'\x00\x00\x00\x18ftypisom' + bytes(50))
        with patch('participant.collection.segment_bridge.encode_clip', encode):
            run_autonomous(sim=sim, actor=actor, obs=sim.obs, args=args, root=root, trace=trace,
                           actor_root=root, task='Use public observations.', interface={}, manifest=manifest,
                           event=events.append, prepare_observation=lambda obs, folder: ({}, []),
                           validate_decision=codex_client.validate_decision, action_schema=codex_client.SCHEMA,
                           token_usage=codex_client.TokenUsageAccounting(), check_interrupt=handle_request,
                           reset_actor=lambda: actor, web=web)
        records = [json.loads(line) for line in journal.export_rows(path, args.run_id).splitlines()]
        self.assertEqual(records[0]['review_source'], 'unassessed')
        self.assertEqual(records[-1]['control_state'], 'closed')
        self.assertEqual(sim.calls[-1][0], 'act' if end_at_horizon else 'finish_episode')
        web.actor_factory.assert_not_called()
        return actor, sim, manifest, records

    def test_auto_first_frame_grouped_full_actions_and_model_close(self):
        actor, sim, m, records = self.execute([proposal(steps=20), proposal(steps=20),
                                               proposal(steps=12), proposal('finish_episode')])
        self.assertEqual([(r['start_step'],r['end_step']) for r in records], [(0,0),(0,40),(40,52)])
        self.assertEqual([x['steps'] for tool,x in sim.calls if tool=='act'], [20,20,12])
        self.assertEqual(m['autonomous_control']['close_reason'], 'model_finish_episode')
        self.assertFalse(m['human_intervention'])
        self.assertEqual(actor.invoke.call_count, 4)
        self.assertTrue(all(CAMERA_BRIEFING not in call.args[0] for call in actor.invoke.call_args_list))

    def test_gentle_bounds_cover_all_stages_and_preserve_coordination_and_grips(self):
        action = np.array([[1, -.5, 0, -.4, .8, 0, -.2, 0, .8],
                           [0, 0, .3, -.1, 0, .4, -.6, 1, -.8]], dtype=np.float32)
        for stage in codex_client.STAGES:
            with self.subTest(stage=stage):
                bounded, steps, scale = bound_gentle_action(action, 20, stage)
                early = stage in ('preparation', 'approach', 'grasp', 'lift')
                self.assertEqual(steps, 8 if early else 4)
                self.assertAlmostEqual(scale, .30 if early else .12)
                np.testing.assert_allclose(bounded[:, :8], action[:, :8] * scale)
                np.testing.assert_array_equal(bounded[:, 8], action[:, 8])
        # With a stationary base, an arm or wrist alone must also respect the early-stage cap.
        action[:, :3] = 0
        bounded, steps, scale = bound_gentle_action(action, 2, 'grasp')
        self.assertEqual((steps, scale), (2, .5))
        np.testing.assert_allclose(bounded[:, :8], action[:, :8] * .5)
        action[:, :8] *= .05
        bounded, steps, scale = bound_gentle_action(action, 2, 'neck')
        self.assertEqual((steps, scale), (2, 1.0))
        np.testing.assert_array_equal(bounded, action)

    def test_gentle_dispatch_matches_logged_limits_and_remaining_episode_budget(self):
        early = proposal(steps=20)
        early['decision']['action'][0][0] = -1
        contact = proposal(steps=20)
        contact['decision'].update(stage='shoulder')
        contact['decision']['action'][1][5] = 1
        contact['decision']['action'][1][8] = -1
        events = []
        actor, sim, _, _ = self.execute([early, contact], gentle_wrist_dressing=True,
                                        max_steps=10, end_at_horizon=True, events=events)
        sent = [value for tool, value in sim.calls if tool == 'act']
        bounds = [e for e in events if e['type'] == 'gentle_wrist_action']
        self.assertEqual([e['sent_steps'] for e in bounds], [8, 2])
        self.assertEqual([e['requested_steps'] for e in bounds], [20, 20])
        self.assertEqual([e['decision_index'] for e in bounds], [0, 1])
        for e, actual in zip(bounds, sent, strict=True):
            self.assertEqual((e['sent_action'], e['sent_steps']), (actual['action'], actual['steps']))
        self.assertEqual(bounds[0]['requested_action'][0][0], -1)
        self.assertAlmostEqual(sent[0]['action'][0][0], -.3)
        self.assertEqual(bounds[1]['requested_action'][1][5], 1)
        self.assertAlmostEqual(sent[1]['action'][1][5], .12)
        self.assertEqual(sent[1]['action'][1][8], -1)
        prompt = actor.invoke.call_args_list[0].args[0]
        for text in ('4 policy steps', '8 steps', '0.12', '0.5', '0.3'):
            self.assertIn(text, prompt)

    def test_camera_briefing_once_per_actor_session(self):
        events = []
        actor, _, _, _ = self.execute([proposal(), RuntimeError('lost session'), proposal(), proposal('stop')],
                                      camera_briefing=True, events=events)
        prompts = [call.args[0] for call in actor.invoke.call_args_list]
        self.assertEqual([p.count(CAMERA_BRIEFING) for p in prompts], [1, 0, 1, 0])
        camera_order = codex_client.CONTRACT['competition_access']['allowed_cameras']
        self.assertIn(', '.join(camera_order), CAMERA_BRIEFING)
        self.assertEqual([e['model_call_index'] for e in events if e['type'] == 'camera_briefing_delivered'],
                         [0, 2])

    def test_recent_visual_reviews_keep_observed_effects_across_segment_boundaries(self):
        decisions = [proposal(steps=3) for _ in range(6)] + [proposal('stop')]
        for i, response in enumerate(decisions):
            response['decision']['observation_review'].update(
                analysis=f'camera report {i}', next_prompt=f'intended action {i}')
        actor, _, _, _ = self.execute(decisions, segment_decisions=1, scores=True)
        last_prompt = actor.invoke.call_args.args[0]
        self.assertNotIn('camera report 1', last_prompt)
        self.assertIn('camera report 3', last_prompt)
        self.assertIn('camera report 5', last_prompt)
        self.assertNotIn('intended action 5', last_prompt)
        self.assertNotIn('raw_points', last_prompt)

    def test_exceptional_intervention_discards_proposed_action_at_same_boundary(self):
        actor, sim, m, records = self.execute([proposal(steps=20), proposal(steps=4), proposal('stop')], True)
        self.assertEqual([x['steps'] for tool,x in sim.calls if tool=='act'], [4])
        self.assertIn('오른쪽 가장자리', actor.invoke.call_args_list[1].args[0])
        self.assertTrue(m['human_intervention'])
        self.assertEqual(records[1]['claimed_feedback_id'], 'correction')
        self.assertEqual(m['autonomous_control']['task_outcome'], 'incomplete')

    def test_actor_errors_retained_and_closed_without_extra_transition(self):
        actor, sim, m, records = self.execute([RuntimeError('x'), RuntimeError('y')])
        self.assertEqual(sim.observation_step, 0)
        self.assertEqual(m['autonomous_control']['task_outcome'], 'technical_failure')
        self.assertEqual([r['hold_reason'] for r in records], ['start_state_review','actor_error','actor_error'])

    def test_four_observed_failures_preserve_new_recovery_chosen_by_actor(self):
        recovery = proposal(steps=9)
        recovery['decision'].update(stage='recovery', visual_assessment='recovering',
                                    reason='Change approach angle and regrasp the exposed rim.')
        attempts = [proposal(steps=3) for _ in range(4)] + [recovery, proposal('stop')]
        actor, sim, m, records = self.execute(attempts, segment_decisions=1, report_stall=True)
        self.assertEqual(m['autonomous_control']['close_reason'], 'model_stop')
        self.assertEqual([x['steps'] for tool,x in sim.calls if tool=='act'], [3,3,3,3,9])
        self.assertEqual(sim.observation_step, 21)
        self.assertTrue(all('no_progress' in r['labels'] for r in records[1:]))

    def test_episode_limit_includes_last_legal_action_and_final_frame(self):
        actor, sim, m, records = self.execute([proposal(steps=20)], max_steps=7, end_at_horizon=True)
        self.assertEqual([x['steps'] for tool,x in sim.calls if tool=='act'], [7])
        self.assertEqual(records[-1]['end_step'], 7)
        self.assertEqual(records[-1]['review_source'], 'unassessed')
        self.assertEqual(m['autonomous_control']['close_reason'], 'hard_horizon')

    def test_full_score_closes_before_settle_or_another_actor_call(self):
        actor, sim, m, records = self.execute(
            [proposal(steps=20), proposal(steps=20), proposal(steps=6)],
            scores=True, settle=2, supervised_close=True)
        self.assertEqual(records[-1]['score_after'], 50)
        self.assertEqual(records[-1]['end_step'], 50)
        self.assertEqual(actor.invoke.call_count, 3)
        self.assertEqual(m['autonomous_control']['close_reason'], 'full_score')

    def test_full_score_reached_during_settle(self):
        _, sim, m, records = self.execute(
            [proposal(steps=20), proposal(steps=20), proposal(steps=4)],
            scores=True, settle=2, supervised_close=True)
        self.assertEqual(sim.observation_step, 50)
        self.assertEqual(records[-1]['score_after'], 50)
        self.assertEqual(m['autonomous_control']['close_reason'], 'full_score')

    def test_repeated_actor_errors_hold_scene_until_feedback(self):
        _, sim, m, records = self.execute([RuntimeError('x'), RuntimeError('y')],
                                           supervised_close=True, feedback_on_error=True)
        self.assertEqual(sim.observation_step, 0)
        self.assertEqual(records[-1]['hold_reason'], 'actor_error')
        self.assertEqual(records[-1]['claimed_feedback_id'], 'correction')
        self.assertEqual(m['autonomous_control']['close_reason'], 'human_feedback')

    def test_submitted_feedback_ends_supervised_run_before_pending_action(self):
        actor, sim, m, records = self.execute([proposal()], interrupt=True, supervised_close=True)
        self.assertEqual(sim.observation_step, 0)
        self.assertEqual(records[-1]['claimed_feedback_id'], 'correction')
        self.assertEqual(m['autonomous_control']['close_reason'], 'human_feedback')

    def test_private_scores_do_not_affect_actions_settling_or_termination(self):
        def example(scores):
            actor, sim, m, records = self.execute([proposal(steps=12),proposal(steps=20),proposal('stop')],
                                                  settle=2, scores=scores)
            return sim.calls, [c.args[0] for c in actor.invoke.call_args_list], records
        a, prompts_a, records_a = example(False)
        b, prompts_b, records_b = example(True)
        self.assertEqual(a,b)
        self.assertEqual(prompts_a,prompts_b)
        self.assertEqual([x['steps'] for tool,x in a if tool=='act'], [12,2,20,2])
        self.assertNotEqual(records_a[-1]['score_after'], records_b[-1]['score_after'])
