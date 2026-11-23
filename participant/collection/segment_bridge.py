"""Connect completed, public observation segments to the local review journal."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

import numpy as np

from participant.collection.boundary import PUBLIC
from src.PhyRC_Sim.Policy.state import rotation
from tools.segment_review import claim_feedback, publish_segment


STAGES = ('setup', 'pickup', 'first_sleeve', 'opposite_shoulder', 'second_sleeve',
          'left_upper_arm', 'right_upper_arm', 'neck', 'front_orientation', 'success_hold')
LABELS = ('initial_observation', 'edge_visible', 'support_retained', 'cloth_follows',
          'alignment_improved', 'hand_entered', 'cuff_exit_visible', 'grasp_slip',
          'opening_collapsed', 'settle_rollback', 'occluded', 'no_progress',
          'housing_obstruction', 'target_unconfirmed', 'recovery', 'other_observed')
OUTCOMES = ('success', 'partial', 'failure', 'uncertain')
SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'properties': {'stage': {'type': 'string', 'enum': list(STAGES)},
                   'outcome': {'type': 'string', 'enum': list(OUTCOMES)},
                   'labels': {'type': 'array', 'items': {'type': 'string', 'enum': list(LABELS)}},
                   'analysis': {'type': 'string'}, 'next_prompt': {'type': 'string'}},
    'required': ['stage', 'outcome', 'labels', 'analysis', 'next_prompt']}
FIRST_PROMPT = '첫 관측에서 옷과 두 로봇의 위치를 확인하고, 양옆에서 밑단을 잡기 위한 첫 움직임을 제안한다. 아직 행동을 실행하지 않았다.'
ACTIVE_TASK = ('Work on the current dressing segment. Use the current approved direction. '
               'Starting from the table, approach opposite sides and seek two supported hem grasps '
               'with enough free edge between them. Observe that cloth follows both grips during '
               'a sustained lift. At the first wrist, identify the same hand and the hanging opening '
               'in successive views. Try a short descent from above when the gripper bodies have '
               'clearance; near the wrist start with 2–4 steps and check again after settling. '
               'Check both wrist and fingertips at the cuff. Retain the first sleeve while bringing '
               'the shirt over the opposite shoulder and the other hand through a different sleeve. '
               'Continue to both upper arms, head through the neck and V-neck facing front. '
               'Choose a supported recovery or request review if progress is unclear.')


def measured_displacement(before, after):
    def positions(obs):
        bases = np.asarray(obs['base_pose_world'])
        grasps = np.asarray(obs['grasp_pose_base'])
        return np.array([b[:3] + rotation(b[3:]) @ g[:3] for b, g in zip(bases, grasps)])
    return np.round(1000 * (positions(after) - positions(before)), 2).tolist()


def boundary_id(obs, run_id, step):
    digest = hashlib.sha256(json.dumps([run_id, step]).encode())
    for key in PUBLIC:
        array = np.ascontiguousarray(obs[key])
        digest.update(repr((key, array.shape, array.dtype.str)).encode())
        digest.update(array.tobytes())
    return digest.hexdigest()


def encode_clip(frames, start, end, clip):
    count = end - start + 1
    if count < 1 or any(not (frames / f'{i:06d}.jpg').is_file() for i in range(start, end + 1)):
        raise ValueError('a recorded segment frame is missing')
    # Use every real boundary, including the initial still. No frame blending.
    subprocess.run(['ffmpeg', '-v', 'error', '-nostdin', '-y', '-framerate',
                    '5' if count > 1 else '1', '-start_number', str(start),
                    '-i', str(frames / '%06d.jpg'), '-frames:v', str(count),
                    '-c:v', 'libx264', '-threads', '2', '-preset', 'veryfast', '-crf', '22',
                    '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(clip)], check=True)


def frame_selection(start, end, actions, limit=8):
    anchors = sorted({start, end, *(a['end'] for a in actions)})
    if len(anchors) > limit:
        return [anchors[i] for i in np.linspace(0, len(anchors) - 1, limit).round().astype(int)]
    evenly = np.linspace(start, end, min(end - start + 1, limit)).round().astype(int)
    for i in evenly:
        if len(anchors) < limit and int(i) not in anchors:
            anchors.append(int(i))
    return sorted(anchors)


def read_physics(log):
    patterns = {'shirt/manikin': r'\[Cloth/human friction\] static=dynamic=([.\d]+)',
                'gripper/cloth': r'\[Gripper/cloth friction\] coefficient=([.\d]+)',
                'table/cloth': r'\[Table/cloth friction\] coefficient=([.\d]+)'}
    values = {}
    with log.open(errors='replace') as lines:
        for line in lines:
            for name, pattern in patterns.items():
                match = re.search(pattern, line)
                if match:
                    values[name] = match[1]
    return ', '.join(f'{name}={values.get(name, "unverified")}' for name in patterns)


def review_visuals(actor, frames, steps, direction, actions):
    # Every argument fed into inference here is public. Add evaluator evidence only afterwards.
    prompt = (
        'Review these chronological samples from a cooperative shirt dressing clip. '
        'Each image contains overview at top, robot_1 left, robot_0 right, head above wrist. '
        'Judge the intended visible change for THIS segment. Do not infer simulator scores, '
        'contact, hidden geometry or success from occlusion. Explain in Korean what happened '
        'before/after motion and settling, and cite boundary steps/views. If only one image '
        'is present, describe the initial or stationary state; outcome=uncertain. Pick relevant '
        'labels. Write a concise next Korean task direction based only on visible evidence, '
        'for one bounded correction and its observable check. A task stage denotes an objective. '
        'Keep next_prompt free of score, evaluation, seed or hidden-state information.\n'
        + ACTIVE_TASK + '\n'
        + json.dumps({'direction': direction, 'frame_steps': steps, 'public_actions': actions},
                     ensure_ascii=False, allow_nan=False))
    result = actor.invoke(prompt, [frames / f'{i:06d}.jpg' for i in steps], SCHEMA)
    decision = validate_summary(result['decision'])
    if steps[0] == steps[-1]:
        decision['outcome'] = 'uncertain'
    return decision, {'wall_s': result.get('wall_s'), 'usage': result.get('usage')}


def validate_summary(decision):
    if (not isinstance(decision, dict) or set(decision) != set(SCHEMA['required'])
            or decision['stage'] not in STAGES or decision['outcome'] not in OUTCOMES
            or not isinstance(decision['labels'], list) or not decision['labels']
            or any(x not in LABELS for x in decision['labels'])
            or any(not isinstance(decision[k], str) or not 0 < len(decision[k].strip()) <= 4000
                   for k in ('analysis', 'next_prompt'))):
        raise ValueError('invalid public visual review')
    return dict(decision, labels=list(dict.fromkeys(decision['labels'])))


class SegmentBridge:
    """Own one run's visual-review session, observation/transition lineage and feedback."""
    def __init__(self, *, root, trace, journal, args, actor_factory):
        self.repo, self.trace, self.journal = root, trace, Path(journal)
        self.args, self.actor_factory, self.reviewer = args, actor_factory, None
        self.frames = trace / 'segment-frames'
        self.actions, self.parent, self.previous_score = [], None, None
        self.direction, self.stage, self.assessment = FIRST_PROMPT, None, None
        self.physics, self.score_offset = None, 0
        self.score_cache, self.last_source, self.public_effect = None, None, None
        self.revision = json.loads((root / 'config/execution_lock.json').read_text())['official_upstream_commit']

    def close(self):
        if self.reviewer is not None:
            self.reviewer.close()
            self.reviewer = None

    def record(self, *, index, kind, start, end, before, after, action, intent):
        delta = measured_displacement(before, after)
        self.actions.append(dict(decision=index, stage=self.stage, assessment=self.assessment, kind=kind, start=start, end=end, intent=intent,
                                 action=action.tolist(), grasp_world_delta_mm_R0_R1=delta))

    def score_at(self, step):
        directory = self.repo / 'output/collections' / self.args.run_id
        paths = list((directory / 'evaluation').glob('*/score_samples.jsonl'))
        if len(paths) != 1:
            return None, None
        tick = step * 12
        source = str(paths[0].relative_to(self.repo))
        if self.score_cache and self.score_cache['physics_tick'] == tick:
            return self.score_cache, source
        with paths[0].open('rb') as stream:
            stream.seek(self.score_offset)
            while True:
                line = stream.readline()
                if not line.endswith(b'\n'):
                    break
                row = json.loads(line)
                if row['physics_tick'] > tick:
                    break
                self.score_offset = stream.tell()
                if row['physics_tick'] == tick:
                    self.score_cache = row
                    return row, source
        return None, None

    def new_award(self, step):
        row, _ = self.score_at(step)
        if self.previous_score is None or row is None:
            return False
        return (row['raw_points'] > self.previous_score['raw_points']
                or (row.get('success_evaluated') and row.get('success')
                    and not self.previous_score.get('success')))

    def review(self, *, obs, start, end, hold, reason, manifest, event, actor_review=None):
        run = self.args.run_id
        started = time.monotonic()
        folder = self.trace / 'segment-evidence' / hold
        folder.mkdir(parents=True)
        clip = folder / 'segment.mp4'
        encode_clip(self.frames, start, end, clip)
        encoded = time.monotonic()
        steps = frame_selection(start, end, self.actions)
        review_reason = reason
        if getattr(self.args, 'gpt_only', False):
            # The action actor saw exactly this endpoint and its preceding observations.
            # Clips still contain every recorded frame; there is no separate reviewer call.
            steps = [end] if actor_review else []
            summary = actor_review or dict(
                stage=(self.public_effect or {}).get('stage', 'setup'), outcome='uncertain',
                labels=['initial_observation' if not self.parent else 'target_unconfirmed'],
                analysis=('첫 관측을 기록했습니다. 아직 모델 판정이나 실행한 행동이 없습니다.'
                          if not self.parent else '이 경계에서 모델의 시각 판정을 받지 못했습니다.'),
                next_prompt='현재 공개 카메라와 로봇 상태를 확인하고 다음 동작을 결정한다.')
            event(dict(type='segment_observation_report', hold_id=hold, frame_steps=steps,
                       source='action_actor' if actor_review else 'unassessed'))
        else:
            try:
                if self.reviewer is None:
                    self.reviewer = self.actor_factory(hold)
                summary, cost = review_visuals(self.reviewer, self.frames, steps, self.direction, self.actions)
                event(dict(type='segment_visual_review', hold_id=hold, frame_steps=steps,
                           model=self.args.model, **cost))
            except (ValueError, RuntimeError, OSError, TimeoutError) as exc:
                self.close()
                event(dict(type='segment_visual_review_error', hold_id=hold, error_type=type(exc).__name__))
                if reason != 'hard_horizon':
                    review_reason = 'review_unavailable'
                summary = dict(stage='setup', outcome='uncertain', labels=['review_unavailable'],
                               analysis='영상 분석을 완료하지 못했습니다. 이 구간의 효과는 미판정입니다.',
                               next_prompt='영상을 확인한 뒤 공개 관측에 근거한 작업 지시를 입력하세요.')
        self.public_effect = {'stage': summary['stage'], 'review': summary['analysis'], 'sample_steps': steps,
                              'last_applied': self.actions[-1] if self.actions else None}
        obs_id = boundary_id(obs, run, end)
        score, source = self.score_at(end)
        before = self.previous_score if self.parent else score
        if self.physics is None:
            self.physics = read_physics(self.trace / 'simulator.log')
        audit = {'hold': hold, 'observation_id': obs_id, 'actions': self.actions,
                 'frame_steps': steps, 'source_hz': 20, 'playback_fps': 5 if end > start else 1,
                 'start_step': start, 'end_step': end, 'direction': self.direction}
        (folder / 'actions.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n')
        evidence = [str((folder / 'actions.json').relative_to(self.repo)),
                    f'output/collections/{run}/policy.hdf5:data/demo_0/actions[{start}:{end}]',
                    '20 Hz source · all observation boundaries · 5 fps playback' if start < end
                    else 'One boundary image, zero new transitions']
        record = dict(run_id=run, segment_id=hold, parent=self.parent, observation_id=obs_id,
                      start_step=start, end_step=end, prompt=self.direction, hold_reason=review_reason,
                      physics_profile=self.physics, upstream_revision=self.revision,
                      score_before=before['raw_points'] if before else None,
                      score_after=score['raw_points'] if score else None,
                      evaluator_success_before=before['success'] if before and before.get('success_evaluated') else None,
                      evaluator_success_after=score['success'] if score and score.get('success_evaluated') else None,
                      score_breakdown_before=before['breakdown'] if before else None,
                      score_breakdown_after=score['breakdown'] if score else None,
                      score_source=source or (self.last_source if before else None),
                      reviewer_model=self.args.model, review_frame_steps=steps,
                      source_group=manifest['source_group'], parent_attempt=manifest.get('parent_attempt'),
                      replay_prefix_steps=manifest['replay_steps_completed'], initial_slot=self.args.initial_slot,
                      evidence=evidence, **summary)
        if getattr(self.args, 'gpt_only', False):
            record.update(review_source='action_actor' if actor_review else 'unassessed')
            if not actor_review:
                record.pop('reviewer_model')
        publish_segment(self.journal, record, clip)
        event(dict(type='segment_published', hold_id=hold, start_step=start, end_step=end,
                   encode_wall_s=encoded - started, review_and_publish_wall_s=time.monotonic() - encoded))
        clip.unlink()  # the journal owns the verified playback copy
        self.parent = {'run_id': run, 'segment_id': hold}
        self.previous_score, self.last_source = score, source
        self.actions = []
        return record

    def wait(self, record, sim, check_interrupt, event):
        while True:
            check_interrupt()
            if sim.process.poll() is not None:
                raise RuntimeError('collector exited during web review')
            reply = claim_feedback(self.journal, record['run_id'], record['segment_id'])
            if reply:
                if reply['action'] == 'finish':
                    action, text = 'finish', ''
                elif reply['action'] in ('accept', 'revise') and record['hold_reason'] != 'hard_horizon':
                    if reply['action'] == 'accept' and record['hold_reason'] == 'review_unavailable':
                        raise ValueError('analysis unavailable; explicit correction required')
                    action = 'continue'
                    text = record['next_prompt'] if reply['action'] == 'accept' else reply['text']
                    self.direction = text
                else:
                    raise ValueError('feedback cannot resume this boundary')
                event(dict(type='user_feedback', run_id=record['run_id'], hold_id=record['segment_id'],
                           observation_id=record['observation_id'], message_id=reply['id'],
                           received_at_utc=reply['created_at'], action=action, web_action=reply['action'],
                           text=reply['text']))
                return dict(action=action, text=text)
            time.sleep(1)
