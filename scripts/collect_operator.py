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


def parse_request(line, *, current_step, seen):
    def reject_constant(_):
        raise ValueError()
    try:
        request = json.loads(line, parse_constant=reject_constant)
    except (ValueError, TypeError):
        raise ProtocolError('invalid_json') from None
    if not isinstance(request, dict) or set(request) - {'tool', 'arguments', 'request_id', 'observation_step'}:
        raise ProtocolError('invalid_request')
    tool = request.get('tool')
    if not isinstance(tool, str) or tool not in TOOLS:
        raise ProtocolError('unsupported_tool')
    arguments = request.get('arguments', {})
    if not isinstance(arguments, dict):
        raise ProtocolError('invalid_arguments')
    if tool != 'act' and arguments:
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
    p.add_argument('--preview', type=Path, help='Human observer HTML served by existing Jupyter')
    p.add_argument('--webrtc', action='store_true', help='Enable existing WebRTC viewer in observation-only mode')
    p.add_argument('--evaluate', action='store_true', help='Save official scoring only in trusted evaluation files')
    p.add_argument('--profile-step-phases', action='store_true',
                   help='Trusted numeric step/observation/capture wall timings; default off')
    p.add_argument('--reset-seed', type=int,
                   help='Trusted reset seed for a recorded-action continuation; never public actor input')
    args = p.parse_args(argv)
    if args.max_steps < 1 or args.max_requests < 1 or not math.isfinite(args.input_timeout) or args.input_timeout <= 0:
        p.error('limits must be positive and finite')
    if args.reset_seed is not None and not 0 <= args.reset_seed < 2**63:
        p.error('reset seed must be in 0..2**63-1')
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
    def encode(value):
        return value.tolist() if hasattr(value, 'tolist') else value
    def emit(value):
        print(json.dumps(value, default=encode, allow_nan=False), file=protocol, flush=True)
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
            env = DressingEnv(max_episode_steps=args.max_steps)
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
            def publish(obs):
                if preview and preview.due():
                    preview.write_frame(obs['rgb'][0], simulation_time=float(obs['simulation_time_s']))
            obs = operator.begin(seed=args.reset_seed)
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
                'raw_archive': False})
            if args.profile_step_phases:
                trace({'event': 'step_phase_profiling_enabled', 'schema_version': 1})
            publish(obs)
            emit({'ready': True, 'observation': obs, 'public_interface': interface, 'observation_step': 0})
            inbox = queue.Queue(maxsize=8)
            threading.Thread(target=read_requests, args=(sys.stdin, inbox, stop), daemon=True).start()
            last_request = time.perf_counter()
            reason = 'input_closed'
            while operator._active and not stop.is_set():
                now = time.perf_counter()
                if now - last_request >= args.input_timeout:
                    reason = 'input_timeout'
                    emit({'ok': False, 'error': reason})
                    break
                if request_count >= args.max_requests:
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
                    request = parse_request(payload, current_step=before_steps, seen=seen)
                except ProtocolError as exc:
                    code = str(exc)
                    trace({'event': 'request_rejected', 'error': code,
                           'input_sha256': hashlib.sha256(payload.encode()).hexdigest()})
                    emit({'ok': False, 'error': code})
                    continue
                if 'request_id' in request:
                    seen.add(request['request_id'])
                method, arguments = request['tool'], request.get('arguments', {})
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
                        if writer.failure_reason:
                            raise RuntimeError(writer.failure_reason)
                        if not operator._active:
                            break
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
                    operator.stop()
                    trace({'event': 'shutdown_neutral_step', 'end_step': operator._tick // 12})
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
