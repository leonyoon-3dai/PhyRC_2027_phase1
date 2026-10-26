#!/usr/bin/env python3
"""Fixed-step diagnostic, separate from official scoring and human collection.

Times synchronous policy calls and unchanged environment steps separately.
Default neutral policy measures the environment, not learned-policy inference.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


def distribution(values):
    import numpy as np
    x = np.asarray(values, dtype=float)
    if not len(x):
        return None
    return {'count': len(x), 'total_s': float(x.sum()), 'mean_s': float(x.mean()),
            'p50_s': float(np.percentile(x, 50)), 'p95_s': float(np.percentile(x, 95)),
            'max_s': float(x.max())}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--steps', type=int, default=100)
    p.add_argument('--warmup', type=int, default=10)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--policy', type=Path)
    p.add_argument('--checkpoint', type=Path)
    p.add_argument('--profile', choices=['actor_rgbd', 'measured_state'], default='actor_rgbd')
    p.add_argument('--without-evaluator', action='store_true', help='Different workload; never compare as identical evaluation')
    p.add_argument('--output', type=Path, required=True, help='New output directory')
    a = p.parse_args()
    if a.steps < 1 or a.warmup < 0 or a.seed < 0 or (a.checkpoint and not a.policy):
        p.error('positive steps, nonnegative warmup/seed; checkpoint requires policy')
    for path in (a.policy, a.checkpoint):
        if path and not path.is_file():
            p.error(f'File missing: {path}')
    a.output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    root = Path('/project') if Path('/project/src').exists() else Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'src/PhyRC_Sim'))
    import numpy as np
    from Policy.environment import DressingEnv
    env = DressingEnv(profile=a.profile, max_episode_steps=a.warmup + a.steps)
    created = time.perf_counter()
    session = None
    if not a.without_evaluator:
        from Policy.evaluation_live import EvaluationSession
        session = EvaluationSession.for_policy(env, a.output / 'episodes')
    policy_start = time.perf_counter()
    if a.policy:
        spec = importlib.util.spec_from_file_location('diagnostic_policy', a.policy)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        policy = module.load_policy(checkpoint=a.checkpoint, observation_space=env.observation_space,
                                    action_space=env.action_space)
    else:
        policy = lambda obs: np.zeros((2, 9), np.float32)
    loaded = time.perf_counter()
    obs, info = env.reset(seed=a.seed)
    if hasattr(policy, 'reset'):
        policy.reset()
    if session:
        session.start({'mode': 'fixed_step_diagnostic', 'seed': a.seed,
                       'source_commit': info['source_commit']})
    reset_done = time.perf_counter()
    totals = {'tick': 0.0, 'observe': 0.0}
    for name, key in (('_tick', 'tick'), ('_observe', 'observe')):
        original = getattr(env, name)
        def timed(*args, _fn=original, _key=key, **kwargs):
            begin = time.perf_counter()
            try:
                return _fn(*args, **kwargs)
            finally:
                totals[_key] += time.perf_counter() - begin
        setattr(env, name, timed)
    rows = []
    report = {'diagnostic_only': True, 'zero_policy': a.policy is None,
              'profile': a.profile, 'evaluator_enabled': session is not None,
              'seed': a.seed, 'warmup_steps': a.warmup, 'requested_measured_steps': a.steps,
              'startup_import_env_s': created-started, 'evaluator_setup_s': policy_start-created,
              'policy_load_s': loaded-policy_start,
              'reset_s': reset_done-loaded,
              'policy_sha256': hashlib.sha256(a.policy.read_bytes()).hexdigest() if a.policy else None,
              'source_commit': info['source_commit'], 'source_dirty': info.get('source_dirty'),
              'policy_timing_note': 'Synchronous call through numpy materialization; first call retained separately.'}
    try:
        with (a.output / 'steps.jsonl').open('x') as log:
            for step in range(a.warmup + a.steps):
                before = float(obs['simulation_time_s'])
                t0 = time.perf_counter()
                action = np.asarray(policy(obs), dtype=np.float32)
                t1 = time.perf_counter()
                old = dict(totals)
                obs, _, terminated, truncated, _ = env.step(action)
                t2 = time.perf_counter()
                dt = float(obs['simulation_time_s']) - before
                if not np.isclose(dt, 0.05, atol=1e-7, rtol=0):
                    raise RuntimeError(f'Unexpected simulated step: {dt}')
                row = {'step': step, 'warmup': step < a.warmup, 'simulation_dt_s': dt,
                       'policy_s': t1-t0, 'env_s': t2-t1,
                       'tick_s': totals['tick']-old['tick'], 'observe_s': totals['observe']-old['observe']}
                log.write(json.dumps(row)+'\n'); log.flush(); rows.append(row)
                if session and not session.active:
                    raise RuntimeError('Official measurement session failed')
                if terminated or truncated:
                    break
        measured = [r for r in rows if not r['warmup']]
        report['completed_measured_steps'] = len(measured)
        report['first_policy_call_s'] = rows[0]['policy_s']
        report['warm'] = {k: distribution([r[k] for r in measured])
                          for k in ('policy_s', 'env_s', 'tick_s', 'observe_s')}
        sim = sum(r['simulation_dt_s'] for r in measured)
        wall = sum(r['policy_s']+r['env_s'] for r in measured)
        report.update(measured_simulation_s=sim, measured_loop_wall_s=wall,
                      simulation_seconds_per_wall_second=sim/wall if wall else None,
                      fixed_step_complete=len(measured) == a.steps,
                      note='Tick includes control/physics and attached callbacks; observe includes sensors/state. Not isolated physics kernel timing or official self-check.')
    except BaseException as error:
        report['error'] = repr(error)
        raise
    finally:
        if session:
            session.finish(reason='fixed_step_diagnostic', valid='error' not in report, take_final=False)
        report['total_before_close_s'] = time.perf_counter()-started
        (a.output / 'timing.json').write_text(json.dumps(report, indent=2)+'\n')
        print(json.dumps(report), flush=True)
        env.close()


if __name__ == '__main__':
    main()
