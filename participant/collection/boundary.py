"""Collection-time operator API. Never expose Gym info or the environment handle.

This module is an allowlist boundary, not an OS security sandbox. Run a model
operator without filesystem/shell tools; only the dispatcher exposes these tools.
"""
from pathlib import Path
import json
import time
import numpy as np

CONTRACT = json.loads((Path(__file__).resolve().parents[2] / 'config/policy_interface.json').read_text())
PUBLIC = tuple(CONTRACT['competition_access']['allowed_policy_observations'])


def public_observation(obs):
    # Build a fresh dictionary, never serialize arbitrary objects or info.
    return {key: np.array(obs[key], copy=True) for key in PUBLIC if key in obs}


def validate_action(action, steps):
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= 20:
        raise ValueError('steps must be an integer in [1,20] (at most 1 simulation second)')
    a = np.asarray(action)
    # JSON numbers are converted explicitly; typed callers must use float32.
    if isinstance(action, np.ndarray) and a.dtype != np.float32:
        raise ValueError('typed actions must be float32')
    if a.dtype.kind not in 'fiu' or a.shape != (2, 9) or not np.isfinite(a).all() or (abs(a) > 1).any():
        raise ValueError('expected finite normalized (2,9) action in [-1,1]')
    return a.astype(np.float32)


class Operator:
    def __init__(self, env, writer, *, source, source_group, model_id, prompt):
        if source not in ('human', 'gpt', 'human_corrected_gpt', 'integration_test'):
            raise ValueError('unknown source')
        if not source_group or not model_id or not prompt:
            raise ValueError('source_group, model_id and prompt required for provenance')
        self._env, self._writer = env, writer
        self._meta = dict(operator_source=source, source_group=source_group, model_id=model_id, prompt=prompt)
        self._obs = None
        self._active = False
        self._tick = 0
        self._calls = []

    def begin(self, *, seed=None):
        # Only the implementation-side runner can reset; seed is never returned.
        if self._active:
            raise RuntimeError('finish episode before reset')
        obs, info = self._env.reset(seed=seed)
        self._obs = public_observation(obs)
        self._writer.start_episode(dict(self._meta, episode_id=info['episode_id']))
        self._tick = 0  # episode-relative ticks, not a claim about raw archives
        self._active = True
        self._calls = []
        return self.observe()

    def observe(self):
        if not self._active:
            raise RuntimeError('no active episode')
        return public_observation(self._obs)

    def act(self, action, steps=1):
        a = validate_action(action, steps)
        if not self._active:
            raise RuntimeError('no active episode')
        started = time.perf_counter()
        for _ in range(steps):
            before = self._obs
            obs, _, terminated, truncated, _ = self._env.step(a.copy())
            after = public_observation(obs)
            self._writer.append(before, a, after, start_tick=self._tick, end_tick=self._tick + 12,
                                audit={'operator_source_code': np.uint8(('human','gpt','human_corrected_gpt','integration_test').index(self._meta['operator_source']))})
            self._tick += 12
            self._obs = after
            if terminated or truncated:
                self.finish_episode(reason='environment_horizon')
                break
        self._calls.append(dict(action=a.tolist(), requested_steps=steps, end_tick=self._tick,
                                wall_s=time.perf_counter()-started))
        return {'active': self._active, 'observation': public_observation(self._obs)}

    def stop(self):
        # Synchronous execution has no pending queue. Neutral motion preserves grip intent.
        return self.act(np.zeros((2,9), np.float32), 1)

    def finish_episode(self, reason='operator_finished'):
        if self._active:
            valid = self._tick > 0
            self._writer.finish_episode(reason, valid=valid)
            self._active = False
        return {'steps': self._tick // 12, 'complete': self._tick > 0}
