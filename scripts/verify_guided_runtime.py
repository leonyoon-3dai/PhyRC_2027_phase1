#!/usr/bin/env python3
"""Actual sequential GPU HOLD/slot diagnostic; no actor and no adoption decision.

Runs original (optional verified replay), saves a held unique checkpoint, then
starts a separate process restoring it with official 90-control-tick settling.
Reports public drift and the effect of the same one-step small lift. The report
is evidence for human review, never automatic proof of suitable cloth topology.
"""
import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src/PhyRC_Sim')]
from participant.collection.codex_client import Simulator
from participant.collection.boundary import CONTRACT, PUBLIC
from participant.collection.continuation import load_replay_prefix, iter_action_chunks


def public_arrays(obs):
    return {name: np.asarray(obs[name], dtype=CONTRACT['observations'][name]['dtype']) for name in PUBLIC}


def store_observation(folder, observation):
    folder.mkdir()
    obs = public_arrays(observation)
    np.savez_compressed(folder / 'public.npz', **obs)
    for index, camera in enumerate(CONTRACT['cameras']):
        Image.fromarray(obs['rgb'][index]).save(folder / (camera['id'] + '.png'))
    return obs


def compare(before, after):
    result = {}
    for name in PUBLIC:
        a, b = np.asarray(before[name]), np.asarray(after[name])
        d = np.abs(a.astype(np.float64) - b.astype(np.float64))
        result[name] = {'equal': bool(np.array_equal(a, b)),
                        'mean_abs': float(d.mean()), 'max_abs': float(d.max())}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--replay-run')
    parser.add_argument('--replay-steps', type=int, default=933)
    parser.add_argument('--startup-timeout', type=float, default=900)
    parser.add_argument('--idle-timeout', type=float, default=5)
    args = parser.parse_args()
    if not args.run_id.replace('-', '').replace('_', '').isalnum():
        parser.error('run-id must be an alphanumeric identifier with hyphens/underscores')
    out = ROOT / 'output/guided-validation' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    replay = load_replay_prefix(ROOT, args.replay_run, args.replay_steps) if args.replay_run else None
    group = replay.public_lineage['source_group'] if replay else args.run_id
    report = {'schema': 'phyrc-guided-runtime-check-v1', 'run_id': args.run_id,
              'actor_called': False, 'slot_adopted': False, 'checks': {}, 'runs': [],
              'replay_parent': args.replay_run, 'replay_steps': args.replay_steps if replay else 0}
    action = np.zeros((2, 9), dtype=np.float32)
    action[:, 3] = .01  # Two small lift velocities, one policy step, grip intent preserved.
    report['probe_action'] = action.tolist()
    original = after_original = slot = None
    try:
        for phase in ('original', 'restored'):
            run = args.run_id + '-' + phase
            report['runs'].append(run)
            command = ['./run.sh', 'python', '-X', 'faulthandler', '/scripts/collect_operator.py',
                '--output', '/output/collections/' + run, '--source', 'integration_test',
                '--source-group', group, '--model-id', 'trusted-checkpoint-probe',
                '--prompt', 'Runtime validation only; no model calls.', '--user-guided',
                '--max-steps', str(args.replay_steps + 20 if replay else 20),
                '--input-timeout', str(args.idle_timeout), '--evaluate']
            if phase == 'original' and replay:
                command += ['--reset-seed', str(replay.trusted_metadata['reset_seed'])]
            if phase == 'restored':
                command += ['--initial-slot', slot['slot_path']]
            with (out / (phase + '-simulator.log')).open('x') as log:
                sim = Simulator(command, ROOT, log, timeout_s=args.startup_timeout)
                ready = sim.receive()
                if ready.get('ready') is not True:
                    raise RuntimeError('collector_not_ready')
                obs = ready['observation']
                def request(tool, arguments=None, *, expected_error=None):
                    request_id = str(sim.request_sequence)
                    sim.request_sequence += 1
                    sim.process.stdin.write(json.dumps({'tool': tool, 'arguments': arguments or {},
                        'request_id': request_id, 'observation_step': sim.observation_step}) + '\n')
                    sim.process.stdin.flush()
                    line = sim.lines.get(timeout=args.startup_timeout)
                    if not isinstance(line, str):
                        raise RuntimeError('collector_protocol_closed')
                    response = json.loads(line)
                    if response.get('request_id') != request_id:
                        raise RuntimeError('uncertain_acknowledgement')
                    if expected_error is not None:
                        if response.get('ok') is not False or response.get('error') != expected_error:
                            raise RuntimeError('wrong_rejection')
                        return response
                    if response.get('ok') is not True:
                        raise RuntimeError('collector_rejected_' + str(response.get('error')))
                    sim.observation_step = response['observation_step']
                    return response['result']
                if phase == 'original' and replay:
                    for chunk in iter_action_chunks(replay.actions):
                        obs = request('act', {'action': chunk.action.tolist(), 'steps': chunk.steps})['observation']
                        print('replay', sim.observation_step, flush=True)
                boundary = sim.observation_step
                obs = request('hold', {'hold_id': 'validation', 'reason': 'runtime-and-slot-validation'})['observation']
                before = store_observation(out / (phase + '-held'), obs)
                time.sleep(args.idle_timeout + 1)
                observed = public_arrays(request('observe'))
                immutable = all(np.array_equal(before[key], observed[key]) for key in PUBLIC)
                report['checks'][phase + '_hold_public_state_unchanged'] = immutable
                report['checks'][phase + '_hold_step_unchanged'] = sim.observation_step == boundary
                if not immutable or sim.observation_step != boundary:
                    raise RuntimeError('hold_changed_boundary')
                request('act', {'action': action.tolist(), 'steps': 1}, expected_error='episode_held')
                report['checks'][phase + '_held_action_rejected'] = True
                if phase == 'original':
                    original = before
                    slot = request('save_checkpoint', {'key': args.run_id + '-slot'})['checkpoint']
                    report['checkpoint'] = slot
                    (out / 'checkpoint.json').write_text(json.dumps(slot, indent=2) + '\n')
                else:
                    report['restored_after_settle_vs_saved'] = compare(original, before)
                    pre = ROOT / 'output/collections' / run / 'slot_reset/before_settle.npz'
                    with np.load(pre, allow_pickle=False) as data:
                        report['restored_before_settle_vs_saved'] = compare(original, data)
                        store_observation(out / 'restored-before-settle', data)
                request('resume', {'hold_id': 'validation'})
                after = request('act', {'action': action.tolist(), 'steps': 1})['observation']
                after = store_observation(out / (phase + '-after-probe'), after)
                if phase == 'original':
                    after_original = after
                else:
                    report['same_probe_end_difference'] = compare(after_original, after)
                    report['probe_effect_difference'] = compare(
                        {k: after_original[k].astype(float) - original[k].astype(float) for k in PUBLIC},
                        {k: after[k].astype(float) - before[k].astype(float) for k in PUBLIC})
                request('finish_episode')
                returncode = sim.close()
                report['checks'][phase + '_closed_normally'] = returncode == 0
                print(phase, 'closed', returncode, flush=True)
                if returncode != 0:
                    raise RuntimeError('collector_close_failed')
        report['runtime_checks_passed'] = all(report['checks'].values())
    except BaseException as exc:
        report['error'] = type(exc).__name__ + ': ' + str(exc)
        report['runtime_checks_passed'] = False
        # A failed/uncertain ACK must not trigger another action or cleanup step.
        # The user-guided collector enters idle/EOF HOLD; PID is left for inspection.
        if 'sim' in locals() and sim.process.poll() is None:
            report['live_collector_pid'] = sim.process.pid
        raise
    finally:
        (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        print('report:', out / 'report.json', flush=True)


if __name__ == '__main__':
    main()
