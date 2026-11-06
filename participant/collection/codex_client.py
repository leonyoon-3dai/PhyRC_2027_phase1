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
PICKUP_TASK = '''For THIS episode, limit the objective to a stable garment pickup. Do not proceed to dressing the mannequin. Approach and grasp using public observations, test whether the cloth follows the gripper, and when visually supported raise and hold it. The published pickup criterion requires the grasped region to rise at least 5 cm from its grasp location with the same gripper and remain raised for 3 simulation seconds. This is task guidance, not feedback that a grasp or score exists. Model waiting does not advance simulation time. Use the public simulation clock and observed cloth motion. Finish after a visually stable hold or when the episode is unproductive. Official evaluation remains outside your inputs.'''
COORDINATED_TASK = '''This episode prioritizes a TWO-ROBOT cooperative dressing demonstration. The operator specifically requires both robots to approach the garment before lifting it; a one-robot pickup while the other robot stays behind is not the intended demonstration.

Coordinate these prerequisites using only CURRENT designated views and public robot state:
1. Bring BOTH robots to useful, noninterfering positions near the garment. Identify safe routes and reachable edges from the images. Move both robots in the same action when their routes are visibly clear; do not leave one idle while the other completes the pickup. One may wait briefly when collision avoidance or alignment requires it. Adjusting an empty gripper's height is allowed.
2. Keep the garment supported on the table while aligning both open grippers at separated accessible edge regions. Both robots must be near the garment and ready before starting to lift the cloth. Do not move an unsupported one-hand-held garment away while the partner is still approaching.
3. Close and settle both grasps, then use a SHORT coordinated lift test. In subsequent current views, check separately whether cloth follows EACH gripper. A close command or raised gripper alone is not grasp evidence. If either side is uncertain or slips, lower/support the cloth and recover the missing grasp before transport. Do not substitute a long one-robot hold for this cooperative test.
4. Once both sides are visibly supported, lift together, preserve a useful opening without excessive stretch, and coordinate transport and dressing. Infer all targets and geometry from current observations, never from a memorized scene layout. Continue toward full dressing, not just pickup.

For collection efficiency, use simultaneous two-robot commands and reasonably long bounded segments for clearly unobstructed positioning. Group predictable segments only when no new contact observation is needed; near cloth/contact, use one short segment and inspect the result. Your brief reason should state the current role/readiness of robot 0 and robot 1, then the action purpose. These are visual hypotheses and intentions, not official success labels.'''


def official_review_points(collection):
    """Trusted termination only. Never include this value in actor observations."""
    paths = list((Path(collection) / 'evaluation').glob('*/score_samples.jsonl'))
    if len(paths) != 1:
        raise ValueError('expected one official score stream for review gate')
    lines = paths[0].read_text().splitlines()
    if not lines:
        raise ValueError('official score stream is empty')
    value = json.loads(lines[-1])['raw_points']
    if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 50:
        raise ValueError('invalid official review points')
    return value


USAGE_FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens')


class TokenUsageAccounting:
    """CLI 0.166.0 usage is cumulative within a thread, including exec resume.

    This client creates a fresh per-attempt CODEX_HOME: each newly encountered
    thread has a zero baseline. Importing a pre-existing thread would require
    supplying its pre-attempt baseline instead. Only usage counters are read;
    private session identifiers are used as in-memory keys, never in reports.
    """
    def __init__(self):
        self.totals = {}
        self._threads = {}
        self._calls = {}

    def record(self, decision_index, result, *, call_failed=False):
        if decision_index in self._calls:
            raise ValueError('usage already recorded for this decision')
        record = {'decision_index': decision_index, 'call_failed': call_failed,
                  'scope': 'thread_cumulative', 'thread_index': None,
                  'cumulative_usage': None, 'incremental_usage': None,
                  'usage_known': False, 'status': 'unavailable'}
        self._calls[decision_index] = record
        if not isinstance(result, dict):
            return record
        thread_id, raw = result.get('session_id'), result.get('usage')
        if not isinstance(thread_id, str) or not thread_id:
            record['status'] = 'missing_thread'
            return record
        thread = self._threads.setdefault(thread_id, {
            'thread_index': len(self._threads), 'baseline': 'fresh_attempt_thread_zero',
            'last_observed_cumulative_usage': None, 'last_accepted_cumulative_usage': None,
        })
        record['thread_index'] = thread['thread_index']
        if (not isinstance(raw, dict) or any(
                type(raw.get(key)) is not int or raw[key] < 0 for key in USAGE_FIELDS)):
            record['status'] = 'invalid_usage'
            return record
        cumulative = {key: raw[key] for key in USAGE_FIELDS}
        record['cumulative_usage'] = cumulative
        thread['last_observed_cumulative_usage'] = cumulative
        if (cumulative['cached_input_tokens'] > cumulative['input_tokens']
                or cumulative['reasoning_output_tokens'] > cumulative['output_tokens']):
            record['status'] = 'invalid_usage'
            return record
        previous = thread['last_accepted_cumulative_usage']
        if previous is not None and any(cumulative[k] < previous[k] for k in USAGE_FIELDS):
            # A lower counter is not a new thread or a negative token charge.
            # Preserve the snapshot, retain the last accepted baseline, and
            # leave this call unresolved even if a later snapshot recovers.
            record['status'] = 'counter_regressed'
            return record
        delta = {key: cumulative[key] - (previous[key] if previous else 0)
                 for key in USAGE_FIELDS}
        for key in USAGE_FIELDS:
            self.totals[key] = self.totals.get(key, 0) + delta[key]
        thread['last_accepted_cumulative_usage'] = cumulative
        record.update(incremental_usage=delta, usage_known=True,
                      status='duplicate_snapshot' if previous == cumulative else 'observed')
        return record

    def summary(self):
        unknown = [index for index, call in self._calls.items() if not call['usage_known']]
        # Return detached metadata: subsequent calls must not mutate an earlier
        # event or manifest snapshot. No raw thread identifier is serialized.
        return json.loads(json.dumps({
            'schema': 'phyrc-token-accounting-v2',
            'cli_usage_scope': 'thread_cumulative',
            'aggregate_scope': 'sum_of_observed_thread_usage',
            'fully_known': not unknown, 'observed_usage': self.totals,
            'calls_recorded': len(self._calls), 'unknown_call_indices': unknown,
            'unknown_usage_is_zero': False,
            'cached_input_is_subset_of_input': True,
            'reasoning_output_is_subset_of_output': True,
            'threads': list(self._threads.values()),
        }))

    def update_manifest(self, manifest):
        # Retain the existing numeric actor_usage interface for readers, while
        # explicitly recording whether these observed totals are exhaustive.
        manifest['actor_usage'] = dict(self.totals)
        manifest['actor_usage_accounting'] = self.summary()


def dump(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def compare_public_state(reference, actual):
    """Numeric robot-state differences are diagnostics, not cloth equivalence."""
    result = {}
    for key, expected in reference.items():
        expected, observed = np.asarray(expected), np.asarray(actual[key])
        if observed.shape != expected.shape or not np.isfinite(observed).all():
            raise ValueError('replayed public state shape or finiteness mismatch')
        result[key] = {'max_absolute_difference': float(np.max(np.abs(
            observed.astype(np.float64) - expected.astype(np.float64))))}
    return {'fields': result, 'cloth_state_equivalence_checked': False,
            'scope': 'public robot numeric state only; no physics checkpoint claim'}


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
    parser.add_argument('--mode', choices=['wiring', 'dressing', 'pickup'], default='wiring')
    parser.add_argument('--strategy', choices=['general', 'coordinated'], default='general')
    parser.add_argument('--actor-backend', choices=['exec', 'app-server'], default='exec')
    parser.add_argument('--plan-size', type=int, default=1,
                        help='Maximum segments per model call; >1 is an open-loop list')
    parser.add_argument('--plan-step-budget', type=int, default=20)
    parser.add_argument('--pickup-hold-seconds', type=float, default=5.0,
                        help='Conservative visible pickup hold target; official scoring is unchanged')
    parser.add_argument('--review-points', type=int, default=5,
                        help='Trusted score termination threshold (5..50); never sent to the actor')
    parser.add_argument('--replay-prefix-run',
                        help='Replay verified recorded actions before a fresh actor; not physics restoration')
    parser.add_argument('--replay-prefix-steps', type=int,
                        help='Exclusive source transition boundary; defaults to the completed source length')
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
    if not 1 <= args.plan_size <= 3 or not 1 <= args.plan_step_budget <= 60:
        parser.error('plan size must be 1..3 and step budget 1..60')
    if not math.isfinite(args.pickup_hold_seconds) or not 3 <= args.pickup_hold_seconds <= 10:
        parser.error('pickup hold target must be finite, 3..10 simulation seconds')
    if not 5 <= args.review_points <= 50:
        parser.error('review-points must be 5..50')
    if args.replay_prefix_steps is not None and (not args.replay_prefix_run or args.replay_prefix_steps < 1):
        parser.error('positive replay-prefix-steps requires replay-prefix-run')
    if args.replay_prefix_run and args.mode == 'wiring':
        parser.error('replay prefixes are not wiring tests')
    if args.strategy == 'coordinated' and args.mode != 'dressing':
        parser.error('coordinated strategy requires the full dressing objective')
    if args.mode == 'wiring' and args.plan_size > 1 and (args.plan_size != 3 or args.decisions != 3):
        parser.error('grouped wiring requires plan-size=3 and decisions=3')
    if not math.isfinite(args.model_timeout) or not 10 <= args.model_timeout <= 1800:
        parser.error('model timeout must be finite, 10..1800 seconds')
    if bool(args.parent_attempt) != bool(args.retry_reason):
        parser.error('parent-attempt and retry-reason must be supplied together')
    root = Path(__file__).resolve().parents[2]
    replay = None
    if args.replay_prefix_run:
        from participant.collection.continuation import load_replay_prefix
        replay = load_replay_prefix(root, args.replay_prefix_run, args.replay_prefix_steps)
        if args.parent_attempt not in (None, args.replay_prefix_run):
            parser.error('replay prefix must be the immediate parent attempt')
        if args.source_group not in (None, replay.public_lineage['source_group']):
            parser.error('replay descendants must retain their source group')
        if len(replay.actions) >= args.max_steps:
            parser.error('max-steps must leave room after the replay prefix')
        args.parent_attempt = args.replay_prefix_run
        args.retry_reason = args.retry_reason or 'recorded_action_prefix_then_fresh_actor'
        args.source_group = replay.public_lineage['source_group']
    trace = root / 'output/operator-traces' / args.run_id
    actor_root = root / 'output/actors' / args.run_id
    trace.mkdir(parents=True, exist_ok=False)
    actor_root.mkdir(parents=True, exist_ok=False, mode=0o700)
    from participant.collection.plans import plan_schema, validate_plan, PLAN_TASK, BATCH_WIRING_TASK
    task = TASK
    if args.strategy == 'coordinated':
        task += '\n\n' + COORDINATED_TASK
    if args.plan_size > 1:
        task += '\n\n' + PLAN_TASK.format(max_segments=args.plan_size, max_total_steps=args.plan_step_budget)
    if replay is not None:
        task += ('\n\nA prefix of previously recorded permitted actions has already been executed '
                 'in this fresh episode. You are a fresh actor. Inspect the CURRENT public observations '
                 'and continue toward the full objective; do not assume any prior grasp or progress '
                 'survived replay. Only the supplied public views and robot state establish your next action.')
    if args.mode == 'wiring':
        task += '\n\n' + (BATCH_WIRING_TASK if args.plan_size > 1 else WIRING_TASK)
    elif args.mode == 'pickup':
        task += '\n\n' + PICKUP_TASK
        task += (f'\nFor this attempt, use a conservative target of at least '
                 f'{args.pickup_hold_seconds:g} simulation seconds of stable visible holding. '
                 'Start counting from a fresh observation that confirms the garment is visibly raised '
                 'and stationary, not from the start of the lift command. This margin does not change '
                 'the published 3-second criterion. A raised gripper pose alone does not prove cloth '
                 'height or grasp. Continue preserving the grip and neutral motion until the hold '
                 'target is met, unless observations require recovery or the controller ends the episode.')
    if args.actor_backend == 'app-server':
        from participant.collection.codex_app_actor import AppActor as Actor
    else:
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
    if replay is not None:
        command += ['--reset-seed', str(replay.trusted_metadata['reset_seed'])]
    started = time.monotonic()
    manifest = {
        'schema': 'phyrc-codex-attempt-v1', 'run_id': args.run_id,
        'parent_attempt': args.parent_attempt, 'retry_reason': args.retry_reason,
        'source_group': args.source_group or args.run_id, 'source': source,
        'model': args.model, 'reasoning_effort': args.effort,
        'prompt_sha256': hashlib.sha256(task.encode()).hexdigest(),
        'mode': args.mode, 'decisions_requested': args.decisions, 'decisions_completed': 0,
        'strategy': args.strategy,
        'actor_backend': args.actor_backend, 'plan_size': args.plan_size,
        'plan_step_budget': args.plan_step_budget,
        'plan_execution': 'open_loop_list' if args.plan_size > 1 else 'single_decision',
        'review_threshold_raw_points': None if args.mode == 'wiring' else args.review_points,
        'pickup_hold_target_simulation_s': args.pickup_hold_seconds if args.mode == 'pickup' else None,
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
        'replay_steps_completed': 0, 'activity': 'initializing',
    }
    if replay is not None:
        manifest['continuation'] = dict(replay.public_lineage)
    token_usage = TokenUsageAccounting()
    token_usage.update_manifest(manifest)
    manifest['source_snapshot'] = source_snapshot(root, trace)
    dump(trace / 'attempt.json', manifest)
    (trace / 'prompt.txt').write_text(task)
    sim, actor, finished, active = None, None, False, False
    pending_plan, stop_reason, simulation_origin = [], 'decision_budget', None
    gate = {'schema': 'phyrc-review-gate-v2', 'run_id': args.run_id,
            'threshold_raw_points': args.review_points, 'policy_input_changed': False,
            'status': 'disabled_wiring' if args.mode == 'wiring' else 'watching',
            'condition': f'official raw_points >= {args.review_points}; stop after acknowledged action'}
    dump(trace / 'review_gate.json', gate)
    with (trace / 'simulator.log').open('x') as log, (trace / 'decisions.jsonl').open('x') as events:
        def event(value):
            events.write(json.dumps(value, allow_nan=False) + '\n')
            events.flush()
        def record_milestones():
            if args.mode == 'wiring' or simulation_origin is None:
                return
            from participant.collection.milestones import write_index
            write_index(trace / 'score_segments.json',
                        collection=root / 'output/collections' / args.run_id,
                        run_id=args.run_id, source_group=manifest['source_group'],
                        acknowledged_steps=manifest['simulation_steps'],
                        simulation_origin=simulation_origin,
                        replay_prefix_steps=manifest['replay_steps_completed'],
                        capture_complete=manifest.get('capture_complete', False))
        def check_review_gate():
            nonlocal stop_reason
            if args.mode == 'wiring':
                return
            points = official_review_points(root / 'output/collections' / args.run_id)
            gate['last_observed_raw_points'] = points
            gate['acknowledged_steps'] = manifest['simulation_steps']
            if points >= args.review_points:
                gate['status'] = 'triggered'
                gate['triggered_at_utc'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
                stop_reason = 'review_points'
            dump(trace / 'review_gate.json', gate)
            record_milestones()
        try:
            sim = Simulator(command, root, log)
            manifest['simulator_pid'] = sim.process.pid
            ready = sim.receive()
            if ready.get('ready') is not True:
                raise ValueError('simulator did not become ready')
            obs, active = ready['observation'], True
            simulation_origin = float(obs['simulation_time_s'])
            interface = public_interface(ready.get('public_interface', {}))
            if replay is not None:
                from participant.collection.continuation import iter_action_chunks
                manifest['status'] = 'replaying_prefix'
                manifest['activity'] = 'replay_prefix'
                manifest['continuation']['initial_public_state_comparison'] = compare_public_state(
                    replay.initial_public_state, obs)
                dump(trace / 'attempt.json', manifest)
                for chunk in iter_action_chunks(replay.actions):
                    before = float(obs['simulation_time_s'])
                    t = time.monotonic()
                    value = sim.dispatch('act', {'action': chunk.action.tolist(), 'steps': chunk.steps})
                    elapsed = time.monotonic() - t
                    manifest['environment_dispatch_wall_s'] += elapsed
                    obs, active = value['observation'], value.get('active', True)
                    finished = not active
                    after = float(obs['simulation_time_s'])
                    steps = round((after - before) * 20)
                    manifest['simulation_steps'] += steps
                    manifest['replay_steps_completed'] += steps
                    event({'type': 'replayed_segment', 'action_source': 'replayed_parent',
                           'source_run_id': args.replay_prefix_run,
                           'source_start_step': chunk.start_step,
                           'source_end_step_exclusive': chunk.start_step + steps,
                           'start_step': manifest['simulation_steps'] - steps,
                           'end_step': manifest['simulation_steps'],
                           'requested_steps': chunk.steps, 'actual_steps': steps,
                           'applied_action': chunk.action.tolist(),
                           'simulation_start_s': before, 'simulation_end_s': after,
                           'environment_dispatch_wall_s': elapsed, 'model_invoked': False})
                    dump(trace / 'attempt.json', manifest)
                    check_review_gate()
                    if steps != chunk.steps or not active:
                        raise RuntimeError('replay prefix ended before the requested branch boundary')
                    if stop_reason == 'review_points':
                        break
                replay_complete = manifest['replay_steps_completed'] == len(replay.actions)
                manifest['continuation']['replay_validation'] = (
                    'actions_reexecuted_new_state_recorded' if replay_complete else 'stopped_at_review_boundary')
                if replay_complete:
                    manifest['continuation']['final_public_state_comparison'] = compare_public_state(
                        replay.final_public_state, obs)
                manifest['policy_suffix_start_step'] = manifest['simulation_steps']
                record_milestones()
            if stop_reason != 'review_points':
                actor = Actor(actor_root / 'runtime', model=args.model, effort=args.effort, timeout_s=args.model_timeout)
            manifest['status'] = 'collecting'
            for index in range(args.decisions if stop_reason != 'review_points' else 0):
                payload, images = prepare_observation(obs, actor_root / 'observations' / f'{index:05d}')
                prompt = (task if index == 0 else 'Continue the same episode using the latest public observation.\n')
                prompt += '\nDecision index: ' + str(index) + '\n'
                if index == 0:
                    prompt += 'Public static interpretation metadata: ' + json.dumps(interface, allow_nan=False) + '\n'
                prompt += json.dumps(payload, allow_nan=False)
                image_hashes = [hashlib.sha256(p.read_bytes()).hexdigest() for p in images]
                input_hash = hashlib.sha256((prompt + json.dumps(image_hashes)).encode()).hexdigest()
                latest_input_hash = input_hash
                if not pending_plan:
                    call_started = time.monotonic()
                    model_call_index = manifest['actor_calls_attempted']
                    manifest['actor_calls_attempted'] += 1
                    manifest['activity'] = 'model_request'
                    dump(trace / 'attempt.json', manifest)
                    result = None
                    try:
                        limit = min(args.plan_size, args.decisions - index)
                        schema = plan_schema(limit) if args.plan_size > 1 else SCHEMA
                        result = actor.invoke(prompt, images, schema)
                        if args.plan_size > 1:
                            actions = validate_plan(result['decision'], max_segments=limit,
                                                    max_total_steps=args.plan_step_budget,
                                                    wiring=args.mode == 'wiring')
                            decisions = result['decision']['decisions']
                        else:
                            decisions = [result['decision']]
                            actions = [validate_decision(decisions[0], wiring=args.mode == 'wiring')]
                    except BaseException as exc:
                        call_wall_s = time.monotonic() - call_started
                        manifest['actor_call_wall_s'] += call_wall_s
                        usage_record = token_usage.record(model_call_index, result, call_failed=True)
                        token_usage.update_manifest(manifest)
                        event({'type': 'model_error', 'decision_index': index, 'input_sha256': input_hash,
                               'model_call_index': model_call_index,
                               'error_type': type(exc).__name__, 'error': str(exc),
                               'actor_call_wall_s': call_wall_s, 'returned_result': result,
                               'usage_accounting': usage_record,
                               'actor_call_timing': getattr(actor, 'last_call_timing', None)})
                        raise
                    usage_record = token_usage.record(model_call_index, result)
                    token_usage.update_manifest(manifest)
                    for offset, (decision, action) in enumerate(zip(decisions, actions)):
                        projected = dict(result, decision=decision)
                        if offset:
                            projected.update(wall_s=0.0, usage={}, phase_wall_s=None)
                            for key in ('staging_wall_s', 'process_wall_s', 'result_parse_wall_s',
                                        'turn_usage_delta', 'last_reported_usage'):
                                projected.pop(key, None)
                        elif args.plan_size > 1:
                            projected['plan_response'] = result['decision']
                        metadata = {
                            'model_call_index': model_call_index,
                            'plan_id': f'{args.run_id}:call-{model_call_index:05d}',
                            'plan_segment_index': offset, 'plan_segment_count': len(decisions),
                            'model_invoked': offset == 0,
                            'input_sha256': input_hash,
                            'observation_simulation_time_s': float(obs['simulation_time_s']),
                            'usage_scope': 'thread_cumulative' if offset == 0 else 'not_invoked',
                            'usage_accounting': usage_record if offset == 0 else None,
                        }
                        pending_plan.append((projected, action, metadata))
                result, action, plan_meta = pending_plan.pop(0)
                decision = result['decision']
                plan_meta['latest_observation_simulation_time_s'] = float(obs['simulation_time_s'])
                plan_meta['latest_input_sha256'] = latest_input_hash
                event({'type': 'decision', 'decision_index': index, **result, **plan_meta})
                manifest['actor_call_wall_s'] += float(result['wall_s'])
                t = time.monotonic()
                tool = decision['tool']
                before = float(obs['simulation_time_s'])
                manifest['activity'] = 'executing_action'
                dump(trace / 'attempt.json', manifest)
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
                       **{key: plan_meta[key] for key in ('model_call_index', 'plan_id',
                          'plan_segment_index', 'plan_segment_count', 'model_invoked',
                          'observation_simulation_time_s', 'latest_observation_simulation_time_s')},
                       'decision_index': index, 'start_step': manifest['simulation_steps'] - steps,
                       'end_step': manifest['simulation_steps'], 'simulation_start_s': before,
                       'simulation_end_s': after, 'environment_dispatch_wall_s': elapsed,
                       'stage_intent': decision['stage'], 'visual_assessment': decision['visual_assessment'],
                       'assessment_source': 'actor_public_observations', 'official_score': None,
                       'action_source': 'model',
                       'requested_steps': decision['steps'] if tool == 'act' else (1 if tool == 'stop' else 0),
                       'applied_action': action.tolist() if tool == 'act' else np.zeros((2, 9)).tolist(),
                       'actual_steps': steps, 'quality_status': 'unreviewed'})
                dump(trace / 'attempt.json', manifest)
                print(json.dumps({'run_id': args.run_id, 'decision': index, 'stage': decision['stage'],
                                  'tool': tool, 'sim_s': after, 'actor_call_wall_s': result['wall_s']}), flush=True)
                check_review_gate()
                if finished or stop_reason == 'review_points':
                    break
            if pending_plan:
                event({'type': 'plan_suffix_discarded', 'reason': stop_reason if active else 'episode_ended',
                       'segments': [{'plan_id': item[2]['plan_id'],
                                     'plan_segment_index': item[2]['plan_segment_index']}
                                    for item in pending_plan]})
                pending_plan.clear()
            if active:
                stopped = sim.dispatch('stop')
                manifest['simulation_steps'] += 1
                if stopped.get('active', True):
                    sim.dispatch('finish_episode')
                event({'type': 'supervisor_stop', 'reason': stop_reason, 'neutral_steps': 1})
                finished, active = True, False
            manifest['status'] = 'review_ready' if stop_reason == 'review_points' else 'completed'
        except BaseException as exc:
            manifest['status'] = 'interrupted' if isinstance(exc, (KeyboardInterrupt, SystemExit)) else 'failed'
            manifest['error'] = {'type': type(exc).__name__, 'message': str(exc)}
            raise
        finally:
            if pending_plan:
                event({'type': 'plan_suffix_discarded', 'reason': manifest['status'],
                       'segments': [{'plan_id': item[2]['plan_id'],
                                     'plan_segment_index': item[2]['plan_segment_index']}
                                    for item in pending_plan]})
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
            manifest['activity'] = 'closed'
            manifest['new_recorded_suffix_steps'] = max(
                0, manifest['simulation_steps'] - manifest['replay_steps_completed'])
            try:
                record_milestones()
            except Exception as exc:
                manifest['score_segment_index_error'] = type(exc).__name__
            if gate['status'] == 'watching':
                gate['status'] = 'collector_ended_before_gate'
            gate['collector_status'] = manifest['status']
            dump(trace / 'review_gate.json', gate)
            dump(trace / 'attempt.json', manifest)
    if manifest.get('simulator_returncode') != 0:
        raise RuntimeError('collector did not exit successfully; inspect attempt record')


if __name__ == '__main__':
    main()
