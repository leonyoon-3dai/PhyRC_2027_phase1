# 자동 시연 수집 시도 · 20261106-astra-sleeve-branch700-003

[전체 수집 기록](../../README.ko.md) · [구조화 요약](manifest.json) · [전체 행동 기록](decisions.jsonl) · [사용한 기본 프롬프트](prompt.txt)

실행 상태는 **completed**, 원본 출처는 `gpt`입니다. 완료 상태와 과제 성공은 아래에서 따로 기록합니다.

## 실행 조건과 시간

| 항목 | 기록 |
|---|---|
| 기록 시작 UTC | 2026-11-06T08:34:12Z |
| 기록 종료 UTC | 2026-11-06T09:01:21Z |
| 이전 시도 | 20261106-astra-coordinated-fresh-001 |
| 재시도 사유 | clean_server_sleeve_visibility_recovery |
| 출처 그룹 | 20261106-coordinated-demo-methods |
| 요청 모델 / 추론 설정 | gpt-6-astra / ultra |
| 전체 실제 경과 시간 (초) | 1628.841 |
| Actor 호출 합계 (초) | 928.077 |
| 환경 요청·응답 합계 (초) | 654.333 |
| 시뮬레이션 시간 (초) | 37.500 |
| 저장 전이 수 | 750.000 |
| 응답 확인 전이 수 | 750.000 |
| 모델 호출 시도 수 | 9.000 |
| 완료한 결정 구간 수 | 9.000 |
| 파일 완료 상태 | true |
| 데이터 정합성 검사 | true |
| 학습 데이터 승인 | unreviewed |
| Actor 호출 방식 | exec |
| 한 호출의 최대 계획 구간 수 | 1.000 |
| 한 계획의 최대 제어 step 수 | 20.000 |

Actor 호출 시간은 공개 입력 저장·요청 전송·응답 처리 등 호출 경로를 측정합니다. 방식에 따라 Docker/CLI 시작이 호출 안에 들어가거나 상주 서버 준비 시간으로 분리됩니다. 내부 모델 추론 시간만 별도로 측정한 값은 아닙니다. 모델이 판단하는 동안 물리 시간은 멈추며 실제 경과 시간과 시뮬레이션 시간은 다릅니다. 세부 요청 프로세스 시간에도 CLI 처리·네트워크·서버 대기·생성이 함께 포함됩니다.

## 토큰 사용량의 범위

`actor_usage`는 thread별 관측 누계를 합친 값입니다. 결정의 `usage`는 원본 CLI 누계이며, 호출별 증가량은 `usage_accounting.incremental_usage`입니다. 캐시 입력은 입력의 부분집합이고 추론 출력은 출력의 부분집합이므로 열들을 다시 합산하지 않습니다.

전체 호출 사용량 확정: **true** · 기록한 호출 수: 9.

| 입력 | 캐시 입력 | 캐시 쓰기 입력 | 출력 | 추론 출력 |
|---:|---:|---:|---:|---:|
| 456141 | 368640 | 0 | 13986 | 12782 |

중복 누계는 추가 사용량 0으로 처리하고, 역행한 누계는 미확정으로 보존합니다. 새 thread는 별도로 집계합니다. 토큰 기록은 화폐 비용이나 청구서가 아닙니다.

## 리뷰 정지 조건

목표 누적 점수 10.000 · 감시 상태 `collector_ended_before_gate` · 수집기 상태 `completed`.

마지막 관측 점수 5.000 · 응답 확인 step 750.

`review_ready`는 정지 조건에 따라 실행을 마치고 리뷰할 준비가 된 상태입니다. 50점·착의 성공이나 학습 데이터 승인을 뜻하지 않습니다. 공식 점수와 success는 아래 평가 결과로 확인합니다.

## 공식 평가 결과

평가 유효성 `true` · 누적 점수 **5.000 / 50** · 착의 success **false** · rate 상태 `no_contact` · 최종 rate 미측정/해당 없음 points/s.

누적 50점, 착의 success, 정상 파일 종료와 데이터 정합성은 서로 다른 상태입니다. 접촉 전 `no_contact`의 rate는 0점/초로 바꾸지 않습니다.

| 단계 | 획득 점수 / 최대 | 획득 시각 (episode 초) |
|---|---:|---:|
| 파지·들기 | 5.000 / 5 | 17.800 |
| 첫 소매 | 0.000 / 5 | 미측정/해당 없음 |
| 반대 어깨 | 0.000 / 5 | 미측정/해당 없음 |
| 두 번째 소매 | 0.000 / 5 | 미측정/해당 없음 |
| 왼쪽 위팔 | 0.000 / 5 | 미측정/해당 없음 |
| 오른쪽 위팔 | 0.000 / 5 | 미측정/해당 없음 |
| 목 통과 | 0.000 / 10 | 미측정/해당 없음 |
| 앞면 방향 | 0.000 / 10 | 미측정/해당 없음 |

## 단계 획득 경로

점수 획득은 [평가 이벤트](score-events.jsonl)에서 같은 physics tick끼리 묶었습니다. 같은 시각에 인정된 항목의 내부 순서는 추정하지 않습니다. 착의 success는 점수 획득과 별도로 기록합니다.

| 순서 | episode 시간 (초) | 전이 경계 step | 누적 점수 변화 | 같은 시각의 항목 변화 |
|---:|---:|---:|---:|---|
| 0 | 17.800 | 356 | 0.000→5.000 | 파지·들기 0.000→5.000 |

평가 clock 0초에 대응하는 공개 simulation clock은 1.525초입니다. 두 시계를 같은 절대 시각으로 혼동하지 않습니다.

별도 success 이벤트 수: **0**. 평가 유효성: `true`.


## 원본 관측 화면

지정된 공개 카메라의 저장 RGB 픽셀입니다. 시작은 첫 `obs`, 종료는 마지막 `next_obs`입니다. 이미지 합성이나 내부 상태 기반 장면 재구성 없이 원본 픽셀로 PNG를 저장했습니다.

| 카메라 | 시작 | 종료 |
|---|---|---|
| `overview` | [![시작 overview](images/initial-overview.png)](images/initial-overview.png) | [![종료 overview](images/final-overview.png)](images/final-overview.png) |
| `robot_0_wrist` | [![시작 robot_0_wrist](images/initial-robot_0_wrist.png)](images/initial-robot_0_wrist.png) | [![종료 robot_0_wrist](images/final-robot_0_wrist.png)](images/final-robot_0_wrist.png) |
| `robot_1_wrist` | [![시작 robot_1_wrist](images/initial-robot_1_wrist.png)](images/initial-robot_1_wrist.png) | [![종료 robot_1_wrist](images/final-robot_1_wrist.png)](images/final-robot_1_wrist.png) |
| `robot_0_head` | [![시작 robot_0_head](images/initial-robot_0_head.png)](images/initial-robot_0_head.png) | [![종료 robot_0_head](images/final-robot_0_head.png)](images/final-robot_0_head.png) |
| `robot_1_head` | [![시작 robot_1_head](images/initial-robot_1_head.png)](images/initial-robot_1_head.png) | [![종료 robot_1_head](images/final-robot_1_head.png)](images/final-robot_1_head.png) |

시작 관측 시각 1.525초 · 종료 관측 시각 39.025초 (공개 simulation clock).

[▶ overview 관측 영상 보기](overview.mp4)

저장된 20 Hz `obs` 중 750프레임을 순서대로 사용했습니다. 재생은 **4.0배 느리게** (5.000 fps), 실제 대기 시간·모델 호출 지연은 영상에 들어가지 않습니다. 종료 `next_obs`는 위 PNG에서 확인합니다.

## 결정과 실행 순서

아래 근거는 모델 최종 JSON의 짧은 행동 설명입니다. 시각적 평가는 행동 전 관측에 대한 판단이며, 그 행동의 실행 후 성공 라벨로 사용하지 않습니다. 공식 점수는 별도의 평가 결과입니다.

행동의 각 행은 로봇 0·1 순서이며 열은 `전진, 왼쪽 이동, 반시계 회전, 리프트, 팔 신장, 손목 yaw, pitch, roll, gripper`입니다. 앞 8개는 정규화 속도이고 gripper는 닫기 `+1`, 열기 `-1`, 의도 유지 `0`입니다.

### 기록된 행동의 재실행 구간

원본 `20261106-astra-coordinated-fresh-001`의 행동 700전이를 새 환경에서 다시 실행했습니다. 이 구간에는 새 모델 호출이 없고 관측·평가를 새로 기록했습니다. 정확한 물리 상태 복원이나 독립적인 새 시연으로 집계하지 않습니다. 원본 step 대응과 실제 행동은 `decisions.jsonl`의 `replayed_segment`에 있습니다.

### 결정 0 · 들기 · `act`

입력 관측 36.525초 · Actor 호출 67.337초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00000` · 모델 호출 인덱스 0 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 36.525초.

공개 입력 저장 0.079초 · 요청 프로세스 67.259초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 16743 / 출력 1012 토큰.

최종 응답의 행동 설명: Robot 0 appears to support the right garment edge and robot 1 the left. Test both contacts with a coordinated 2 cm lift, then check cloth following separately. The opening near the raised hand is not yet confirmed as a sleeve.

요청 행동:

```json
[[0, 0, 0, 0.08, 0, 0, 0, 0, 1], [0, 0, 0, 0.08, 0, 0, 0, 0, 1]]
```

실행 구간 step **[700, 703)** · 요청 3 step / 실제 3 step · 환경 요청·응답 3.155초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.07999999821186066, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.07999999821186066, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 1 · 첫 소매 · `act`

입력 관측 36.675초 · Actor 호출 99.525초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00001` · 모델 호출 인덱스 1 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 36.675초.

공개 입력 저장 0.072초 · 요청 프로세스 99.453초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 24971 / 출력 1457 토큰.

최종 응답의 행동 설명: Robot 0’s right edge and robot 1’s left edge remained near their fingertips during the small lift. Preserve both grips and gently counter-roll to expose the rim facing the overview’s raised left-side hand. Sleeve identity and hand passage remain uncertain; do not advance yet.

요청 행동:

```json
[[0, 0, 0, 0, 0, 0, 0, 0.1, 1], [0, 0, 0, 0, 0, 0, 0, -0.1, 1]]
```

실행 구간 step **[703, 707)** · 요청 4 step / 실제 4 step · 환경 요청·응답 4.165초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.10000000149011612, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.10000000149011612, 1.0]]
```

### 결정 2 · 방향 · `act`

입력 관측 36.875초 · Actor 호출 75.596초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00002` · 모델 호출 인덱스 2 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 36.875초.

공개 입력 저장 0.077초 · 요청 프로세스 75.518초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 33642 / 출력 1029 토큰.

최종 응답의 행동 설명: Robot 0 appears to retain the right edge; robot 1 supports the opposite edge. Counter-rolling did not clarify a sleeve cuff or hand passage. Retract robot 0 slightly while robot 1 anchors, turning the rim for inspection before advancing toward the overview-left raised hand.

요청 행동:

```json
[[0, 0, 0, 0, -0.16, 0, 0, 0, 1], [0, 0, 0, 0, 0, 0, 0, 0, 1]]
```

실행 구간 step **[707, 712)** · 요청 5 step / 실제 5 step · 환경 요청·응답 4.950초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.0, -0.1599999964237213, 0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 3 · 방향 · `act`

입력 관측 37.125초 · Actor 호출 76.291초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00003` · 모델 호출 인덱스 3 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 37.125초.

공개 입력 저장 0.070초 · 요청 프로세스 76.221초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 41858 / 출력 1110 토큰.

최종 응답의 행동 설명: Robot 0’s fabric followed its retraction; robot 1 retained the opposite edge. The dark rim still has uncertain topology. Move both slightly outward to unfold it while preserving both grips, without advancing toward the overview-left raised hand.

요청 행동:

```json
[[0, -0.12, 0, 0, 0, 0, 0, 0, 1], [0, 0.12, 0, 0, 0, 0, 0, 0, 1]]
```

실행 구간 step **[712, 718)** · 요청 6 step / 실제 6 step · 환경 요청·응답 5.508초.

실제 적용 행동:

```json
[[0.0, -0.11999999731779099, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.11999999731779099, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 4 · 방향 · `act`

입력 관측 37.425초 · Actor 호출 77.089초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00004` · 모델 호출 인덱스 4 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 37.425초.

공개 입력 저장 0.070초 · 요청 프로세스 77.019초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 50191 / 출력 1092 토큰.

최종 응답의 행동 설명: Robot 0 retains the right edge and robot 1 the left; spreading flattened the dark rim without identifying a cuff. Stop spreading and gently tilt the shirt by lowering robot 0 and raising robot 1. Keep both grips and expose the side opening before approaching the same raised hand.

요청 행동:

```json
[[0, 0, 0, -0.08, 0, 0, 0, 0, 1], [0, 0, 0, 0.08, 0, 0, 0, 0, 1]]
```

실행 구간 step **[718, 724)** · 요청 6 step / 실제 6 step · 환경 요청·응답 6.089초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, -0.07999999821186066, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.07999999821186066, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 5 · 방향 · `act`

입력 관측 37.725초 · Actor 호출 85.555초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00005` · 모델 호출 인덱스 5 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 37.725초.

공개 입력 저장 0.071초 · 요청 프로세스 85.484초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 58517 / 출력 1233 토큰.

최종 응답의 행동 설명: Robot 0 supports the lower right edge; robot 1 supports the higher left edge. Tilting has not exposed a definite sleeve cuff. Pitch both wrists upward slightly to reveal the folded rim’s underside, preserving both grips and avoiding advancement toward the overview-left raised hand.

요청 행동:

```json
[[0, 0, 0, 0, 0, 0, -0.12, 0, 1], [0, 0, 0, 0, 0, 0, -0.12, 0, 1]]
```

실행 구간 step **[724, 730)** · 요청 6 step / 실제 6 step · 환경 요청·응답 5.720초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.11999999731779099, 0.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.11999999731779099, 0.0, 1.0]]
```

### 결정 6 · 방향 · `act`

입력 관측 38.025초 · Actor 호출 169.823초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00006` · 모델 호출 인덱스 6 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 38.025초.

공개 입력 저장 0.069초 · 요청 프로세스 169.754초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 66946 / 출력 2731 토큰.

최종 응답의 행동 설명: Robot 0 anchors the far edge; robot 1 retains the near edge, but its arm obscures the target hand and possible cuff. Sidestep robot 1 left while yawing its wrist right to approximately preserve the cloth position and improve the sightline. Keep both grips; do not advance onto the arm.

요청 행동:

```json
[[0, 0, 0, 0, 0, 0, 0, 0, 1], [0, 0.2, 0, 0, 0, -0.08, 0, 0, 1]]
```

실행 구간 step **[730, 740)** · 요청 10 step / 실제 10 step · 환경 요청·응답 8.962초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.20000000298023224, 0.0, 0.0, 0.0, -0.07999999821186066, 0.0, 0.0, 1.0]]
```

### 결정 7 · 방향 · `act`

입력 관측 38.525초 · Actor 호출 147.295초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-sleeve-branch700-003:call-00007` · 모델 호출 인덱스 7 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 38.525초.

공개 입력 저장 0.069초 · 요청 프로세스 147.225초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 76878 / 출력 2335 토큰.

최종 응답의 행동 설명: Robot 0 maintains far-edge support; robot 1 retains the near edge. The first sidestep changed the view, but its arm still obscures the hand–rim junction. Continue a small compensated sidestep to clear that sightline, preserving both grips without advancing onto the mannequin.

요청 행동:

```json
[[0, 0, 0, 0, 0, 0, 0, 0, 1], [0, 0.18, 0, 0, 0, -0.08, 0, 0, 1]]
```

실행 구간 step **[740, 750)** · 요청 10 step / 실제 10 step · 환경 요청·응답 9.088초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.18000000715255737, 0.0, 0.0, 0.0, -0.07999999821186066, 0.0, 0.0, 1.0]]
```

### 결정 8 · 최종 확인 · `finish_episode`

입력 관측 39.025초 · Actor 호출 129.566초 · 시각적 판단 `blocked`.

계획 `20261106-astra-sleeve-branch700-003:call-00008` · 모델 호출 인덱스 8 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 39.025초.

공개 입력 저장 0.068초 · 요청 프로세스 129.498초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 86395 / 출력 1987 토큰.

최종 응답의 행동 설명: Robot 0 and robot 1 still appear to support opposite garment edges. Repeated unfolding and sightline adjustments have not revealed a definite sleeve–hand passage, and visibility has worsened. End this unproductive attempt with both grips preserved; complete dressing is not visible.

요청 행동:

```json
[[0, 0, 0, 0, 0, 0, 0, 0, 0], [0, 0, 0, 0, 0, 0, 0, 0, 0]]
```

실행 구간 step **[750, 750)** · 요청 0 step / 실제 0 step · 환경 요청·응답 0.008초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]]
```

## 검수와 후속 판단

현재 데이터 승인은 `unreviewed`입니다. 형식과 시간 정합성 검사를 통과해도 시연의 유용성이나 착의 성공을 보장하지 않습니다.

이 페이지의 원본 파일 SHA256과 생성 파일 SHA256은 [manifest.json](manifest.json)에 있습니다. 실행 실패도 같은 run ID와 부모 시도 관계로 보존합니다. 공개 범위는 카메라, 최종 행동 응답, 시간, 평가 요약입니다.

[개발 피드백과 변경 근거](../../feedback/2026-11-06.jsonl)
