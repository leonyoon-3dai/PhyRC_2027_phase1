"""GPT owns every dressing action. A human may request a hold between bounded actions."""
import json
import time

import numpy as np

from participant.collection.segment_bridge import SCHEMA as REVIEW_SCHEMA, validate_summary
from participant.collection.user_review import apply_action, write_json
from tools.segment_review import control_state, decide_boundary, get_segment, register_autonomy, set_control_state


CAMERA_BRIEFING = (
    'Camera orientation for this session. The five current RGB images arrive in this order: '
    'overview, robot_0_wrist, robot_1_wrist, robot_0_head, robot_1_head. '
    'The overview stays fixed during the episode and shows both robots relative to the mannequin. '
    'Each wrist view moves with its gripper and shows the nearby jaws and cloth. '
    'Each head view looks forward and down from its own robot and gives a wider view of the arms and shirt. '
    'In the review gallery the overview is above the head and wrist rows; robot_1 is the left column '
    'and robot_0 the right. An appended wrist-depth panel uses the same left/right columns. '
    'Robot IDs identify the cameras. Identify each mannequin hand by tracing its own forearm. '
    'If anatomical left or right is unclear, name the view and describe the nearer or farther hand. '
    'When a housing or cloth hides the hand or rim, compare the opposite head view and overview. '
    'Describe the relation as unconfirmed if it remains hidden.'
)

GENTLE_NEAR_BODY_STAGES = frozenset({
    'transport', 'first_sleeve', 'shoulder', 'second_sleeve', 'neck', 'orientation', 'final_check', 'recovery',
})
NEAR_BODY_MAX_STEPS, OTHER_MAX_STEPS = 4, 8
NEAR_BODY_VELOCITY_LIMIT, OTHER_VELOCITY_LIMIT, OTHER_BASE_LIMIT = 0.12, 0.50, 0.30


def bound_gentle_action(action, steps, stage):
    near_body = stage in GENTLE_NEAR_BODY_STAGES
    # Scale both robots together to preserve the requested direction and relative velocities.
    # The ninth channel is gripper intent, not a velocity.
    limit = NEAR_BODY_VELOCITY_LIMIT if near_body else OTHER_VELOCITY_LIMIT
    ratio = float(np.abs(action[:, :8]).max()) / limit
    if not near_body:
        ratio = max(ratio, float(np.abs(action[:, :3]).max()) / OTHER_BASE_LIMIT)
    scale = 1 / max(1.0, ratio)
    bounded = action.copy()
    bounded[:, :8] *= scale
    max_steps = NEAR_BODY_MAX_STEPS if near_body else OTHER_MAX_STEPS
    return bounded, min(steps, max_steps), scale


def run_autonomous(*, sim, actor, obs, args, root, trace, actor_root, task, interface,
                   manifest, event, prepare_observation, validate_decision, action_schema,
                   token_usage, check_interrupt, reset_actor, web, checkpoint_control=None,
                   checkpoint_rejected=None):
    schema = dict(action_schema, required=[*action_schema['required'], 'observation_review'],
                  properties=dict(action_schema['properties'], observation_review=REVIEW_SCHEMA))
    study_stop = getattr(args, 'slot_study_stop_step', None)
    action_limit = study_stop or args.max_steps
    supervised_close = args.until_full_score_or_feedback
    if supervised_close:
        schema['properties']['tool'] = {'type': 'string', 'enum': ['act']}
    end_guidance = ('The supervisor controls episode closure. Continue with a bounded action.'
                    if supervised_close else 'Use stop only when meaningful recovery is exhausted; '
                    'use finish_episode when dressing appears complete. Each ends the episode.')
    run, journal = args.run_id, web.journal
    hold_count = actions = consecutive_failures = 0
    start = acknowledged_step = manifest['simulation_steps']
    receipt = manifest['autonomous_control'] = dict(mode='gpt_only', intervention_count=0)
    manifest['human_intervention'] = False
    direction = None
    recent_actions = []
    recent_visual_reviews = []
    active = True
    camera_briefing_pending = args.camera_briefing
    gentle = getattr(args, 'gentle_wrist_dressing', False)
    recheck = 'after at most 20 policy steps. '
    if gentle:
        near_stages = ', '.join(sorted(GENTLE_NEAR_BODY_STAGES))
        recheck = (f'after at most {NEAR_BODY_MAX_STEPS} policy steps in these stages: {near_stages}. '
                   f'For those stages the normalized velocity component limit is {NEAR_BODY_VELOCITY_LIMIT}. '
                   f'All other stages allow at most {OTHER_MAX_STEPS} steps, with a velocity component limit '
                   f'of {OTHER_VELOCITY_LIMIT} and a base velocity component limit of {OTHER_BASE_LIMIT}. '
                   'A single factor scales all eight motion channels of both robots when needed. '
                   'Gripper intents are preserved. ')

    def persist():
        write_json(trace / 'attempt.json', manifest)

    def execute(action, steps, kind, index, intent):
        nonlocal obs, active, acknowledged_step, recent_actions
        step = manifest['simulation_steps']
        end = step + steps
        boundaries = checkpoint_control.boundaries(step, end) if checkpoint_control else (end,)
        first_action = len(web.actions)
        for boundary_step in boundaries:
            obs, active = apply_action(sim, obs, manifest, event, web, action, boundary_step - step,
                                       kind, index, intent, allow_end=True)
            acknowledged_step = manifest['simulation_steps']
            persist()
            check_interrupt()
            if not active:
                break
            if checkpoint_control:
                record = checkpoint_control.save_due(sim, acknowledged_step, obs,
                                                     rejected=checkpoint_rejected, prefix='step')
                if record is not None:
                    event({'type': 'dressing_checkpoint', 'step': acknowledged_step, **record})
            step = acknowledged_step
        recent_actions = (recent_actions + web.actions[first_action:])[-4:]

    def infer():
        nonlocal consecutive_failures, actor, camera_briefing_pending
        call = manifest['actor_calls_attempted']
        folder = actor_root / 'observations' / f'autonomous-{call:05d}'
        payload, images = prepare_observation(obs, folder)
        instructions = task
        if camera_briefing_pending:
            instructions += '\n\n' + CAMERA_BRIEFING
        prompt = (instructions + '\nReturn observation_review in Korean. Its analysis and outcome describe the observed '
                  'effect of recent executed actions up to this CURRENT camera observation; label failures '
                  'and uncertainties. Its next_prompt is the NEW intended action and is not observed evidence. '
                  'Review the whole current segment when possible. Your next action is rechecked by observation '
                  + recheck + end_guidance + '\n'
                  + 'Compare your recent public visual reviews with the current hand, rim and support. '
                  + 'These are earlier camera interpretations and may have been occluded.\n'
                  + json.dumps(dict(current_step=manifest['simulation_steps'], recent_actions=recent_actions,
                                    recent_visual_reviews=recent_visual_reviews),
                               ensure_ascii=False, allow_nan=False))
        if direction:
            prompt += '\nHuman direction from the reviewed public clip: ' + direction
        prompt += '\nPublic interface: ' + json.dumps(interface, allow_nan=False)
        prompt += '\nCurrent public observation: ' + json.dumps(payload, allow_nan=False)
        if args.wrist_depth_panel:
            from participant.collection.wrist_depth import append_wrist_depth_panel
            images, panel = append_wrist_depth_panel(obs, images, folder, None)
            prompt += '\nCurrent public wrist depth: ' + json.dumps(panel, allow_nan=False)
        manifest['activity'] = 'model_request'
        manifest['actor_calls_attempted'] += 1
        persist()
        begun, result = time.monotonic(), None
        try:
            try:
                result = actor.invoke(prompt, images, schema)
            finally:
                actor_ended = time.monotonic()
            if camera_briefing_pending:
                event(dict(type='camera_briefing_delivered', model_call_index=call))
                camera_briefing_pending = False
            if args.named_actions:
                from participant.collection.named_actions import normalize_result
                result = normalize_result(result)
            decision = dict(result['decision'])
            summary = validate_summary(decision.pop('observation_review'))
            if supervised_close and decision['tool'] != 'act':
                raise ValueError('expected an act decision in supervisor-terminated collection')
            action = validate_decision(decision)
        except Exception as exc:
            consecutive_failures += 1
            usage = token_usage.record(call, result, call_failed=True)
            event(dict(type='model_error', model_call_index=call, error_type=type(exc).__name__,
                       error=str(exc), usage_accounting=usage, actor_started_monotonic_s=begun,
                       actor_ended_monotonic_s=actor_ended))
            if consecutive_failures == 1:
                try:
                    actor = reset_actor()
                    camera_briefing_pending = args.camera_briefing
                except Exception as reset_error:
                    consecutive_failures += 1
                    event(dict(type='actor_reset_error', error_type=type(reset_error).__name__, error=str(reset_error)))
            return None
        finally:
            manifest['actor_call_wall_s'] += time.monotonic() - begun
            token_usage.update_manifest(manifest)
        consecutive_failures = 0
        index = manifest['decisions_completed']
        manifest['decisions_completed'] += 1
        usage = token_usage.record(call, result)
        token_usage.update_manifest(manifest)
        event(dict(type='decision', decision_index=index, model_call_index=call, **result,
                   actor_started_monotonic_s=begun, actor_ended_monotonic_s=actor_ended,
                   usage_accounting=usage, human_guided=bool(direction), method='gpt_only'))
        return decision, action, summary, index

    def boundary(reason, summary, terminal=None):
        nonlocal hold_count, start, actions, direction, obs
        hold_count += 1
        hold = f'hold-{hold_count:04d}'
        step, sim_time = manifest['simulation_steps'], float(obs['simulation_time_s'])
        if active:
            result = sim.dispatch('hold', dict(hold_id=hold, reason=reason))
            if (not result.get('held') or not result.get('active') or sim.observation_step != step
                    or float(result['observation']['simulation_time_s']) != sim_time):
                raise RuntimeError('collector failed to hold at the observed boundary')
            obs = result['observation']
            if reason == 'start_state_review' and args.save_checkpoint_on_start:
                write_json(trace / 'start-checkpoint.json', sim.dispatch('save_checkpoint', {'key': run + '-start'}))
        record = web.review(obs=obs, start=start, end=step, hold=hold, reason=reason,
                            manifest=manifest, event=event, actor_review=summary)
        if summary:
            # Only repeat what the action actor observed. Journal rows also contain evaluator data.
            recent_visual_reviews.append(dict(start_step=start, end_step=step, outcome=summary['outcome'],
                                              analysis=summary['analysis']))
            del recent_visual_reviews[:-3]
        # This transaction linearizes an intervention arriving during clip publication.
        if active and terminal != 'full_score':
            status = decide_boundary(journal, run, hold, bool(terminal),
                                     require_feedback=supervised_close and terminal == 'actor_error')
        else:
            status = 'closing'
            set_control_state(journal, run, status)
        overridden = status == 'held'
        manifest.update(status='held', activity='awaiting_web_feedback' if overridden else 'autonomous_review')
        receipt.update(current_hold=hold, hold_count=hold_count, observation_step=step)
        persist()
        automatic_checkpoints = checkpoint_control is not None and getattr(args, 'checkpoint_every_review', False)
        if active and automatic_checkpoints and step > start and not terminal:
            record = checkpoint_control.reuse_saved(step, str(step))
            if record is None:
                record = checkpoint_control.save_held(
                    sim, step, obs, f'review-{step:06d}', str(step), rejected=checkpoint_rejected)
            event({'type': 'review_checkpoint', 'step': step, **record})
        if overridden:
            reply = web.wait(record, sim, check_interrupt, event)
            receipt['intervention_count'] += 1
            manifest['human_intervention'] = True
            persist()
            if reply['action'] == 'finish':
                terminal = 'human_finish'
            elif supervised_close:
                terminal = 'human_feedback'
            elif reason != 'hard_horizon':
                terminal = None
                direction = reply['text']
            set_control_state(journal, run, 'closing' if terminal else 'running')
        if terminal:
            save_final = checkpoint_control is not None and checkpoint_control.begin_finish()
            if active:
                if save_final or automatic_checkpoints:
                    record = checkpoint_control.reuse_saved(step, 'finish')
                    if record is None:
                        record = checkpoint_control.save_held(
                            sim, step, obs, f'finish-{step:06d}', 'finish', rejected=checkpoint_rejected)
                    event({'type': 'final_checkpoint', 'step': step, **record})
                sim.dispatch('finish_episode')
            set_control_state(journal, run, 'closed')
            receipt['close_reason'] = terminal
            receipt['task_outcome'] = {
                'model_finish_episode': 'visually_complete_unverified',
                'actor_error': 'technical_failure', 'human_finish': 'human_finished',
                'human_feedback': 'human_finished', 'full_score': 'full_score',
            }.get(terminal, 'incomplete')
            event(dict(type='autonomous_finish', reason=terminal, observation_step=step,
                       neutral_steps=0, human_intervention=manifest['human_intervention']))
            persist()
            return 'closed'
        result = sim.dispatch('resume', {'hold_id': hold, 'human_feedback': overridden})
        if (result.get('held') or not result.get('active') or sim.observation_step != step
                or float(result['observation']['simulation_time_s']) != sim_time):
            raise RuntimeError('collector failed to resume the same observed boundary')
        obs = result['observation']
        start, actions = step, 0
        if summary and not overridden:
            web.direction = summary['next_prompt']
        manifest.update(status='collecting', activity='observing')
        persist()
        return 'reobserve' if overridden else 'continue'

    def full_score(step):
        if not supervised_close:
            return False
        sample, _ = web.score_at(step)
        if sample is None:
            raise RuntimeError(f'official score sample missing at acknowledged step {step}')
        return sample['raw_points'] == 50

    register_autonomy(journal, run)
    try:
        starting_reason = 'replay_boundary' if manifest.get('replay_steps_completed') else 'start_state_review'
        if boundary(starting_reason, None) == 'closed':
            return obs
        reason = None
        while True:
            check_interrupt()
            if control_state(journal, run) == 'pause_requested':
                if boundary('human_intervention', None) == 'closed':
                    return obs
            proposal = infer()
            check_interrupt()
            if not proposal:
                terminal = 'actor_error' if consecutive_failures >= 2 else None
                if boundary('actor_error', None, terminal) == 'closed':
                    return obs
                continue
            decision, action, summary, index = proposal
            step = manifest['simulation_steps']
            requested_action, model_steps = action, decision['steps']
            if gentle and decision['tool'] == 'act':
                action, model_steps, scale = bound_gentle_action(action, model_steps, decision['stage'])
            settle = args.post_action_settle_steps if np.any(action[:, :8]) else 0
            terminal = None
            if decision['tool'] != 'act':
                reason = terminal = 'model_' + decision['tool']
            elif control_state(journal, run) == 'pause_requested':
                reason = 'human_intervention'
            elif not reason and actions and (actions >= args.segment_decisions or
                    step - start + model_steps + settle > args.segment_steps):
                reason = 'segment_budget'
            elif not reason and actions and web.stage != decision['stage']:
                reason = 'stage_change'
            if reason:
                disposition = boundary(reason, summary, terminal)
                reason = None
                if disposition == 'closed':
                    return obs
                if disposition == 'reobserve':
                    continue  # the proposed action predates the human correction
            if control_state(journal, run) == 'pause_requested':
                continue  # a newly requested intervention owns the next action boundary
            if not actions:
                web.direction = summary['next_prompt']
            web.stage, web.assessment = decision['stage'], decision['visual_assessment']
            duration = min(model_steps, action_limit - step)
            if duration < model_steps:
                event(dict(type='episode_budget_cap', decision_index=index,
                           requested_steps=model_steps, executable_steps=duration))
            if gentle:
                event(dict(type='gentle_wrist_action', decision_index=index, stage=decision['stage'],
                           velocity_scale=scale, requested_action=requested_action.tolist(),
                           sent_action=action.tolist(), requested_steps=decision['steps'], sent_steps=duration))
            execute(action, duration, 'model', index, decision['reason'])
            actions += 1
            settle = min(settle, action_limit - acknowledged_step)
            goal_reached = full_score(acknowledged_step)
            if not goal_reached and active and settle and control_state(journal, run) != 'pause_requested':
                execute(np.zeros((2, 9), dtype=np.float32), settle, 'controller_settle',
                        index, decision['reason'])
                goal_reached = full_score(acknowledged_step)
            if goal_reached:
                boundary('full_score', None, 'full_score')
                return obs
            if active and acknowledged_step == study_stop:
                boundary('comparison_endpoint', None, 'comparison_endpoint')
                return obs
            if not active or acknowledged_step == args.max_steps:
                terminal = 'hard_horizon' if acknowledged_step == args.max_steps else 'environment_end'
                boundary(terminal, None, terminal)
                return obs
            if web.assessment == 'blocked':
                reason = 'visual_blockage'
    except BaseException as failure:
        # A disconnected simulator may already be parked. Publish only the clip
        # through the last acknowledged observation, without issuing another RPC.
        try:
            set_control_state(journal, run, 'unavailable')
            previous = get_segment(journal, run)
            last_published = previous['end_step'] if previous else 0
            if last_published < acknowledged_step == manifest['simulation_steps']:
                web.review(obs=obs, start=last_published, end=acknowledged_step,
                           hold=f'hold-{hold_count + 1:04d}', reason='controller_interrupted',
                           manifest=manifest, event=event, actor_review=None)
        except Exception as publication_error:
            event(dict(type='interrupted_review_error', error_type=type(publication_error).__name__,
                       error=str(publication_error), controller_error=type(failure).__name__))
        raise
