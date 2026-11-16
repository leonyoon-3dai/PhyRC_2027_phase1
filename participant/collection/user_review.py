"""Trusted, opt-in live review supervisor. Evaluator and inbox never reach actor files.

A trusted operator publishes the exported files, verifies their remote bytes, and
writes ``published.json`` beside ``hold.json``. Only then can a matching
``inbox/<message-id>.json`` resume a held collector. Publication alone never moves it.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time

import numpy as np
from PIL import Image, ImageDraw

METHODS = {
    'M1': 'For the first correction start with 2–4 policy steps (0.1–0.2 simulation seconds), inspect the actual effect, and then adapt within the official action limits. Preserve both current useful grasps. Make one bounded local alignment or shape correction at a time toward the SAME selected hand and connected forearm, using only current public observations. Do not open either gripper. Keep housings away from the intended passage; examine actual robot and cloth displacement after every action. Propose finish if a useful supported correction is exhausted; the supervisor will request human review.',
    'M2': 'Preserve useful grasps and compare a changed base orientation or lateral approach to the SAME selected hand. Choose direction from current public views and robot state, not fixed world coordinates. Make one bounded motion and inspect its effect before continuing. Do not open either gripper. Propose finish if a useful supported correction is exhausted.',
    'M3': 'Consider ONE supported one-sided regrasp only when current public views show table support or a useful partner anchor. Never release both useful grips. Choose a visible reachable boundary, inspect closing and cloth following, then reassess the same-hand approach. Do not repeat regrasp cycles without human review.',
}
CAMERAS = ('overview', 'robot_1_head', 'robot_0_head', 'robot_1_wrist', 'robot_0_wrist')
SAFE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,119}\Z')


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    temporary.replace(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export_review(obs, *, root, trace, run_id, hold_id, step, reason, method,
                  source_checkpoint, prepare_observation, last_intent=None):
    """Copy one validated public boundary, retaining depth privately and no audit."""
    private = trace / 'user-review' / hold_id
    payload, images = prepare_observation(obs, private)
    source_images = dict(zip(payload['rgb_image_order'], images))
    public = root / 'docs/collection/user-reviews' / run_id / hold_id
    public.mkdir(parents=True, exist_ok=False)
    hashes = {}
    for name in CAMERAS:
        target = public / (name + '.png')
        target.write_bytes(source_images[name].read_bytes())
        hashes[name] = sha(target)
    panel = Image.new('RGB', (512, 828), '#151b26')
    draw = ImageDraw.Draw(panel)
    placements = [('overview', 128, 20), ('robot_1_head', 0, 296),
                  ('robot_0_head', 256, 296), ('robot_1_wrist', 0, 572), ('robot_0_wrist', 256, 572)]
    for name, x, y in placements:
        draw.text((x + 4, y - 17), name, fill='white')
        with Image.open(public / (name + '.png')) as im:
            panel.paste(im, (x, y))
    panel.save(public / 'cameras.png')
    observation_id = hashlib.sha256(json.dumps({
        'run_id': run_id, 'step': step, 'camera_sha256': hashes,
        'state': payload['public_robot_observation'], 'depth_sha256': sha(private / 'public_depth.npz'),
    }, sort_keys=True).encode()).hexdigest()
    meta = {'schema': 'phyrc-user-review-v1', 'run_id': run_id, 'hold_id': hold_id,
            'observation_id': observation_id, 'observation_step': step,
            'physics_tick_since_recording_start': step * 12,
            'simulation_time_s': float(obs['simulation_time_s']), 'captured_at_utc': utc(),
            'source_checkpoint': source_checkpoint, 'method': method, 'reason': reason,
            'camera_sha256': hashes, 'live_hold_at_capture': True,
            'last_intent': last_intent, 'observed_effect': 'Inspect the five current views against the preceding review; intent alone is not evidence of effect.',
            'unknown': 'Grasp support, garment topology and sleeve passage require review of public observations.',
            'question': 'Continue with a direction, change M1/M2/M3, choose another checkpoint, or finish?'}
    write_json(public / 'observation-metadata.json', meta)
    write_json(private / 'hold.json', dict(meta, public_directory=str(public.relative_to(root)),
                                         publication_status='pending', status='held'))
    links = ' · '.join(f'[{name}]({name}.png)' for name in CAMERAS)
    (public / 'README.ko.md').write_text(
        f'# 사용자 검토: {run_id} / {hold_id}\n\n'
        f'**촬영 당시 live HOLD · {method} · {reason}**\n\n'
        f'관측 `{observation_id}` · 전이 {step} · 시뮬레이션 {meta["simulation_time_s"]:.2f}s. '
        '모든 화면은 같은 경계입니다. 이후 상태는 저장소 최상단을 확인하세요.\n\n'
        '![5카메라](cameras.png)\n\n' + links + '\n\n'
        '파지·천 경계·소매 통과는 화면 검토가 필요합니다. 같은 상태에서 방향 교정 계속 / '
        'M2 또는 M3 / 다른 checkpoint / 종료 중 다음 지시를 텍스트로 알려주세요.\n')
    return private, public, meta


def validate_reply(value, meta, seen):
    if not isinstance(value, dict) or set(value) - {'run_id', 'hold_id', 'observation_id', 'message_id',
            'action', 'text', 'method', 'checkpoint', 'segment_decisions', 'segment_steps'}:
        raise ValueError('unexpected feedback fields')
    for key in ('run_id', 'hold_id', 'observation_id'):
        if value.get(key) != meta[key]:
            raise ValueError('stale or mismatched feedback ' + key)
    message = value.get('message_id')
    if not isinstance(message, str) or not SAFE.fullmatch(message) or message in seen:
        raise ValueError('invalid or duplicate message ID')
    if value.get('action') not in ('continue', 'change_method', 'checkpoint', 'finish'):
        raise ValueError('unknown feedback action')
    if not isinstance(value.get('text'), str) or not 1 <= len(value['text']) <= 8000:
        raise ValueError('feedback needs user text')
    if value.get('method', 'M1') not in METHODS:
        raise ValueError('unknown method')
    if value['action'] == 'change_method' and 'method' not in value:
        raise ValueError('change_method requires method')
    if value['action'] == 'checkpoint' and (not isinstance(value.get('checkpoint'), str) or not value['checkpoint'].strip()):
        raise ValueError('checkpoint choice required')
    for key, default, bound in [('segment_decisions', 20, 2000), ('segment_steps', 400, 18000)]:
        number = value.get(key, default)
        if type(number) is not int or not 1 <= number <= bound:
            raise ValueError('invalid ' + key)
    return dict(value)


def publication_verified(path, meta):
    try:
        value = json.loads(path.read_text())
        return (all(value.get(k) == meta[k] for k in ('run_id', 'hold_id', 'observation_id'))
                and bool(re.fullmatch('[0-9a-f]{40}', value.get('commit_sha', '')))
                and value.get('verified_camera_sha256') == meta['camera_sha256'])
    except (OSError, ValueError, TypeError):
        return False


def await_reply(private, meta, sim, seen, event, *, sleep=time.sleep, check_interrupt=lambda: None):
    inbox = private / 'inbox'
    inbox.mkdir(exist_ok=True)
    rejected = set()
    while True:
        check_interrupt()
        if sim.process.poll() is not None:
            raise RuntimeError('collector exited during user HOLD; live state lost')
        if publication_verified(private / 'published.json', meta):
            for path in sorted(inbox.glob('*.json')):
                signature = (path.name, sha(path))
                if signature in rejected:
                    continue
                try:
                    if path.stat().st_size > 16000:
                        raise ValueError('feedback too large')
                    value = validate_reply(json.loads(path.read_text()), meta, seen)
                    # At a hard boundary only a new branch or explicit finish is possible.
                    if meta['reason'] == 'hard_horizon' and value['action'] not in ('checkpoint', 'finish'):
                        raise ValueError('hard horizon requires checkpoint or finish')
                except (ValueError, OSError) as exc:
                    rejected.add(signature)
                    event({'type': 'feedback_rejected', 'hold_id': meta['hold_id'],
                           'file': path.name, 'reason': str(exc)})
                    continue
                seen.add(value['message_id'])
                event({'type': 'user_feedback', 'received_at_utc': utc(), **value})
                return value
        sleep(1)


def first_sleeve_points(collection):
    paths = list((collection / 'evaluation').glob('*/score_samples.jsonl'))
    if len(paths) != 1:
        raise ValueError('expected one trusted score sample stream')
    rows = paths[0].read_text().splitlines()
    if not rows:
        raise ValueError('trusted score stream empty')
    value = json.loads(rows[-1])['breakdown']['first_sleeve']
    if type(value) not in (int, float) or value not in (0, 5):
        raise ValueError('invalid trusted first_sleeve component')
    return value


def validate_start_state(root, initial_slot, receipt_path):
    value = json.loads(receipt_path.read_text())
    expected_checks = ('save_restore', 'settled_public_state', 'next_action_effect', 'visual_suitability')
    if (value.get('schema') != 'phyrc-start-state-validation-v1'
            or value.get('status') != 'validated'
            or value.get('initial_slot') != initial_slot
            or any(value.get('checks', {}).get(key) is not True for key in expected_checks)
            or value.get('first_sleeve_baseline') not in (0, 5)):
        raise ValueError('incomplete or mismatched start state validation')
    if not initial_slot.startswith('/output/'):
        raise ValueError('validated initial slot must be in /output/')
    slot = root / 'output' / initial_slot.removeprefix('/output/')
    if not slot.resolve().is_relative_to((root / 'output').resolve()) or sha(slot) != value.get('slot_sha256'):
        raise ValueError('validated slot hash mismatch')
    evidence = value.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        raise ValueError('validation evidence required')
    for item in evidence:
        path = root / item['path']
        if not path.resolve().is_relative_to(root.resolve()) or sha(path) != item['sha256']:
            raise ValueError('validation evidence mismatch')
    return {'receipt_sha256': sha(receipt_path), 'slot_sha256': value['slot_sha256'],
            'first_sleeve_baseline': value['first_sleeve_baseline'], 'checks': value['checks']}


def run_guided(*, sim, actor, obs, args, root, trace, actor_root, task, interface,
               manifest, event, prepare_observation, validate_decision, action_schema,
               token_usage, check_interrupt, score_reader=first_sleeve_points,
               wait=await_reply, reset_actor=None):
    """Run until an explicit finish/checkpoint reply; no silent budget extension."""
    seen, hold_count, feedback, method = set(), 0, None, 'M1'
    segment_decisions, segment_steps = args.segment_decisions, args.segment_steps
    start_decisions, start_steps = manifest['decisions_completed'], manifest['simulation_steps']
    baseline = score_reader(root / 'output/collections' / args.run_id) if args.mode != 'wiring' else 0
    goal_seen = baseline == 5
    manifest['user_guided'] = {'enabled': True, 'method': method, 'initial_first_sleeve': baseline,
                               'segment_decisions': segment_decisions, 'segment_steps': segment_steps,
                               'hold_count': 0, 'wait_wall_s': 0.0}
    source = {'initial_slot': args.initial_slot, 'replay_run': args.replay_prefix_run,
              'replay_steps': manifest['replay_steps_completed'], 'exact_physics_checkpoint': False}
    reason, last_intent = 'start_state_review', None
    if getattr(args, 'start_state_validation', None):
        validation = validate_start_state(root, args.initial_slot, Path(args.start_state_validation))
        manifest['user_guided']['start_state_validation'] = validation
        write_json(trace / 'start-state-validation.json', json.loads(Path(args.start_state_validation).read_text()))
        if baseline != validation['first_sleeve_baseline']:
            raise ValueError('restored first_sleeve differs from validation baseline')
        reason = None
    actor_needs_reset = False

    def persist():
        write_json(trace / 'attempt.json', manifest)

    def applied(action, steps, kind, index):
        nonlocal obs
        before = float(obs['simulation_time_s'])
        t = time.monotonic()
        result = sim.dispatch('act', {'action': action.tolist(), 'steps': steps})
        elapsed = time.monotonic() - t
        obs = result['observation']
        actual = round((float(obs['simulation_time_s']) - before) * 20)
        manifest['simulation_steps'] += actual
        manifest['environment_dispatch_wall_s'] += elapsed
        event({'type': 'applied_segment', 'decision_index': index,
               'action_source': kind, 'model_invoked': kind == 'model',
               'start_step': manifest['simulation_steps'] - actual, 'end_step': manifest['simulation_steps'],
               'requested_steps': steps, 'actual_steps': actual, 'applied_action': action.tolist(),
               'simulation_start_s': before, 'simulation_end_s': float(obs['simulation_time_s']),
               'environment_dispatch_wall_s': elapsed, 'quality_status': 'unreviewed'})
        persist()
        if not result.get('active', True) or actual != steps:
            raise RuntimeError('collector ended or action length differed; not a live HOLD')

    while True:
        check_interrupt()
        if reason:
            hold_count += 1
            hold_id = f'hold-{hold_count:04d}'
            before_step, before_time = manifest['simulation_steps'], float(obs['simulation_time_s'])
            result = sim.dispatch('hold', {'hold_id': hold_id, 'reason': reason})
            if not result.get('held') or not result.get('active'):
                raise RuntimeError('collector did not acknowledge live HOLD')
            obs = result['observation']
            if float(obs['simulation_time_s']) != before_time or sim.observation_step != before_step:
                raise RuntimeError('HOLD advanced physics')
            if reason == 'start_state_review' and args.save_checkpoint_on_start:
                saved = sim.dispatch('save_checkpoint', {'key': f'{args.run_id}-start'})
                write_json(trace / 'start-checkpoint.json', saved)
            private, public, meta = export_review(obs, root=root, trace=trace, run_id=args.run_id,
                hold_id=hold_id, step=before_step, reason=reason, method=method,
                source_checkpoint=source, prepare_observation=prepare_observation, last_intent=last_intent)
            if getattr(args, 'prepare_checkpoint_only', False) and reason == 'start_state_review':
                sim.dispatch('finish_episode')
                meta['run_closed_after_capture'] = True
                meta['purpose'] = 'checkpoint_preparation_only_no_actor_actions'
                write_json(public / 'observation-metadata.json', meta)
                (public / 'README.ko.md').write_text(
                    f'# Checkpoint 준비: {args.run_id}\n\n'
                    '출발 후보 복원·저장 후 정상 종료한 준비 실행입니다. 현재 live HOLD가 아닙니다.\n\n'
                    '![공개 5카메라](cameras.png)\n\n' +
                    ' · '.join(f'[{c}]({c}.png)' for c in CAMERAS) + '\n')
                write_json(private / 'hold.json', dict(meta, status='closed_checkpoint_preparation'))
                manifest['status'], manifest['activity'] = 'completed', 'checkpoint_prepared'
                manifest['user_guided']['close_reason'] = 'authorized_checkpoint_preparation'
                persist()
                return obs
            manifest['status'], manifest['activity'] = 'held', 'awaiting_publication_and_user'
            manifest['user_guided'].update(hold_count=hold_count, current_hold=hold_id,
                                          observation_id=meta['observation_id'], reason=reason)
            persist()
            print(json.dumps({'run_id': args.run_id, 'status': 'held', 'hold_id': hold_id,
                              'reason': reason, 'public_directory': str(public.relative_to(root))}), flush=True)
            waiting = time.monotonic()
            reply = wait(private, meta, sim, seen, event, check_interrupt=check_interrupt)
            check_interrupt()
            manifest['user_guided']['wait_wall_s'] += time.monotonic() - waiting
            manifest['human_intervention'] = True
            if reply['action'] in ('finish', 'checkpoint'):
                # Explicit human close is physics-zero. Checkpoint selection is a new run.
                sim.dispatch('finish_episode')
                manifest['user_guided']['next_checkpoint'] = reply.get('checkpoint')
                manifest['user_guided']['close_reason'] = reply['action']
                manifest['status'] = 'completed'
                persist()
                return obs
            result = sim.dispatch('resume', {'hold_id': hold_id})
            if result.get('held') or not result.get('active'):
                raise RuntimeError('collector did not acknowledge resume')
            obs = result['observation']
            if float(obs['simulation_time_s']) != before_time or sim.observation_step != before_step:
                raise RuntimeError('resume advanced physics')
            if actor_needs_reset:
                if reset_actor is None:
                    raise RuntimeError('fresh actor factory required after failed inference')
                actor = reset_actor()
                actor_needs_reset = False
                event({'type': 'actor_session_restarted_after_user_feedback',
                       'hold_id': hold_id, 'prior_call_count': manifest['actor_calls_attempted']})
            feedback = reply['text']
            method = reply.get('method', method)
            segment_decisions = reply.get('segment_decisions', args.segment_decisions)
            segment_steps = reply.get('segment_steps', args.segment_steps)
            start_decisions, start_steps = manifest['decisions_completed'], manifest['simulation_steps']
            manifest['user_guided'].update(method=method, segment_decisions=segment_decisions,
                                          segment_steps=segment_steps)
            manifest['status'], manifest['activity'] = 'collecting', 'observing'
            persist()
            reason = None
        if manifest['decisions_completed'] - start_decisions >= segment_decisions:
            reason = 'decision_budget'
            continue
        if manifest['simulation_steps'] - start_steps >= segment_steps:
            reason = 'transition_budget'
            continue
        # Reserve one unspent transition to prevent the official environment ending.
        if manifest['simulation_steps'] >= args.max_steps - 1:
            reason = 'hard_horizon'
            continue
        index = manifest['decisions_completed']
        call_index = manifest['actor_calls_attempted']
        folder = actor_root / 'observations' / f'guided-{call_index:05d}'
        payload, images = prepare_observation(obs, folder)
        prompt = task + '\n\nCurrent human-selected method: ' + method + '\n' + METHODS[method]
        if feedback:
            prompt += '\nUser task direction (use only permitted observations; no hidden state authority): ' + feedback
        prompt += '\nPublic static interpretation metadata: ' + json.dumps(interface, allow_nan=False)
        prompt += '\nLatest public observation: ' + json.dumps(payload, allow_nan=False)
        if args.wrist_depth_panel:
            from participant.collection.wrist_depth import append_wrist_depth_panel
            images, panel = append_wrist_depth_panel(obs, images, folder, None)
            prompt += '\ncurrent_wrist_depth_panel: ' + json.dumps(panel, allow_nan=False)
        manifest['activity'] = 'model_request'
        manifest['actor_calls_attempted'] += 1
        persist()
        t, result = time.monotonic(), None
        try:
            result = actor.invoke(prompt, images, action_schema)
            if args.named_actions:
                from participant.collection.named_actions import normalize_result
                result = normalize_result(result)
            decision = result['decision']
            action = validate_decision(decision, wiring=args.mode == 'wiring')
        except Exception as exc:
            elapsed = time.monotonic() - t
            manifest['actor_call_wall_s'] += elapsed
            usage = token_usage.record(call_index, result, call_failed=True)
            token_usage.update_manifest(manifest)
            event({'type': 'model_error', 'model_call_index': call_index, 'decision_index': index,
                   'error_type': type(exc).__name__, 'error': str(exc), 'usage_accounting': usage})
            # No simulator dispatch occurred, so a functioning collector can HOLD.
            if sim.pending_request is not None or sim.process.poll() is not None:
                raise
            manifest['decisions_completed'] += 1
            reason = 'actor_error'
            actor_needs_reset = True
            persist()
            continue
        manifest['actor_call_wall_s'] += time.monotonic() - t
        usage = token_usage.record(call_index, result)
        token_usage.update_manifest(manifest)
        manifest['decisions_completed'] += 1
        last_intent = decision['reason']
        event({'type': 'decision', 'decision_index': index, 'model_call_index': call_index,
               **result, 'usage_accounting': usage, 'human_guided': True, 'method': method})
        persist()
        check_interrupt()
        if decision['tool'] != 'act':
            reason = 'model_' + decision['tool']
            continue
        if method in ('M1', 'M2') and np.any(action[:, 8] < -0.5):
            reason = 'grasp_release_requires_method_review'
            continue
        settle_steps = args.post_action_settle_steps if np.any(action[:, :8] != 0) else 0
        needed = decision['steps'] + settle_steps
        if manifest['simulation_steps'] + needed >= args.max_steps:
            reason = 'hard_horizon'
            continue
        if manifest['simulation_steps'] - start_steps + needed > segment_steps:
            reason = 'transition_budget'
            continue
        applied(action, decision['steps'], 'model', index)
        check_interrupt()
        if args.mode != 'wiring' and not goal_seen and score_reader(root / 'output/collections' / args.run_id) == 5:
            goal_seen, reason = True, 'first_sleeve_new_5'
            continue
        if settle_steps:
            applied(np.zeros((2, 9), dtype=np.float32), settle_steps, 'controller_settle', index)
            if args.mode != 'wiring' and not goal_seen and score_reader(root / 'output/collections' / args.run_id) == 5:
                goal_seen, reason = True, 'first_sleeve_new_5'
