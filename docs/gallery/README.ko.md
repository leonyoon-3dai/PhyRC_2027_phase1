# 시연 데이터 수집 갤러리

[저장소 소개](../../README.md) · [챌린지와 점수](../project/CHALLENGE_GUIDE.ko.md) · [수집 방식과 데이터](../collection/README.ko.md) · [Astra 수집의 전체 흐름](../collection/guides/astra-end-to-end.ko.md) · [현재 상태](../project/STATUS.md)

## 먼저 보는 최신 장면 · E27

<a href="assets/20261107-e27-arm-approach/event.mp4"><img src="assets/20261107-e27-arm-approach/preview.gif" width="960" alt="E27 실제 공개 RGB 네 카메라. 새 파지로 운반한 뒤 팔과 노란 옷 경계 사이 공간이 드러나고, 가림과 다른 손으로의 목표 전환이 이어진다"></a>

[**MP4 크게 보기**](assets/20261107-e27-arm-approach/event.mp4) · [**운반부터 최종 관측까지**](20261107-astra-regrasp698-progress-named-001.ko.md) · [**장면별 분석**](../collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md) · [**피드백 남기기**](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new?title=%5BE27%20%ED%94%BC%EB%93%9C%EB%B0%B1%5D)

**로컬 공식 평가기의 최신 결과와 최고 기록은 원점수 5/50, 착의 득점 0, `success=false`입니다.** Codabench의 공식 제출·리더보드 성적을 뜻하지 않습니다. E25에서 새로 잡은 경계를 유지하며 옷을 들어 운반했고, E27 경계928에서는 전완과 노란 경계 사이 큰 공간이 보였습니다. 후반에는 관절 추종 오차와 시야가 일부 회복됐지만, 연속 소매 통과와 추가 득점은 확인하지 못했습니다.

**현재는 E27에서 수집을 마감한 상태입니다. E28은 준비된 후보이며 미시작·미예약입니다.** 기술 검사 통과와 좋은 시연의 학습 승인은 다르며, 공개 검수 출발점의 승인은 `unreviewed`입니다. [11월 7일 마감](../project/SESSION_WRAPUP_20261107.ko.md) · [후속 후보](../collection/research/2026-11-07-e27-single-arm-continuation.ko.md)

## 이 갤러리를 읽는 방법

처음에는 **직접 조작한 시연**, 다음에는 **Astra가 공개 관측을 보고 행동한 시연**을 시간순으로 봅니다. 각 장은 “무엇을 바꿨나 / 실제 무엇이 보였나 / 무엇이 아직 남았나” 순서입니다. 점수가 같더라도 파지·운반·관측 복구가 어떻게 달라졌는지 비교합니다.

| 보고 싶은 내용 | 바로 가기 |
|---|---|
| 사람이 두 로봇을 직접 움직인 모습 | [1. 직접 조작](#1-직접-조작--두-로봇을-움직이며-수집-경로-확인) |
| 모델의 첫 행동, 첫 5점, 두 로봇 운반 | [2. Astra 연결과 픽업](#2-astra-연결과-픽업--0점에서-첫-5점으로) |
| 관측·파지·명령 표현이 달라진 과정 | [3. 더 잘 보고 정확하게 움직이기](#3-더-잘-보고-정확하게-움직이기--e10e19) |
| 목·위쪽·짧은 탐색 등 경로 비교 | [4. 진입 전략 비교](#4-진입-전략-비교--e20e24) |
| 새 파지, 자세 보상, 최신 운반·접근 | [5. E25–E27](#5-새-파지와-접근을-연결하기--e25e27) |
| 모든 시도와 실패를 빠짐없이 찾기 | [7. 전체 색인](#7-전체-실행과-관련-자료-찾기) |

### 직접 조작과 Astra 자동 수집은 무엇이 다른가

| 구분 | 직접 조작 | Astra 자동 수집 |
|---|---|---|
| 행동을 고르는 주체 | Chrome 화면을 보는 사람 | Codex CLI의 `gpt-6-astra` |
| 입력과 출력 | 영상 확인 후 키보드 입력 | 공개 RGB-D·로봇 상태 → JSON 행동 |
| 수집 운영 | 기본 deferred export: ESC 뒤 이미지·학습 파일 생성, READY 대기 | `collector_stream`: 관측·행동·다음 관측을 실행 중 기록 |
| 이 갤러리의 대표 자료 | 10월 26일 부분 시연 | 11월 6–7일 E00–E27과 별도 연결 시험 |
| 확인한 범위 | 집기·들기·운반 일부, 공식 점수 미확인 | 공식 평가기 픽업5, 착의0; 실패·복구 포함 |

두 경로는 같은 공식 로봇 행동 인터페이스를 사용하지만, 동일 레이아웃·시간·평가 조건으로 통제한 사람 대 AI 성능 비교는 아닙니다. 실시간 사람–모델 제어권 전환이 완성됐다는 뜻도 아닙니다.

### 영상의 시간과 점수

- **전이 1개 = 관측 → 행동 → 다음 관측의 0.05초 기록**입니다. 전이 수와 모델 호출 수는 다릅니다.
- 자동 수집의 4분할 사건 영상은 위쪽이 머리, 아래쪽이 손목입니다. **두 행 모두 왼쪽 robot_1, 오른쪽 robot_0**이며 원본 카메라는 각각256×256입니다. 카메라 안의 장면은 좌우 반전하지 않습니다.
- 일반적인 자동 시연 미리보기는 **20Hz 기록을 5fps로 재생한 4배 느린 영상**입니다. 모델을 기다린 실제 시간은 빠져 있습니다. 사람 편집 영상과 짧은 연결 시험의 배속은 별도 표기를 따릅니다.
- **공식 원점수, 영상의 시각적 진전, 파일 QC, 학습 승인은 서로 다릅니다.** 모델의 `first_sleeve` 같은 단계명은 행동 의도이며 득점 증거가 아닙니다.
- 재실행은 과거 공개 행동을 새 환경에서 다시 수행하는 방식입니다. 정확한 천 상태 checkpoint 복원이나 독립 성공 시연 추가가 아닙니다.

[화면 배치 변경의 원본·산출물 해시](assets/robot-layout-20261110/provenance.json) · [사건 영상과 경계의 정의](EVENT_EXPORT.ko.md) · [공식 점수 정의](../competition/EVALUATION.md) · [출발점·방법·계보 색인](../collection/catalog/README.ko.md)

## 1. 직접 조작 · 두 로봇을 움직이며 수집 경로 확인

### 10월 26일 · Chrome 키보드 부분 시연

<a href="../videos/20261026-human-pickup-transport.mp4"><img src="assets/20261026-human-pickup-transport/preview.gif" width="960" alt="사람이 Chrome 키보드로 두 로봇을 조작해 옷에 접근하고 양쪽을 들어 마네킹 방향으로 옮기는 실제 편집 영상"></a>

[**33초 편집 MP4**](../videos/20261026-human-pickup-transport.mp4) · [장면과 제어 출처](20261026-human-pickup-transport.ko.md) · [당시 수집 기록](../project/DEMO_20261026.ko.md) · [변환 출처](assets/20261026-human-pickup-transport/provenance.json)

| 무엇을 했나 | 확인한 것 | 남은 것 |
|---|---|---|
| 두 로봇 접근·집기·들기·운반을 직접 조작 | 2,225전이, 로봇 시간111.25초의 부분 시연 | 소매·머리 통과, 공식 점수와 성공 승인 |
| 다수 키와 두 로봇을 함께 제어 | 조작 부담과 느린 시각 피드백을 실제로 경험 | 반복 가능한 성공 시연의 확보 |

영상은 33.08초 편집본이고 구간별 배속이 다릅니다. 편집 영상의 재생시간을 로봇 시간이나 실제 조작시간으로 읽지 않습니다. 11월 3일에는 Chrome UI와 수집 환경을 다시 점검했습니다. [UI 복구 기록](../project/END_20261103.ko.md)

## 2. Astra 연결과 픽업 · 0점에서 첫 5점으로

### 11월 6일 · 먼저 관측과 실제 행동이 연결되는지 확인

모델이 로봇을 잘 다루는지 평가하기 전에, 공개 관측을 전달하고 작은 행동을 실행한 뒤 정상 종료·기록하는 경로를 검증했습니다. 연결 시험은 착의 시연과 별도로 분류합니다.

| 기록 | 무엇을 바꿨나 | 확인한 것 / 미확인 |
|---|---|---|
| [r5 연결 시험](20261106-codex-robot-wiring-r5.ko.md) | 세 번 판단해 작은 lift·정지·종료 | 3전이·0.15로봇초, 파지·착의 성능 시험 아님 |
| [plan3 연결 시험](20261106-exec-plan3-wiring-001.ko.md) | 한 응답에 세 행동 목록 | 목록3개 실행. 중간 관측 기반 조건부 복구는 아님 |
| [E00 첫 착의 시도](20261106-astra-dressing-001.ko.md) | 실제 옷 접근·닫기·시험 들기 | 167전이·8.35로봇초, 0점·파지 성공 미확인 |
| E04 유지 시험 | 들고 기다리기 | 유효 유지2.9초로3초 조건 미달. 모델의 완료와 평가 조건 차이 확인 |

### E05 · 유지 여유를 둔 뒤 첫 공식 픽업 5점

<a href="../collection/attempts/20261106-astra-pickup-hold5-001/overview.mp4"><img src="../collection/milestones/20261106-astra-pickup-hold5-001/images/pickup-5-step-000246-overview.png" width="760" alt="E05 공식 픽업 첫5점 경계246의 실제 전체 배치. 로봇0이 옷자락을 들어 유지한다"></a>

[**재파지부터 유지까지 MP4**](../collection/attempts/20261106-astra-pickup-hold5-001/overview.mp4) · [시간순 행동](20261106-astra-pickup-hold5-001.ko.md) · [첫5점 경계246](../collection/milestones/20261106-astra-pickup-hold5-001/README.ko.md) · [종료 검토](../collection/reviews/20261106-astra-pickup-hold5-001.ko.md) · [영상 출처](assets/20261106-astra-pickup-hold5-001/provenance.json)

**바꾼 것:** 유지에 여유를 둔 목표. **확인:** 253전이·12.65로봇초, 평가 유효 유지3.35초로 픽업5점. **미확인:** 협력 착의·소매 통과. 로봇0 위주로 들었으므로 두 로봇의 공동 들기 성과와 구분합니다.

### E07 · 처음부터 두 로봇이 함께 들고 운반

<a href="assets/20261106-astra-coordinated-fresh-001-multiview/event.mp4"><img src="assets/20261106-astra-coordinated-fresh-001-multiview/preview.gif" width="960" alt="E07 공동 운반 후 손 근처 접근 경계620~700. 위는 두 머리, 아래는 두 손목의 실제 공개 RGB"></a>

[**손 근처 접근 MP4**](assets/20261106-astra-coordinated-fresh-001-multiview/event.mp4) · [전체 운반·사건 설명](20261106-astra-coordinated-fresh-001.ko.md) · [전체 MP4](../collection/attempts/20261106-astra-coordinated-fresh-001/overview.mp4) · [픽업356·접근700](../collection/milestones/20261106-astra-coordinated-fresh-001/README.ko.md) · [종료 분석](../collection/reviews/20261106-astra-coordinated-fresh-001.ko.md)

**바꾼 것:** 두 로봇의 역할을 둔 집기·들기·공동 이동. **확인:** 경계356에서 픽업5점, 경계700에서 손 근처 접근. 전체1,067전이·53.35로봇초이며 실제 경과는83분54초였습니다. **남은 것:** 소매 의도24개 행동 구간·254전이를 진행했지만 착의 득점은0이었습니다.

이 실행이 이후 준비·접근 분기의 원본이 됐습니다. [평평한 옷→초기 들기 MP4](assets/20261106-e07-flat-to-lift/event.mp4) · [운반 overview 미리보기](assets/20261106-astra-coordinated-fresh-001/preview.gif) · [네 카메라 출처](assets/20261106-astra-coordinated-fresh-001-multiview/provenance.json)

## 3. 더 잘 보고 정확하게 움직이기 · E10–E19

### 11월 6–7일 · 관측 → 지지 → 거리 → 명령 표현

| 변화 | 실제 실행 | 확인한 것 | 여전히 미확인 |
|---|---|---|---|
| E10–E13 관측·경로 | 접근 분기, 과거 RGB, 밑단 경로, 손목 depth 패널 | 손·천의 거리와 가림을 더 구체적으로 검토 | 어느 입구를 어떻게 통과하는가 |
| E14–E15 준비·대기 | 중립6전이, 더 이른264부터 입구 준비 | 실제 들기·운반, 끝부분 가림·손가락 변화 기록 | 연속 입구·소매 통과 |
| E16–E17 지지·재파지 | 한쪽씩 들기, R0의 다른 경계 후보 재파지 | 재파지 부근 천의 국소 동행 | 두 자유 경계·독립 양측 지지 |
| E18 깊이 질의 | 픽셀 depth 질의3회, 운반·팔 접근 | 20개 유효점의 가시 표면 깊이 | 의미·가림 뒤 표면·입구 통과 |
| E19 명명된 행동 | 이름을 공식9채널에 변환, 세 접근·복구 | 이 시도의12개 act 변환 일치 | 관절 추종·천 상태·소매 성공 |

### E15 · 들어 올린 틈이 통과 가능한 입구인가

<a href="20261106-astra-opening264-001.ko.md"><img src="../collection/assets/20261106-opening-first-partial-review/obs00003-robot_0_head.png" width="480" alt="E15 입력3의 실제 로봇0 머리 관측. 천이 들리고 층 사이 어두운 공간이 보이지만 입구 정체는 미확인"></a>

[준비264–325 MP4](assets/20261106-e15-preparation/event.mp4) · [운반325–509 MP4](assets/20261106-e15-transport/event.mp4) · [가림·복구509–611 MP4](assets/20261106-e15-hand-recovery/event.mp4) · [E15 전체 갤러리](20261106-astra-opening264-001.ko.md) · [정량 분석](../collection/reviews/20261106-astra-opening264-001.ko.md)

천이 올라오고 실제 lift가 움직인 것은 확인했습니다. 그러나 어두운 주름, 몸통 입구, 소매를 한 장면으로 구별할 수는 없었습니다. E15는5점으로 마감했으며 depth 패널·중립 대기를 붙였다는 사실만으로 효과가 입증된 것은 아닙니다.

### E16–E19 · 문제를 하나씩 분리

| 실험 | 가장 먼저 볼 영상 | 핵심 설명 |
|---|---|---|
| [E16 지지·재파지](20261106-astra-support264-002.ko.md) | [순차 지지](assets/20261106-e16-support/event.mp4) / [재파지](assets/20261106-e16-regrasp/event.mp4) / [입구 준비](assets/20261106-e16-opening/event.mp4) | 국소 천 동행을 확인했으나 최종0점. 0점만으로 파지 실패를 단정하지 않음 |
| [E17 lower-rim 변경](20261106-astra-layer352-001.ko.md) | [재파지·공동 들기](assets/20261106-e17-regrasp/event.mp4) | 새 경계를 겨냥한 조작은 실제 수행, 최종5점. 서로 다른 입구 층 획득은 미확인 |
| [E18 깊이·운반](20261106-astra-guide470-depth-001.ko.md) | [운반](assets/20261107-e18-transport/event.mp4) / [배열 roll 오류와 복구](assets/20261107-e18-roll-recovery/event.mp4) | 거리 질의는 작동. 설명 없는 roll+1 반복으로 감독 중단, 최종5점 |
| [E19 명명 행동](20261107-astra-entry801-named-001.ko.md) | [세 접근·복구](assets/20261107-e19-named-entry/event.mp4) | 명령 변환은 일치했으나 손 가림·복구 뒤 연속 통과 미확인, 최종5점 |

E18·E19의 전략명에 guide가 있지만, 실제 새 가이드 경계를 열고 다시 잡은 횟수는0입니다. **전략 이름·모델 설명·실제 행동을 따로 기록**한 것이 중요한 변화입니다. [depth 입력 표현](../collection/research/2026-11-06-wrist-depth-input.ko.md) · [E18 리뷰](../collection/reviews/20261106-astra-guide470-depth-001.ko.md) · [E19 리뷰](../collection/reviews/20261107-astra-entry801-named-001.ko.md)

## 4. 진입 전략 비교 · E20–E24

### 11월 7일 · 목 준비, 위에서 하강, 작은 탐색, 목적 있는 진행

| 실험 | 무엇을 바꿨나 | 확인된 범위 | 결과와 한계 |
|---|---|---|---|
| [E20 목 우선](20261107-astra-neckline470-named-001.ko.md) | 목 후보 두 곳으로 실제 재파지 | [목 후보 파지 준비](assets/20261107-e20-neckline-regrasp/event.mp4) | 0점. 운반·머리 통과는 미시험이므로 목 우선 전체 경로 실패로 확대하지 않음 |
| [E21 상방·하강](20261107-astra-overhead470-named-001.ko.md) | 높은 공동 접근과 두 번 하강 | [하강·복구](assets/20261107-e21-overhead-entry/event.mp4), [테이블 복귀·재파지](assets/20261107-e21-table-regrasp/event.mp4) | 5점.40판단 소진 후 새 파지 지지 시험은 못 함 |
| [E22 작은 탐색](20261107-astra-probe787-named-001.ko.md) | 작은 전진 한 번·시점 보정 | [새26전이·1.3초](assets/20261107-e22-entry-probe/event.mp4) | 5점.18판단 예산 중4판단에서 종료, 접근 불가능을 입증한 기록은 아님 |
| [E23 과제 진행](20261107-astra-progress787-named-001.ko.md) | 더 목적 있는 전진·방향·높이 변경 | [방향 전환](assets/20261107-e23-direction-change/event.mp4), [손·전완 노출](assets/20261107-e23-arm-head-progress/event.mp4) | 5점. 새 노출 관계는 유용하지만 공식 소매 통과 아님 |
| [E24 이어가기](20261107-astra-progress1179-named-001.ko.md) | E23/1179에서 추가 조정 | [진입·재가림·부분 복구](assets/20261107-e24-entry-recovery/event.mp4) | 5점.22행동 후 감독 종료. 마지막 부분 복구도 보존 |

이 비교는 하나의 원본 계보에서 시작 조건과 예산이 다른 관찰 실험입니다. **특정 프롬프트만의 효과를 분리한 ablation이나 독립 성공률 표본은 아닙니다.** E20의 파지를 E21이 이어받은 것도 아니고, E21의 마지막 재파지를 E22가 이어받은 것도 아닙니다.

E24에서는 retract 목표를 보냈지만 실제 arm이 반대 방향으로 움직인 구간도 확인했습니다. 명령·제어기 목표·실제 위치를 나눠야 이후 접촉과 복구를 설명할 수 있습니다. [목표·실제 팔 운동 대조](../collection/reviews/20261107-astra-progress1179-named-001-motion.ko.md) · [E21 depth 검토](../collection/reviews/20261107-astra-overhead470-named-001-local-depth.ko.md)

## 5. 새 파지와 접근을 연결하기 · E25–E27

### 11월 7일 · E25에서 실제 새 파지, E27에서 그 파지의 운반

| 단계 | 영상 | 잘된 부분 | 아직 남은 부분 |
|---|---|---|---|
| **E25 열기→새 위치→닫기** | [재파지591–698](assets/20261107-e25-rim-regrasp/event.mp4) | R1이 실제 열고 낮은 경계로 옮겨 한 번 보정한 뒤 다시 닫음 | 반대인 두 입구 경계인지 미확인 |
| **E25 한쪽 들기** | [국소 동행657–698](assets/20261107-e25-local-follow/event.mp4) | R1 실제+26.62mm와 주변 천의 동행 | 테이블·닫힘 기여가 남아 독립 하중 지지는 미확인 |
| **E26 다른 손·접근면** | [하강·접근](assets/20261107-e26-lower-approach/event.mp4) | 경계953에서 두 손·전완 관계 재노출 | E25 새 파지의 후속이 아니며 새로운 파지는0회 |
| **E26 자세·시점 보상** | [자세 보상](assets/20261107-e26-compensated-posture/event.mp4) / [시점 회전](assets/20261107-e26-view-orbit/event.mp4) | 큰 손목 자세 변화와 작은 grasp 기준점 변화, 손 일부 재노출 | 천 재료점 고정·연결 전완·소매 통과는 미확인 |
| **E27 새 파지 운반** | [상승·운반698–842](assets/20261107-e27-lift-transport/event.mp4) | E25 행동 재실행 뒤 경계790에서 테이블 이탈·운반 유지 | 안정된 소매 입구와 독립 양측 지지는 미확인 |
| **E27 팔 접근·복구** | [868–968](assets/20261107-e27-arm-approach/event.mp4) / [전체·최종 관측](20261107-astra-regrasp698-progress-named-001.ko.md) | 928 팔–경계 관계, D17 목표 추종 회복, D20·21 부분 시야 복구 | D11 목표 손 전환 이후에도 착의 득점0. 목표 전환이 실패 원인인지는 미검증 |

**세 실험 모두 최종5점·착의0입니다.** 같은 점수 안에서도 “다른 곳을 잡았다 → 국소적으로 따라왔다 → 테이블 밖으로 운반했다”는 증거가 단계적으로 늘었습니다. E25의 원래 경계가 독립 하중을 인증받았다는 뜻은 아니며, E26은 기존 파지에서 다른 손·접근면·관측을 비교한 별도 분기입니다.

[E25 갤러리](20261107-astra-opposing563-named-001.ko.md) · [E25 분석](../collection/reviews/20261107-astra-opposing563-named-001.ko.md) · [E26 갤러리](20261107-astra-hand-swap787-named-001.ko.md) · [E26 분석](../collection/reviews/20261107-astra-hand-swap787-named-001.ko.md) · [E27 분석](../collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md)

### 최신 E27을 숫자로 읽기

| 지표 | 값 | 읽는 법 |
|---|---:|---|
| 전체 기록 | 1,159전이 /57.95로봇초 | 재실행과 새 구간 모두 포함 |
| 새 후속 구간 | 461전이 /23.05로봇초 | 334모델 행동+126자동 정착+1예산 정리 |
| 재실행 | 698전이 /34.90로봇초 | 과거 행동을 새 환경에서 다시 실행 |
| 판단과 행동 | 23모델 호출 /22행동 | depth 질의1회6유효점, 질의 물리진행0 |
| 실제 경과 | 40분50.624초 | 모델 호출 경로·재실행·환경·기록 시간 포함 |
| 마감·검사 | 판단 예산 종료 /1,159개 QC 통과 | 모델 자율 성공 선언도, 학습 승인도 아님 |

[전이 출처와 최종 평가](../collection/attempts/20261107-astra-regrasp698-progress-named-001/manifest.json) · [학습 검토 구간](../collection/reviews/20261107-astra-regrasp698-progress-named-001-learning-segments.json) · [고정 백업 검증](../project/sessions/20261107-e27-backup-verification.json)

## 6. 다음 비교는 무엇을 검증할까

**현재 미실행 후보 E28:** E27/928과 그 이전890·906의 관측을 이용해 같은 팔의 목표 진행을 더 이어가는 비교를 준비했습니다. 928의 정확 경계 점수와 독립 지지는 미확인입니다. CPU325검사·소스166개 해시 일치로 코드 준비를 확인했지만, 실제 모델·물리·득점 효과는 아직 시험하지 않았습니다. 자동 재개하지 않습니다.

다음 질문은 “같은 팔의 유용한 관계를 유지하면 연속 통과 증거를 만들 수 있는가”입니다. 완벽한 시야가 생길 때까지 멈추는 규칙이 아니라, 공개 관측의 추적 근거를 갱신하며 유한한 접근·복구를 비교하려는 후보입니다. [후보 설계와 범위](../collection/research/2026-11-07-e27-single-arm-continuation.ko.md)

| 확보한 것 | 이어서 확인할 것 |
|---|---|
| 공식 픽업5점 | 반복 가능한 출발 준비·파지 유지 |
| 새 파지의 국소 동행과 운반 | 원하는 입구의 두 경계·같은 손의 연속 관계 |
| 거리 질의·정확한 명령 변환 | 관절 목표 추종과 천의 실제 반응 |
| 접근 실패·부분 시야 복구 기록 | 짧은 진입의 공식 추가 득점 |
| QC·계보·원본 백업 | 구간별 학습 승인, 새 baseline 학습과 로컬 평가 |

원점수10점은 실용적인 중간 목표이며 전체 착의 성공과 다릅니다. 첫 소매에만 경로를 고정하지 않지만, 어떤 경로든 실제 행동·공개 관측·별도 공식 평가로 검증해야 합니다. [0→5→10 조합 장기계획](../collection/research/2026-11-07-composable-scoring-data-plan.ko.md) · [현재 복원·재개 안내](../project/START_HERE.ko.md)

## 7. 전체 실행과 관련 자료 찾기

아래는 이 페이지에서 선별한 장면 외의 자료까지 찾는 색인입니다. **과제 시연, 연결 시험, 실패, 미실행 계획을 따로 유지합니다.** 각 상세 페이지의 “다음” 문장은 당시 계획일 수 있으므로 현재 실행 여부는 [STATUS](../project/STATUS.md)와 [최신 마감](../project/SESSION_WRAPUP_20261107.ko.md)을 따릅니다.

<details>
<summary>전체 갤러리 · 사람 시연과 Astra 실제 실행</summary>

| 구분 | 상세 갤러리 |
|---|---|
| 사람 직접 조작 | [10/26 부분 시연](20261026-human-pickup-transport.ko.md) |
| 연결 시험 | [r5](20261106-codex-robot-wiring-r5.ko.md) / [plan3](20261106-exec-plan3-wiring-001.ko.md) |
| 초기 착의·픽업 | [E00 첫 시도](20261106-astra-dressing-001.ko.md) / [E05 첫5점](20261106-astra-pickup-hold5-001.ko.md) / [E07 공동 운반](20261106-astra-coordinated-fresh-001.ko.md) |
| 관측·경로·정착 | [E10 접근 분기](20261106-astra-sleeve-branch700-003.ko.md) / [E11 과거 RGB](20261106-astra-sleeve-history-001.ko.md) / [E12 밑단 경로](20261106-astra-hem-route-001.ko.md) / [E13 depth](20261106-astra-hem-depth-001.ko.md) / [E14 정착](20261106-astra-hem-settle-001.ko.md) / [E15 입구 준비](20261106-astra-opening264-001.ko.md) |
| 지지·명령 표현 | [E16 순차 지지](20261106-astra-support264-002.ko.md) / [E17 재파지](20261106-astra-layer352-001.ko.md) / [E18 깊이 질의](20261106-astra-guide470-depth-001.ko.md) / [E19 명명 행동](20261107-astra-entry801-named-001.ko.md) |
| 진입 전략 | [E20 목 후보](20261107-astra-neckline470-named-001.ko.md) / [E21 상방·하강](20261107-astra-overhead470-named-001.ko.md) / [E22 탐색](20261107-astra-probe787-named-001.ko.md) / [E23 진행](20261107-astra-progress787-named-001.ko.md) / [E24 연속 진행](20261107-astra-progress1179-named-001.ko.md) |
| 최신 파지·관측·운반 | [E25 새 파지](20261107-astra-opposing563-named-001.ko.md) / [E26 접근면·보상](20261107-astra-hand-swap787-named-001.ko.md) / [E27 새 파지 운반](20261107-astra-regrasp698-progress-named-001.ko.md) |
| 출발점 비교 | [5개 초기 출발점 화면](20261107-support-startpoints.ko.md) / [전체13개 출발점과 방법 catalog](../collection/catalog/README.ko.md) |

</details>

<details>
<summary>연결 실패·부분 자료·중단 이력</summary>

- E01 시간 계측 수정, E02 AppServer 호환성 실패, E04 유지 조건 미달, E06 prefix 이어하기는 [전체 역사](../project/HISTORY.ko.md)에서 봅니다. 연결 실패를 착의 능력의 실패로 집계하지 않습니다.
- E08은 설정 누락으로 환경·actor 시작 전 실패했습니다. E09는 중단 응답 순서 문제로141개 부분 전이를 남겼고 QC에 실패했습니다. 원본은 보존하고 정상 재실행 출처나 학습 자료로 사용하지 않습니다. [E07 이후 분기 이력](../project/HISTORY.ko.md) · [분기와 재실행 원칙](../collection/guides/continuation-and-branches.ko.md)
- E18의 설명 밖 roll 반복과 감독 중단, E24 감독 종료, E21·E23·E27 예산 종료, 그 외 자율 종료는 각 상세 리뷰에 구분돼 있습니다. 종료 방식만으로 성공·실패 원인을 대신하지 않습니다.
- 같은 계보의 여러 클립·시도는 독립 성공 데이터가 아닙니다. [실행 종류·QC·계보·계획을 구분한 정본](../collection/catalog/catalog.v1.json)

</details>

<details>
<summary>관측·경로·외부 참고를 주제별로 찾기</summary>

| 주제 | 근거 문서 |
|---|---|
| 초기 준비와 관측 이력 | [11/6 저녁 재개 기록](../project/sessions/20261106-evening-resume.ko.md) / [E11 관측 비교](../project/sessions/20261106-resume10.ko.md) / [E14 전체 기록](../collection/attempts/20261106-astra-hem-settle-001/README.ko.md) |
| 파지·천 방향·입구 가설 | [더 이른5점 출발점](../collection/research/2026-11-07-earlier-support-startpoints.ko.md) / [의복 방향 가설](../collection/research/2026-11-07-garment-direction-hypotheses.ko.md) / [E25 재파지 후보](../collection/research/2026-11-07-opposing-rim-candidate.ko.md) |
| 진입 경로 비교 | [named 이후 경로](../collection/research/2026-11-07-post-named-route-choice.ko.md) / [상방 후보](../collection/research/2026-11-07-overhead-drape-candidate.ko.md) / [상방 이후 대안](../collection/research/2026-11-07-post-overhead-method-options.ko.md) / [작은 탐색 후보](../collection/research/2026-11-07-entry-probe-candidate.ko.md) / [다른 손 후보](../collection/research/2026-11-07-leading-hand-candidate.ko.md) |
| 거리·제어 추종 | [E21 depth 국소 검토](../collection/reviews/20261107-astra-overhead470-named-001-local-depth.ko.md) / [E24 목표·실제 운동](../collection/reviews/20261107-astra-progress1179-named-001-motion.ko.md) |
| 실험별 상세 분석 | [E16](../collection/reviews/20261106-astra-support264-002.ko.md) / [E17](../collection/reviews/20261106-astra-layer352-001.ko.md) / [E20](../collection/reviews/20261107-astra-neckline470-named-001.ko.md) / [E21](../collection/reviews/20261107-astra-overhead470-named-001.ko.md) / [E22](../collection/reviews/20261107-astra-probe787-named-001.ko.md) / [E23](../collection/reviews/20261107-astra-progress787-named-001.ko.md) / [E24](../collection/reviews/20261107-astra-progress1179-named-001.ko.md) |
| 외부 방법 검토 | [공식 시연 경로](../collection/research/2026-11-07-official-demo-route-review.ko.md) / [BEHAVIOR 우승 방법 글](../collection/research/2026-11-07-behavior-champion-text-review.ko.md) / [시각적 이전 검토](../collection/research/2026-11-07-behavior-champion-visual-transfer.ko.md) |
| 파일·영상 출처 | [원본 경계와 영상 변환](EVENT_EXPORT.ko.md) / [실행별 공개 패키지](../collection/attempts/) / [원본 보존과 복원](../project/START_HERE.ko.md) |

</details>

피드백은 **실험 번호, 경계 또는 영상 시각, 카메라, 보이는 사실, 해석, 다음 비교 질문** 순서로 남기면 다음 수집에 연결하기 쉽습니다. [이슈 작성](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/issues/new) · [갤러리 처음으로](README.ko.md)
