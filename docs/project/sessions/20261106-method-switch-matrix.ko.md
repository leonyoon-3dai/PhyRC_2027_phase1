# 2026-11-06 저녁 · 미세조정 포화와 방법 전환 비교표

사용자 재개 요청에 따라 다양한 방법을 비교한다. 추가 지시는 **미세조정을 충분히 한 뒤 새로운 방법이 필요한지 계속 분석**하는 것이다. 이 문서는 공개 영상·최종 행동의 사후 분석과 다음 후보 설계다. **아래 세 후보는 이 문서 작성 시 아직 실행하지 않았으며 효과·점수 개선을 검증하지 않았다.** 독립 지지 진단은 별도 구현·실행 기록에서 확인한다.

## 관측 근거와 해석 한계

| 근거 | 확인한 것 | 결론 내리지 않은 것 |
|---|---|---|
| E15 준비 입력0·3·5: [입력0](../../collection/assets/20261106-opening-first-partial-review/obs00000-robot_0_head.png), [입력3](../../collection/assets/20261106-opening-first-partial-review/obs00003-robot_0_head.png), [입력5](../../collection/assets/20261106-opening-first-partial-review/obs00005-robot_0_head.png) | 초기에는 테이블 위 셔츠 외곽이 보인다. 이후 밑단 후보 부근에 좁은 가로 틈이 보이고 로봇 팔의 가림이 커진다. | 색이나 어두운 선만으로 실제 두 층·통과 가능한 입구·파지 위치를 확정하지 않는다. |
| E15 손 근처: [입력18](../../collection/assets/20261106-opening-final-review/obs00018-robot_0_wrist.png), [입력20](../../collection/assets/20261106-opening-final-review/obs00020-robot_0_wrist.png), [입력23](../../collection/assets/20261106-opening-final-review/obs00023-robot_0_wrist.png) | 손이 robot0 그리퍼 가까이에 나타나고, 개방·철수 후 그리퍼와 천의 관계가 달라진다. | 손이 입구 내부 공간에 정렬됐거나 통과했다고 판단하지 않는다. 특정 충돌 상대도 확정하지 않는다. |
| [E13 최종 결정](../../collection/attempts/20261106-astra-hem-depth-001/decisions.jsonl), D2·D13 | 한쪽 높이를 달리하는 짧은 형태 조정이 이미 실행됐다. | 비대칭 lift 자체를 신규 방법으로 세지 않는다. |
| 같은 E13 기록, D9–D13 | 신장→철수·형태 조정→재신장 사이클이 실행됐다. | 실제 이동만으로 손의 입구 통과가 진전됐다고 보지 않는다. |
| [E15 최종 결정](../../collection/attempts/20261106-astra-opening264-001/decisions.jsonl), D2·D13–D19 | 비대칭 높이 조정과 손 근처 옆 이동·철수·반전이 이미 있었다. | 작은 높이·속도·방향 보정을 다시 적용했다는 이유만으로 구조적으로 새로운 전략이라고 기록하지 않는다. |

원문 해석 범위: [E15 공개 검토](../../collection/reviews/20261106-astra-opening264-001.ko.md), [E13 공개 영상·과정](../../gallery/20261106-astra-hem-depth-001.ko.md), [E12 밑단 경로](../../gallery/20261106-astra-hem-route-001.ko.md). 원인 검토는 공개 RGB·공개 로봇 상태·최종 행동에 한정하며, 내부 천/마네킹 기하나 평가기의 내부 판정을 행동 정답으로 쓰지 않는다.

## 미세조정과 구조 변경을 구분

- **미세조정:** 같은 파지 배치·같은 추정 입구·같은 접근 방향에서 속도, steps, 작은 높이/옆 이동, 짧은 손목 각도, 중립 대기 등을 조절한다. 프롬프트 표현만 바꾼 것도 실제 행동 구조가 같으면 이 범주다.
- **구조 변경:** 실제 파지 위치나 잡는 층/가장자리 가설을 바꾸거나, 한쪽 지지·다른 쪽 가이드로 역할을 바꾸고 접근면을 변경하거나, 현재 보이지 않는 관계가 드러나도록 로봇 배치와 관측 방향을 바꾼다. 단순한 명칭 변경이 아니라 최종 행동·관측으로 실제 변경 여부를 확인한다.
- **먼저 구분할 문제:** 명령 후 로봇이 아직 목표로 움직이는 중인지, 충분히 움직였지만 천 형태가 원하는 방향으로 변하지 않는지, 형태는 바뀌었으나 가려져 판단할 수 없는지. 이 세 경우를 모두 “미세조정 실패”로 묶지 않는다.

## 시행 순서와 전환 기준 · 미실행 후보

독립 지지가 확인되면 **A → C**를 우선 검토한다. A가 테이블 준비 단계에서 포화되면 B를 비교한다. 출발 경계는 신뢰된 수집 설정에만 기록하며 actor 프롬프트에 과거 점수·평가·배치 정답을 넣지 않는다. E07 행동 재실행은 정확한 천 checkpoint가 아니다.

| 후보 | 권고 출발 | 바꿀 조작 구조 | 계속 미세조정할 근거 | 포화·방법 전환 근거 |
|---|---|---|---|---|
| **A. 테이블 지지 아래 반대쪽 밑단 층 재파지** | E07 258경계, 또는264에서 다시 지지 확보 | 기존 두 모서리 파지를 그대로 당기지 않고 한쪽씩 실제 파지 위치/층을 변경. 색으로 층을 단정하지 않음 | 분리된 경계가 더 명확해지고 새로운 관측에서도 유지됨. 각 파지에 대한 천의 반응이 구분됨 | 실제 로봇 이동을 확인한2–3회 보정에도 같은 좁은 틈만 남거나 층을 구분할 수 없음. 같은 파지에서 벌리기를 반복하지 않고 다른 가장자리·펼침 방법 검토 |
| **B. 소매 쪽 가이드 재파지** | 새 초기 상태 또는258경계 | 한 로봇은 몸통 지지, 다른 로봇은 목표 소매 쪽의 보이는 가장자리로 재파지. 몸통 입구→소매 경로의 늘어진 부분을 줄이는 가설 | 몸통 입구와 대응 소매 후보의 연결이 더 잘 보이고 새 가이드 파지가 유지됨 | 재파지 후에도 서로 다른 입구/경로를 구분하지 못함. 수치 조정보다 관측·옷 펼침 방법 변경 |
| **C. 손 진행 공간 확보 후 다른 방향 접근** | 독립 지지·입구가 확인된 초기264 분기 이후.700분기 반복은 우선순위 낮음 | 그리퍼를 손의 진행 공간 밖으로 두고 지지/가이드 역할과 접근 방향을 변경 | 손과 관련 테두리가 함께 보이며 작은 동작 뒤 예상한 상대 관계 변화가 확인됨 | 접근→실제 이동 확인→관측2–3회 후 손이 같은 하우징/외부 패널 뒤로 반복 소실. 철수하여 파지나 접근면 변경 |

**2–3회는 성공 판정이나 강제 종료 규칙이 아닌 포화 분석 기준이다.** 매번 다른 관련 관계가 드러나는 등 관측 가능한 진전이 있으면 같은 방법을 계속 다듬는다. 반대로 가림이나 비정상 형상 변화가 커지면 횟수를 채우려고 밀어 넣지 않는다. 잔류 운동이 큰 경우는 완료 관측을 먼저 확인하며, 모델 응답 대기는 simulation 시간을 진행시키지 않는다.

기록에는 매 보정의 의도한 오차, 실제 로봇 변화, 새로 보인 관계, 반복된 막힘, 방법을 유지/전환한 이유를 남긴다. 공식 점수는 별도 결과 확인이며 actor 입력·포화 판정의 정답 좌표로 사용하지 않는다.

## 후보 actor 지침 · 미적용 초안

아래 문장은 후보 전략 설명이다. 실제 적용 시 기존 공개 관측·행동 계약과 함께 별도 prompt hash·실행 소스를 남긴다. 프롬프트 파일이 존재한다는 사실을 실행이나 성능 검증으로 기록하지 않는다.

### A. 반대쪽 밑단 층 재파지

> While the shirt remains supported near the table, investigate whether the current grips control distinct boundaries of a usable body opening or merely pull along the same folded edge. Do not infer layers from color alone. If the opening remains a narrow slit despite observed robot motion, preserve one verified support and change only the other grasp to a separately visible rim region, using table support during release and regrasp. Aim to separate opposing visible lips of the opening rather than only increasing the distance between the same corners. Reconfirm each support and the aperture in current views before transport. Do not release both grips together or assume a regrasp succeeded.

### B. 소매 쪽 가이드 재파지

> Use a support-and-guide grasp arrangement. With the garment safely supported by the table and the partner, inspect the visible body opening and a candidate sleeve path. Consider moving one grasp from its current hem corner to an accessible visible edge nearer the intended sleeve while the partner supports the garment body. This is a change of grasp arrangement, not a blind push toward a presumed cuff. Preserve the intended topology: the hand should enter the body opening and emerge through the corresponding sleeve; do not treat pushing a hand into a cuff from outside as equivalent. Reassess the visible connection and support after each regrasp.

### C. 손 진행 공간과 접근 방향 변경

> Before approaching the hand, identify an actual free passage through the hypothesized opening and keep both grippers outside that passage. Do not align the hand with a held corner merely because the corner is easy to see. Assign one robot to preserve support and the other to guide the opening; equal movements are not required. If the wrist housing repeatedly hides the hand, retreat enough to restore the hand and both relevant rim edges, then change the approach direction or grasp arrangement before another entry attempt. Every viewpoint change must use the permitted robot controls and be followed by current observations.

### 공통 포화 분석

> Distinguish a command that has not yet produced its intended measured robot motion from a manipulation method that is not working. Allow short settling observations when needed. For each local correction, state the visible error being tested and compare the next observation with that prediction. After two or three executed correction-and-observation cycles leave the same ambiguity or obstruction, do not continue changing only speed, duration, or a small offset. Preserve support and change the grasp arrangement, opening orientation, approach direction, or observable view. Count renewed motion as progress only when it reveals a new relevant relationship; repeated disappearance of the hand is not entry evidence.

## 현재 상태

본 문서는 분석·실험 설계만 수행했다. 새 GPU 실행, 새 actor 호출, 코드 변경, 후보 적용, 추가 점수 확인은 수행하지 않았다. 기존 공개 자료에서 확인된 사실과 후보 가설을 구분하며, 실제 실험 결과는 [저녁 재개 일지](20261106-evening-resume.ko.md) 및 각 시도 기록으로 연결한다.

후속 구현 상태: A/B는 각각 `coordinated-regrasp-hem`·`coordinated-support-guide`로 구현하고 CPU 선택·경계 검사를 통과했다. 모델 행동과 점수 효과는 아직 미검증이며, C는 B의 접근 지침에도 포함하되 독립 실행 후보로는 미실행이다.
