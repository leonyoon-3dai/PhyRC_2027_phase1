import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock

import numpy as np

from participant.collection import codex_client as client
from participant.collection import user_review as review
from participant.collection.boundary import CONTRACT


def observation():
    dims = CONTRACT['default_dimensions']
    return {key: np.zeros(tuple(dims.get(v, v) for v in spec['shape']), dtype=spec['dtype'])
            for key, spec in CONTRACT['observations'].items()}


def decision(tool='act', steps=2, value=.03):
    action = np.zeros((2, 9))
    if tool == 'act':
        action[:, 3] = value
    return {'tool': tool, 'action': action.tolist(), 'steps': steps if tool == 'act' else 1,
            'stage': 'preparation', 'visual_assessment': 'uncertain', 'reason': 'test current public effect'}


class Simulator:
    def __init__(self):
        self.obs = observation()
        self.process = SimpleNamespace(poll=lambda: None)
        self.observation_step, self.pending_request, self.held = 0, None, False
        self.calls = []

    def dispatch(self, tool, arguments=None):
        self.calls.append((tool, arguments))
        if tool == 'hold':
            self.held = True
        elif tool == 'resume':
            self.held = False
        elif tool == 'act':
            assert not self.held
            self.observation_step += arguments['steps']
            self.obs['simulation_time_s'] = self.observation_step / 20
        elif tool == 'finish_episode':
            return {}
        elif tool == 'save_checkpoint':
            return {'active': True, 'held': True, 'checkpoint': {'path': '/output/test/slot.npz'}}
        else:
            raise AssertionError(tool)
        return {'held': self.held, 'active': True, 'observation': self.obs}


class GuidedTests(unittest.TestCase):
    def run_loop(self, decisions, replies, *, max_steps=100, segment_steps=400,
                 segment_decisions=20, settle=0, scores=None, prepare_only=False):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        trace, actor_root = root / 'trace', root / 'actor'
        trace.mkdir()
        actor_root.mkdir()
        sim = Simulator()
        results = [RuntimeError(d) if isinstance(d, str) else {'decision': d, 'wall_s': 0, 'usage': {}}
                   for d in decisions]
        actor = SimpleNamespace(invoke=Mock(side_effect=results))
        args = SimpleNamespace(run_id='test-guided', segment_decisions=segment_decisions,
            segment_steps=segment_steps, mode='dressing' if scores else 'wiring', initial_slot=None,
            replay_prefix_run=None, save_checkpoint_on_start=prepare_only, max_steps=max_steps,
            prepare_checkpoint_only=prepare_only,
            wrist_depth_panel=False, named_actions=False, post_action_settle_steps=settle)
        manifest = dict(decisions_completed=0, simulation_steps=0, replay_steps_completed=0,
                        actor_calls_attempted=0, actor_call_wall_s=0., environment_dispatch_wall_s=0.)
        events, holds = [], []
        replies = iter(replies)
        def wait(private, meta, sim, seen, event, **kwargs):
            holds.append(meta)
            reply = next(replies)
            return dict(action=reply, text='public direction') if isinstance(reply, str) else reply
        kwargs = {}
        if scores:
            kwargs['score_reader'] = Mock(side_effect=scores)
        review.run_guided(sim=sim, actor=actor, obs=sim.obs, args=args, root=root, trace=trace,
            actor_root=actor_root, task='Use public views.', interface={}, manifest=manifest,
            event=events.append, prepare_observation=client.prepare_observation,
            validate_decision=client.validate_decision, action_schema=client.SCHEMA,
            token_usage=client.TokenUsageAccounting(), check_interrupt=lambda: None, wait=wait, reset_actor=lambda: actor, **kwargs)
        return sim, actor, manifest, holds, events, root

    def test_checkpoint_preparation_closes_without_actor_or_fake_feedback(self):
        sim, actor, manifest, holds, events, root = self.run_loop([], [], prepare_only=True)
        self.assertEqual([x[0] for x in sim.calls], ['hold', 'save_checkpoint', 'finish_episode'])
        self.assertEqual(actor.invoke.call_count, 0)
        self.assertEqual(holds, [])
        self.assertTrue(manifest['user_guided']['enabled'])
        folder = root / 'docs/collection/user-reviews/test-guided/hold-0001'
        self.assertTrue(json.loads((folder / 'observation-metadata.json').read_text())['run_closed_after_capture'])

    def test_finish_proposal_never_dispatched_before_user(self):
        sim, actor, manifest, holds, *_ = self.run_loop([decision('finish_episode')], ['continue', 'finish'])
        self.assertEqual([h['reason'] for h in holds], ['start_state_review', 'model_finish_episode'])
        self.assertEqual([x[0] for x in sim.calls], ['hold', 'resume', 'hold', 'finish_episode'])
        self.assertEqual(manifest['simulation_steps'], 0)

    def test_stop_proposal_zero_physics_and_retry_timeout(self):
        sim, actor, manifest, holds, *_ = self.run_loop(
            ['Codex inference timed out', decision('stop')], ['continue', 'continue', 'finish'])
        self.assertEqual([h['reason'] for h in holds], ['start_state_review', 'actor_error', 'model_stop'])
        self.assertEqual(manifest['actor_calls_attempted'], 2)
        self.assertEqual(manifest['simulation_steps'], 0)
        self.assertNotIn('stop', [x[0] for x in sim.calls])

    def test_transition_budget_counts_settle_and_discards_pending_act(self):
        sim, actor, manifest, holds, *_ = self.run_loop(
            [decision(steps=2), decision(steps=2)], ['continue', 'finish'], segment_steps=5, settle=1)
        self.assertEqual(holds[-1]['reason'], 'transition_budget')
        self.assertEqual(manifest['simulation_steps'], 3)
        self.assertEqual([x[1]['steps'] for x in sim.calls if x[0] == 'act'], [2, 1])

    def test_decision_budget_resets_only_on_reply_and_keeps_cumulative(self):
        sim, actor, manifest, holds, *_ = self.run_loop(
            [decision(), decision()], ['continue', 'continue', 'finish'], segment_decisions=1)
        self.assertEqual([h['reason'] for h in holds], ['start_state_review', 'decision_budget', 'decision_budget'])
        self.assertEqual(manifest['simulation_steps'], 4)
        self.assertEqual(manifest['decisions_completed'], 2)

    def test_hard_horizon_checked_before_action_plus_settle(self):
        sim, actor, manifest, holds, *_ = self.run_loop([decision(steps=2)],
                            ['continue', 'finish'], max_steps=4, settle=2)
        self.assertEqual(holds[-1]['reason'], 'hard_horizon')
        self.assertEqual(manifest['simulation_steps'], 0)

    def test_first_sleeve_new_points_hold_before_settle(self):
        sim, actor, manifest, holds, *_ = self.run_loop([decision()],
                            ['continue', 'finish'], scores=[0, 5], settle=2)
        self.assertEqual(holds[-1]['reason'], 'first_sleeve_new_5')
        self.assertEqual(manifest['simulation_steps'], 2)
        self.assertNotIn('first_sleeve_new_5', actor.invoke.call_args.args[0])

    def test_initial_points_do_not_count_as_new(self):
        sim, actor, manifest, holds, *_ = self.run_loop([decision(), decision('stop')],
                            ['continue', 'finish'], scores=[5])
        self.assertEqual(holds[-1]['reason'], 'model_stop')

    def test_m1_release_is_held_before_action(self):
        d = decision()
        d['action'][0][8] = -1
        sim, actor, manifest, holds, *_ = self.run_loop([d], ['continue', 'finish'])
        self.assertEqual(holds[-1]['reason'], 'grasp_release_requires_method_review')
        self.assertEqual(manifest['simulation_steps'], 0)

    def test_export_exact_five_cameras_and_safe_metadata(self):
        *_, root = self.run_loop([], ['finish'])
        folder = root / 'docs/collection/user-reviews/test-guided/hold-0001'
        self.assertTrue(all((folder / (c + '.png')).exists() for c in review.CAMERAS))
        meta = json.loads((folder / 'observation-metadata.json').read_text())
        self.assertEqual(set(meta['camera_sha256']), set(review.CAMERAS))
        self.assertNotIn('first_sleeve', meta)


class FeedbackTests(unittest.TestCase):
    def test_validation_receipt_requires_hashes_all_stages_and_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'output').mkdir()
            slot = root / 'output/slot_TEST.npz'
            slot.write_bytes(b'slot')
            evidence = root / 'output/validation.json'
            evidence.write_text('{}')
            receipt = root / 'output/receipt.json'
            value = {'schema': 'phyrc-start-state-validation-v1', 'status': 'validated',
                'initial_slot': '/output/slot_TEST.npz', 'slot_sha256': review.sha(slot),
                'first_sleeve_baseline': 0,
                'checks': dict.fromkeys(('save_restore', 'settled_public_state', 'next_action_effect', 'visual_suitability'), True),
                'evidence': [{'path': 'output/validation.json', 'sha256': review.sha(evidence)}]}
            review.write_json(receipt, value)
            self.assertEqual(review.validate_start_state(root, value['initial_slot'], receipt)['first_sleeve_baseline'], 0)
            value['checks']['next_action_effect'] = False
            review.write_json(receipt, value)
            with self.assertRaises(ValueError):
                review.validate_start_state(root, value['initial_slot'], receipt)
            value['checks']['next_action_effect'] = True
            review.write_json(receipt, value)
            slot.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                review.validate_start_state(root, value['initial_slot'], receipt)

    def test_stale_duplicate_and_publication_gate(self):
        meta = {'run_id': 'run', 'hold_id': 'hold-1', 'observation_id': 'a'*64,
                'camera_sha256': dict.fromkeys(review.CAMERAS, 'b'*64), 'reason': 'decision_budget'}
        reply = dict({k: meta[k] for k in ('run_id', 'hold_id', 'observation_id')},
                     message_id='msg-1', action='continue', text='Keep the current support.')
        self.assertEqual(review.validate_reply(reply, meta, set()), reply)
        for key in ('run_id', 'hold_id', 'observation_id'):
            with self.assertRaises(ValueError):
                review.validate_reply(dict(reply, **{key: 'stale'}), meta, set())
        with self.assertRaises(ValueError):
            review.validate_reply(reply, meta, {'msg-1'})
        with tempfile.TemporaryDirectory() as tmp:
            private = Path(tmp)
            (private / 'inbox').mkdir()
            review.write_json(private / 'inbox/msg-1.json', reply)
            calls = []
            def sleep(_):
                calls.append('waited')
                review.write_json(private / 'published.json', dict(
                    {k: meta[k] for k in ('run_id', 'hold_id', 'observation_id')},
                    commit_sha='c'*40, verified_camera_sha256=meta['camera_sha256']))
            seen = set()
            value = review.await_reply(private, meta, Simulator(), seen, lambda x: None, sleep=sleep)
            self.assertEqual(calls, ['waited'])
            self.assertEqual(value, reply)
            self.assertEqual(seen, {'msg-1'})


if __name__ == '__main__':
    unittest.main()
