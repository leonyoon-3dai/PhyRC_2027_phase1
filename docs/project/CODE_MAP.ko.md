# 코드 지도: 관측에서 로봇 행동과 수집 파일까지

[전체 개요](../../README.md) · [시간순 갤러리](../gallery/README.ko.md) · [Astra 단계별 설명](../collection/guides/astra-end-to-end.ko.md) · [현재 상태](STATUS.md) · [새 서버 준비](START_HERE.ko.md)

**확인 기준: 2026-11-10, 소스 `ae434d08ddd4b384fbc8648bd9cf470e5b201ea5`.** 실제 수집은 E27 종료·최고5/50·착의0이며 E28은 미시작입니다. 문서 정리로 GPU·모델·학습 검사를 재실행한 것은 아닙니다. 이전 E15 기준의 “픽셀 질의 미적용” 설명은 현재 코드와 E18 이후 시연에는 적용되지 않습니다.

## 1. 폴더를 읽는 순서

| 위치 | 역할 | 먼저 볼 파일 |
|---|---|---|
| `docs/gallery/` | 사람·Astra의 실제 장면과 변화 | [시간순 갤러리](../gallery/README.ko.md) |
| `docs/collection/` | 수집 방식·시도·리뷰·계보 | [수집 안내](../collection/README.ko.md), [catalog](../collection/catalog/README.ko.md) |
| `docs/project/` | 목표·현재 상태·날짜별 기록·복원 | [STATUS](STATUS.md), [최신 마감](SESSION_WRAPUP_20261107.ko.md) |
| `participant/collection/` | 관측→모델→행동 검사→수집 조율 | [`codex_client.py`](../../participant/collection/codex_client.py) |
| `src/PhyRC_Sim/Policy/` | 공식 행동 적용과 HDF5 기록 | [`environment.py`](../../src/PhyRC_Sim/Policy/environment.py), [`training_dataset.py`](../../src/PhyRC_Sim/Policy/training_dataset.py) |
| `participant/pi05/` | 자료 선택·변환·정책 학습 연결 | [`data.py`](../../participant/pi05/data.py), [`preprocessing.py`](../../participant/pi05/preprocessing.py) |
| `participant/ops/` | 환경 점검·제출 포장·검사 | [`bootstrap.sh`](../../participant/ops/bootstrap.sh) |

`run.sh`·Dockerfile은 공식 환경 진입점입니다. 장면·사람 조작의 큰 구현은 [`Teleop_TShirt_Stretch4_Env.py`](../../src/PhyRC_Sim/Env_StandAlone/Teleop_TShirt_Stretch4_Env.py), 공개 계약은 [`policy_interface.json`](../../config/policy_interface.json)입니다. 실제 설치·복원 명령은 [START_HERE](START_HERE.ko.md)에서 확인합니다.

## 2. 두 수집 방식의 진입점

| 방식 | 행동을 정하는 주체 | 로봇으로 가는 경로 | 기록 |
|---|---|---|---|
| 사람 Chrome teleop | 화면을 보고 키를 누르는 사람 | 키 상태→로봇 명령 | 기본 deferred export, ESC 뒤 READY까지 대기 |
| Astra 자동 시연 | 공개 RGB-D·상태를 보는 모델 | CLI JSON→검사→operator→공식 환경 | 실행 중20Hz 즉시 저장, 이후 QC·영상·점수 |
| 연결 시험 | 제한된 작은 시험 입력·시험 모델 | 같은 계약을 작은 예산으로 통과 | 착의 시연과 별도 분류 |
| 사람 수정 시연 | 사람·모델 출처를 구분하는 계약 | source=`human_corrected_gpt` | 실시간 제어권 handoff가 구현됐다는 뜻은 아님 |

현재 자동 수집은 Chrome·WebRTC OFF입니다. [`gpt_client.py`](../../participant/collection/gpt_client.py)는 별도 Responses API 시험이며 현재 CLI 경로가 아닙니다. [`codex_app_actor.py`](../../participant/collection/codex_app_actor.py)의 App Server 경로는 실제 호환성 검증 미통과로 보류했습니다.

## 3. 자동 수집의 함수 연결

전체 단계와 코드 예제는 [Astra end-to-end](../collection/guides/astra-end-to-end.ko.md)를 봅니다. 아래 줄 링크는 확인한 고정 소스로 연결합니다.

| 순서 | 함수·파일 | 실제 역할 |
|---|---|---|
| 관측 준비 | [`prepare_observation()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/codex_client.py#L397) | RGB5·상태 JSON·16×16 depth 요약, 원본 공개 depth 보존 |
| 선택 입력 | [`replay_image_context()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/codex_client.py#L448), [`wrist_depth.py`](../../participant/collection/wrist_depth.py) | 같은 새 episode의 과거 RGB·현재 손목 depth 패널 |
| 모델 호출 | [`Actor.invoke()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/codex_actor.py#L305) | 격리 CLI에 공개 입력·schema 전달, 완결된 최종 JSON 수신 |
| 선택 깊이 질의 | [`depth_query.py`](../../participant/collection/depth_query.py) | `freeze_public_frame()`·`route_initial()`·`lookup()`으로 현재 픽셀 조회, 물리0·후속 호출1회 |
| 이름 변환 | [`pack()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/named_actions.py#L48) | 명령 이름을 공식2×9 순서로 재배열, 값 보정·IK 없음 |
| 행동 검사 | [`validate_decision()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/codex_client.py#L362), [`validate_action()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/boundary.py#L20), [`plans.py`](../../participant/collection/plans.py) | schema·형태·유한값·범위·steps·고정 행동 목록 검사 |
| 요청·응답 | [`Simulator.dispatch()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/codex_client.py#L532) | JSON Lines observe·act·stop·finish_episode |
| 환경 구성 | [`collect_operator.main()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/scripts/collect_operator.py#L158) | 신뢰된 별도 프로세스에 환경·writer·평가·operator 구성 |
| 전이 실행 | [`Operator.act()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/boundary.py#L62) | 요청한 각 step마다 env.step과 writer.append |
| 물리·제어 | [`DressingEnv.step()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/src/PhyRC_Sim/Policy/environment.py#L268) | 두 로봇 명령·0.05초 물리 진행·다음 관측 |
| 동기 저장 | [`DatasetWriter.append()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/src/PhyRC_Sim/Policy/training_dataset.py#L87) | obs·실제 action·next_obs와 별도 audit |
| 전수 검사 | [`validate_capture()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/validate_capture.py#L169) | 완료·전이·SHA·평가 요약 정합성 |
| 공개·보존 | [`export_report.py`](../../participant/collection/export_report.py), [`preserve_collection.py`](../../scripts/preserve_collection.py) | 허용된 공개 자료 선별, 닫힌 원본의 허용 목록 보존 |

E18부터 실제 픽셀 질의, E19부터 named action을 사용했습니다. E15는 RGB5+현재 손목 depth 패널1이고 과거 이미지 주입은 없었습니다. 입력 추가와 착의 득점 개선은 별도 검증입니다.

`boundary.py`는 허용 필드 경계이며 OS 격리 자체가 아닙니다. `codex_actor.py`가 별도 Docker 파일시스템·내부망·제한된 송신과 tool-event 거부를 구현합니다. 같은 episode에서 CLI resume으로 문맥을 이어가고 다른 실험의 기억은 자동 공유하지 않습니다. 저장소·audit·점수·seed·내부 옷 상태를 행동 세션에 연결하지 않습니다.

## 4. 데이터와 시간의 계약

| 항목 | 형태·주기 | 읽는 법 |
|---|---|---|
| RGB | `(5,256,256,3)` | overview·양 손목·양 머리 |
| depth / valid | 각각 `(5,256,256,1)` | 광축 Z(m)·유효성. invalid는 빈 공간 아님 |
| 관절 위치·속도 | 각각 `(2,13)` | 측정 관절13개씩 |
| 제어기 목표·직전 행동 | 각각 `(2,9)` | 실제 관절 상태와 별개 |
| 실행 행동 | `float32 (2,9)` | 로봇2×명령9=18개 |
| HDF5 행동 | `(N,18)` | 실제 행동을 펼쳐 저장 |
| 한 전이 |0.05로봇초|20Hz 경계·60Hz 제어3회·240Hz 물리12tick|
| 한 모델 판단 |최대20전이 요청|호출·판단·전이·episode는 다른 수|

표시용 로봇 비교 화면은 **왼쪽 robot_1·오른쪽 robot_0**으로 통일합니다.4분할은 윗행 머리·아랫행 손목이며, 이 표시 순서는 원본 RGB5 배열과 행동 행0/행1의 계약을 변경하지 않습니다.

행동 순서는 전후·좌우·base yaw·lift·arm extension·wrist yaw/pitch/roll·gripper입니다. 앞8개는 속도 비율이고 gripper는 `>0.5`닫기·`<−0.5`열기·중간은 이전 의도 유지입니다.

선택한 중립6전이는0.3초이며 `action_source=controller_settle`로 구분합니다.0명령은 실제 정지·목표 도달·파지 성공 인증이 아닙니다. [`step_profile.py`](../../participant/collection/step_profile.py)는 관측·capture 등 수치 시간 계측을 지원합니다. 모델 경로 시간에는 입력·CLI·통신·대기·생성이 포함되어 순수 추론시간으로 부르지 않습니다.

## 5. 수집 뒤 파일을 찾는 법

| 위치 | 대표 파일 | 확인할 것 |
|---|---|---|
| `output/collections/<run-id>/` | `policy.hdf5` |20Hz 공개 관측·실제 행동·다음 관측|
| 같은 위치 | `audit.hdf5`, 평가 자료 |tick·공식 점수·success, actor 입력 밖|
| 같은 위치 | `capture.json`, `validation.json` |완료·SHA·전수 기술 검사|
| `output/operator-traces/<run-id>/` | `attempt.json`, `decisions.jsonl` |관계·최종 결정·적용 구간·오류·종료|
| 같은 위치 | `prompt.txt`, `source_snapshot/` |실제 프롬프트·코드·설정|
| 같은 위치 | `score_segments.json` |득점 시각·경계의 사후 색인|
| `output/actors/<run-id>/` |공개 입력·비공개 runtime|통째 공개하지 않는 모델 자료|
| `docs/collection/attempts/<run-id>/` |선별 manifest·결정·영상|웹 공개 패키지|
| `docs/collection/reviews/` |분석·학습 검토 구간|확인·가설·미확인·학습 승인|

기본 reward0, done, complete, 모델 stage, 공식 success는 다른 값입니다. **파일 마감·QC·과제 평가·시각 검토·학습 승인**을 각각 확인합니다. E27은1159/1159 QC 통과·5/50·success=false·unreviewed입니다.

## 6. 재실행·분기와 데이터 누출 방지

[`load_replay_prefix()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/collection/continuation.py#L129)는 원본의 완료·전수 QC·SHA를 확인하고 공개 행동을 읽습니다. `iter_action_chunks()`로 새 환경에서 실행하며 정확한 천 상태 snapshot 복원이 아닙니다. [`milestones.py`](../../participant/collection/milestones.py)는 사후 득점·분기 색인을 지원합니다.

직접 부모·prefix·새 모델 행동·자동 중립·종료 정리를 구분하고 새 run ID를 사용합니다. 같은 E07 계보의 인접 프레임·분기를 독립 성공 시연이나 별도 검증 출처로 세지 않습니다. E09 불완전 원본은 실패 근거로 보존하며 학습·정상 replay에서 제외합니다. 당시 미응답 요청·종료 순서 문제는 이후 수정했고 실패 원본을 성공으로 바꾸지 않습니다.

[출발점 catalog](../collection/catalog/README.ko.md) · [재실행 세부 가이드](../collection/guides/continuation-and-branches.ko.md)

## 7. 수집 자료를 정책으로 바꾸는 코드

| 단계 | 파일 | 현재 구현과 한계 |
|---|---|---|
| 승인·split | [`data.py`](../../participant/pi05/data.py) |SHA·complete·source_group 검사. 승인 gate는 초기 시험용 `approved_pipeline_test`|
| 입력 | [`preprocessing.inputs()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/pi05/preprocessing.py#L10) |overview+양 손목 RGB3·state32|
| 행동 | [`pack_actions()`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/ae434d08ddd4b384fbc8648bd9cf470e5b201ea5/participant/pi05/preprocessing.py#L26) |실제18개 뒤14개0 padding, 여기 자체에 유효18차원 loss mask 없음|
| 학습 | [`config.py`](../../participant/pi05/config.py), [`train.py`](../../participant/pi05/train.py) |OpenPI/JAX π0.5·horizon10·LoRA·통계·저장|
| 추론 | [`participant/policy.py`](../../participant/policy.py) |bundle 로딩·청크·앞18개를(2,9)로 복원|
| 제출 | [`package.py`](../../participant/ops/package.py), [`selfcheck.sh`](../../participant/ops/selfcheck.sh) |묶음 생성·검사. 고정 소스 검사 범위는 재개 시 재확인|

state32는 관절26+손끝 원점 거리2+닫기 의도2+직전 gripper2입니다. 파지 성공 flag나32개 물리 자유도가 아닙니다. 학생은 길이10 청크를 만들고 bundle의 `execute_steps`에 따라 앞1–10개를 실행합니다. `policy.py` 외에 bundle·파라미터·tokenizer·정규화 통계·고정 OpenPI 코드가 필요합니다.

Astra 교사는 RGB5·depth·문맥을 사용하고 현재 학생은 RGB3·state32를 봅니다. 새 자료의 승인과 입력 차이 검토가 남아 있습니다. 과거63 scripted 전이·30 updates는 연결 시험이며 새 자동 시연으로 학습한 착의 baseline 결과는 없습니다.

## 8. 실행 기능과 연구 후보

| 구분 | 현재 범위 |
|---|---|
| named action·픽셀 질의 |실제 E19/E18 이후 사용, 착의 득점 효과는 미확인|
| `participant/research/` |공개 기록 사후 분석·변환, 전부 actor에 자동 적용되지 않음|
| E28 same-arm 후보 |E27 뒤 통합·325 CPU·166소스 해시 대조, 실제 시연0|
| 별도 손목 방향 보조 |미통합·미적용. 기존 query XYZ와 구분|
| 새 정책 학습·RL |검수·관측 계약·공통 평가 기준을 먼저 정할 후속 작업|

이전208 CPU·계측v1·GPU6전이 검사는 [당시 기록](performance/20261106-speedup-plan.ko.md)입니다. 이번 문서 변경을 검사 재실행으로 쓰지 않습니다. 최신 중단·후보 범위는 [11월7일 마감](SESSION_WRAPUP_20261107.ko.md), 날짜별 변화는 [HISTORY](HISTORY.ko.md)를 따릅니다.
