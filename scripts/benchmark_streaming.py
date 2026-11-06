#!/usr/bin/env python3
"""Model-free ABBA benchmark of the existing collector's full --webrtc path.

Default is a CPU-only plan. --execute starts four sequential GPU collectors.
This measures the operational flag, including viewport and idle render changes;
it does NOT isolate the SDK. No network/firewall settings are changed.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORDER = (False, True, True, False)
ZERO_ACTION = [[0.0] * 9 for _ in range(2)]


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def stats(values):
    if not values:
        return {'count': 0}
    return {'count': len(values), 'sum_s': sum(values),
            'mean_s': statistics.mean(values), 'median_s': statistics.median(values),
            'min_s': min(values), 'max_s': max(values)}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run-id', required=True)
    p.add_argument('--execute', action='store_true', help='Actually start sequential GPU processes')
    p.add_argument('--warmup-steps', type=int, default=5)
    p.add_argument('--chunk-steps', type=int, default=20)
    p.add_argument('--chunks', type=int, default=3)
    p.add_argument('--idle-seconds', type=float, default=10)
    p.add_argument('--connection-wait-seconds', type=float, default=0,
                   help='Equal pre-warmup wait in all conditions; does not prove a viewer connected')
    p.add_argument('--response-timeout', type=float, default=600)
    p.add_argument('--viewport', choices=('native', 'matched'), default='native',
                   help='native=current production flag; matched=identical 1280x720 app config')
    args = p.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}', args.run_id):
        p.error('run-id must be a safe filename component')
    if not 1 <= args.warmup_steps <= 20 or not 1 <= args.chunk_steps <= 20 or not 1 <= args.chunks <= 100:
        p.error('warmup/chunk steps must be 1..20; chunks must be 1..100')
    for name in ('idle_seconds', 'connection_wait_seconds', 'response_timeout'):
        value = getattr(args, name)
        if not math.isfinite(value) or value < 0 or (name == 'response_timeout' and value == 0):
            p.error('waits must be finite and nonnegative; response timeout must be positive')
    return args


def command_for(args, index, enabled):
    name = f'{args.run_id}-{index:02}-' + ('on' if enabled else 'off')
    script = '/scripts/collect_operator.py' if args.viewport == 'native' else '/scripts/collect_benchmark_viewport.py'
    command = ['./run.sh', 'python', '--no-randomization', script,
               '--output', '/output/collections/' + name,
               '--source', 'integration_test', '--source-group', args.run_id,
               '--model-id', 'scripted-neutral-stream-benchmark',
               '--prompt', 'Model-free neutral actions for streaming cost measurement.',
               '--max-steps', str(args.warmup_steps + args.chunk_steps * args.chunks + 10),
               '--input-timeout', str(max(120, args.idle_seconds + args.connection_wait_seconds + 60)),
               '--evaluate']
    if enabled:
        command.append('--webrtc')
    return name, command


def protocol_measure(sim, tool, arguments=None):
    started = time.perf_counter()
    value = sim.dispatch(tool, arguments)
    return value, time.perf_counter() - started


def idle_measure(sim, observation, duration, *, sleep=time.sleep):
    before = float(observation['simulation_time_s'])
    started = time.perf_counter()
    sleep(duration)
    waited = time.perf_counter() - started
    after, dispatch = protocol_measure(sim, 'observe')
    if abs(float(after['simulation_time_s']) - before) > 1e-9:
        raise RuntimeError('idle advanced public simulation clock')
    return after, {'requested_wait_s': duration, 'actual_wait_s': waited,
                   'observe_dispatch_wall_s': dispatch,
                   'simulation_clock_unchanged': True, 'simulation_time_s': before}


def summarize_saved(collection, warmup_steps, measured_steps):
    capture = json.loads((collection / 'capture.json').read_text())
    run = json.loads((collection / 'run_metadata.json').read_text())
    rows = [json.loads(line) for line in (collection / 'step_timings.jsonl').read_text().splitlines()]
    subset = rows[warmup_steps:warmup_steps + measured_steps]
    if len(subset) != measured_steps:
        raise RuntimeError('measured transition count mismatch')
    if not capture.get('complete') or capture.get('steps') != warmup_steps + measured_steps:
        raise RuntimeError('incomplete collector or unexpected cleanup transition')
    for row in rows:
        if abs(row['next_observation_time_s'] - row['observation_time_s'] - .05) > 1e-6:
            raise RuntimeError('recorded policy cadence mismatch')
    return {'saved_transitions': len(rows), 'measured_transitions': len(subset),
            'cadence_20hz_verified': True,
            'environment_step_wall_s': stats([r['environment_step_wall_s'] for r in subset]),
            'dataset_write_wall_s': stats([r['dataset_write_wall_s'] for r in subset]),
            'reset_wall_s': run['reset_wall_s'],
            'collector_wall_s': capture['wall_s'],
            'idle_render_calls_total': capture['idle_render_calls'],
            'idle_render_wall_s_total': capture['idle_render_wall_s'],
            'idle_render_scope': 'all request-free intervals, not only the explicit idle window',
            'evaluation_enabled': capture['evaluation_enabled'],
            'hdf5_sha256': capture['files'], 'complete': capture['complete'],
            'full_capture_qc': 'not_run_by_benchmark'}


def run_condition(args, root, output, index, enabled, simulator_factory):
    name, command = command_for(args, index, enabled)
    directory = output / name
    directory.mkdir()
    collection = root / 'output/collections' / name
    if collection.exists():
        raise FileExistsError('collection output already exists')
    result = {'run_id': name, 'webrtc_enabled': enabled,
              'comparison': 'operational_flag' if args.viewport == 'native' else 'operational_flag_matched_viewport',
              'started_utc': utc(), 'status': 'running',
              'viewer_connection_status': 'unverified',
              'viewer_note': 'A listening port, GPU encoder activity or key heartbeat does not prove decoded video.',
              'command': command, 'chunks': []}
    save(directory / 'result.json', result)
    sim = None
    active = False
    started = time.perf_counter()
    with (directory / 'simulator.log').open('x') as log:
        try:
            sim = simulator_factory(command, root, log, timeout_s=args.response_timeout)
            ready = sim.receive()
            if ready.get('ready') is not True or ready.get('observation_step') != 0:
                raise RuntimeError('invalid initial collector response')
            result['startup_to_public_ready_wall_s'] = time.perf_counter() - started
            active = True
            obs = ready['observation']
            initial = float(obs['simulation_time_s'])
            result['simulation_time_at_ready_s'] = initial
            result['public_interface_sha256'] = hashlib.sha256(
                json.dumps(ready['public_interface'], sort_keys=True).encode()).hexdigest()
            print(f'{name}: ready, SDK={enabled}; viewer connection remains unverified', flush=True)
            save(directory / 'result.json', result)
            if args.connection_wait_seconds:
                obs, result['connection_wait'] = idle_measure(sim, obs, args.connection_wait_seconds)
            value, result['warmup_dispatch_wall_s'] = protocol_measure(
                sim, 'act', {'action': ZERO_ACTION, 'steps': args.warmup_steps})
            obs = value['observation']
            obs, result['explicit_idle_window'] = idle_measure(sim, obs, args.idle_seconds)
            for i in range(args.chunks):
                before = float(obs['simulation_time_s'])
                value, elapsed = protocol_measure(sim, 'act', {'action': ZERO_ACTION, 'steps': args.chunk_steps})
                if not value.get('active'):
                    raise RuntimeError('unexpected environment horizon')
                obs = value['observation']
                delta = float(obs['simulation_time_s']) - before
                if abs(delta - args.chunk_steps * .05) > 1e-6:
                    raise RuntimeError('action simulation clock mismatch')
                result['chunks'].append({'index': i, 'steps': args.chunk_steps,
                                         'simulation_delta_s': delta, 'dispatch_wall_s': elapsed})
                save(directory / 'result.json', result)
                print(f'{name}: measured chunk {i + 1}/{args.chunks}, {elapsed:.3f}s', flush=True)
            final, result['finish_dispatch_wall_s'] = protocol_measure(sim, 'finish_episode')
            active = False
            if not final.get('complete'):
                raise RuntimeError('collector did not complete')
            result['status'] = 'completed'
        except BaseException as exc:
            result['status'] = 'interrupted' if isinstance(exc, KeyboardInterrupt) else 'failed'
            result['error_type'] = type(exc).__name__
            raise
        finally:
            if sim:
                if active and sim.process.poll() is None:
                    try:
                        sim.dispatch('stop')
                        sim.dispatch('finish_episode')
                        result['cleanup_neutral_step'] = True
                    except Exception as exc:
                        result['cleanup_error_type'] = type(exc).__name__
                closed = time.perf_counter()
                try:
                    result['returncode'] = sim.close()
                except Exception as exc:
                    result['shutdown_error_type'] = type(exc).__name__
                    result['status'] = 'failed'
                result['shutdown_wall_s'] = time.perf_counter() - closed
            result['whole_process_wall_s'] = time.perf_counter() - started
            result['finished_utc'] = utc()
            save(directory / 'result.json', result)
    if result.get('returncode') != 0 or result['status'] != 'completed':
        raise RuntimeError('benchmark process did not exit cleanly; later conditions not started')
    try:
        result['saved'] = summarize_saved(collection, args.warmup_steps, args.chunk_steps * args.chunks)
        result['measured_dispatch_wall_s'] = stats([r['dispatch_wall_s'] for r in result['chunks']])
    except Exception as exc:
        result.update(status='failed', error_type=type(exc).__name__)
        save(directory / 'result.json', result)
        raise
    save(directory / 'result.json', result)
    return result


def main(argv=None):
    args = parse_args(argv)
    plan = {'schema': 'phyrc-stream-benchmark-v1', 'run_id': args.run_id,
            'comparison': 'operational_flag' if args.viewport == 'native' else 'operational_flag_matched_viewport',
            'sdk_only_isolated': False, 'fixed_initial_placement': True,
            'neutral_action': ZERO_ACTION, 'warmup_steps': args.warmup_steps,
            'measured_steps_per_process': args.chunk_steps * args.chunks,
            'idle_seconds': args.idle_seconds, 'order': ['off', 'on', 'on', 'off'],
            'gpu_execution_requested': args.execute,
            'gpu_executed': None if args.execute else False, 'model_calls': 0,
            'commands': [command_for(args, i, enabled)[1] for i, enabled in enumerate(ORDER)]}
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return 0
    if not os.environ.get('STRETCH4_STREAM_HOST'):
        raise SystemExit('Set the existing private STRETCH4_STREAM_HOST before execution.')
    output = ROOT / 'output/stream-benchmarks' / args.run_id
    output.mkdir(parents=True, exist_ok=False)
    output.chmod(0o775)
    plan['source_sha256'] = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in (
        'scripts/benchmark_streaming.py', 'scripts/collect_benchmark_viewport.py',
        'scripts/collect_operator.py', 'participant/streaming/collector_stream.py',
        'participant/collection/evaluation.py', 'src/PhyRC_Sim/Policy/environment.py',
        'src/PhyRC_Sim/Policy/sensors.py', 'config/policy_interface.json')}
    save(output / 'plan.json', plan)
    from participant.collection.codex_client import Simulator
    def interrupted(signum, frame):
        raise KeyboardInterrupt(signal.Signals(signum).name)
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    results = []
    try:
        for i, enabled in enumerate(ORDER):
            results.append(run_condition(args, ROOT, output, i, enabled, Simulator))
    finally:
        save(output / 'summary.json', {'run_id': args.run_id,
                                      'complete': len(results) == len(ORDER), 'conditions': results,
                                      'comparison': plan['comparison'], 'sdk_only_isolated': False,
                                      'viewer_connected_effect_measured': False,
                                      'note': 'Pairwise operational timings only; video client state is unverified.'})
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
