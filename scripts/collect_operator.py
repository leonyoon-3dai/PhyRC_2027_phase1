#!/usr/bin/env python3
"""Trusted JSON-lines collector with optional spectator streaming and scoring.

The actor protocol exposes only public observations and bounded actions. All
simulator diagnostics, score events and detailed errors remain in trusted files
or stderr. An isolated external actor must not mount this output directory.
"""
import argparse
import contextlib
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import signal
import sys
import threading
import time
import traceback

ROOT = Path('/project') if Path('/project/config').is_dir() else Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src/PhyRC_Sim')]
MAX_REQUEST_BYTES = 16384
MAX_PROMPT_BYTES = 256 * 1024
TOOLS = ('observe', 'act', 'stop', 'finish_episode')
SUPERVISOR_TOOLS = ('hold', 'resume', 'save_checkpoint')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,127}\Z')


class ProtocolError(ValueError):
    """Only fixed error codes from this class are returned to the actor."""


def isolate_simulator_arguments():
    """Keep collector options out of Kit's process-wide argument parser.

    Call only after argparse has retained the collector configuration in its
    Namespace. SimulationApp receives its official settings through config;
    prompts, paths and collection flags are not Kit startup options.
    """
    sys.argv[:] = sys.argv[:1]


def open_protocol_stream():
    """Keep the original stdout pipe for JSON; route native fd-1 logs to stderr.

    Python redirect_stdout alone cannot redirect Kit/C++ os.write(1) output.
    Duplicate before importing Isaac so no native bootstrap line enters JSON.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    protocol_fd = os.dup(1)
    os.dup2(2, 1)
    return os.fdopen(protocol_fd, 'w', encoding='utf-8', buffering=1)


def parse_request(line, *, current_step, seen, user_guided=False):
    def reject_constant(_):
        raise ValueError()
    try:
        request = json.loads(line, parse_constant=reject_constant)
    except (ValueError, TypeError):
        raise ProtocolError('invalid_json') from None
    if not isinstance(request, dict) or set(request) - {'tool', 'arguments', 'request_id', 'observation_step'}:
        raise ProtocolError('invalid_request')
    tool = request.get('tool')
    if not isinstance(tool, str) or tool not in TOOLS + (SUPERVISOR_TOOLS if user_guided else ()):
        raise ProtocolError('unsupported_tool')
    arguments = request.get('arguments', {})
    if not isinstance(arguments, dict):
        raise ProtocolError('invalid_arguments')
    if tool not in ('act', *SUPERVISOR_TOOLS) and arguments:
        raise ProtocolError('invalid_arguments')
    if tool in SUPERVISOR_TOOLS:
        required = {'hold_id', 'reason'} if tool == 'hold' else ({'hold_id'} if tool == 'resume' else {'key'})
        if set(arguments) != required:
            raise ProtocolError('invalid_arguments')
        identifier = arguments.get('key', arguments.get('hold_id'))
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier):
            raise ProtocolError('invalid_arguments')
        if tool == 'hold' and (not isinstance(arguments['reason'], str) or not 1 <= len(arguments['reason']) <= 512):
            raise ProtocolError('invalid_arguments')
    if tool == 'act':
        if set(arguments) - {'action', 'steps'} or 'action' not in arguments:
            raise ProtocolError('invalid_arguments')
        from participant.collection.boundary import validate_action
        try:
            validate_action(arguments['action'], arguments.get('steps', 1))
        except (ValueError, TypeError, OverflowError):
            raise ProtocolError('invalid_action') from None
    if 'observation_step' in request:
        step = request['observation_step']
        if type(step) is not int or step != current_step:
            raise ProtocolError('stale_observation')
    if 'request_id' in request:
        rid = request['request_id']
        if not isinstance(rid, str) or not 1 <= len(rid) <= 128:
            raise ProtocolError('invalid_request_id')
        if rid in seen:
            raise ProtocolError('duplicate_request')
    return request


def read_requests(stream, inbox, stop):
    """Only this daemon thread blocks on stdin; Isaac stays on the main thread."""
    def put(value):
        while not stop.is_set():
            try:
                inbox.put(value, timeout=.1)
                return
            except queue.Full:
                pass
    try:
        while not stop.is_set():
            line = stream.readline(MAX_REQUEST_BYTES + 1)
            if not line:
                put(('eof', None))
                return
            if len(line.encode('utf-8')) > MAX_REQUEST_BYTES:
                while line and not line.endswith('\n') and not stop.is_set():
                    line = stream.readline(MAX_REQUEST_BYTES + 1)
                put(('error', 'request_too_large'))
            else:
                put(('line', line))
    except Exception:
        put(('error', 'input_read_error'))
        put(('eof', None))


def parse_arguments(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--source', choices=['human', 'gpt', 'human_corrected_gpt', 'integration_test'], required=True)
    p.add_argument('--source-group', required=True)
    p.add_argument('--model-id', required=True)
    prompt = p.add_mutually_exclusive_group(required=True)
    prompt.add_argument('--prompt')
    prompt.add_argument('--prompt-file', type=Path,
                        help='Trusted UTF-8 prompt file, at most 256 KiB')
    p.add_argument('--max-steps', type=int, default=400)
    p.add_argument('--max-requests', type=int, default=10000)
    p.add_argument('--input-timeout', type=float, default=900,
                   help='Maximum wall seconds without a request; then neutral one step and close')
    p.add_argument('--segment-frame-dir', type=Path,
                   help='Write public five-camera panels for a local review run')
    p.add_argument('--preview', type=Path, help='Human observer HTML served by existing Jupyter')
    p.add_argument('--webrtc', action='store_true', help='Enable existing WebRTC viewer in observation-only mode')
    p.add_argument('--evaluate', action='store_true', help='Save official scoring only in trusted evaluation files')
    p.add_argument('--profile-step-phases', action='store_true',
                   help='Trusted numeric step/observation/capture wall timings; default off')
    p.add_argument('--reset-seed', type=int,
                   help='Trusted reset seed for practice or recorded-action continuation')
    p.add_argument('--nearest-table', action='store_true',
                   help='Start a new local collection on the positive-X central table with checkpoint-2 friction')
    p.add_argument('--user-guided', action='store_true',
                   help='Enable trusted hold/resume/checkpoint control; idle/EOF preserve live state')
    p.add_argument('--initial-slot', type=Path,
                   help='Trusted slot_NAME.npz approximate restore; default 90-tick settling is retained')
    p.add_argument('--checkpoint-dir', type=Path,
                   help='Trusted checkpoint output root (default OUTPUT/checkpoints)')
    args = p.parse_args(argv)
    if args.max_steps < 1 or args.max_requests < 1 or not math.isfinite(args.input_timeout) or args.input_timeout <= 0:
        p.error('limits must be positive and finite')
    if args.reset_seed is not None and not 0 <= args.reset_seed < 2**63:
        p.error('reset seed must be in 0..2**63-1')
    if args.segment_frame_dir and not args.user_guided:
        p.error('segment frames require user-guided collection')
    if args.initial_slot is not None and not args.initial_slot.is_file():
        p.error('--initial-slot must be an existing slot_NAME.npz file')
    if args.nearest_table and (args.initial_slot or os.environ.get('STRETCH4_LOAD_SLOT')):
        p.error('nearest-table collection starts from a fresh scene')
    if args.checkpoint_dir is not None and not args.user_guided:
        p.error('--checkpoint-dir requires --user-guided')
    if args.prompt_file is not None:
        try:
            with args.prompt_file.open('rb') as stream:
                data = stream.read(MAX_PROMPT_BYTES + 1)
            if len(data) > MAX_PROMPT_BYTES:
                p.error('--prompt-file exceeds 256 KiB')
            args.prompt = data.decode('utf-8')
        except (OSError, UnicodeDecodeError):
            p.error('--prompt-file must be a readable UTF-8 file')
    return args


def initial_slot_provenance(path):
    if path is None:
        return None
    path = Path(path)
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    receipt_path = path.parent / 'receipt.json'
    receipt = json.loads(receipt_path.read_text())
    return {'path': str(path), 'sha256': digest, 'exact_physics_checkpoint': False,
            'receipt_path': str(receipt_path),
            'receipt_sha256': hashlib.sha256(receipt_path.read_bytes()).hexdigest(),
            'source_group': receipt['source_group'], 'parent_run': receipt['run_id'],
            'reset_settle_control_ticks': 90, 'reset_settle_simulation_seconds': 1.5,
            'evaluation_restarts': True}


def main():
    args = parse_arguments()
    isolate_simulator_arguments()
    protocol = open_protocol_stream()
    stop = threading.Event()
    stop_reason = [None]
    def interrupted(signum, _frame):
        stop_reason[0] = 'signal_' + signal.Signals(signum).name.lower()
        stop.set()
    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    started = time.perf_counter()
    env = dataset = writer = operator = evaluator = stream = transcript = preview = None
    complete = False
    reason = 'initialization_failed'
    idle_render_s = idle_render_calls = 0
    seen = set()
    request_count = 0
    request_epoch = 0
    automatic_holds = 0
    protocol_failed = False
    def encode(value):
        return value.tolist() if hasattr(value, 'tolist') else value
    def emit(value):
        nonlocal protocol_failed
        if protocol_failed:
            return
        try:
            print(json.dumps(value, default=encode, allow_nan=False), file=protocol, flush=True)
        except (BrokenPipeError, OSError):
            if not args.user_guided:
                raise
            protocol_failed = True
    def trace(value):
        if transcript:
            transcript.write(json.dumps(dict(value, wall_elapsed_s=time.perf_counter() - started),
                                        default=encode, allow_nan=False) + '\n')
            transcript.flush()
    with contextlib.redirect_stdout(sys.stderr):
        try:
            if args.webrtc:
                from participant.streaming.collector_stream import CollectorStream
                stream = CollectorStream.from_environment()
                stream.install()
            from Policy.environment import DressingEnv
            from Policy.training_dataset import DatasetWriter
            from participant.collection.boundary import Operator
            from participant.collection.evaluation import (
                CollectionEvaluation, RecordedEnvironment, RecordedWriter, public_interface, write_json)
            from participant.streaming.collector_stream import render_without_physics
            env_config = {'max_episode_steps': args.max_steps}
            if args.initial_slot:
                from participant.collection.checkpoint import verify_checkpoint
                verify_checkpoint(args.initial_slot, source_group=args.source_group)
                env_config['initial_slot'] = args.initial_slot
                def record_slot_reset(phase, observation):
                    import numpy as np
                    from participant.collection.boundary import public_observation
                    destination = args.output / 'slot_reset'
                    destination.mkdir(exist_ok=True)
                    with (destination / (phase + '.npz')).open('xb') as handle:
                        np.savez_compressed(handle, **public_observation(observation))
                env_config['slot_reset_observer'] = record_slot_reset
            env = DressingEnv(**env_config)
            dataset = DatasetWriter(args.output, env.contract, {
                'recorder': 'participant-live-v2', 'raw_archive': False,
                'tick_basis': 'episode-relative', 'source': args.source,
                'source_group': args.source_group, 'evaluation_enabled': args.evaluate,
                'webrtc_mode': 'observer_only' if args.webrtc else 'disabled'})
            transcript = (args.output / 'operator.jsonl').open('x', encoding='utf-8')
            measured_env = RecordedEnvironment(env, profile_step_phases=args.profile_step_phases)
            if args.evaluate:
                evaluator = CollectionEvaluation(env, args.output / 'evaluation')
            writer = RecordedWriter(dataset, measured_env, evaluator)
            operator = Operator(measured_env, writer, source=args.source, source_group=args.source_group,
                                model_id=args.model_id, prompt=args.prompt)
            if args.preview:
                from participant.streaming.jupyter_observer import JupyterObserver
                preview = JupyterObserver(args.preview, run_label=args.output.name)
            if args.segment_frame_dir:
                from participant.collection.segment_frames import write_boundary
            def record_frame(obs):
                if args.segment_frame_dir:
                    write_boundary(args.segment_frame_dir, obs, operator._tick // 12)
            def publish(obs):
                if preview and preview.due():
                    preview.write_frame(obs['rgb'][0], simulation_time=float(obs['simulation_time_s']))
            fresh_profile = None
            reset_seed = args.reset_seed
            if args.nearest_table:
                from participant.collection.fresh_start import select_practice_reset, verify_reset
                fresh_profile = select_practice_reset(env.backend.garment_table_centers, env.M.BOX_SIZE,
                    (env.M.ROBOT1_SPAWN, env.M.ROBOT2_SPAWN), reset_seed)
                reset_seed = fresh_profile['episode_seed']
            obs = operator.begin(seed=reset_seed)
            if fresh_profile:
                fresh_profile = verify_reset(measured_env.reset_info, fresh_profile, env.stage)
            interface = public_interface(env, measured_env.reset_info)
            write_json(args.output / 'run_metadata.json', {
                'schema': 'participant-collection-run-v1', 'source': args.source,
                'source_group': args.source_group, 'model_id': args.model_id,
                'prompt_sha256': hashlib.sha256(args.prompt.encode()).hexdigest(),
                'code_commit': measured_env.reset_info.get('source_commit'),
                'source_sha256': measured_env.reset_info.get('source_sha256'),
                'max_steps': args.max_steps, 'max_requests': args.max_requests,
                'input_timeout_s': args.input_timeout, 'webrtc_observer_only': args.webrtc,
                'evaluation_enabled': args.evaluate, 'public_interface': interface,
                'reset_wall_s': measured_env.reset_wall_s,
                'simulation_time_at_ready_s': float(obs['simulation_time_s']),
                'raw_archive': False, 'user_guided': args.user_guided,
                **({'collection_start': fresh_profile, 'episode_seed': reset_seed} if fresh_profile else {}),
                'initial_slot': initial_slot_provenance(args.initial_slot)})
            if args.profile_step_phases:
                trace({'event': 'step_phase_profiling_enabled', 'schema_version': 1})
            publish(obs)
            record_frame(obs)
            emit({'ready': True, 'observation': obs, 'public_interface': interface, 'observation_step': 0})
            inbox = queue.Queue(maxsize=8)
            threading.Thread(target=read_requests, args=(sys.stdin, inbox, stop), daemon=True).start()
            last_request = time.perf_counter()
            reason = 'input_closed'
            def save_supervisor_state(reason):
                write_json(args.output / 'supervisor_state.json', {
                    'schema': 'phyrc-supervisor-state-v1', 'held': operator._hold_id is not None,
                    'hold_id': operator._hold_id, 'reason': reason, 'active': operator._active,
                    'observation_step': operator._tick // 12, 'episode_tick': operator._tick,
                    'simulation_time_s': float(operator._obs['simulation_time_s']),
                    'requests': request_count, 'protocol_connected': not protocol_failed})
            def automatic_hold(why):
                nonlocal automatic_holds
                if operator._hold_id is None:
                    automatic_holds += 1
                    operator.hold('collector-' + str(automatic_holds), why)
                    trace({'event': 'automatic_hold', 'reason': why, 'hold_id': operator._hold_id,
                           'observation_step': operator._tick // 12})
                    save_supervisor_state(why)
            while operator._active and not stop.is_set():
                now = time.perf_counter()
                if protocol_failed:
                    automatic_hold('protocol_closed')
                if operator._hold_id is None and now - last_request >= args.input_timeout:
                    if args.user_guided:
                        automatic_hold('input_timeout')
                        continue
                    reason = 'input_timeout'
                    emit({'ok': False, 'error': reason})
                    break
                if operator._hold_id is None and request_count - request_epoch >= args.max_requests:
                    if args.user_guided:
                        automatic_hold('request_limit')
                        continue
                    reason = 'request_limit'
                    emit({'ok': False, 'error': reason})
                    break
                try:
                    kind, payload = inbox.get(timeout=.05 if args.webrtc else .1)
                except queue.Empty:
                    if args.webrtc:
                        render_started = time.perf_counter()
                        render_without_physics(env, evaluator)
                        idle_render_s += time.perf_counter() - render_started
                        idle_render_calls += 1
                    continue
                if kind == 'eof':
                    if args.user_guided:
                        automatic_hold('input_closed')
                        save_supervisor_state('input_closed')
                        continue
                    break
                request_count += 1
                waited = time.perf_counter() - last_request
                last_request = time.perf_counter()
                if kind == 'error':
                    trace({'event': 'request_rejected', 'error': payload})
                    emit({'ok': False, 'error': payload})
                    continue
                before_steps = operator._tick // 12
                try:
                    request = parse_request(payload, current_step=before_steps, seen=seen, user_guided=args.user_guided)
                except ProtocolError as exc:
                    code = str(exc)
                    trace({'event': 'request_rejected', 'error': code,
                           'input_sha256': hashlib.sha256(payload.encode()).hexdigest()})
                    emit({'ok': False, 'error': code})
                    continue
                if 'request_id' in request:
                    seen.add(request['request_id'])
                method, arguments = request['tool'], request.get('arguments', {})
                rejection = None
                if operator._hold_id is not None and method in ('act', 'stop'):
                    rejection = 'episode_held'
                elif method == 'resume' and operator._hold_id != arguments['hold_id']:
                    rejection = 'stale_hold'
                elif method == 'hold' and operator._hold_id not in (None, arguments['hold_id']):
                    rejection = 'different_hold_active'
                elif method == 'save_checkpoint' and operator._hold_id is None:
                    rejection = 'checkpoint_requires_hold'
                if rejection:
                    trace({'event': 'request_rejected', 'error': rejection})
                    emit({'ok': False, 'error': rejection, 'request_id': request.get('request_id')})
                    continue
                command_started = time.perf_counter()
                trace({'event': 'request_accepted', 'request': request, 'observation_step': before_steps,
                       'request_wait_wall_s': waited})
                if method == 'act':
                    result = {'active': operator._active, 'observation': operator.observe()}
                    for _ in range(arguments.get('steps', 1)):
                        if stop.is_set():
                            break
                        result = operator.act(arguments['action'], 1)
                        publish(result['observation'])
                        record_frame(result['observation'])
                        if writer.failure_reason:
                            raise RuntimeError(writer.failure_reason)
                        if not operator._active:
                            break
                elif method == 'hold':
                    result = operator.hold(**arguments)
                    save_supervisor_state(arguments['reason'])
                elif method == 'resume':
                    result = operator.resume(**arguments)
                    request_epoch = request_count
                    save_supervisor_state('user_resumed')
                elif method == 'save_checkpoint':
                    from participant.collection.checkpoint import save_checkpoint
                    try:
                        checkpoint = save_checkpoint(env, operator, args.checkpoint_dir or args.output / 'checkpoints',
                                                     arguments['key'], run_id=args.output.name,
                                                     source_group=args.source_group)
                    except (FileExistsError, ValueError) as exc:
                        trace({'event': 'checkpoint_rejected', 'error': type(exc).__name__})
                        emit({'ok': False, 'error': 'checkpoint_rejected', 'request_id': request.get('request_id')})
                        continue
                    result = {'active': True, 'held': True, 'checkpoint': checkpoint}
                else:
                    result = getattr(operator, method)()
                    if method == 'observe':
                        publish(result)
                    elif 'observation' in result:
                        publish(result['observation'])
                trace({'event': 'request_finished', 'tool': method,
                       'request_id': request.get('request_id'),
                       'executed_steps': operator._tick // 12 - before_steps,
                       'end_step': operator._tick // 12,
                       'execution_wall_s': time.perf_counter() - command_started,
                       'interrupted': stop.is_set()})
                if stop.is_set():
                    break
                emit({'ok': True, 'result': result, 'observation_step': operator._tick // 12,
                      'request_id': request.get('request_id')})
                if method == 'finish_episode' or not operator._active:
                    reason = 'operator_finished' if method == 'finish_episode' else 'environment_horizon'
                    complete = bool(result.get('complete', operator._tick > 0))
                    break
                # Idle timeout concerns waiting for the NEXT request, not the last action's runtime.
                last_request = time.perf_counter()
            reason = stop_reason[0] or reason
        except (BrokenPipeError, KeyboardInterrupt):
            reason = stop_reason[0] or 'protocol_closed'
        except BaseException:
            reason = 'collector_error'
            traceback.print_exc(file=sys.stderr)
            if writer and not writer.failure_reason:
                writer.failure_reason = reason
            try:
                emit({'ok': False, 'error': 'collector_error'})
            except (BrokenPipeError, OSError):
                pass
        finally:
            stop.set()
            if operator and operator._active:
                try:
                    # One recorded neutral policy step preserves gripper intent.
                    # Applies on EOF, model timeout and interruption, never by teleport.
                    if operator._hold_id is None:
                        operator.stop()
                        trace({'event': 'shutdown_neutral_step', 'end_step': operator._tick // 12})
                    else:
                        trace({'event': 'held_shutdown_without_motion', 'end_step': operator._tick // 12})
                except Exception:
                    traceback.print_exc(file=sys.stderr)
                    if writer:
                        writer.failure_reason = 'shutdown_step_failed'
                try:
                    operator.finish_episode(reason)
                except Exception:
                    complete = False
                    traceback.print_exc(file=sys.stderr)
            if evaluator and evaluator.active:
                try:
                    evaluator.finish(reason, valid=False)
                except Exception:
                    traceback.print_exc(file=sys.stderr)
            if writer:
                try:
                    writer.close(complete=complete)
                except Exception:
                    complete = False
                    traceback.print_exc(file=sys.stderr)
            elif dataset:
                dataset.close(complete=False)
            if transcript:
                trace({'event': 'collection_finished', 'reason': reason, 'complete': complete,
                       'steps': operator._tick // 12 if operator else 0})
                transcript.close()
            if dataset:
                manifest = {'schema': 'participant-live-capture-v2', 'complete': complete,
                            'termination_reason': reason, 'raw_archive': False,
                            'deferred_export_check': False, 'wall_s': time.perf_counter() - started,
                            'requests': request_count, 'steps': operator._tick // 12 if operator else 0,
                            'idle_render_calls': idle_render_calls, 'idle_render_wall_s': idle_render_s,
                            'evaluation_enabled': args.evaluate,
                            'evaluation_valid': (writer.result or {}).get('valid') if writer else None,
                            'files': {}}
                for path in sorted(args.output.glob('*.hdf5')):
                    with path.open('rb') as handle:
                        manifest['files'][path.name] = hashlib.file_digest(handle, 'sha256').hexdigest()
                (args.output / 'capture.json').write_text(json.dumps(manifest, indent=2) + '\n')
            if preview:
                try:
                    preview.finish(error=not complete)
                except Exception:
                    traceback.print_exc(file=sys.stderr)
            if stream:
                stream.close()
            if env:
                env.close()
    return 0 if complete else 1


if __name__ == '__main__':
    raise SystemExit(main())
