"""Codex CLI collection orchestrator; the actor receives only public observations.

Run from the repository root with ``python -m participant.collection.codex_client``.
This trusted process owns simulator/evaluation files. The separate actor container
never mounts this repository, trace directory, or the simulator output directory.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import shutil
import signal
import subprocess
import threading
import time

import numpy as np
from PIL import Image

from participant.collection.boundary import CONTRACT, PUBLIC, validate_action


STAGES = ['preparation', 'approach', 'grasp', 'lift', 'transport', 'first_sleeve',
          'shoulder', 'second_sleeve', 'neck', 'orientation', 'recovery', 'final_check']
ASSESSMENTS = ['uncertain', 'progressing', 'blocked', 'recovering', 'visually_complete']
SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['tool', 'action', 'steps', 'stage', 'visual_assessment', 'reason'],
    'properties': {
        'tool': {'type': 'string', 'enum': ['act', 'stop', 'finish_episode']},
        'action': {'type': 'array', 'minItems': 2, 'maxItems': 2,
                   'items': {'type': 'array', 'minItems': 9, 'maxItems': 9,
                             'items': {'type': 'number', 'minimum': -1, 'maximum': 1}}},
        'steps': {'type': 'integer', 'minimum': 1, 'maximum': 20},
        'stage': {'type': 'string', 'enum': STAGES},
        'visual_assessment': {'type': 'string', 'enum': ASSESSMENTS},
        'reason': {'type': 'string'},
    },
}
TASK = '''Operate two Stretch 4 robots to pick up a T-shirt cooperatively and dress the seated mannequin. Work toward a continuous complete dressing demonstration: thread both arms into the sleeves, seat the shirt over shoulders and upper arms, pass the head through the neck opening, and orient the front correctly. Use only the supplied designated RGB/depth observations and public robot state. You have no access to hidden garment/object state or evaluation results. Infer object positions visually; distinguish visual hypotheses from facts. Stage and visual_assessment describe your intended phase and visual judgement, never official score or success.

Return exactly one decision matching the schema. Each action has two rows in robot order 0,1; each row is [base_forward, base_left, base_CCW_yaw, lift, arm_extension, wrist_yaw, wrist_pitch, wrist_roll, gripper]. The first 8 are normalized VELOCITIES in [-1,1], not positions or deltas. Use the supplied static action scales to interpret them. Base axes are robot-local: +X forward,+Y left,+Z up. Gripper >0.5 closes, <-0.5 opens; zero holds previous intent. A stop applies neutral motion for one control step and preserves grip intent. One step is 0.05 simulation seconds; at most 20 steps per decision. Use shorter steps near contact, observe the result, and correct. Both robots act simultaneously. The world is paused while you reason, so repeated action is not applied during model latency.

Use all designated camera views and public robot localization to identify which gripper is where. Do not treat fingertip_origin_distance as the inner contact gap. Do not assume a close command attached cloth; confirm motion in subsequent images. Coordinate support while approaching and threading sleeves; recover visibly failed grasps before transporting. Keep useful grips until the task is visually complete. Never request scene edits, hidden state, arbitrary simulator code, or evaluator feedback. You may plan using permitted observations and remember earlier observations and your decisions within this episode. Finish when visually complete or when continuing the current episode is unproductive; state the visual reason. Zero action and steps=1 are required for stop and finish_episode. Give a brief operational reason, not a claim of measured success.'''
WIRING_TASK = '''This is a short collection wiring test, not a dressing demonstration. On decision 0 request a small lift velocity of +0.03 for both robots and gripper -1, for 2 steps. On decision 1 request stop. On decision 2 finish_episode. All other velocity values must be zero. Use the same action contract and schema. Do not attempt grasp or dressing; label stage preparation and visual_assessment uncertain.'''


def dump(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def source_snapshot(root, trace):
    paths = [root / 'run.sh', root / 'scripts/collect_operator.py',
             root / 'participant/streaming/collector_stream.py',
             root / 'config/policy_interface.json', root / 'config/assets.lock.json']
    paths += sorted((root / 'participant/collection').glob('*.py'))
    hashes = {}
    for path in paths:
        relative = path.relative_to(root)
        target = trace / 'source_snapshot' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        hashes[str(relative)] = hashlib.sha256(target.read_bytes()).hexdigest()
    return {'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
            'working_tree_modified': bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=root, text=True).strip()),
            'files_sha256': hashes}


def validate_decision(value, *, wiring=False):
    if not isinstance(value, dict) or set(value) != set(SCHEMA['required']):
        raise ValueError('decision fields do not match schema')
    if value['tool'] not in SCHEMA['properties']['tool']['enum']:
        raise ValueError('unsupported tool')
    if value['stage'] not in STAGES or value['visual_assessment'] not in ASSESSMENTS:
        raise ValueError('unknown stage or visual assessment')
    if not isinstance(value['reason'], str) or not 1 <= len(value['reason']) <= 8000:
        raise ValueError('reason must be a nonempty bounded string')
    # Reject JSON bools even when mixed into an otherwise numeric action.
    a = value['action']
    if not isinstance(a, list) or any(not isinstance(row, list) for row in a):
        raise ValueError('action must be a JSON array of arrays')
    if any(type(x) not in (int, float) for row in a for x in row):
        raise ValueError('action entries must be numbers')
    action = validate_action(a, value['steps'])
    if value['tool'] != 'act' and (action.any() or value['steps'] != 1):
        raise ValueError('stop/finish require zeros and one step')
    if wiring and (np.any(abs(action[:, :8]) > .05) or value['steps'] > 2):
        raise ValueError('wiring test exceeds motion/step limit')
    return action


def public_interface(value):
    """Only explicitly allowed, static interpretation metadata enters actor input."""
    allowed = ('action_scales', 'joint_names', 'joint_units', 'camera_intrinsics')
    result = {k: value[k] for k in allowed if k in value}
    if 'camera_calibration' in value:
        static_fields = ('id', 'resolution_wh', 'intrinsics', 'clip_m', 'mount_role',
                         'eye_mount_m', 'target_mount_m', 'up_mount')
        result['camera_calibration'] = [{k: c[k] for k in static_fields if k in c}
                                        for c in value['camera_calibration']]
    return result


def prepare_observation(obs, directory):
    """Five exact RGB images, public state, and spatially indexed depth medians.

    Full public depth and mask are retained in the public workspace as NPZ for
    reproducibility. No arbitrary incoming metadata is serialized.
    """
    directory.mkdir(parents=True, exist_ok=False)
    if set(PUBLIC) - set(obs):
        raise ValueError('missing public observation fields')
    state = {}
    for key in PUBLIC:
        if key in ('rgb', 'depth', 'depth_valid'):
            continue
        a = np.asarray(obs[key])
        if not np.isfinite(a).all():
            raise ValueError('non-finite public state')
        state[key] = a.tolist()
    rgb = np.asarray(obs['rgb'])
    if rgb.shape != (5, 256, 256, 3) or rgb.dtype.kind not in 'iu' or rgb.min() < 0 or rgb.max() > 255:
        raise ValueError('unexpected public RGB images')
    depth = np.asarray(obs['depth'], dtype=np.float32)
    valid = np.asarray(obs['depth_valid'], dtype=bool)
    if depth.shape != (5, 256, 256, 1) or valid.shape != depth.shape:
        raise ValueError('unexpected public depth images')
    if not np.isfinite(depth).all() or np.any(depth < 0):
        raise ValueError('invalid depth values')
    images, depth_grids = [], {}
    for i, name in enumerate(CONTRACT['competition_access']['allowed_cameras']):
        image = directory / (name + '.png')
        Image.fromarray(rgb[i].astype(np.uint8)).save(image)
        images.append(image)
        grid = []
        for y in range(0, 256, 16):
            row = []
            for x in range(0, 256, 16):
                cells = depth[i, y:y+16, x:x+16, 0]
                mask = valid[i, y:y+16, x:x+16, 0] & (cells > 0)
                row.append(round(float(np.median(cells[mask])), 3) if mask.any() else None)
            grid.append(row)
        depth_grids[name] = grid
    payload = {
        'public_robot_observation': state,
        'rgb_image_order': CONTRACT['competition_access']['allowed_cameras'],
        'depth_16x16_grid_m': depth_grids,
        'depth_interpretation': 'Each entry is median valid optical-axis Z in a 16x16 pixel tile of the matching 256x256 RGB view; row top-to-bottom, column left-to-right. null means no valid positive depth. This grid is a lossy summary, not an object pose.',
    }
    dump(directory / 'observation.json', payload)
    np.savez_compressed(directory / 'public_depth.npz', depth=depth, depth_valid=valid)
    return payload, images


class Simulator:
    """Timeout-bounded transport; stdout contains public JSON, logs stay private."""
    def __init__(self, command, root, log, *, timeout_s=600):
        env = {k: v for k, v in os.environ.items()
               if k not in ('OPENAI_API_KEY', 'HF_TOKEN', 'GH_TOKEN', 'GITHUB_TOKEN')}
        env['STRETCH4_OPERATOR_STDIN'] = '1'
        self.process = subprocess.Popen(command, cwd=root, env=env, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=log, text=True, bufsize=1)
        self.timeout_s = timeout_s
        self.log = log
        self.observation_step = 0
        self.request_sequence = 0
        self.lines = queue.Queue(maxsize=2)
        self.closing = threading.Event()
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        def enqueue(value):
            while not self.closing.is_set():
                try:
                    self.lines.put(value, timeout=.1)
                    return
                except queue.Full:
                    pass
        try:
            for line in self.process.stdout:
                if len(line) > 64_000_000:
                    enqueue(ValueError('oversized simulator response'))
                    self.closing.set()
                    continue
                # Drain native output even after a failed receive. Otherwise a
                # full stdout pipe can prevent the recorder from saving/exiting.
                enqueue(line)
        finally:
            enqueue(None)

    def receive(self):
        try:
            line = self.lines.get(timeout=self.timeout_s)
        except queue.Empty:
            raise TimeoutError('simulator response timeout; inspect private log') from None
        if isinstance(line, Exception):
            raise line
        if line is None:
            raise RuntimeError('simulator closed; inspect private log')
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            self.log.write('\n[collector protocol: non-JSON stdout]\n' + line)
            self.log.flush()
            raise ValueError('non-JSON simulator output; inspect private simulator.log') from None
        if value.get('ok') is False:
            raise ValueError('simulator rejected request: ' + str(value.get('error')))
        if 'observation_step' in value:
            self.observation_step = value['observation_step']
        return value

    def dispatch(self, tool, arguments=None):
        request_id = str(self.request_sequence)
        self.request_sequence += 1
        self.process.stdin.write(json.dumps({'tool': tool, 'arguments': arguments or {},
                                            'request_id': request_id,
                                            'observation_step': self.observation_step}, allow_nan=False) + '\n')
        self.process.stdin.flush()
        response = self.receive()
        if response.get('request_id') != request_id:
            raise ValueError('simulator response does not match request')
        return response.get('result', {})

    def close(self):
        self.closing.set()
        self.process.stdin.close()
        try:
            code = self.process.wait(timeout=180)
            self.reader.join(timeout=5)
            if not self.reader.is_alive():
                self.process.stdout.close()
            return code
        except subprocess.TimeoutExpired:
            # Do not destroy an unflushed GPU recorder. Record the failure and
            # leave its PID for the trusted operator to inspect and stop.
            raise TimeoutError(f'simulator shutdown timeout; PID {self.process.pid}') from None


def main():
    def interrupted(signum, _frame):
        raise KeyboardInterrupt(signal.Signals(signum).name)
    signal.signal(signal.SIGTERM, interrupted)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--parent-attempt')
    parser.add_argument('--retry-reason')
    parser.add_argument('--source-group')
    parser.add_argument('--mode', choices=['wiring', 'dressing'], default='wiring')
    parser.add_argument('--model', default='gpt-6-astra')
    parser.add_argument('--effort', default='ultra')
    parser.add_argument('--decisions', type=int, default=3)
    parser.add_argument('--max-steps', type=int, default=2400)
    parser.add_argument('--model-timeout', type=float, default=600)
    parser.add_argument('--webrtc', action='store_true')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_.-]{0,119}', args.run_id):
        parser.error('run-id must be a safe unique name')
    if not 1 <= args.decisions <= 2000 or not 1 <= args.max_steps <= 18000:
        parser.error('decision/step budget out of range')
    if not math.isfinite(args.model_timeout) or not 10 <= args.model_timeout <= 1800:
        parser.error('model timeout must be finite, 10..1800 seconds')
    if bool(args.parent_attempt) != bool(args.retry_reason):
        parser.error('parent-attempt and retry-reason must be supplied together')
    root = Path(__file__).resolve().parents[2]
    trace = root / 'output/operator-traces' / args.run_id
    actor_root = root / 'output/actors' / args.run_id
    trace.mkdir(parents=True, exist_ok=False)
    actor_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    task = TASK + ('\n\n' + WIRING_TASK if args.mode == 'wiring' else '')
    from participant.collection.codex_actor import Actor
    source = 'integration_test' if args.mode == 'wiring' else 'gpt'
    command = ['./run.sh', 'python', '-X', 'faulthandler', '/scripts/collect_operator.py', '--output',
               '/output/collections/' + args.run_id, '--source', source,
               '--source-group', args.source_group or args.run_id, '--model-id', args.model,
               '--prompt-file', '/output/operator-traces/' + args.run_id + '/prompt.txt',
               '--max-steps', str(args.max_steps), '--evaluate',
               '--input-timeout', str(args.model_timeout + 120)]
    if args.webrtc:
        command += ['--webrtc']
    started = time.monotonic()
    manifest = {
        'schema': 'phyrc-codex-attempt-v1', 'run_id': args.run_id,
        'parent_attempt': args.parent_attempt, 'retry_reason': args.retry_reason,
        'source_group': args.source_group or args.run_id, 'source': source,
        'model': args.model, 'reasoning_effort': args.effort,
        'prompt_sha256': hashlib.sha256(task.encode()).hexdigest(),
        'mode': args.mode, 'decisions_requested': args.decisions, 'decisions_completed': 0,
        'actor_calls_attempted': 0, 'actor_usage': {},
        'finished': False, 'status': 'starting', 'error': None,
        'started_at_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'actor_call_wall_s': 0.0, 'model_internal_inference_wall_s': None,
        'actor_call_timing_scope': 'public staging + Docker/CLI startup + request/response; internal model time unavailable',
        'environment_dispatch_wall_s': 0.0,
        'official_evaluation': 'separate collector output; never actor input',
        'input_profile': 'five_public_RGB_images_all_public_state_and_16x16_depth_medians',
        'simulation_steps': 0, 'human_intervention': False,
        'quality_status': 'unreviewed',
    }
    manifest['source_snapshot'] = source_snapshot(root, trace)
    dump(trace / 'attempt.json', manifest)
    (trace / 'prompt.txt').write_text(task)
    sim, actor, finished, active = None, None, False, False
    with (trace / 'simulator.log').open('x') as log, (trace / 'decisions.jsonl').open('x') as events:
        def event(value):
            events.write(json.dumps(value, allow_nan=False) + '\n')
            events.flush()
        try:
            sim = Simulator(command, root, log)
            manifest['simulator_pid'] = sim.process.pid
            ready = sim.receive()
            if ready.get('ready') is not True:
                raise ValueError('simulator did not become ready')
            obs, active = ready['observation'], True
            interface = public_interface(ready.get('public_interface', {}))
            actor = Actor(actor_root / 'runtime', model=args.model, effort=args.effort, timeout_s=args.model_timeout)
            manifest['status'] = 'collecting'
            for index in range(args.decisions):
                payload, images = prepare_observation(obs, actor_root / 'observations' / f'{index:05d}')
                prompt = (task if index == 0 else 'Continue the same episode using the latest public observation.\n')
                prompt += '\nDecision index: ' + str(index) + '\n'
                if index == 0:
                    prompt += 'Public static interpretation metadata: ' + json.dumps(interface, allow_nan=False) + '\n'
                prompt += json.dumps(payload, allow_nan=False)
                image_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in images]
                input_hash = hashlib.sha256((prompt + json.dumps(image_hashes)).encode()).hexdigest()
                call_started = time.monotonic()
                manifest['actor_calls_attempted'] += 1
                result = None
                try:
                    result = actor.invoke(prompt, images, SCHEMA)
                    decision = result['decision']
                    action = validate_decision(decision, wiring=args.mode == 'wiring')
                except BaseException as exc:
                    call_wall_s = time.monotonic() - call_started
                    manifest['actor_call_wall_s'] += call_wall_s
                    event({'type': 'model_error', 'decision_index': index, 'input_sha256': input_hash,
                           'error_type': type(exc).__name__, 'error': str(exc),
                           'actor_call_wall_s': call_wall_s, 'returned_result': result})
                    raise
                event({'type': 'decision', 'decision_index': index, 'input_sha256': input_hash,
                       'observation_simulation_time_s': float(obs['simulation_time_s']), **result})
                manifest['actor_call_wall_s'] += float(result['wall_s'])
                for key, count in result['usage'].items():
                    manifest['actor_usage'][key] = manifest['actor_usage'].get(key, 0) + count
                t = time.monotonic()
                tool = decision['tool']
                before = float(obs['simulation_time_s'])
                value = sim.dispatch(tool, {'action': action.tolist(), 'steps': decision['steps']} if tool == 'act' else None)
                elapsed = time.monotonic() - t
                manifest['environment_dispatch_wall_s'] += elapsed
                if tool == 'finish_episode':
                    finished, active = True, False
                else:
                    obs = value['observation']
                    active = value.get('active', True)
                    finished = not active
                after = float(obs['simulation_time_s'])
                steps = round((after - before) * 20)
                manifest['simulation_steps'] += steps
                manifest['decisions_completed'] += 1
                event({'type': 'applied_segment', 'segment_id': f'{args.run_id}:{index:05d}',
                       'decision_index': index, 'start_step': manifest['simulation_steps'] - steps,
                       'end_step': manifest['simulation_steps'], 'simulation_start_s': before,
                       'simulation_end_s': after, 'environment_dispatch_wall_s': elapsed,
                       'stage_intent': decision['stage'], 'visual_assessment': decision['visual_assessment'],
                       'assessment_source': 'actor_public_observations', 'official_score': None,
                       'requested_steps': decision['steps'] if tool == 'act' else (1 if tool == 'stop' else 0),
                       'applied_action': action.tolist() if tool == 'act' else np.zeros((2, 9)).tolist(),
                       'actual_steps': steps, 'quality_status': 'unreviewed'})
                dump(trace / 'attempt.json', manifest)
                print(json.dumps({'run_id': args.run_id, 'decision': index, 'stage': decision['stage'],
                                  'tool': tool, 'sim_s': after, 'actor_call_wall_s': result['wall_s']}), flush=True)
                if finished:
                    break
            if active:
                stopped = sim.dispatch('stop')
                manifest['simulation_steps'] += 1
                if stopped.get('active', True):
                    sim.dispatch('finish_episode')
                event({'type': 'supervisor_stop', 'reason': 'decision_budget', 'neutral_steps': 1})
                finished, active = True, False
            manifest['status'] = 'completed'
        except BaseException as exc:
            manifest['status'] = 'interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'failed'
            manifest['error'] = {'type': type(exc).__name__, 'message': str(exc)}
            raise
        finally:
            if sim is not None:
                if active and sim.process.poll() is None:
                    try:
                        stopped = sim.dispatch('stop')
                        manifest['simulation_steps'] += 1
                        if stopped.get('active', True):
                            sim.dispatch('finish_episode')
                        event({'type': 'supervisor_stop', 'reason': manifest['status'], 'neutral_steps': 1})
                        finished, active = True, False
                    except Exception as exc:
                        manifest['shutdown_error'] = str(exc)
                try:
                    manifest['simulator_returncode'] = sim.close()
                except Exception as exc:
                    manifest['shutdown_error'] = str(exc)
            if actor is not None:
                try:
                    actor.close()
                except Exception as exc:
                    manifest['actor_cleanup_error'] = str(exc)
            manifest['finished'] = finished
            manifest['acknowledged_simulation_steps'] = manifest['simulation_steps']
            capture_path = root / 'output/collections' / args.run_id / 'capture.json'
            manifest['recorded_simulation_steps'] = None
            if capture_path.is_file():
                try:
                    capture = json.loads(capture_path.read_text())
                    manifest['capture_complete'] = capture['complete']
                    manifest['capture_termination_reason'] = capture.get('termination_reason')
                    manifest['recorded_simulation_steps'] = capture['steps']
                    manifest['simulation_steps'] = capture['steps']
                except (ValueError, KeyError, OSError) as exc:
                    manifest['capture_metadata_error'] = str(exc)
            if manifest.get('simulator_returncode') not in (None, 0) or 'shutdown_error' in manifest:
                manifest['status'] = 'failed'
            manifest['wall_s'] = time.monotonic() - started
            manifest['simulation_time_s'] = manifest['simulation_steps'] / 20
            manifest['ended_at_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
            dump(trace / 'attempt.json', manifest)
    if manifest.get('simulator_returncode') != 0:
        raise RuntimeError('collector did not exit successfully; inspect attempt record')


if __name__ == '__main__':
    main()
