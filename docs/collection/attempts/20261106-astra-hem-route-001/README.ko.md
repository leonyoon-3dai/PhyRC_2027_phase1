# 자동 시연 수집 시도 · 20261106-astra-hem-route-001

[전체 수집 기록](../../README.ko.md) · [구조화 요약](manifest.json) · [전체 행동 기록](decisions.jsonl) · [사용한 기본 프롬프트](prompt.txt)

실행 상태는 **interrupted**, 원본 출처는 `gpt`입니다. 완료 상태와 과제 성공은 아래에서 따로 기록합니다.

## 실행 조건과 시간

| 항목 | 기록 |
|---|---|
| 기록 시작 UTC | 2026-11-06T09:53:49Z |
| 기록 종료 UTC | 2026-11-06T10:26:45Z |
| 이전 시도 | 20261106-astra-coordinated-fresh-001 |
| 재시도 사유 | distinguish_body_hem_entry_from_sleeve_exit |
| 출처 그룹 | 20261106-coordinated-demo-methods |
| 요청 모델 / 추론 설정 | gpt-6-astra / ultra |
| 전체 실제 경과 시간 (초) | 1975.678 |
| Actor 호출 합계 (초) | 1244.481 |
| 환경 요청·응답 합계 (초) | 679.752 |
| 시뮬레이션 시간 (초) | 39.050 |
| 저장 전이 수 | 781.000 |
| 응답 확인 전이 수 | 781.000 |
| 모델 호출 시도 수 | 12.000 |
| 완료한 결정 구간 수 | 11.000 |
| 파일 완료 상태 | true |
| 데이터 정합성 검사 | true |
| 학습 데이터 승인 | unreviewed |
| Actor 호출 방식 | exec |
| 한 호출의 최대 계획 구간 수 | 1.000 |
| 한 계획의 최대 제어 step 수 | 20.000 |

Actor 호출 시간은 공개 입력 저장·요청 전송·응답 처리 등 호출 경로를 측정합니다. 방식에 따라 Docker/CLI 시작이 호출 안에 들어가거나 상주 서버 준비 시간으로 분리됩니다. 내부 모델 추론 시간만 별도로 측정한 값은 아닙니다. 모델이 판단하는 동안 물리 시간은 멈추며 실제 경과 시간과 시뮬레이션 시간은 다릅니다. 세부 요청 프로세스 시간에도 CLI 처리·네트워크·서버 대기·생성이 함께 포함됩니다.

## 토큰 사용량의 범위

`actor_usage`는 thread별 관측 누계를 합친 값입니다. 결정의 `usage`는 원본 CLI 누계이며, 호출별 증가량은 `usage_accounting.incremental_usage`입니다. 캐시 입력은 입력의 부분집합이고 추론 출력은 출력의 부분집합이므로 열들을 다시 합산하지 않습니다.

전체 호출 사용량 확정: **true** · 기록한 호출 수: 12.

| 입력 | 캐시 입력 | 캐시 쓰기 입력 | 출력 | 추론 출력 |
|---:|---:|---:|---:|---:|
| 839369 | 724480 | 0 | 24246 | 22602 |

중복 누계는 추가 사용량 0으로 처리하고, 역행한 누계는 미확정으로 보존합니다. 새 thread는 별도로 집계합니다. 토큰 기록은 화폐 비용이나 청구서가 아닙니다.

## 리뷰 정지 조건

목표 누적 점수 10.000 · 감시 상태 `collector_ended_before_gate` · 수집기 상태 `interrupted`.

마지막 관측 점수 5.000 · 응답 확인 step 780.

`review_ready`는 정지 조건에 따라 실행을 마치고 리뷰할 준비가 된 상태입니다. 50점·착의 성공이나 학습 데이터 승인을 뜻하지 않습니다. 공식 점수와 success는 아래 평가 결과로 확인합니다.

## 공식 평가 결과

평가 유효성 `true` · 누적 점수 **5.000 / 50** · 착의 success **false** · rate 상태 `no_dressing_points` · 최종 rate 0.000 points/s.

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

시작 관측 시각 1.525초 · 종료 관측 시각 40.575초 (공개 simulation clock).

[▶ overview 관측 영상 보기](overview.mp4)

저장된 20 Hz `obs` 중 781프레임을 순서대로 사용했습니다. 재생은 **4.0배 느리게** (5.000 fps), 실제 대기 시간·모델 호출 지연은 영상에 들어가지 않습니다. 종료 `next_obs`는 위 PNG에서 확인합니다.

## 결정과 실행 순서

아래 근거는 모델 최종 JSON의 짧은 행동 설명입니다. 시각적 평가는 행동 전 관측에 대한 판단이며, 그 행동의 실행 후 성공 라벨로 사용하지 않습니다. 공식 점수는 별도의 평가 결과입니다.

행동의 각 행은 로봇 0·1 순서이며 열은 `전진, 왼쪽 이동, 반시계 회전, 리프트, 팔 신장, 손목 yaw, pitch, roll, gripper`입니다. 앞 8개는 정규화 속도이고 gripper는 닫기 `+1`, 열기 `-1`, 의도 유지 `0`입니다.

### 기록된 행동의 재실행 구간

원본 `20261106-astra-coordinated-fresh-001`의 행동 700전이를 새 환경에서 다시 실행했습니다. 이 구간에는 새 모델 호출이 없고 관측·평가를 새로 기록했습니다. 정확한 물리 상태 복원이나 독립적인 새 시연으로 집계하지 않습니다. 원본 step 대응과 실제 행동은 `decisions.jsonl`의 `replayed_segment`에 있습니다.

### 결정 0 · 첫 소매 · `act`

입력 관측 36.525초 · Actor 호출 171.160초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-hem-route-001:call-00000` · 모델 호출 인덱스 0 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 36.525초.

공개 입력 저장 0.256초 · 요청 프로세스 170.904초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 18240 / 출력 3129 토큰.

최종 응답의 행동 설명: Robot 0 appears to support the outer rim; robot 1 supports the hand-side rim. Shift both robot-left about 7 cm to align the probable hem opening with the raised hand, then reassess cloth following and clearance. Hand entry is not yet established.

요청 행동:

```json
[[0, 0.3, 0, 0, 0, 0, 0, 0, 1], [0, 0.3, 0, 0, 0, 0, 0, 0, 1]]
```

실행 구간 step **[700, 708)** · 요청 8 step / 실제 8 step · 환경 요청·응답 7.661초.

실제 적용 행동:

```json
[[0.0, 0.30000001192092896, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.30000001192092896, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 1 · 첫 소매 · `act`

입력 관측 36.925초 · Actor 호출 154.451초 · 시각적 판단 `progressing`.

계획 `20261106-astra-hem-route-001:call-00001` · 모델 호출 인덱스 1 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 36.925초.

공개 입력 저장 0.070초 · 요청 프로세스 154.381초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 28634 / 출력 2974 토큰.

최종 응답의 행동 설명: Cloth followed both grippers during the last shift. Robot 0 supports the outer rim; robot 1 guides the hand-side rim. Move both another short distance robot-left to reduce the visible hand–opening offset; entry remains unconfirmed.

요청 행동:

```json
[[0, 0.3, 0, 0, 0, 0, 0, 0, 1], [0, 0.3, 0, 0, 0, 0, 0, 0, 1]]
```

실행 구간 step **[708, 716)** · 요청 8 step / 실제 8 step · 환경 요청·응답 7.516초.

실제 적용 행동:

```json
[[0.0, 0.30000001192092896, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.30000001192092896, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 2 · 복구 · `act`

입력 관측 37.325초 · Actor 호출 58.217초 · 시각적 판단 `recovering`.

계획 `20261106-astra-hem-route-001:call-00002` · 모델 호출 인덱스 2 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 37.325초.

공개 입력 저장 0.071초 · 요청 프로세스 58.146초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 38850 / 출력 1167 토큰.

최종 응답의 행동 설명: Robot 0 retains outer support; robot 1 retains the hand-side rim. Two lateral corrections have not established entry. Hold both bases and reshape the probable hem opening by slightly raising robot 0’s edge and lowering robot 1’s edge toward the visible hand.

요청 행동:

```json
[[0, 0, 0, 0.03, 0, 0, 0, 0, 1], [0, 0, 0, -0.09, 0, 0, 0, 0, 1]]
```

실행 구간 step **[716, 722)** · 요청 6 step / 실제 6 step · 환경 요청·응답 5.919초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.029999999329447746, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, -0.09000000357627869, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 3 · 첫 소매 · `act`

입력 관측 37.625초 · Actor 호출 104.783초 · 시각적 판단 `progressing`.

계획 `20261106-astra-hem-route-001:call-00003` · 모델 호출 인덱스 3 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 37.625초.

공개 입력 저장 0.071초 · 요청 프로세스 104.711초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 47239 / 출력 1950 토큰.

최종 응답의 행동 설명: Robot 0 supports the higher outer rim; robot 1 supports the lowered hand-side rim. The same visible hand remains left and below the probable hem opening. Move both left and slightly down to reduce that gap, then inspect before attempting rim crossing.

요청 행동:

```json
[[0, 0.4, 0, -0.06, 0, 0, 0, 0, 1], [0, 0.4, 0, -0.06, 0, 0, 0, 0, 1]]
```

실행 구간 step **[722, 732)** · 요청 10 step / 실제 10 step · 환경 요청·응답 9.832초.

실제 적용 행동:

```json
[[0.0, 0.4000000059604645, 0.0, -0.05999999865889549, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.4000000059604645, 0.0, -0.05999999865889549, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 4 · 첫 소매 · `act`

입력 관측 38.125초 · Actor 호출 89.114초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-hem-route-001:call-00004` · 모델 호출 인덱스 4 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 38.125초.

공개 입력 저장 0.075초 · 요청 프로세스 89.039초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 56415 / 출력 1698 토큰.

최종 응답의 행동 설명: Robot 0 maintains upper-rim support; robot 1 guides the near rim, with cloth still following both. Make a short leftward, slightly forward and downward hem-entry attempt toward the same visible hand. Recheck the hand against the rim; crossing is not yet established.

요청 행동:

```json
[[0.08, 0.4, 0, -0.04, 0, 0, 0, 0, 1], [0.08, 0.4, 0, -0.04, 0, 0, 0, 0, 1]]
```

실행 구간 step **[732, 738)** · 요청 6 step / 실제 6 step · 환경 요청·응답 5.411초.

실제 적용 행동:

```json
[[0.07999999821186066, 0.4000000059604645, 0.0, -0.03999999910593033, 0.0, 0.0, 0.0, 0.0, 1.0], [0.07999999821186066, 0.4000000059604645, 0.0, -0.03999999910593033, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 5 · 복구 · `act`

입력 관측 38.425초 · Actor 호출 168.425초 · 시각적 판단 `recovering`.

계획 `20261106-astra-hem-route-001:call-00005` · 모델 호출 인덱스 5 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 38.425초.

공개 입력 저장 0.074초 · 요청 프로세스 168.351초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 65381 / 출력 3018 토큰.

최종 응답의 행동 설명: Robot 0 supports the outer rim; robot 1 holds the near rim. The hand is partly hidden by robot 1’s jaw without a visible rim crossing. Halt base advance and turn both wrists slightly to expose the hand–rim relationship while preserving support.

요청 행동:

```json
[[0, 0, 0, 0, 0, -0.1, 0, 0, 1], [0, 0, 0, 0, 0, -0.1, 0, 0, 1]]
```

실행 구간 step **[738, 744)** · 요청 6 step / 실제 6 step · 환경 요청·응답 5.010초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.0, 0.0, -0.10000000149011612, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.0, 0.0, -0.10000000149011612, 0.0, 0.0, 1.0]]
```

### 결정 6 · 복구 · `act`

입력 관측 38.725초 · Actor 호출 54.814초 · 시각적 판단 `recovering`.

계획 `20261106-astra-hem-route-001:call-00006` · 모델 호출 인덱스 6 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 38.725초.

공개 입력 저장 0.074초 · 요청 프로세스 54.740초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 75623 / 출력 998 토큰.

최종 응답의 행동 설명: Robot 0 retains outer-rim support; robot 1 retains near-rim support. The wrist turn did not reveal a hand crossing the opening. Retract and raise both held edges a few centimeters to clear the hand and restore visibility before another entry attempt.

요청 행동:

```json
[[0, 0, 0, 0.08, -0.1, 0, 0, 0, 1], [0, 0, 0, 0.08, -0.1, 0, 0, 0, 1]]
```

실행 구간 step **[744, 752)** · 요청 8 step / 실제 8 step · 환경 요청·응답 6.568초.

실제 적용 행동:

```json
[[0.0, 0.0, 0.0, 0.07999999821186066, -0.10000000149011612, 0.0, 0.0, 0.0, 1.0], [0.0, 0.0, 0.0, 0.07999999821186066, -0.10000000149011612, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 7 · 첫 소매 · `act`

입력 관측 39.125초 · Actor 호출 82.904초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-hem-route-001:call-00007` · 모델 호출 인덱스 7 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 39.125초.

공개 입력 저장 0.074초 · 요청 프로세스 82.829초 · 결과 해석 0.001초.

호출 사용량 상태 `observed` · 이번 증가량 입력 83850 / 출력 1574 토큰.

최종 응답의 행동 설명: Robot 0 supports the higher rim; robot 1 controls the near rim. The target hand is visible again just left of that rim in robot 1’s head view. Make one short left/down entry motion, then check whether the hand lies between the opening’s rims.

요청 행동:

```json
[[0, 0.4, 0, -0.08, 0.06, 0, 0, 0, 1], [0, 0.4, 0, -0.08, 0.06, 0, 0, 0, 1]]
```

실행 구간 step **[752, 760)** · 요청 8 step / 실제 8 step · 환경 요청·응답 6.534초.

실제 적용 행동:

```json
[[0.0, 0.4000000059604645, 0.0, -0.07999999821186066, 0.05999999865889549, 0.0, 0.0, 0.0, 1.0], [0.0, 0.4000000059604645, 0.0, -0.07999999821186066, 0.05999999865889549, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 8 · 첫 소매 · `act`

입력 관측 39.525초 · Actor 호출 50.658초 · 시각적 판단 `uncertain`.

계획 `20261106-astra-hem-route-001:call-00008` · 모델 호출 인덱스 8 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 39.525초.

공개 입력 저장 0.073초 · 요청 프로세스 50.584초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 92668 / 출력 1044 토큰.

최종 응답의 행동 설명: Robot 0 supports the higher outer corner; robot 1 guides the near corner. The hand is adjacent to the yellow rim, but crossing remains unclear. Make one small leftward, forward and downward correction, then require visible rim-crossing evidence before further threading.

요청 행동:

```json
[[0, 0.2, 0, -0.04, 0.12, 0, 0, 0, 1], [0, 0.2, 0, -0.04, 0.12, 0, 0, 0, 1]]
```

실행 구간 step **[760, 766)** · 요청 6 step / 실제 6 step · 환경 요청·응답 4.972초.

실제 적용 행동:

```json
[[0.0, 0.20000000298023224, 0.0, -0.03999999910593033, 0.11999999731779099, 0.0, 0.0, 0.0, 1.0], [0.0, 0.20000000298023224, 0.0, -0.03999999910593033, 0.11999999731779099, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 9 · 복구 · `act`

입력 관측 39.825초 · Actor 호출 146.243초 · 시각적 판단 `recovering`.

계획 `20261106-astra-hem-route-001:call-00009` · 모델 호출 인덱스 9 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 39.825초.

공개 입력 저장 0.074초 · 요청 프로세스 146.168초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 100949 / 출력 3085 토큰.

최종 응답의 행동 설명: Both robots still support their respective rim sections, but two entry corrections have not shown a clear crossing. Pause forward and downward motion. Move robot 0 slightly outward and robot 1 left to gently widen the opening and expose the hand beside robot 1’s jaw.

요청 행동:

```json
[[0, -0.1, 0, 0, 0, 0, 0, 0, 1], [0, 0.2, 0, 0, 0, 0, 0, 0, 1]]
```

실행 구간 step **[766, 772)** · 요청 6 step / 실제 6 step · 환경 요청·응답 5.030초.

실제 적용 행동:

```json
[[0.0, -0.10000000149011612, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0], [0.0, 0.20000000298023224, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]]
```

### 결정 10 · 복구 · `act`

입력 관측 40.125초 · Actor 호출 68.787초 · 시각적 판단 `recovering`.

계획 `20261106-astra-hem-route-001:call-00010` · 모델 호출 인덱스 10 · 계획 구간 1/1 · 이 구간에서 모델 호출 `true`.

실행 직전 최신 관측 40.125초.

공개 입력 저장 0.075초 · 요청 프로세스 68.712초 · 결과 해석 0.000초.

호출 사용량 상태 `observed` · 이번 증가량 입력 111267 / 출력 1562 토큰.

최종 응답의 행동 설명: Robot 0 and robot 1 retain opposite corners. Spreading narrowed the visible opening, and hand crossing remains unconfirmed. Ease the corners inward and pitch the held rim toward the mannequin, raising both lifts to limit downward movement while reshaping.

요청 행동:

```json
[[0, 0.1, 0, 0.1, 0, 0, 0.16, 0, 1], [0, -0.1, 0, 0.1, 0, 0, 0.16, 0, 1]]
```

실행 구간 step **[772, 780)** · 요청 8 step / 실제 8 step · 환경 요청·응답 6.461초.

실제 적용 행동:

```json
[[0.0, 0.10000000149011612, 0.0, 0.10000000149011612, 0.0, 0.0, 0.1599999964237213, 0.0, 1.0], [0.0, -0.10000000149011612, 0.0, 0.10000000149011612, 0.0, 0.0, 0.1599999964237213, 0.0, 1.0]]
```

미실행 계획 후속 구간 폐기: `interrupted`. 아래 구간은 실행된 행동으로 라벨링하지 않습니다.

- 계획 `20261106-astra-hem-route-001:call-00011` · 구간 인덱스 0 · 실행 안 함

수집기 정지: `interrupted` · 중립 명령 1 step.

## 종료 오류

`KeyboardInterrupt`: SIGTERM

## 검수와 후속 판단

현재 데이터 승인은 `unreviewed`입니다. 형식과 시간 정합성 검사를 통과해도 시연의 유용성이나 착의 성공을 보장하지 않습니다.

이 페이지의 원본 파일 SHA256과 생성 파일 SHA256은 [manifest.json](manifest.json)에 있습니다. 실행 실패도 같은 run ID와 부모 시도 관계로 보존합니다. 공개 범위는 카메라, 최종 행동 응답, 시간, 평가 요약입니다.

[개발 피드백과 변경 근거](../../feedback/2026-11-06.jsonl)
