"""CPU wiring regression using a fixed observation/score stream and an isolated fake actor."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

import numpy as np
from PIL import Image

from participant.collection import codex_client, user_review
from participant.collection.boundary import CONTRACT
from participant.collection.segment_bridge import SegmentBridge, frame_selection, measured_displacement
from participant.collection.segment_frames import POSITIONS, write_boundary
from test_user_review import Simulator, decision
from tools.segment_review import get_segment, submit_feedback


class SegmentBridgeTests(unittest.TestCase):
    def test_order_and_bound_on_visual_inputs(self):
        self.assertEqual(frame_selection(11, 11, []), [11])
        actions = [{'end': i} for i in range(10, 31)]
        steps = frame_selection(9, 30, actions)
        self.assertEqual((steps[0], steps[-1], len(steps)), (9, 30, 8))
        with tempfile.TemporaryDirectory() as tmp:
            rgb = np.stack([np.full((256, 256, 3), 35 + i * 40, dtype=np.uint8) for i in range(5)])
            write_boundary(Path(tmp), {'rgb': rgb}, 7)
            with Image.open(Path(tmp) / '000007.jpg') as im:
                for i, name in enumerate(CONTRACT['competition_access']['allowed_cameras']):
                    x, y = POSITIONS[name]
                    self.assertAlmostEqual(im.getpixel((x + 100, y + 100))[0], 35 + i * 40, delta=2)

    def test_gripper_displacement_uses_public_base_motion_and_rotation(self):
        before = {'base_pose_world': np.array([[0, 0, 0, 1, 0, 0, 0]] * 2),
                  'grasp_pose_base': np.array([[1, 0, 0, 1, 0, 0, 0]] * 2)}
        after = {'base_pose_world': np.array([[0.1, 0, 0, 1, 0, 0, 0],
                       [0, 0, 0, 2**-.5, 0, 0, 2**-.5]]),
                 'grasp_pose_base': before['grasp_pose_base']}
        self.assertEqual(measured_displacement(before, after), [[100, 0, 0], [-1000, 1000, 0]])

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'), 'needs ffmpeg')
    def test_actual_hold_video_public_analysis_and_bound_reply(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            run = 'cpu-review'
            trace = repo / 'output/operator-traces' / run
            frames = trace / 'segment-frames'
            frames.mkdir(parents=True)
            journal = repo / 'journal'
            (repo / 'config').mkdir()
            (repo / 'config/execution_lock.json').write_text('{"official_upstream_commit":"aaaaaaaaaa"}')
            (trace / 'simulator.log').write_text('[Cloth/human friction] static=dynamic=0.35, tests\n')
            score_dir = repo / 'output/collections' / run / 'evaluation' / 'fake'
            score_dir.mkdir(parents=True)
            values = [dict(physics_tick=i*12, raw_points=(0 if i == 0 else 5),
                           breakdown={'pickup': 0 if i == 0 else 5}) for i in range(3)]
            (score_dir / 'score_samples.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in values))
            sim = Simulator()
            sim.obs['base_pose_world'][:, 3] = 1
            write_boundary(frames, sim.obs, 0)
            original_dispatch = sim.dispatch
            def dispatch(tool, arguments=None):
                if tool == 'act':
                    self.assertFalse(sim.held)
                    for i in range(sim.observation_step + 1, sim.observation_step + 1 + arguments['steps']):
                        write_boundary(frames, sim.obs, i)
                return original_dispatch(tool, arguments)
            sim.dispatch = dispatch
            review_actor = Mock()
            report = dict(stage='pickup', outcome='partial', labels=['occluded'],
                          analysis='손과 천의 경계가 가려짐', next_prompt='영상을 기준으로 파지를 확인')
            review_actor.invoke.return_value = {'decision': report, 'usage': {}}
            actor = Mock()
            actor.invoke.return_value = {'decision': decision(), 'usage': {}}
            args = SimpleNamespace(run_id=run, model='gpt-6.2-astra', segment_decisions=1,
                    segment_steps=10, mode='dressing', initial_slot=None, replay_prefix_run=None,
                    save_checkpoint_on_start=False, max_steps=100, named_actions=False,
                    wrist_depth_panel=False, post_action_settle_steps=0)
            bridge = SegmentBridge(root=repo, trace=trace, journal=journal, args=args,
                                   actor_factory=lambda _: review_actor)
            checked = []
            def user_reply():
                rec = get_segment(journal, run) if journal.exists() else None
                if rec and sim.held and rec['segment_id'] not in checked:
                    checked.append(rec['segment_id'])
                    feedback = 'revise' if len(checked) == 1 else 'finish'
                    submit_feedback(journal, dict(id='reply', run_id=run, segment_id=rec['segment_id'],
                                      action=feedback, text='사용자가 관측한 밑단을 기준으로 확인'))
            events = []
            user_review.run_guided(sim=sim, actor=actor, obs=sim.obs, args=args, root=repo, trace=trace,
                actor_root=repo / 'actor', task='Use public observations.', interface={},
                manifest=dict(decisions_completed=0, simulation_steps=0, replay_steps_completed=0,
                              source_group=run, actor_calls_attempted=0, actor_call_wall_s=0,
                              environment_dispatch_wall_s=0), event=events.append,
                prepare_observation=codex_client.prepare_observation,
                validate_decision=codex_client.validate_decision, action_schema=codex_client.SCHEMA,
                token_usage=codex_client.TokenUsageAccounting(), check_interrupt=user_reply,
                score_reader=lambda _: 0, web=bridge)
            self.assertEqual(checked, ['hold-0001','hold-0002'])
            self.assertEqual([s for s, _ in sim.calls], ['hold','resume','act','hold','finish_episode'])
            record = get_segment(journal, run)
            self.assertEqual(record['hold_reason'], 'evaluator_milestone')
            self.assertEqual(record['review_frame_steps'], [0, 1, 2])
            self.assertEqual((record['start_step'], record['end_step']), (0, 2))
            self.assertEqual((record['score_before'], record['score_after']), (0, 5))
            self.assertEqual(record['score_breakdown_after'], {'pickup': 5})
            self.assertEqual(record['parent']['segment_id'], 'hold-0001')
            history = json.loads((trace/'segment-evidence/hold-0002/actions.json').read_text())
            self.assertEqual([a['kind'] for a in history['actions']], ['model'])
            np.testing.assert_allclose(history['actions'][0]['action'], decision()['action'])
            self.assertIn('사용자가 관측한 밑단', record['prompt'])
            self.assertIn('사용자가 관측한 밑단', actor.invoke.call_args.args[0])
            self.assertIn('손과 천의 경계', actor.invoke.call_args.args[0])
            for call in actor.invoke.call_args_list + review_actor.invoke.call_args_list:
                for keyword in ('score_samples.jsonl','score_breakdown','\"raw_points\"','hard_horizon','evaluator_milestone'):
                    self.assertNotIn(keyword, call.args[0])
            count = subprocess.check_output(['ffprobe', '-v','error','-select_streams','v:0',
                        '-show_entries','stream=nb_frames','-of','default=noprint_wrappers=1:nokey=1',
                        str(journal / record['clip_path'])], text=True)
            self.assertEqual(int(count), 3)
            self.assertFalse((repo / 'docs').exists())
            self.assertFalse((trace / 'user-review').exists())
