"""Trusted collection diagnostics. No value from this module is actor input.

Official evaluation is observed through an instance hook; scorer, geometry and
physics are unchanged. Files remain beside audit data in the trusted runner.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import time


def write_json(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


class ScoreEvents:
    """Record official 20 Hz score snapshots and changes, including zero scores."""
    def __init__(self, path):
        self.path = Path(path)
        self.samples = (self.path / 'score_samples.jsonl').open('x', encoding='utf-8')
        self.events = (self.path / 'score_events.jsonl').open('x', encoding='utf-8')
        self.started = time.perf_counter()
        self.previous = None

    def record(self, session):
        points = session.scorer.points()
        rate = session.clock_result(points)
        row = {
            'wall_utc': datetime.now(timezone.utc).isoformat(),
            'wall_elapsed_s': time.perf_counter() - self.started,
            'physics_tick': session.ticks,
            'evaluation_time_s': session.ticks * session.dt,
            'raw_points': points['raw_points'],
            'breakdown': dict(points['breakdown']),
            'success_evaluated': bool(points['success_evaluated']),
            'success': bool(points['success']),
            'first_contact_tick': session.clock.first_contact_tick,
            'score_status': rate['score_status'],
            'final_score': rate['final_score'],
            'rate_points': rate.get('rate_points'),
            'task_time_s': rate['task_time_s'],
            'last_score_award_time_s': rate.get('last_score_award_time_s'),
        }
        self.samples.write(json.dumps(row, allow_nan=False) + '\n')
        self.samples.flush()
        previous = self.previous
        events = []
        if previous is None:
            events.append({'event': 'evaluation_started'})
        for stage, points in row['breakdown'].items():
            old = 0 if previous is None else previous['breakdown'].get(stage, 0)
            if points > old:
                events.append({'event': 'score_awarded', 'stage': stage,
                               'previous_points': old, 'points': points})
        if row['first_contact_tick'] is not None and (previous is None or previous['first_contact_tick'] is None):
            events.append({'event': 'first_contact', 'contact_tick': row['first_contact_tick']})
        if row['success'] and (previous is None or not previous['success']):
            events.append({'event': 'dressing_success'})
        for event in events:
            self.events.write(json.dumps(dict(row, **event), allow_nan=False) + '\n')
        self.events.flush()
        self.previous = row

    def close(self):
        self.samples.close()
        self.events.close()


class CollectionEvaluation:
    """Wrap EvaluationSession and persist a final report without exposing it."""
    def __init__(self, env, output, *, session=None):
        self.output = Path(output)
        if session is None:
            from Policy.evaluation_live import EvaluationSession
            session = EvaluationSession.for_policy(env, self.output)
        self.session = session
        self.trace = None
        original_record = session._record

        def record(sample):
            original_record(sample)
            if self.trace is None:
                self.trace = ScoreEvents(session.path)
            self.trace.record(session)

        session._record = record

    def start(self, metadata):
        self.session.start(dict(metadata, mode='operator_collection', actor_receives_evaluation=False))

    @property
    def active(self):
        return self.session.active

    @property
    def ticks(self):
        return getattr(self.session, 'ticks', None)

    def finish(self, reason, *, valid=True):
        try:
            report = self.session.finish(reason=reason, valid=valid, take_final=valid)
            if report is not None:
                write_json(self.output.parent / 'evaluation_summary.json', {
                    'evaluation_path': str(self.session.path.relative_to(self.output.parent)),
                    'report': report,
                })
            return report
        finally:
            if self.trace is not None:
                self.trace.close()
                self.trace = None


class RecordedEnvironment:
    """Measure adapter step cost and retain reset info on the trusted side."""
    def __init__(self, env, *, profile_step_phases=False):
        self.env = env
        self.profile_step_phases = profile_step_phases
        self.reset_info = None
        self.last_step = None

    def reset(self, **kwargs):
        started = time.perf_counter()
        observation, info = self.env.reset(**kwargs)
        self.reset_info = info
        self.reset_wall_s = time.perf_counter() - started
        return observation, info

    def step(self, action):
        started = time.perf_counter()
        profile = None
        if self.profile_step_phases:
            from participant.collection.step_profile import StepProfiler
            with StepProfiler(self.env) as profile:
                result = self.env.step(action)
        else:
            result = self.env.step(action)
        self.last_step = {'environment_step_wall_s': time.perf_counter() - started,
                          'simulation_time_s': float(result[0]['simulation_time_s'])}
        if profile is not None:
            self.last_step.update(profile.metrics(self.last_step['environment_step_wall_s']))
        return result


class RecordedWriter:
    """Attach evaluation lifecycle and per-step timing to the existing writer."""
    def __init__(self, writer, recorded_env, evaluation=None):
        self.writer, self.env, self.evaluation = writer, recorded_env, evaluation
        self.steps = (writer.path / 'step_timings.jsonl').open('x', encoding='utf-8')
        self.started = time.perf_counter()
        self.failure_reason = None
        self.result = None
        self.step_count = 0
        self.closed = False

    def start_episode(self, metadata):
        self.writer.start_episode(metadata)
        if self.evaluation:
            info = self.env.reset_info
            trusted = {key: info[key] for key in ('source_commit', 'source_sha256', 'episode_seed') if key in info}
            self.evaluation.start(dict(metadata, **trusted))

    def append(self, obs, action, next_obs, *, start_tick, end_tick, audit):
        if self.evaluation and not self.evaluation.active:
            self.failure_reason = 'evaluation_invalid'
        started = time.perf_counter()
        self.writer.append(obs, action, next_obs, start_tick=start_tick, end_tick=end_tick, audit=audit)
        duration = time.perf_counter() - started
        row = dict(self.env.last_step or {}, step_index=self.step_count,
                   start_tick=start_tick, end_tick=end_tick,
                   observation_time_s=float(obs['simulation_time_s']),
                   next_observation_time_s=float(next_obs['simulation_time_s']),
                   dataset_write_wall_s=duration,
                   evaluation_active=self.evaluation.active if self.evaluation else None,
                   collection_wall_elapsed_s=time.perf_counter() - self.started)
        self.steps.write(json.dumps(row, allow_nan=False) + '\n')
        self.steps.flush()
        self.step_count += 1

    def finish_episode(self, reason, result=None, valid=True):
        if self.evaluation:
            self.result = self.evaluation.finish(self.failure_reason or reason,
                                                 valid=valid and self.failure_reason is None)
            result = self.result
        self.writer.finish_episode(self.failure_reason or reason, result=result, valid=valid)

    def close(self, complete=True):
        if self.closed:
            return
        try:
            self.writer.close(complete=complete)
        finally:
            self.steps.close()
            self.closed = True


def public_interface(env, reset_info):
    """Build a NEW static-calibration dictionary; never copy arbitrary info."""
    import math
    import numpy as np
    robots = reset_info['state']['robots']
    result = {
        'joint_names': [[joint['name'] for joint in robot['joints']] for robot in robots],
        'joint_units': [[joint['unit'] for joint in robot['joints']] for robot in robots],
        'action_scales': {key: float(env._runtime[key]) for key in
                               ('BASE_LINEAR_RATE', 'BASE_ANGULAR_RATE', 'LIFT_RATE', 'ARM_RATE', 'WRIST_RATE')},
        'camera_intrinsics': {},
        'camera_calibration': [],
    }
    width = env.contract['default_dimensions']['width']
    height = env.contract['default_dimensions']['height']
    for spec in env.contract['cameras']:
        focal = width / (2 * math.tan(math.radians(spec['horizontal_fov_deg']) / 2))
        calibration = {'id': spec['id'], 'resolution_wh': [width, height],
                       'intrinsics': [[focal, 0, width / 2], [0, focal, height / 2], [0, 0, 1]],
                       'clip_m': list(spec['clip_m'])}
        for key in ('mount_role', 'eye_mount_m', 'target_mount_m', 'up_mount'):
            if key in spec:
                calibration[key] = spec[key].copy() if isinstance(spec[key], list) else spec[key]
        result['camera_intrinsics'][spec['id']] = calibration['intrinsics']
        result['camera_calibration'].append(calibration)
    if not all(np.isfinite(v) and v > 0 for v in result['action_scales'].values()):
        raise ValueError('invalid public rate scales')
    return result
