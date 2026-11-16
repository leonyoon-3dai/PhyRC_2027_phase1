# 사용자 피드백 시연 실행 계약

[현재 계획](../COLLECTION_PLAN.md) · [Astra 코드](../ASTRA.md) · [환경 복원](../OPERATIONS.md) · [현재 상태](../project/STATUS.md)

`codex_client --user-guided`는 초기 상태와 종료 제안·soft 예산·첫 소매 새5점에서 물리0 HOLD한다. 이 문서는 구현 인터페이스이며 실제 GPU·모델 검증 결과는 STATUS에서 확인한다. 기존 E36 원본을 덮어쓰지 않으며 각 준비·검증·본시연에 고유 run ID를 쓴다.

## 1. 준비 실행

고정 HF revision의 자산·E36 원본을 복원·QC한 뒤, 고정 Codex CLI0.166.0 환경과 simulator를 검증한다. 다음은 E36/933을 새 환경에서 행동 재실행하여 출발 후보를 저장하는 명령 형태다. `RUN_ID`는 실제 고유 이름으로 바꾼다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id RUN_ID --mode dressing --user-guided \
  --actor-backend exec --model gpt-6-astra --effort ultra --plan-size 1 \
  --replay-prefix-run 20261114-astra-wrist-body835-001 --replay-prefix-steps 933 \
  --max-steps 2400 --save-checkpoint-on-start --prepare-checkpoint-only
```

이 모드는 replay933 → HOLD → 고유 checkpoint 저장 → 공개5카메라 export → 물리0 finish로 마감한다. 모델 행동을 호출하지 않는다. 게시물은 마감한 준비 상태로 표시되며 현재 live HOLD로 설명하지 않는다. 결과는 `output/operator-traces/RUN_ID/start-checkpoint.json`과 collection의 checkpoint 디렉터리에 기록된다. 슬롯 경로는 실제 반환값을 사용한다.

준비 모드 없이 `--save-checkpoint-on-start`를 쓰면 첫 경계에서 실제 사용자 HOLD를 유지한다. 부적합한 펼침·파지·손 관계라면 이 경로에서 화면을 게시하고 사용자 판단을 받는다.

## 2. 저장·복원·정착·짧은 행동 검증

준비 슬롯을 별도 고유 검증 실행에서 복원한다. 기존 기본 정착90 control ticks를 유지하고 저장 직전/복원 직후/정착 후의 공개 관측, 로봇 상태, 다음 짧은 행동의 효과를 비교한다. 슬롯은 근사 복원이며 solver cache·속도 등 초기화 요소를 기록한다. 검증 전이가 첫 소매를 새로 만든 것인지 기존 상태를 재평가한 것인지 분리한다.

검증 증거를 확인한 운영자는 아래 receipt를 비공개 `output/`에 작성한다. boolean을 채우는 행위가 검증을 수행하지는 않는다. 시각 적합성이 불명확하면 validated로 표시하지 않고 사용자 화면 검토를 요청한다.

```json
{
  "schema": "phyrc-start-state-validation-v1",
  "status": "validated",
  "initial_slot": "/output/collections/PREPARE_RUN/checkpoints/KEY/slot_KEY.npz",
  "slot_sha256": "ACTUAL_SHA256",
  "first_sleeve_baseline": 0,
  "checks": {
    "save_restore": true,
    "settled_public_state": true,
    "next_action_effect": true,
    "visual_suitability": true
  },
  "evidence": [{"path": "output/ACTUAL_VALIDATION_RECORD.json", "sha256": "ACTUAL_SHA256"}]
}
```

helper는 슬롯 경로·SHA와 각 근거 파일 SHA를 확인하고 네 검증 항목 및 최초 평가 기준을 요구한다. receipt 원본은 새 trace의 `start-state-validation.json`에 복사한다. 검증 기준을 만족한 동일 슬롯만 초기 사용자 HOLD를 생략할 수 있다.

## 3. 검증된 슬롯에서 M1

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id NEW_RUN_ID --mode dressing --user-guided \
  --actor-backend exec --model gpt-6-astra --effort ultra --plan-size 1 \
  --initial-slot /output/collections/PREPARE_RUN/checkpoints/KEY/slot_KEY.npz \
  --start-state-validation output/ACTUAL_VALIDATION_RECEIPT.json \
  --segment-decisions 20 --segment-steps 400 --max-steps 2400 \
  --named-actions --model-timeout 180
```

경로와 ID를 실제 값으로 바꾼다. 슬롯 출처는 `--parent-attempt`와 `--retry-reason`, `--source-group`으로 이어서 명시한다. 슬롯에서 바로 M1을 시작할 때는 replay 옵션을 생략한다. 슬롯으로 시작했던 이전 시연의 경계를 재현할 때는 아래3a절의 출처 검증을 거쳐 같은 슬롯과 replay를 함께 사용한다. 최초 M1은 현재 파지를 유지하는 국소 교정이며 첫 교정은2–4전이(0.1–0.2시뮬레이션초)로 시작해 실제 효과를 확인하고 공식 범위 안에서 조정하도록 지시한다. 이는 고정 좌표나 정답 행동을 지정하지 않는다. M1/M2의 open 제안은 실행 전에 HOLD한다. 같은 상태의 M2/M3 전환은 사용자 응답에서 선택한다.

`--pixel-depth-query`는 현재 guided 경로와 함께 사용할 수 없다. 기본 공개 depth 요약, `--named-actions`, 선택적 `--wrist-depth-panel`, `--post-action-settle-steps 0..20`을 지원한다. act와 settle 합계가 soft 예산을 넘으면 그 행동 전체를 폐기하고 HOLD한다. 공식 hard horizon에 닿기 전 최소1전이를 남기며 하드 경계에서는 새 checkpoint 분기 또는 종료만 받는다. raw pickup점수를 첫 소매 목표로 사용하지 않는다.

## 3a. 같은 시작 슬롯에서 이전 시연의 경계 재현

이전 시연이 `initial_slot`으로 시작했다면, 그 행동을 일반 무작위 reset에서 재생하지 않는다. `--initial-slot`과 `--replay-prefix-run`의 조합은 `--user-guided`에서만 허용하며, source의 `run_metadata.initial_slot`과 선택한 슬롯의 **경로·SHA256·receipt 경로와 SHA256·source group·직접 슬롯 parent**가 일치해야 한다. 빠진 정보, 다른 슬롯, 바뀐 receipt/파일, symlink는 재생 전에 거절한다. source가 일반 seed reset으로 시작했다면 슬롯을 덧붙일 수 없다. 기존 일반 replay는 동일 seed reset 경로를 유지한다. simulator의 기존 슬롯 형상·코드·자산 검증도 그대로 적용한다.

현재 run의 과거 HOLD로 돌아가는 예에서는 먼저 해당 run을 `checkpoint` 응답으로 물리0 마감하고 **전체 원본의 QC·보존**을 완료한다. 불완전 live capture나 검토용 고정 사본으로 정상 replay gate를 우회하지 않는다. 그다음 별도 고유 run에서 원래 시작 슬롯을 복원하고 선택 경계까지 기록된 행동을 다시 실행한다. 아래는 `20261116-astra-m1-checkpoint-001`의 HOLD10 경계110을 대상으로 한 명령 형태다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id NEW_REPLAY_RUN --mode dressing --user-guided \
  --actor-backend exec --model gpt-6-astra --effort ultra --plan-size 1 \
  --initial-slot /output/collections/20261116-e36-checkpoint-001-original/checkpoints/20261116-e36-checkpoint-001-slot/slot_20261116-e36-checkpoint-001-slot.npz \
  --replay-prefix-run 20261116-astra-m1-checkpoint-001 --replay-prefix-steps 110 \
  --save-checkpoint-on-start --max-steps 2400 \
  --named-actions --model-timeout 180
```

실제 원본은120전이 전체가 정상 마감·QC를 통과해야 하며, 선택된 prefix는 **actions[0:110]**, 목표 관측은 **next_obs[109]**다. 재생 요청을 묶어도 모든 원본 행동과 순서를 보존하며 추가 settle/stop 전이를 삽입하지 않는다. 첫110전이는 새 정책 성과가 아니라 replay로 기록한다. 직접 parent는 이전 run, source group은 같은 E28 계보를 유지한다.

원래 슬롯의90 control ticks 정착은 유지한다. 초기와 재생 말단의 공개 로봇 상태 차이를 `attempt.json`의 continuation에 기록하지만, 이 수치만으로 천 상태의 동일성을 보장하지 않는다. 새5카메라·depth·파지·손 관계를 과거 HOLD10과 비교한다. **물리 solver의 정확한 시간 되감기가 아니라 근사 슬롯 복원과 행동 재실행**이다.

슬롯 원본의 `--start-state-validation`을 replay와 함께 지정하면 거절한다. 원래 시작 슬롯의 검증을110전이 뒤 상태의 검증으로 대신할 수 없기 때문이다. 재생 말단에서는 모델 행동을 호출하기 전에 실제 `start_state_review` HOLD를 만들고, 선택한 경우 고유 checkpoint를 저장한다. 게시·관측 비교·사용자 지시 처리 뒤 새 방향의 시연을 시작한다. 출발 관계가 달라졌다면 기존 HOLD10과 동일하다고 표시하지 않고 차이를 먼저 검토한다.

## 4. HOLD 게시와 사용자 응답

사용자 검토에는 **구간별 움직임 GIF와 최종5카메라를 함께 게시**한다. 실제 기록의 모든 경계를 사용하고 원래 시간·배속·끝점 정지를 표시한다. 열린 원본을 닫거나 live 파일을 직접 분석하지 않고, HOLD 경계와 원본 해시가 복사 전후 같은 고정 사본을 확보한 뒤 `scripts/export_held_segments.py`로 export한다. [현재 GIF와 사본·프레임 검증](../gallery/20261116-m1-guided-segments/README.ko.md). 게시 receipt의 자동 gate는 아래5카메라를 검증하며, GIF의 원격 SHA 확인도 운영자가 별도로 수행한다.

HOLD가 출력되면 다음 두 디렉터리를 확인한다.

- 공개: `docs/collection/user-reviews/RUN_ID/hold-NNNN/` — 같은 경계의 RGB5장, 패널, metadata, 설명.
- 비공개: `output/operator-traces/RUN_ID/user-review/hold-NNNN/` — 공개 관측 원본과 depth/valid, HOLD metadata, 게시 receipt, 응답 inbox.

운영자는 README 최상단 `PHYRC_USER_REVIEW:START/END` 영역에 현재 run/HOLD/관측·사유와 패널·5원본 링크를 붙이고 새 공개 파일과 함께 push한다. 로봇 배치는 왼쪽 R1·오른쪽 R0, 위 head·아래 wrist다. 원격5이미지의 bytes와 현재 README run/HOLD를 확인한 후 비공개 HOLD 디렉터리에 `published.json`을 원자적으로 쓴다.

```json
{
  "run_id": "RUN_ID",
  "hold_id": "hold-0001",
  "observation_id": "EXACT_HOLD_OBSERVATION_ID",
  "commit_sha": "ACTUAL_40_HEX_COMMIT",
  "verified_camera_sha256": {
    "overview": "ACTUAL_SHA256",
    "robot_1_head": "ACTUAL_SHA256",
    "robot_0_head": "ACTUAL_SHA256",
    "robot_1_wrist": "ACTUAL_SHA256",
    "robot_0_wrist": "ACTUAL_SHA256"
  }
}
```

helper는 이 receipt와 HOLD metadata의 일치를 확인한다. 원격 접근 확인 자체는 운영자의 게시 단계이며, helper가 GitHub에 자동 push하거나 원격 bytes를 독립 검증하지는 않는다. 게시 실패 또는 receipt 부재에서 계속 HOLD한다. 게시 receipt만으로 재개하지 않는다.

사용자에게 원격 링크와 다음 선택을 질문한 뒤 **실제 사용자 답변**을 다음 JSON으로 `inbox/MESSAGE_ID.json`에 원자적으로 전달한다. 게시 또는 일반 준비 승인을 사용자 행동 답변으로 꾸며 넣지 않는다.

```json
{
  "run_id": "RUN_ID",
  "hold_id": "hold-0001",
  "observation_id": "EXACT_HOLD_OBSERVATION_ID",
  "message_id": "unique-message-id",
  "action": "continue",
  "text": "사용자가 요청한 공개 관측 기반 작업 방향",
  "segment_decisions": 20,
  "segment_steps": 400
}
```

| action | 추가 필드 | 처리 |
|---|---|---|
| `continue` | 선택적 구간 예산 | 같은 상태에서 새 관측 기반 판단. 이전 pending 행동은 재사용하지 않음 |
| `change_method` | `method`: `M1`, `M2`, `M3` | 같은 상태에서 방법 변경·새 구간 |
| `checkpoint` | `checkpoint`: 선택한 출발점 | 현재 run을 물리0 마감하고 선택을 기록. 운영자가 새 run 복원·QC·계보 연결 |
| `finish` | 없음 | 물리0 정상 마감 후 운영자가 전수 QC·백업 |

stale run/HOLD/관측, 중복 message ID, 잘못된 예산은 거절한다. 원문·수신 시각·적용 경계는 비공개 `decisions.jsonl`에 남는다. actor에는 공개 관측·허용된 작업 지시만 전달한다. 사용자 응답은 환경 reset이나 과거 점수 초기화를 허용하지 않는다.

모델 오류는 행동 미전송과 simulator 생존이 확인된 경우 HOLD한다. 이후 실제 계속 응답에는 새 격리 actor 세션을 만든다. 불명확한 ACK·실제 종료는 정상 HOLD라고 표시하지 않는다. 감독 프로세스가 실패하면 추가 stop/finish를 보내지 않고 stdin을 닫으며 collector는 orphan HOLD한다. 이것은 사용자 응답 가능한 정상 supervisor의 생존과 구분하며, 서버/cgroup 장애 생존 보장이 아니다.
