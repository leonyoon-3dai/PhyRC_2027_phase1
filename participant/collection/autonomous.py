"""GPT owns every dressing action. A human may request a hold between bounded actions."""
import json
import time

import numpy as np

from participant.collection.segment_bridge import SCHEMA as REVIEW_SCHEMA, validate_summary
from participant.collection.user_review import apply_action, write_json
from tools.segment_review import control_state, decide_boundary, get_segment, register_autonomy, set_control_state


def run_autonomous(*, sim, actor, obs, args, root, trace, actor_root, task, interface,
                   manifest, event, prepare_observation, validate_decision, action_schema,
                   token_usage, check_interrupt, reset_actor, web):
    schema = dict(action_schema, required=[*action_schema['required'], 'observation_review'],
                  properties=dict(action_schema['properties'], observation_review=REVIEW_SCHEMA))
    run, journal = args.run_id, web.journal
    hold_count = start = actions = consecutive_failures = stalled_segments = 0
    receipt = manifest['autonomous_control'] = dict(mode='gpt_only', intervention_count=0)
    manifest['human_intervention'] = False
    direction = None
    recent_actions = []
    active, acknowledged_step = True, 0

    def persist():
        write_json(trace / 'attempt.json', manifest)

    def infer():
        nonlocal consecutive_failures, actor
        call = manifest['actor_calls_attempted']
        folder = actor_root / 'observations' / f'autonomous-{call:05d}'
        payload, images = prepare_observation(obs, folder)
        prompt = (task + '\nReturn observation_review in Korean. Its analysis and outcome describe the observed '
                  'effect of recent executed actions up to this CURRENT camera observation; label failures '
                  'and uncertainties. Its next_prompt is the NEW intended action and is not observed evidence. '
                  'Review the whole current segment when possible. Your next action is rechecked by observation '
                  'after at most 20 policy steps. Use stop only when meaningful recovery is exhausted; '
                  'use finish_episode when dressing appears complete. Each ends the episode.\n'
                  + 'Public action and observations in this segment: '
                  + json.dumps(dict(current_step=manifest['simulation_steps'], recent_actions=recent_actions),
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
            result = actor.invoke(prompt, images, schema)
            if args.named_actions:
                from participant.collection.named_actions import normalize_result
                result = normalize_result(result)
            decision = dict(result['decision'])
            summary = validate_summary(decision.pop('observation_review'))
            action = validate_decision(decision)
        except Exception as exc:
            consecutive_failures += 1
            usage = token_usage.record(call, result, call_failed=True)
            event(dict(type='model_error', model_call_index=call, error_type=type(exc).__name__,
                       error=str(exc), usage_accounting=usage))
            if consecutive_failures == 1:
                try:
                    actor = reset_actor()
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
                   usage_accounting=usage, human_guided=bool(direction), method='gpt_only'))
        return decision, action, summary, index

    def boundary(reason, summary, terminal=None):
        nonlocal hold_count, start, actions, direction, obs, stalled_segments
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
        if summary and actions:
            stalled = 'no_progress' in summary['labels'] and summary['outcome'] in ('failure', 'uncertain')
            stalled_segments = stalled_segments + 1 if stalled else 0
            if stalled_segments >= 4 and not terminal:
                terminal = 'repeated_no_progress'
        record = web.review(obs=obs, start=start, end=step, hold=hold, reason=reason,
                            manifest=manifest, event=event, actor_review=summary)
        # Scores attached to the journal record are for retrospective review only.
        # This transaction linearizes an intervention arriving during clip publication.
        if active:
            status = decide_boundary(journal, run, hold, bool(terminal))
        else:
            status = 'closing'
            set_control_state(journal, run, status)
        overridden = status == 'held'
        manifest.update(status='held', activity='awaiting_web_feedback' if overridden else 'autonomous_review')
        receipt.update(current_hold=hold, hold_count=hold_count, observation_step=step)
        persist()
        if overridden:
            receipt['intervention_count'] += 1
            manifest['human_intervention'] = True
            persist()
            reply = web.wait(record, sim, check_interrupt, event)
            if reply['action'] == 'finish':
                terminal = 'human_finish'
            elif reason != 'hard_horizon':
                terminal = None
                direction = reply['text']
                stalled_segments = 0
            set_control_state(journal, run, 'closing' if terminal else 'running')
        if terminal:
            if active:
                sim.dispatch('finish_episode')
            set_control_state(journal, run, 'closed')
            receipt['close_reason'] = terminal
            receipt['task_outcome'] = {
                'model_finish_episode': 'visually_complete_unverified',
                'actor_error': 'technical_failure', 'human_finish': 'human_finished',
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

    register_autonomy(journal, run)
    try:
        if boundary('start_state_review', None) == 'closed':
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
            settle = args.post_action_settle_steps if np.any(action[:, :8]) else 0
            terminal = None
            if decision['tool'] != 'act':
                reason = terminal = 'model_' + decision['tool']
            elif control_state(journal, run) == 'pause_requested':
                reason = 'human_intervention'
            elif not reason and actions and (actions >= args.segment_decisions or
                    step - start + decision['steps'] + settle > args.segment_steps):
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
            duration = min(decision['steps'], args.max_steps - step)
            if duration < decision['steps']:
                event(dict(type='episode_budget_cap', decision_index=index,
                           requested_steps=decision['steps'], executable_steps=duration))
            obs, active = apply_action(sim, obs, manifest, event, web, action, duration,
                                       'model', index, decision['reason'], allow_end=True)
            acknowledged_step = manifest['simulation_steps']
            actions += 1
            recent_actions = (recent_actions + [web.actions[-1]])[-4:]
            persist()
            check_interrupt()
            settle = min(settle, args.max_steps - acknowledged_step)
            if active and settle and control_state(journal, run) != 'pause_requested':
                obs, active = apply_action(sim, obs, manifest, event, web, np.zeros((2, 9), dtype=np.float32),
                                           settle, 'controller_settle', index, decision['reason'], allow_end=True)
                acknowledged_step = manifest['simulation_steps']
                recent_actions = (recent_actions + [web.actions[-1]])[-4:]
                persist()
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
