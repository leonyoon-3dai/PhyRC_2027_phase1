# 사용자 안내 시연: 전체 이동 장부와 다음 출발 후보

**이번 세션의 새 조작 47개를 명령과 실제 운동으로 정리했다.** 기존 M1은 38 act·120전이, 새 오른손 분기는 9 act·25전이다. 두 run의 새 모델 조작은 합계 145전이·7.25시뮬레이션초이며, 새 분기의 복귀 재생 110전이는 별도로 표시한다. 이 장부를 만들기 위해 시뮬레이션을 진행하지 않았다.

[전체 수치·명령·관측 SHA JSON](20261116-user-guided-movement-ledger.json) · [현재 기전](../../MECHANISMS.ko.md) · [현재 계획](../../COLLECTION_PLAN.md)

## 읽는 기준

- `M`은 `20261116-astra-m1-checkpoint-001`, `B`는 `20261116-astra-right-hand-hold10-001`이다. D번호는 각 run의 0부터 시작하는 모델 결정 번호이므로 중간 번호의 빈칸은 stop 제안이다. P번호는 이 문서의 구간 번호이며 전략 이름 M1/M2/M3과 다르다.
- 아래 47행은 완료 ACK와 정확한 전후 공개 관측이 모두 있는 실제 act다. 각 전이는 0.05초이며 모든 구간의 별도 자동 settle은 0이다. M의 stop 10회·B의 stop 1회는 물리0 HOLD로 전환되어 이동표에서 제외했다.
- `ΔXYZ`는 파지 기준점의 world 좌표 변화(mm)다. 몸통까지 거리·천 변위·통과 깊이와 구분한다. 표의 표시 정밀도는 측정 정확도를 뜻하지 않는다.
- 현재 시각 식별은 **R0=해부학적 오른손 가까운 로봇, R1=왼손 가까운 로봇**이다. 기존 사용자 요청의 목적은 그대로 요약하되, 이전 actor가 R1 wrist의 손을 오른손이라고 단정한 판단은 [분기 검토](20261116-right-hand-hold10-branch.ko.md)에서 교정했다.

## 사용자 지시별 구간

| 구간 | 전이 / act | 사용자 목적 | 확인된 결과·원문 분석 | 움직임 |
|---|---|---|---|---|
| P01 | 0→16 / 5 | 앞쪽 후퇴 → 하강 → 같은 손 재접근 | [파지점 약16mm 하강, 진입 미확인](20261116-m1-front-lower-wrist.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/full.gif) |
| P02 | 16→39 / 5 | 손 노출·옷 처짐을 위한 추가 후퇴 | [손 노출 증가와 처진 형상 관측; 해부학적 식별은 현재 교정 기준 적용](20261116-m1-right-hand-clearance.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/right-hand-retreat.gif) |
| P03 | 39→42 / 2 | 아주 작은 추가 후퇴·하강 | [중립1전이의 추가 이동과 미세 하강](20261116-m1-small-clearance-lower.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/neutral-and-tiny-lowering.gif) |
| P04 | 42→44 / 1 | 몸쪽 미세 접근·점진 하강 | [lift 명령0에서 미세 하강 관측](20261116-m1-tiny-body-approach.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/tiny-bodyward-approach.gif) |
| P05 | 44→52 / 3 | 같은 방향 약15mm 추가 | [XY 순변위14.87/14.96mm](20261116-m1-bodyward-15mm.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/bodyward-15mm.gif) |
| P06 | 52→68 / 5 | 같은 방향 약30mm 추가 | [XY 순변위30.44/30.19mm](20261116-m1-bodyward-30mm.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/bodyward-30mm.gif) |
| P07 | 68→84 / 5 | 약30mm 추가·아주 작은 상승 | [XY30.40/30.08mm·상승2.24/2.31mm, 중심·통과 미확인](20261116-m1-bodyward-30mm-slight-rise.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/bodyward-30mm-slight-rise.gif) |
| P08 | 84→93 / 3 | 약50mm 추가·아주 작은 상승 요청 | [약17mm에서 가림에 따른 중간 HOLD; 50mm 미완료](20261116-m1-bodyward-50mm-slight-rise.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/bodyward-50mm-slight-rise.gif) |
| P09 | 93→110 / 6 | 사용자 검토 후 남은33mm 요청 | [추가 XY31.97/31.45mm; 원래50mm 전체는49.06/48.30mm](20261116-m1-bodyward-33mm-completion.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/bodyward-33mm-completion.gif) |
| P10 | 110→120 / 3 | 손목 위 세 번째 짙은 띠까지 접근 | [마지막 R1 전진 성분 감소·자세 변화, 목표 미확인](20261116-m1-third-stripe.ko.md) | [GIF](../../gallery/20261116-m1-guided-segments/third-stripe-approach.gif) |
| P11 | 110→135 / 9 | 복귀 뒤 오른손 가까운 R0만 접근 명령 | [R0 XY41.57mm, 중립 R1도12.66mm; 두 간격 미확인](20261116-right-hand-hold10-branch.ko.md) | [GIF](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) |

P01의 세부 움직임은 [최초 후퇴](../../gallery/20261116-m1-guided-segments/retreat.gif) · [하강/중립](../../gallery/20261116-m1-guided-segments/lower-and-neutral.gif) · [재접근](../../gallery/20261116-m1-guided-segments/reapproach.gif)으로도 나뉜다. 겹치는 GIF 프레임을 별도 act로 세지 않는다.

## 실제 명령 사전

`base_fwd`·`base_left`는 각 로봇의 로컬 평면 방향, `lift`는 높이 명령이다. 아래는 정규화 명령의 0이 아닌 채널만 표시하며 **표에 없는 채널은 0**이다. 모든 47개 act에서 기존 닫기 의도는 유지됐다. JSON에는 9채널 순서와 각 act의 전체 2×9 실제 배열을 보존했다.

| 명령 | R0 | R1 |
|---|---|---|
| C01 | `base_fwd=+0.037, base_left=-0.197` | `base_fwd=+0.072, base_left=+0.187` |
| C02 | `lift=-0.08` | `lift=-0.08` |
| C03 | 9채널 모두0 | 9채널 모두0 |
| C04 | `base_fwd=-0.022, base_left=+0.118` | `base_fwd=-0.043, base_left=-0.112` |
| C05 | `base_fwd=+0.036, base_left=-0.197` | `base_fwd=+0.071, base_left=+0.187` |
| C06 | `base_fwd=+0.022, base_left=-0.118` | `base_fwd=+0.043, base_left=+0.112` |
| C07 | `lift=-0.02` | `lift=-0.02` |
| C08 | `base_fwd=-0.007, base_left=+0.039` | `base_fwd=-0.014, base_left=-0.037` |
| C09 | `base_fwd=-0.012, base_left=+0.067` | `base_fwd=-0.019, base_left=-0.05` |
| C10 | `base_fwd=-0.012, base_left=+0.067, lift=+0.01` | `base_fwd=-0.019, base_left=-0.05, lift=+0.01` |
| C11 | `base_fwd=-0.012, base_left=+0.067` | 9채널 모두0 |

## 기존 M1의 38개 act

| 결정 | 구간·GIF | 명령 | 시작→끝 / 전이 | 초 | R0 grasp ΔXYZ,mm | R1 grasp ΔXYZ,mm |
|---|---|---|---|---:|---|---|
| M-D00 | [P01](../../gallery/20261116-m1-guided-segments/full.gif) | C01 | 0→3 / 3 | 0.15 | +0.142, -10.067, +0.082 | -0.285, -7.327, +0.008 |
| M-D01 | [P01](../../gallery/20261116-m1-guided-segments/full.gif) | C01 | 3→6 / 3 | 0.15 | +0.406, -18.619, +0.109 | -0.985, -16.964, -0.038 |
| M-D02 | [P01](../../gallery/20261116-m1-guided-segments/full.gif) | C02 | 6→9 / 3 | 0.15 | +0.257, -9.431, -5.847 | -0.892, -8.187, -5.982 |
| M-D03 | [P01](../../gallery/20261116-m1-guided-segments/full.gif) | C03 | 9→13 / 4 | 0.20 | -0.236, -0.742, -7.879 | +0.858, +1.208, -7.900 |
| M-D04 | [P01](../../gallery/20261116-m1-guided-segments/full.gif) | C04 | 13→16 / 3 | 0.15 | +0.171, +6.538, -2.401 | -0.117, +7.555, -2.408 |
| M-D06 | [P02](../../gallery/20261116-m1-guided-segments/right-hand-retreat.gif) | C05 | 16→20 / 4 | 0.20 | +0.472, -5.592, -1.288 | +0.211, -4.133, -1.292 |
| M-D07 | [P02](../../gallery/20261116-m1-guided-segments/right-hand-retreat.gif) | C05 | 20→26 / 6 | 0.30 | +0.381, -37.525, -0.488 | -2.236, -36.284, -0.763 |
| M-D08 | [P02](../../gallery/20261116-m1-guided-segments/right-hand-retreat.gif) | C05 | 26→32 / 6 | 0.30 | -0.415, -37.813, -0.054 | -1.450, -36.040, -0.267 |
| M-D09 | [P02](../../gallery/20261116-m1-guided-segments/right-hand-retreat.gif) | C05 | 32→36 / 4 | 0.20 | +0.206, -25.247, -0.028 | -0.932, -24.163, -0.169 |
| M-D10 | [P02](../../gallery/20261116-m1-guided-segments/right-hand-retreat.gif) | C06 | 36→39 / 3 | 0.15 | +0.768, -13.873, -0.053 | -0.726, -13.050, -0.137 |
| M-D12 | [P03](../../gallery/20261116-m1-guided-segments/neutral-and-tiny-lowering.gif) | C03 | 39→40 / 1 | 0.05 | +0.159, -3.016, +0.003 | -0.150, -2.750, -0.035 |
| M-D13 | [P03](../../gallery/20261116-m1-guided-segments/neutral-and-tiny-lowering.gif) | C07 | 40→42 / 2 | 0.10 | +0.183, -1.570, -0.728 | -0.267, -0.944, -0.781 |
| M-D15 | [P04](../../gallery/20261116-m1-guided-segments/tiny-bodyward-approach.gif) | C08 | 42→44 / 2 | 0.10 | -0.013, +1.240, -0.917 | +0.048, +1.913, -0.951 |
| M-D17 | [P05](../../gallery/20261116-m1-guided-segments/bodyward-15mm.gif) | C09 | 44→47 / 3 | 0.15 | -0.044, +5.200, -0.749 | +0.289, +5.384, -0.775 |
| M-D18 | [P05](../../gallery/20261116-m1-guided-segments/bodyward-15mm.gif) | C09 | 47→50 / 3 | 0.15 | -0.028, +5.810, -0.376 | +0.142, +5.770, -0.366 |
| M-D19 | [P05](../../gallery/20261116-m1-guided-segments/bodyward-15mm.gif) | C09 | 50→52 / 2 | 0.10 | +0.046, +3.857, -0.138 | -0.065, +3.799, -0.132 |
| M-D21 | [P06](../../gallery/20261116-m1-guided-segments/bodyward-30mm.gif) | C09 | 52→56 / 4 | 0.20 | +0.142, +7.645, -0.142 | -0.202, +7.518, -0.124 |
| M-D22 | [P06](../../gallery/20261116-m1-guided-segments/bodyward-30mm.gif) | C09 | 56→60 / 4 | 0.20 | +0.098, +7.617, -0.062 | -0.154, +7.506, -0.043 |
| M-D23 | [P06](../../gallery/20261116-m1-guided-segments/bodyward-30mm.gif) | C09 | 60→64 / 4 | 0.20 | +0.176, +7.628, -0.012 | -0.135, +7.619, -0.023 |
| M-D24 | [P06](../../gallery/20261116-m1-guided-segments/bodyward-30mm.gif) | C09 | 64→66 / 2 | 0.10 | +0.103, +3.790, -0.011 | -0.079, +3.768, -0.000 |
| M-D25 | [P06](../../gallery/20261116-m1-guided-segments/bodyward-30mm.gif) | C09 | 66→68 / 2 | 0.10 | +0.076, +3.749, -0.012 | -0.065, +3.768, +0.004 |
| M-D27 | [P07](../../gallery/20261116-m1-guided-segments/bodyward-30mm-slight-rise.gif) | C10 | 68→71 / 3 | 0.15 | +0.083, +5.723, +0.728 | -0.096, +5.675, +0.749 |
| M-D28 | [P07](../../gallery/20261116-m1-guided-segments/bodyward-30mm-slight-rise.gif) | C09 | 71→75 / 4 | 0.20 | +0.062, +7.561, +0.983 | -0.139, +7.520, +1.013 |
| M-D29 | [P07](../../gallery/20261116-m1-guided-segments/bodyward-30mm-slight-rise.gif) | C09 | 75→79 / 4 | 0.20 | +0.118, +7.657, +0.369 | -0.171, +7.502, +0.377 |
| M-D30 | [P07](../../gallery/20261116-m1-guided-segments/bodyward-30mm-slight-rise.gif) | C09 | 79→82 / 3 | 0.15 | +0.111, +5.667, +0.118 | -0.156, +5.633, +0.120 |
| M-D31 | [P07](../../gallery/20261116-m1-guided-segments/bodyward-30mm-slight-rise.gif) | C09 | 82→84 / 2 | 0.10 | +0.089, +3.791, +0.043 | -0.111, +3.738, +0.047 |
| M-D33 | [P08](../../gallery/20261116-m1-guided-segments/bodyward-50mm-slight-rise.gif) | C10 | 84→87 / 3 | 0.15 | +0.136, +5.682, +0.789 | -0.137, +5.629, +0.779 |
| M-D34 | [P08](../../gallery/20261116-m1-guided-segments/bodyward-50mm-slight-rise.gif) | C09 | 87→90 / 3 | 0.15 | +0.120, +5.686, +0.858 | -0.129, +5.628, +0.850 |
| M-D35 | [P08](../../gallery/20261116-m1-guided-segments/bodyward-50mm-slight-rise.gif) | C09 | 90→93 / 3 | 0.15 | +0.105, +5.710, +0.408 | -0.084, +5.595, +0.409 |
| M-D37 | [P09](../../gallery/20261116-m1-guided-segments/bodyward-33mm-completion.gif) | C09 | 93→96 / 3 | 0.15 | +0.110, +5.684, +0.182 | -0.015, +5.568, +0.203 |
| M-D38 | [P09](../../gallery/20261116-m1-guided-segments/bodyward-33mm-completion.gif) | C09 | 96→99 / 3 | 0.15 | +0.095, +5.678, +0.075 | -0.003, +5.548, +0.105 |
| M-D39 | [P09](../../gallery/20261116-m1-guided-segments/bodyward-33mm-completion.gif) | C09 | 99→102 / 3 | 0.15 | +0.118, +5.611, +0.022 | +0.058, +5.551, +0.069 |
| M-D40 | [P09](../../gallery/20261116-m1-guided-segments/bodyward-33mm-completion.gif) | C09 | 102→105 / 3 | 0.15 | +0.147, +5.628, +0.003 | +0.100, +5.527, +0.048 |
| M-D41 | [P09](../../gallery/20261116-m1-guided-segments/bodyward-33mm-completion.gif) | C09 | 105→108 / 3 | 0.15 | +0.164, +5.633, +0.001 | +0.077, +5.560, +0.042 |
| M-D42 | [P09](../../gallery/20261116-m1-guided-segments/bodyward-33mm-completion.gif) | C09 | 108→110 / 2 | 0.10 | +0.082, +3.731, +0.003 | +0.071, +3.691, +0.033 |
| M-D44 | [P10](../../gallery/20261116-m1-guided-segments/third-stripe-approach.gif) | C09 | 110→113 / 3 | 0.15 | +0.190, +5.635, +0.013 | +0.206, +5.572, +0.073 |
| M-D45 | [P10](../../gallery/20261116-m1-guided-segments/third-stripe-approach.gif) | C09 | 113→117 / 4 | 0.20 | +0.657, +7.384, +0.022 | -0.196, +7.645, +0.008 |
| M-D46 | [P10](../../gallery/20261116-m1-guided-segments/third-stripe-approach.gif) | C09 | 117→120 / 3 | 0.15 | +0.468, +5.306, -0.023 | -1.454, +0.259, +0.240 |

## 새 분기의 9개 act

| 결정 | 구간·GIF | 명령 | 시작→끝 / 전이 | 초 | R0 grasp ΔXYZ,mm | R1 grasp ΔXYZ,mm |
|---|---|---|---|---:|---|---|
| B-D00 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 110→112 / 2 | 0.10 | +0.166, +3.698, -0.006 | +0.320, +1.895, +0.042 |
| B-D01 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 112→115 / 3 | 0.15 | +0.382, +5.279, -0.069 | +0.101, +1.018, +0.071 |
| B-D02 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 115→118 / 3 | 0.15 | +0.468, +5.058, -0.102 | +0.148, +1.176, +0.088 |
| B-D03 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 118→121 / 3 | 0.15 | +0.441, +4.890, -0.107 | +0.136, +1.348, +0.072 |
| B-D04 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 121→124 / 3 | 0.15 | +0.464, +4.890, -0.083 | +0.158, +1.469, +0.073 |
| B-D05 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 124→127 / 3 | 0.15 | +0.457, +4.870, -0.078 | +0.066, +1.516, +0.036 |
| B-D06 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 127→130 / 3 | 0.15 | +0.522, +4.817, -0.081 | +0.039, +1.527, +0.053 |
| B-D07 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 130→133 / 3 | 0.15 | +0.509, +4.729, -0.089 | +0.075, +1.615, +0.058 |
| B-D08 | [P11](../../gallery/20261116-right-hand-hold10/right-hand-only-two-stripes.gif) | C11 | 133→135 / 2 | 0.10 | +0.308, +3.172, -0.042 | -0.000, +1.054, +0.028 |

B의 9개 act는 R0에만 접근 명령 C11을 보냈지만 R1도 실제로 움직였다. R1의 전체 XY 순변위는 12.66mm이며, 이를 위치 고정 대조로 취급하지 않는다. [일측 명령의 실제 제약](20261116-right-hand-hold10-branch.ko.md)

## 복귀 재생과 다음 시작 후보

새 분기는 같은 원본 근사 슬롯에서 기존 M1의 앞 110전이를 재생한 뒤 모델0호출의 **B/HOLD1·step110**을 만들었다. 이 재생은 새 9개 act에 포함하지 않는다. [새 run에서 실제로 재생한 93→110 GIF](../../gallery/20261116-right-hand-hold10/restore-tail.gif) · [새 출발 5뷰](../user-reviews/20261116-astra-right-hand-hold10-001/hold-0001/README.ko.md)

새 HOLD1과 기존 M/HOLD10의 파지점 차이 노름은 R0/R1 **1.859/0.634mm**였다. 큰 지지 배치는 유사했으나 미세한 천 경계·속도·제어 목표 차이가 있어 정확한 되감기로 표시하지 않는다. 새 HOLD1에서 슬롯을 추가 물리0으로 저장했지만 그 저장 슬롯의 재복원 검증은 아직 하지 않았다. [복귀 비교](20261116-right-hand-hold10-branch.ko.md) · [저장 검증](../../gallery/20261116-right-hand-hold10/start-checkpoint-verification.json)

**다음 출발 후보는 최종 R0 단독 조작 전의 B/HOLD1·110전이**다. 최종 B/HOLD2·135전이나 기존 마지막 M/HOLD11·120전이를 기본 출발로 가정하지 않는다. 다음 세션에서 실제 복원 관측을 다시 비교해야 한다.

## 다음 방향 — 아직 실행하지 않음

사용자는 공식 시연을 참고하여, 위 출발 후보에서 **두 로봇을 함께 마네킹의 해부학적 왼손 쪽으로 접근시킨 뒤 옷을 양손에 걸치는 방향**을 제시했다. 이는 이번 세션에서 실행·검증하지 않은 가설이다. 이 문서는 공식 시연의 내부 경로나 물리 기전을 확인했다는 주장을 하지 않는다.

다음 비교에서는 어깨→팔꿈치→손 연결로 좌우를 고정하고, 두 손과 자유 옷 경계의 관계·양쪽 지지·각 로봇의 실제 운동을 확인한다. 양손 가까이 옮긴 것, 화면상 천이 겹친 것, 실제로 양손에 걸쳐진 것과 통과한 것을 나누어 판단한다. 이번 세션은 사용자 요청으로 종료되었으며 이 방향의 물리 실행은 없다.

## 검증 범위

47개 act를 각 run의 완료 ACK와 대조하여 명령 배열·전이 구간·실행 길이·전후 공개 관측 SHA를 검증했다. JSON은 계산된 로봇 운동과 출처만 담으며 사용자 원문·모델 원문 로그·내부 인체/천 기하·평가를 담지 않는다. 실행 중 HDF5는 열지 않았다. 각 단계의 촬영 당시 HOLD 설명과 원본 기록은 그대로 보존한다. 종료·백업·학습 승인 상태는 [현재 상태](../../project/STATUS.md)를 따른다.
