"""Export a reviewed, explicit public subset of one completed collection attempt.

This tool never publishes or commits. It creates a new report directory containing
public camera pixels, final action decisions, timing, and a score summary. Raw CLI
events, full evaluation reports, audit contents, and arbitrary metadata are never
copied. Free-text prompts and action reasons fail closed on private endpoint,
credential, absolute-path, or serialized privileged-state markers.
"""
import argparse
import html
import ipaddress
import json
import math
from pathlib import Path
import re
import shutil
import subprocess

import h5py
import numpy as np
from PIL import Image

from participant.collection.boundary import CONTRACT, validate_action
from participant.collection.validate_capture import load_json, sha256


CAMERAS = tuple(CONTRACT['competition_access']['allowed_cameras'])
SCORES = {
    'pickup': ('파지·들기', 5), 'first_sleeve': ('첫 소매', 5),
    'opposite_shoulder': ('반대 어깨', 5), 'second_sleeve': ('두 번째 소매', 5),
    'left_upper_arm': ('왼쪽 위팔', 5), 'right_upper_arm': ('오른쪽 위팔', 5),
    'neck': ('목 통과', 10), 'front_orientation': ('앞면 방향', 10),
}
STAGES = {
    'preparation': '준비', 'approach': '접근', 'grasp': '파지', 'lift': '들기',
    'transport': '운반', 'first_sleeve': '첫 소매', 'shoulder': '어깨',
    'second_sleeve': '두 번째 소매', 'neck': '목', 'orientation': '방향',
    'recovery': '복구', 'final_check': '최종 확인',
}
USAGE_FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens')
HASH = re.compile(r'[0-9a-f]{64}')
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,159}')
SENSITIVE = re.compile(
    r'(?:https?|wss?)://|gobrev\.dev|run\.brev\.nvidia\.com|'
    r'(?i:authorization\s*:|bearer\s+\S+|access_token|refresh_token|'
    r'OPENAI_API_KEY|HF_TOKEN|GH_TOKEN|GITHUB_TOKEN)|'
    r'\b(?:sk-[A-Za-z0-9_-]{16,}|hf_[A-Za-z0-9]{16,})\b|'
    r'(?:^|[\s\"\x27=])/(?:home|root|tmp|workspace|project|output|etc|var|mnt|usr|opt|isaac-sim)(?:/|$)|'
    r'\b[A-Za-z]:[\\/]|'
    r'\b(?:cloth_world_positions|episode_seed|human_spawn|garment_spawn|'
    r'neck_chain_world_m|arms_world_m|native_attachment_present)\b|취업|면접|인터뷰'
)


def text(value, *, max_length=32768):
    if not isinstance(value, str) or len(value) > max_length or '\x00' in value:
        raise ValueError('invalid or oversized public text')
    if SENSITIVE.search(value):
        raise ValueError('public text requires manual privacy review')
    for match in re.findall(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])', value):
        try:
            ipaddress.ip_address(match)
        except ValueError:
            continue
        raise ValueError('public text contains an IP address')
    for match in re.findall(r'(?<!\w)[0-9a-fA-F]*:[0-9a-fA-F:]+(?!\w)', value):
        if match.count(':') < 2:
            continue
        try:
            ipaddress.IPv6Address(match)
        except ValueError:
            continue
        raise ValueError('public text contains an IP address')
    return value


def identifier(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise ValueError('invalid public identifier')
    return text(value, max_length=160)


def number(value):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError('expected a finite number')
    return value


def integer(value):
    if type(value) is not int or value < 0:
        raise ValueError('expected a nonnegative integer')
    return value


def boolean(value):
    if type(value) is not bool:
        raise ValueError('expected a boolean')
    return value


def digest(value):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise ValueError('invalid SHA256')
    return value


def select(source, fields):
    """A field must be explicitly named and typed; nested objects need a mapper."""
    if not isinstance(source, dict):
        raise ValueError('expected an input object')
    return {key: None if source[key] is None else convert(source[key])
            for key, convert in fields.items() if key in source}


def safe_error(value):
    if not isinstance(value, dict):
        return None
    result = select(value, {'type': identifier})
    if isinstance(value.get('message'), str):
        try:
            result['message'] = text(value['message'])
        except ValueError:
            result['message'] = '비공개 세부 정보가 포함되어 공개 설명을 생략했습니다.'
    return result


def public_attempt(value):
    result = select(value, {
        'run_id': identifier, 'parent_attempt': identifier, 'retry_reason': text,
        'source_group': identifier, 'source': identifier, 'mode': identifier,
        'model': identifier, 'reasoning_effort': identifier, 'prompt_sha256': digest,
        'status': identifier, 'finished': boolean, 'started_at_utc': text, 'ended_at_utc': text,
        'decisions_requested': integer, 'decisions_completed': integer, 'actor_calls_attempted': integer,
        'actor_call_wall_s': number, 'model_internal_inference_wall_s': number,
        'actor_call_timing_scope': text, 'environment_dispatch_wall_s': number,
        'wall_s': number, 'simulation_time_s': number, 'simulation_steps': integer,
        'acknowledged_simulation_steps': integer, 'recorded_simulation_steps': integer,
        'capture_complete': boolean, 'capture_termination_reason': identifier,
        'human_intervention': boolean, 'quality_status': identifier, 'input_profile': identifier,
    })
    result['error'] = safe_error(value.get('error'))
    result['actor_usage'] = select(value.get('actor_usage', {}), dict.fromkeys(USAGE_FIELDS, integer))
    snapshot = value.get('source_snapshot', {})
    if isinstance(snapshot, dict):
        result['code'] = select(snapshot, {'commit': identifier, 'working_tree_modified': boolean})
    return result


def action(value):
    if not isinstance(value, list) or any(not isinstance(row, list) for row in value):
        raise ValueError('action must be a list of lists')
    if any(type(v) not in (int, float) for row in value for v in row):
        raise ValueError('action must contain numbers')
    validate_action(value, 1)
    return value


def public_events(path):
    output, skipped = [], 0
    if not path.is_file():
        return output, skipped
    with path.open() as stream:
        for line in stream:
            value = load_json(line)
            kind = value.get('type')
            if kind == 'decision':
                row = select(value, {'type': identifier, 'decision_index': integer,
                    'input_sha256': digest, 'observation_simulation_time_s': number,
                    'wall_s': number, 'model': identifier, 'effort': identifier,
                    'cli_version': text, 'prompt_sha256': digest})
                row['decision'] = select(value['decision'], {'tool': identifier, 'action': action,
                    'steps': integer, 'stage': identifier, 'visual_assessment': identifier, 'reason': text})
                row['usage'] = select(value.get('usage', {}), dict.fromkeys(USAGE_FIELDS, integer))
            elif kind == 'applied_segment':
                row = select(value, {'type': identifier, 'segment_id': identifier, 'decision_index': integer,
                    'start_step': integer, 'end_step': integer, 'simulation_start_s': number,
                    'simulation_end_s': number, 'environment_dispatch_wall_s': number,
                    'stage_intent': identifier, 'visual_assessment': identifier, 'assessment_source': identifier,
                    'requested_steps': integer, 'applied_action': action, 'actual_steps': integer,
                    'quality_status': identifier})
            elif kind == 'model_error':
                row = select(value, {'type': identifier, 'decision_index': integer, 'input_sha256': digest,
                    'error_type': identifier, 'actor_call_wall_s': number})
                row['error'] = safe_error({'type': value.get('error_type', 'UnknownError'),
                                           'message': value.get('error', '')})
            elif kind == 'supervisor_stop':
                row = select(value, {'type': identifier, 'reason': identifier, 'neutral_steps': integer})
            else:
                skipped += 1
                continue
            output.append(row)
    return output, skipped


def public_score(report):
    """Only reported outcomes/times; never evaluator metadata or geometric tests."""
    if not isinstance(report, dict):
        return {'evaluated': False, 'valid': None, 'raw_points': None, 'success': None,
                'score_status': None, 'final_score': None, 'breakdown': {}, 'milestone_times_s': {}}
    valid = report.get('valid') is True
    result = report.get('result') if valid else None
    if not isinstance(result, dict):
        result = {}
    score = {'evaluated': True, 'valid': valid, 'raw_points': None, 'success': None,
             'score_status': None, 'final_score': None, 'breakdown': {}, 'milestone_times_s': {}}
    if not valid:
        return score
    score.update(select(result, {'raw_points': number, 'max_raw_points': number,
        'success_evaluated': boolean, 'score_status': identifier, 'final_score': number,
        'rate_points': number, 'max_rate_points': number, 'task_time_s': number,
        'elapsed_episode_time_s': number, 'first_contact_time_s': number,
        'last_score_award_time_s': number, 'dressing_completed_at_s': number,
        'rate_rule': identifier, 'scoring_revision': identifier, 'score_unit': text}))
    if result.get('success_evaluated') is True:
        score['success'] = boolean(result['success'])
    score['breakdown'] = select(result.get('breakdown', {}), dict.fromkeys(SCORES, number))
    score['milestone_times_s'] = select(result.get('milestone_times_s', {}), dict.fromkeys(SCORES, number))
    overall = result.get('score_items', {}).get('overall_dressing', {})
    for stage, key in [('neck', 'neck_confirmed_at_s'), ('front_orientation', 'front_confirmed_at_s')]:
        if key in overall:
            score['milestone_times_s'][stage] = None if overall[key] is None else number(overall[key])
    return score


def public_score_events(collection, evaluation):
    """Select score events without copying their enclosing evaluator metadata."""
    if not isinstance(evaluation, dict) or not evaluation.get('evaluation_path'):
        return [], None
    relative = Path(evaluation['evaluation_path'])
    if len(relative.parts) != 2 or relative.parts[0] != 'evaluation':
        raise ValueError('unexpected evaluation evidence path')
    identifier(relative.parts[1])
    path = collection / relative / 'score_events.jsonl'
    if not path.is_file():
        return [], None
    events = []
    with path.open() as stream:
        for line in stream:
            value = load_json(line)
            kind = value.get('event')
            if kind not in ('evaluation_started', 'score_awarded', 'first_contact', 'dressing_success'):
                continue
            event = select(value, {'event': identifier, 'wall_utc': text, 'wall_elapsed_s': number,
                'physics_tick': integer, 'evaluation_time_s': number, 'raw_points': number,
                'success_evaluated': boolean, 'success': boolean, 'first_contact_tick': integer,
                'score_status': identifier, 'final_score': number, 'rate_points': number,
                'task_time_s': number, 'last_score_award_time_s': number,
                'previous_points': number, 'points': number, 'contact_tick': integer})
            event['breakdown'] = select(value.get('breakdown', {}), dict.fromkeys(SCORES, number))
            if 'stage' in value:
                if value['stage'] not in SCORES:
                    raise ValueError('unknown official score stage')
                event['stage'] = value['stage']
            events.append(event)
    return events, path


def milestone_path(events, *, valid, simulation_origin):
    """All awards at one physics tick form one unordered simultaneous batch."""
    batches = []
    for event in events:
        tick = event['physics_tick']
        if batches and tick < batches[-1][0]:
            raise ValueError('score events are not chronological')
        if not batches or tick != batches[-1][0]:
            batches.append((tick, []))
        batches[-1][1].append(event)
    previous = dict.fromkeys(SCORES, 0)
    points_before = 0
    path, successes = [], []
    for tick, group in batches:
        breakdown = group[-1]['breakdown']
        if any(e['breakdown'] != breakdown for e in group):
            raise ValueError('same-tick score snapshots disagree; cannot infer an order')
        changes = [{ 'stage': key, 'before': previous.get(key, 0), 'after': breakdown[key]}
                   for key in SCORES if key in breakdown and breakdown[key] != previous.get(key, 0)]
        when = group[-1]['evaluation_time_s']
        temporal = {'physics_tick': tick, 'transition_boundary_step': tick // 12,
                    'step_alignment_exact': tick % 12 == 0, 'evaluation_time_s': when,
                    'public_simulation_time_s': None if simulation_origin is None else simulation_origin + when}
        if changes:
            path.append(dict(temporal, batch_index=len(path), raw_points_before=points_before,
                             raw_points_after=group[-1]['raw_points'], changes=changes,
                             simultaneous=len(changes) > 1, order_within_batch='not_inferred'))
        if any(e['event'] == 'dressing_success' for e in group):
            successes.append(temporal)
        previous = dict(breakdown)
        points_before = group[-1]['raw_points']
    return {'evaluation_valid': valid, 'award_batches': path, 'success_events': successes,
            'time_origin_public_simulation_s': simulation_origin,
            'time_basis': 'episode evaluation clock begins after reset; physics_tick/12 is transition boundary',
            'order_rule': 'different ticks chronological; same-tick awards unordered'}


def public_qc(value):
    if not isinstance(value, dict):
        return {'available': False, 'quality_passed': None, 'training_approval': 'unreviewed'}
    result = select(value, {'schema': identifier, 'quality_passed': boolean,
        'training_approval': identifier, 'scope': identifier, 'total_transitions': integer,
        'validated_transitions': integer})
    result['available'] = True
    result['checks'] = [identifier(v) for v in value.get('checks', [])]
    result['error_count'] = len(value.get('errors', []))
    # Error text can include local paths/privileged data; publish only a count.
    result['episodes'] = [select(e, {'episode': identifier, 'transitions': integer,
        'complete': boolean, 'simulation_seconds': number, 'quality_passed': boolean})
        for e in value.get('episodes', [])]
    return result


def load_optional(path):
    return load_json(path.read_text()) if path.is_file() else None


def markdown(value):
    return html.escape(str(value)).replace('|', '\\|').replace('\n', '<br>')


def fmt(value, digits=3):
    if value is None:
        return '미측정/해당 없음'
    if type(value) is bool:
        return 'true' if value else 'false'
    return f'{value:.{digits}f}' if isinstance(value, (int, float)) else markdown(value)


def write_readme(output, manifest, events):
    attempt, score, qc = manifest['attempt'], manifest['evaluation'], manifest['quality']
    media = manifest['media']
    mode = '연결 시험' if attempt.get('mode') == 'wiring' else '자동 시연 수집 시도'
    rows = [f"# {mode} · {attempt['run_id']}", '',
        f"[전체 수집 기록](../../README.ko.md) · [구조화 요약](manifest.json) · [전체 행동 기록](decisions.jsonl) · [사용한 기본 프롬프트](prompt.txt)", '',
        f"실행 상태는 **{markdown(attempt.get('status'))}**, 원본 출처는 `{markdown(attempt.get('source'))}`입니다. "
        + ('작은 들기·정지·저장 연결을 확인한 시험이며 착의 성공 시연이 아닙니다.' if attempt.get('mode') == 'wiring'
           else '완료 상태와 과제 성공은 아래에서 따로 기록합니다.'), '',
        '## 실행 조건과 시간', '', '| 항목 | 기록 |', '|---|---|']
    facts = [
        ('기록 시작 UTC', attempt.get('started_at_utc')), ('기록 종료 UTC', attempt.get('ended_at_utc')),
        ('이전 시도', attempt.get('parent_attempt')), ('재시도 사유', attempt.get('retry_reason')),
        ('출처 그룹', attempt.get('source_group')), ('요청 모델 / 추론 설정',
            f"{attempt.get('model')} / {attempt.get('reasoning_effort')}"),
        ('전체 실제 경과 시간 (초)', attempt.get('wall_s')), ('Actor 호출 합계 (초)', attempt.get('actor_call_wall_s')),
        ('환경 요청·응답 합계 (초)', attempt.get('environment_dispatch_wall_s')),
        ('시뮬레이션 시간 (초)', attempt.get('simulation_time_s')),
        ('저장 전이 수', media.get('transitions')), ('응답 확인 전이 수', attempt.get('acknowledged_simulation_steps')),
        ('완료한 모델 결정 수', attempt.get('decisions_completed')),
        ('파일 완료 상태', manifest['capture'].get('complete')), ('데이터 정합성 검사', qc.get('quality_passed')),
        ('학습 데이터 승인', qc.get('training_approval', 'unreviewed')),
    ]
    rows.extend(f'| {key} | {fmt(value)} |' for key, value in facts)
    rows += ['', 'Actor 호출 시간은 공개 입력 준비·Docker/CLI 시작·요청과 응답을 포함합니다. 내부 모델 추론 시간만 별도로 측정한 값은 아닙니다. '
             '모델이 판단하는 동안 물리 시간은 멈추며 실제 경과 시간과 시뮬레이션 시간은 다릅니다.', '',
             '## 공식 평가 결과', '',
             f"평가 유효성 `{fmt(score.get('valid'))}` · 누적 점수 **{fmt(score.get('raw_points'))} / 50** · "
             f"착의 success **{fmt(score.get('success'))}** · rate 상태 `{fmt(score.get('score_status'))}` · "
             f"최종 rate {fmt(score.get('final_score'))} points/s.", '',
             '누적 50점, 착의 success, 정상 파일 종료와 데이터 정합성은 서로 다른 상태입니다. 접촉 전 `no_contact`의 rate는 0점/초로 바꾸지 않습니다.', '',
             '| 단계 | 획득 점수 / 최대 | 획득 시각 (episode 초) |', '|---|---:|---:|']
    for key, (label, maximum) in SCORES.items():
        rows.append(f"| {label} | {fmt(score.get('breakdown', {}).get(key))} / {maximum} | "
                    f"{fmt(score.get('milestone_times_s', {}).get(key))} |")
    rows += ['', '## 단계 획득 경로', '',
             '점수 획득은 [평가 이벤트](score-events.jsonl)에서 같은 physics tick끼리 묶었습니다. '
             '같은 시각에 인정된 항목의 내부 순서는 추정하지 않습니다. 착의 success는 점수 획득과 별도로 기록합니다.', '',
             '| 순서 | episode 시간 (초) | 전이 경계 step | 누적 점수 변화 | 같은 시각의 항목 변화 |',
             '|---:|---:|---:|---:|---|']
    path = manifest['milestone_path']
    for batch in path['award_batches']:
        changes = ', '.join(f"{SCORES[c['stage']][0]} {fmt(c['before'])}→{fmt(c['after'])}" for c in batch['changes'])
        rows.append(f"| {batch['batch_index']} | {fmt(batch['evaluation_time_s'])} | {batch['transition_boundary_step']} | "
                    f"{fmt(batch['raw_points_before'])}→{fmt(batch['raw_points_after'])} | {changes} |")
    if not path['award_batches']:
        rows += ['| — | — | — | — | 기록된 공식 항목 획득 없음 |']
    rows += ['', f"평가 clock 0초에 대응하는 공개 simulation clock은 {fmt(path['time_origin_public_simulation_s'])}초입니다. "
             '두 시계를 같은 절대 시각으로 혼동하지 않습니다.', '',
             f"별도 success 이벤트 수: **{len(path['success_events'])}**. 평가 유효성: `{fmt(path['evaluation_valid'])}`.", '']
    if path['success_events']:
        rows += ['success 시각 (episode 초): ' + ', '.join(fmt(e['evaluation_time_s']) for e in path['success_events']), '']
    rows += ['', '## 원본 관측 화면', '']
    if media.get('images'):
        rows += ['지정된 공개 카메라의 저장 RGB 픽셀입니다. 시작은 첫 `obs`, 종료는 마지막 `next_obs`입니다. '
                 '이미지 합성이나 내부 상태 기반 장면 재구성 없이 원본 픽셀로 PNG를 저장했습니다.', '',
                 '| 카메라 | 시작 | 종료 |', '|---|---|---|']
        for camera in CAMERAS:
            first, last = f'images/initial-{camera}.png', f'images/final-{camera}.png'
            rows.append(f'| `{camera}` | [![시작 {camera}]({first})]({first}) | [![종료 {camera}]({last})]({last}) |')
        rows += ['', f"시작 관측 시각 {fmt(media.get('initial_simulation_time_s'))}초 · "
                     f"종료 관측 시각 {fmt(media.get('final_simulation_time_s'))}초 (공개 simulation clock).", '']
    else:
        rows += ['사용 가능한 저장 카메라 프레임이 없습니다. 이미지나 영상을 만들어 성공 장면처럼 표시하지 않습니다.', '']
    video = media.get('video', {})
    if video.get('created'):
        rows += ['[▶ overview 관측 영상 보기](overview.mp4)', '',
                 f"저장된 20 Hz `obs` 중 {video['exported_frames']}프레임을 순서대로 사용했습니다. "
                 f"재생은 **{video['slowdown_factor']}배 느리게** ({fmt(video['playback_fps'])} fps), "
                 '실제 대기 시간·모델 호출 지연은 영상에 들어가지 않습니다. 종료 `next_obs`는 위 PNG에서 확인합니다.']
        if video['truncated']:
            rows += [f"명시된 영상 한도에 따라 전체 {video['available_frames']}프레임 중 앞부분만 내보냈습니다. "
                     f"샘플링 없이 연속된 처음 {video['exported_frames']}프레임입니다."]
        rows.append('')
    rows += ['## 결정과 실행 순서', '',
             '아래 근거는 모델 최종 JSON의 짧은 행동 설명입니다. 시각적 평가는 행동 전 관측에 대한 판단이며, '
             '그 행동의 실행 후 성공 라벨로 사용하지 않습니다. 공식 점수는 별도의 평가 결과입니다.', '',
             '행동의 각 행은 로봇 0·1 순서이며 열은 `전진, 왼쪽 이동, 반시계 회전, 리프트, 팔 신장, 손목 yaw, pitch, roll, gripper`입니다. '
             '앞 8개는 정규화 속도이고 gripper는 닫기 `+1`, 열기 `-1`, 의도 유지 `0`입니다.', '']
    segments = {e['decision_index']: e for e in events if e['type'] == 'applied_segment'}
    for event in events:
        kind = event['type']
        if kind == 'decision':
            decision, i = event['decision'], event['decision_index']
            segment = segments.get(i)
            rows += [f"### 결정 {i} · {STAGES.get(decision.get('stage'), decision.get('stage'))} · `{decision.get('tool')}`", '',
                     f"입력 관측 {fmt(event.get('observation_simulation_time_s'))}초 · Actor 호출 {fmt(event.get('wall_s'))}초 · "
                     f"시각적 판단 `{markdown(decision.get('visual_assessment'))}`.", '',
                     f"최종 응답의 행동 설명: {markdown(decision.get('reason', ''))}", '',
                     '요청 행동:', '', '```json', json.dumps(decision.get('action'), ensure_ascii=False), '```', '']
            if segment:
                rows += [f"실행 구간 step **[{segment.get('start_step')}, {segment.get('end_step')})** · "
                         f"요청 {segment.get('requested_steps')} step / 실제 {segment.get('actual_steps')} step · "
                         f"환경 요청·응답 {fmt(segment.get('environment_dispatch_wall_s'))}초.", '',
                         '실제 적용 행동:', '', '```json', json.dumps(segment.get('applied_action'), ensure_ascii=False), '```', '']
            else:
                rows += ['대응하는 실행 완료 응답이 없습니다. 행동이 적용되었다고 확정하지 않습니다.', '']
        elif kind == 'model_error':
            rows += [f"### 호출 실패 · 결정 {event.get('decision_index')}", '',
                     f"오류 종류 `{markdown(event.get('error_type'))}` · 사용 시간 {fmt(event.get('actor_call_wall_s'))}초.", '',
                     markdown((event.get('error') or {}).get('message', '')), '']
        elif kind == 'supervisor_stop':
            rows += [f"수집기 정지: `{markdown(event.get('reason'))}` · 중립 명령 {event.get('neutral_steps')} step.", '']
    if not events:
        rows += ['모델 결정이나 실행 구간이 생성되기 전에 종료되었습니다.', '']
    if attempt.get('error'):
        rows += ['## 종료 오류', '', f"`{markdown(attempt['error'].get('type'))}`: "
                 + markdown(attempt['error'].get('message', '')), '']
    rows += ['## 검수와 후속 판단', '',
             f"현재 데이터 승인은 `{markdown(qc.get('training_approval', 'unreviewed'))}`입니다. "
             '형식과 시간 정합성 검사를 통과해도 시연의 유용성이나 착의 성공을 보장하지 않습니다.', '',
             '이 페이지의 원본 파일 SHA256과 생성 파일 SHA256은 [manifest.json](manifest.json)에 있습니다. '
             '실행 실패도 같은 run ID와 부모 시도 관계로 보존합니다. 공개 범위는 카메라, 최종 행동 응답, 시간, 평가 요약입니다.', '']
    date = str(attempt.get('started_at_utc', ''))[:10]
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}', date) and (output.parents[1] / 'feedback' / (date + '.jsonl')).is_file():
        rows += [f'[개발 피드백과 변경 근거](../../feedback/{date}.jsonl)', '']
    (output / 'README.ko.md').write_text('\n'.join(rows))


def export_media(policy_path, output, *, video=False, max_video_frames=2000, slowdown=None):
    result = {'available': policy_path.is_file(), 'transitions': None, 'images': [],
              'video': {'created': False, 'requested': video}}
    if not policy_path.is_file():
        result['status'] = 'no_policy_file'
        return result
    with h5py.File(policy_path, 'r') as file:
        episodes = list(file.get('data', {}))
        if not episodes:
            result.update(status='no_recorded_episode', transitions=0)
            return result
        if len(episodes) != 1:
            raise ValueError('public attempt exporter requires one episode; split reports explicitly')
        episode = file['data'][episodes[0]]
        if 'actions' not in episode or not len(episode['actions']):
            result.update(status='no_recorded_transition', transitions=0)
            return result
        count = len(episode['actions'])
        result.update(status='recorded_public_frames', episode=identifier(episodes[0]), transitions=count,
                      file_complete=bool(file.attrs.get('complete', False)),
                      initial_simulation_time_s=float(episode['obs/simulation_time_s'][0, 0]),
                      final_simulation_time_s=float(episode['next_obs/simulation_time_s'][-1, 0]))
        (output / 'images').mkdir()
        for label, group, index in [('initial', 'obs', 0), ('final', 'next_obs', -1)]:
            for camera in CAMERAS:
                pixels = episode[f'{group}/{camera}_rgb'][index]
                if pixels.dtype != np.uint8 or pixels.ndim != 3 or pixels.shape[-1] != 3:
                    raise ValueError('unexpected public camera shape/dtype')
                path = Path('images') / f'{label}-{camera}.png'
                Image.fromarray(pixels).save(output / path)
                result['images'].append(str(path))
        if video:
            executable = shutil.which('ffmpeg')
            if not executable:
                raise ValueError('ffmpeg is required for --video')
            frames = min(count, max_video_frames)
            slow = slowdown if slowdown is not None else (20 if count < 20 else 1)
            fps = 20 / slow
            dataset = episode['obs/overview_rgb']
            height, width, channels = dataset.shape[1:]
            if channels != 3 or width % 2 or height % 2:
                raise ValueError('video requires even image dimensions and RGB')
            command = [executable, '-hide_banner', '-loglevel', 'error', '-nostdin', '-f', 'rawvideo',
                       '-pixel_format', 'rgb24', '-video_size', f'{width}x{height}', '-framerate', str(fps),
                       '-i', 'pipe:0', '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20',
                       '-threads', '2', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output / 'overview.mp4')]
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            try:
                for index in range(frames):
                    process.stdin.write(dataset[index].tobytes())
                process.stdin.close()
                process.stdin = None
                process.communicate(timeout=120)
                if process.returncode:
                    raise RuntimeError('ffmpeg failed; report export aborted')
            except BaseException:
                process.kill(); process.wait(timeout=10)
                raise
            finally:
                process.stderr.close()
            result['video'] = {'created': True, 'requested': True, 'file': 'overview.mp4',
                               'source': 'obs/overview_rgb', 'source_policy_hz': 20,
                               'available_frames': count, 'exported_frames': frames,
                               'maximum_frames': max_video_frames, 'truncated': frames < count,
                               'sampling': 'contiguous_prefix_no_frame_skipping',
                               'slowdown_factor': slow, 'playback_fps': fps,
                               'playback_duration_s': frames / fps, 'includes_wall_time_waits': False}
    return result


def export_report(trace, collection, output, *, video=False, max_video_frames=2000, slowdown=None):
    trace, collection, output = Path(trace), Path(collection), Path(output)
    if output.exists():
        raise FileExistsError('report output already exists')
    if type(max_video_frames) is not int or max_video_frames < 1:
        raise ValueError('max_video_frames must be positive')
    if slowdown is not None and (type(slowdown) not in (int, float) or not math.isfinite(slowdown) or slowdown <= 0):
        raise ValueError('slowdown must be positive and finite')
    raw_attempt = load_json((trace / 'attempt.json').read_text())
    attempt = public_attempt(raw_attempt)
    if attempt.get('status') not in ('completed', 'failed', 'interrupted'):
        raise ValueError('wait until the attempt stops before exporting its report')
    prompt = text((trace / 'prompt.txt').read_text(), max_length=262144)
    if attempt.get('prompt_sha256') != sha256(trace / 'prompt.txt'):
        raise ValueError('prompt hash differs from recorded attempt')
    events, skipped = public_events(trace / 'decisions.jsonl')
    capture_raw = load_optional(collection / 'capture.json') or {}
    capture = select(capture_raw, {'schema': identifier, 'complete': boolean, 'termination_reason': identifier,
        'raw_archive': boolean, 'wall_s': number, 'requests': integer, 'steps': integer,
        'idle_render_calls': integer, 'idle_render_wall_s': number,
        'evaluation_enabled': boolean, 'evaluation_valid': boolean})
    evaluation = load_optional(collection / 'evaluation_summary.json')
    score = public_score(evaluation.get('report') if isinstance(evaluation, dict) else None)
    score_events, score_path = public_score_events(collection, evaluation)
    quality_raw = load_optional(collection / 'validation.json')
    quality = public_qc(quality_raw)
    sources = {}
    for prefix, parent, names in [('trace', trace, ['attempt.json', 'prompt.txt', 'decisions.jsonl']),
                                  ('capture', collection, ['capture.json', 'policy.hdf5', 'audit.hdf5',
                                                          'evaluation_summary.json', 'validation.json'])]:
        for name in names:
            path = parent / name
            if path.is_file():
                sources[f'{prefix}/{name}'] = {'sha256': sha256(path), 'bytes': path.stat().st_size}
    if score_path:
        sources['capture/score_events.jsonl'] = {'sha256': sha256(score_path), 'bytes': score_path.stat().st_size}
    for name in ('policy.hdf5', 'audit.hdf5'):
        expected = capture_raw.get('files', capture_raw.get('checksums', {})).get(name)
        actual = sources.get('capture/' + name, {}).get('sha256')
        if expected is not None and expected != actual:
            raise ValueError('capture hash mismatch before public export')
        qc_hash = (quality_raw or {}).get('sha256', {}).get(name)
        if qc_hash is not None and qc_hash != actual:
            raise ValueError('quality report refers to a different source file')
    manifest = {'schema': 'phyrc-public-attempt-report-v1', 'attempt': attempt, 'capture': capture,
                'quality': quality, 'evaluation': score, 'source_files': sources,
                'unrecognized_events_omitted': skipped,
                'publication_review': 'generated_allowlisted_subset_requires_repository_review',
                'decision_reason_scope': 'final_action_explanation_only',
                'artifacts': {}}
    # All text selected above has passed the privacy checks before creating an
    # output directory. A failed media export removes only this newly made path.
    output.mkdir(parents=True, exist_ok=False)
    try:
        (output / 'prompt.txt').write_text(prompt)
        with (output / 'decisions.jsonl').open('x') as stream:
            for event in events:
                stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n')
        with (output / 'score-events.jsonl').open('x') as stream:
            for event in score_events:
                stream.write(json.dumps(event, ensure_ascii=False, allow_nan=False) + '\n')
        manifest['media'] = export_media(collection / 'policy.hdf5', output, video=video,
                                         max_video_frames=max_video_frames, slowdown=slowdown)
        manifest['milestone_path'] = milestone_path(score_events, valid=score['valid'],
            simulation_origin=manifest['media'].get('initial_simulation_time_s'))
        write_readme(output, manifest, events)
        for path in sorted(output.rglob('*')):
            if path.is_file():
                manifest['artifacts'][str(path.relative_to(output))] = {'sha256': sha256(path), 'bytes': path.stat().st_size}
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    except BaseException:
        shutil.rmtree(output)
        raise
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-id', required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--output', type=Path, required=True, help='New directory; never overwrites an existing report')
    parser.add_argument('--video', action='store_true')
    parser.add_argument('--max-video-frames', type=int, default=2000,
                        help='Explicit continuous-prefix video limit, recorded in the manifest and page')
    parser.add_argument('--slowdown', type=float, help='Playback slowdown; default 20x for under 20 frames, otherwise 1x')
    args = parser.parse_args()
    identifier(args.run_id)
    if ':' in args.run_id:
        parser.error('run-id must be a directory basename')
    result = export_report(args.root / 'output/operator-traces' / args.run_id,
                           args.root / 'output/collections' / args.run_id, args.output,
                           video=args.video, max_video_frames=args.max_video_frames, slowdown=args.slowdown)
    print(json.dumps({'run_id': result['attempt']['run_id'], 'status': result['attempt']['status'],
                      'frames': result['media']['transitions'], 'video': result['media']['video']['created'],
                      'quality_passed': result['quality'].get('quality_passed')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
