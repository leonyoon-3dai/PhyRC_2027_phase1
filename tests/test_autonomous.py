"""Exercise the autonomous controller and the same intervention journal used by the browser."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from participant.collection import codex_client
from participant.collection.autonomous import run_autonomous
from participant.collection.segment_bridge import SegmentBridge
from tools import segment_review as journal
from test_user_review import Simulator, decision


def proposal(tool='act', steps=12):
    summary = dict(stage='pickup', outcome='partial', labels=['edge_visible'],
                   analysis='현재 영상에 옷단이 보인다.', next_prompt='양쪽을 이동한다.')
    return dict(decision=dict(decision(tool, steps), observation_review=summary), usage={})


class AutonomousTests(unittest.TestCase):
    def execute(self, responses, interrupt=False, segment_decisions=2, report_stall=False,
                max_steps=90, settle=0, scores=False, end_at_horizon=False):
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
                               save_checkpoint_on_start=False)
        web = SegmentBridge(root=root, trace=trace, journal=path, args=args, actor_factory=Mock())
        if scores:
            evaluation = root / 'output/collections' / args.run_id / 'evaluation/fixture'
            evaluation.mkdir(parents=True)
            values = [dict(physics_tick=i*12, raw_points=i, breakdown={}, success=True, success_evaluated=True)
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
        events = []

        def reply(prompt, images, schema):
            initial = journal.get_segment(path, args.run_id)
            self.assertIsNotNone(initial)
            self.assertIn('observation_review', schema['required'])
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
            if interrupt and journal.control_state(path, args.run_id) == 'held':
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

    def test_persistent_observed_failure_closes_instead_of_looping(self):
        actor, sim, m, records = self.execute([proposal(steps=3) for _ in range(5)],
                                               segment_decisions=1, report_stall=True)
        self.assertEqual(m['autonomous_control']['close_reason'], 'repeated_no_progress')
        self.assertEqual(sim.observation_step, 12)

    def test_episode_limit_includes_last_legal_action_and_final_frame(self):
        actor, sim, m, records = self.execute([proposal(steps=20)], max_steps=7, end_at_horizon=True)
        self.assertEqual([x['steps'] for tool,x in sim.calls if tool=='act'], [7])
        self.assertEqual(records[-1]['end_step'], 7)
        self.assertEqual(records[-1]['review_source'], 'unassessed')
        self.assertEqual(m['autonomous_control']['close_reason'], 'hard_horizon')

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
