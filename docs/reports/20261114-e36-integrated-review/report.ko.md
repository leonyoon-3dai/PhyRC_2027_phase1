# PhyRC E00–E36 통합 분석과 다음 사용자 개입 실험

[슬라이드 PDF](phyrc-e36-integrated-review.ko.pdf) · [재현·출처](README.ko.md)


## 01. 옷을 펼친 뒤, 손목을 통과시키기까지

E00–E36 통합 분석 · 사용자 관찰 × Codex 실행 근거 × Agentic Robotics 연구

근거: [현재 상태](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/project/STATUS.md) · [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [다음 작업 계획](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/COLLECTION_PLAN.md)

E36 최종5/50·새 착의점0·QC933/933. E37 이후 실행 없음.


## 02. 세 관점이 만나는 결론

관찰과 가설, 측정 결과, 연구의 적용 제안을 한 층으로 섞지 않는다.

근거: [E34 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-middle-grip470-retain-001.ko.md) · [E35 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wide-hem723-001.ko.md) · [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [연구 검증 범위](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/reports/20261114-e36-integrated-review/research-sources.json)

**사용자 관찰** — 옷의 폭과 손목 근처 위치는 유용해 보인다.  정확히 방향을 맞추고 몸쪽으로 밀면 다음 단계에 도달할 수 있다는 가설.

**Codex 실행 분석** — 접근·하강과 상대 위치 변화는 실제로 있었다.  E36의 새 base yaw 명령은 모두 0. 정확한 베이스 방향 정렬까지 충분히 시험하지는 못했다.

**연구에서 가져올 것** — 사람 개입의 경계, 실제 행동, 전후 효과를 구분해 기록한다.  연구의 기능·성과가 현재 PhyRC에 구현되거나 재현된 것은 아니다.

공통 우선순위: 같은 실패 설명을 늘리기보다, 사람의 짧은 조작으로 구분 가능한 질문을 만든다.


## 03. 사용자의 제안은 어디까지 시험됐는가

“방향을 맞춰 서기”와 “몸쪽 이동”을 별개의 수행 항목으로 검토한다.

근거: [E35 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wide-hem723-001.ko.md) · [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [E35–E36 배치](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/project/sessions/20261114-wide-hem-five-attempt-batch.ko.md)

| 사용자 관찰·요청 | 실제 반영 | 현재 판단 |
| --- | --- | --- |
| 옷 아래를 넓게 펼쳐 약간 위·옆에서 접근 | E35: 형상 조절·방향 변경 후 같은 손에 측면 접근 | 새 근접 관계 관측. 통과 미확인 |
| E34 형상이 이미 유용하므로 보존 | E36: E34/835에서 시작, 재파지·운반 준비 반복 없음 | 기존 형상 활용은 반영 |
| 정확히 손목 방향에 맞춰 서기 | E36: wrist yaw 2회, 새 base yaw 명령 0 | 베이스 방향 정렬의 충분한 시험은 아님 |
| 몸쪽으로 밀어 넣기 | E36: 몸쪽·하강 시험 5회, 매번 후속 관측 | 실제 운동 있음. 연속 전완 진행·소매 출구 미확인 |

“추가 5점 가능”은 사용자 가설이다. 다음 5점인 첫 소매 통과는 별도 평가에서 충족되지 않았다.


## 04. 축적된 경험: 이미 되는 부분과 남은 문제

전체 경험은 보존된 리뷰·계보·코드를 종합했다. 모든 과거 영상을 이번에 전수 재시청한 것은 아니다.

근거: [전체 시연](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/EPISODES.md) · [전체 경험·설계 근거](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/research/2026-11-14-collection-system-redesign.ko.md)

**사람·E00–E07** — 사람 부분 시연 2,225전이. 초기 픽업과 두 로봇 공동 운반을 관측.

**E10–E19** — 관측·depth·지지 검사·재파지·정착을 이미 비교. 중립에서도 실제 운동이 남음.

**E20–E27** — 새 경계 파지와 운반, 첫 팔 접근을 시험. 손 선택 전환·통과 미확인이 남음.

**E28–E32** — 같은 손 유지·대각선/중앙 접근 비교. E32는 불완전 원본이며 정상 replay에서 제외.

**E33–E34** — 새 파지 준비 뒤 들기·운반·하강까지 확인. 준비가 끝난 것과 진입 성공은 다름.

**E35–E36** — 넓은 형상과 즉시 몸쪽 접근을 비교. 사용자 피드백을 반영했으나 새 착의점 0.


## 05. 최근 네 시연: 무엇을 새로 수집했는가

결정 수와 모델 호출, 재생 전이와 새 전이를 구분한다.

근거: [E33 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-middle-grip264-001.ko.md) · [E34 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-middle-grip470-retain-001.ko.md) · [E35 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wide-hem723-001.ko.md) · [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md)

| 시연 / 직접 출발 | 결정 / 호출 | 전체 = 재생 + 새 전이 | 최종 raw / 새 착의점 | 수집 경과 |
| --- | --- | --- | --- | --- |
| E33 · E28/264 | 20 / 21 | 471 = 264 + 207 | 0 / 0 | 22.52분 |
| E34 · E33/470 | 20 / 24 | 836 = 470 + 366 | 5 / 0 | 32.66분 |
| E35 · E34/723 | 19 / 21 | 983 = 723 + 260 | 5 / 0 | 40.17분 |
| E36 · E34/835 | 11 / 12 | 933 = 835 + 98 | 5 / 0 | 28.12분 |

새 전이는 model·settle·종료 정리를 포함한다. E35/E36의 픽업5는 각 replay에서 얻었다.

E34/723 이후는 7act, E35는 18act다. 다른 출발점·예산·재생 편차를 전략 하나의 인과 효과로 해석하지 않는다.


## 06. 최근 공개 영상: 근접은 보이지만 통과는 미확인

각 시연의 마지막 robot_1 head. 카메라·로봇 자세가 달라 픽셀 폭을 물리 개방률로 비교하지 않는다.

근거: [E34 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-middle-grip470-retain-001.ko.md) · [E35 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wide-hem723-001.ko.md) · [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md)

E34 · 836: 운반 후 손목 근처 형상

E35 · 983: 더 넓은 외관과 새 근접 관계

E36 · 933: 몸쪽 시험 뒤에도 파지부 곁에 손


## 07. E36: 같은 손·전완은 보였고, 진입은 남았다

각 묶음은 왼쪽 robot_1 / 오른쪽 robot_0, 위 head / 아래 wrist. 원본 픽셀을 반전하지 않았다.

근거: [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [E36 원본 근거](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/attempts/20261114-astra-wrist-body835-001/manifest.json)

초기와 최종 공개 head/wrist를 비교. 손·연결 전완은 유지됐지만 자유 경계 통과와 소매 출구는 확인하지 못했다.


## 08. E36에서 새로 분명해진 실행 차이

명령값·관절 변위·그리퍼 실제 이동·천의 진행은 같은 양이 아니다.

근거: [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md)

**5회 진입 시험** — 10act 중 몸쪽/하강 5회, wrist 방향 2회, 팔 수축 1회, 중립 관찰 2회.  처음부터 진입을 시도했다.

**-17mm ≠ -1mm** — D5 robot_1 lift 약 -16.97mm. base 기준 grasp Z는 약 -0.97mm.  손목 pitch 편차가 함께 나타났다.

**정착 중 일부 되돌림** — D5 base Y: 명령 +10.97mm → settle -2.78mm. D9: +11.44mm → -1.23mm.  world Y는 몸쪽 거리가 아니다.

같은 손이 파지 모서리/housing 가까이에 남았다는 관측은 있으나, 정확한 접촉 원인은 확정하지 않았다.


## 09. 관측 판정 기준: 확인할 수 있는 만큼만

unknown을 허용한다. 아래 단계의 증거가 위 단계의 성공을 대신하지 않는다.

근거: [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [전체 경험·설계 근거](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/research/2026-11-14-collection-system-redesign.ko.md)

| 층 | 이번에 확인한 근거 | 남겨야 할 한계 |
| --- | --- | --- |
| 1. 명령·실행 | 실제 적용 action, 로봇 pose, 동작/정착 경계 | 속도 명령만으로 이동 거리·천 효과를 확정하지 않음 |
| 2. 국소 천 변화 | jaw 근처 천 동행, 주름·윤곽과 상대 위치 변화 | 열기0이나 국소 동행은 독립 지지·부착의 인증이 아님 |
| 3. 유효 자유 구간 | 손·경계·housing을 여러 공개 시점에서 비교 | 색 띠·파란 면·가림만으로 통로 정체/깊이를 확정하지 않음 |
| 4. 손목·전완 진행 | 같은 손 식별과 경계의 전후 관계 | 가림은 통과도 이탈도 아님. 이번 진행 판정은 미확인 |
| 5. 별도 과제 결과 | 공식 raw5/50, 착의0, success=false | 평가 정답을 actor 입력이나 시각 라벨로 역주입하지 않음 |


## 10. 비용을 해석하려면 재생부터 분리해야 한다

수집 클라이언트 wall 시간. 후속 QC·검토·백업·게시 시간은 이 그래프에 포함하지 않는다.

근거: [E34 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-middle-grip470-retain-001.ko.md) · [E35 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wide-hem723-001.ko.md) · [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md)

E34: 전체 1959.323s / actor 1170.153s / replay 418.908s / 새 환경 318.601s

E35: 전체 2410.110s / actor 1473.917s / replay 634.765s / 새 환경 248.767s

E36: 전체 1686.999s / actor 806.640s / replay 735.678s / 새 환경 96.534s

모델 대기 중 물리는 정지한다. actor 시간은 CLI·통신·대기 등을 포함하며 순수 추론시간이 아니다.


## 11. 데이터 수량과 독립적인 시연 가치는 다르다

카탈로그의 demonstration만 집계. 연결 시험·실행 실패·미실행 계획과 사람 부분 시연은 이 수량에서 제외.

근거: [카탈로그](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/catalog/catalog.v1.json) · [E35 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wide-hem723-001.ko.md) · [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md)

**33개 시연 기록** — QC 통과 31 / 실패 2

**24,296개 전이** — QC 통과 기록의 합계

**16,095개 replay** — 명시된 재생 완료 합계

demonstration33 / QCpassed31 / QCfailed2 / transitions24296 / known replay16095 / remainder8201 / replay null3 / source-group labels4.


## 12. Codex 진단: 단일 실패 원인으로 단정하지 않는다

직접 조작은 답을 대신하는 수단이 아니라, 경쟁하는 설명을 나눌 실험이다.

근거: [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [전체 경험·설계 근거](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/research/2026-11-14-collection-system-redesign.ko.md)

| 설명 후보 | 이미 있는 반증·제약 | 다음에 구분할 질문 |
| --- | --- | --- |
| 명령이 전혀 실행되지 않는다 | E19/E34/E36에서 실제 이동·하강과 settle 운동 확인 | 원하는 grasp 방향이 실제로 얼마나 만들어지는가? |
| 같은 손을 기억하면 해결된다 | E31/E36은 같은 손을 유지해도 통과 미확인 | 손 identity와 유효 통로 정렬을 별개로 판정할 수 있는가? |
| 현재 형상·접근이 유효한 통로를 만든다 | 폭·주름·손 가림은 통로의 확정 증거가 아님 | 사람의 짧은 방향 교정으로 손–자유 경계 관계가 바뀌는가? |
| 더 많은 결정을 주면 해결된다 | E35 18act, E36 10act 뒤 자발적 마감 | 무엇을 바꾸면 같은 정체를 벗어나는지 관측으로 명시할 수 있는가? |


## 13. 연구에서 가져올 것은 작고 검증 가능한 원칙

네 논문의 고정 버전 초록·관련 본문을 확인했다. 코드·실험 재현은 수행하지 않았다.

근거: [ENCORE v1](https://arxiv.org/abs/2609.37359v1) · [HELP v2](https://arxiv.org/abs/2607.09776v2) · [PHIL v1](https://arxiv.org/abs/2611.05667v1) · [FEIJOA v1](https://arxiv.org/abs/2611.04080v1)

| 연구 | 논문에서 확인한 내용 | 우리에게 적용할 후보 | 바로 옮기지 않을 것 |
| --- | --- | --- | --- |
| ENCORE v1 | 시연 근거로 정책 프로그램 개발 후 동결 평가 | 개발자용 전후 근거 묶음 | 배포는 모델 호출 없음. 온라인 Astra와 동일 구조 아님 |
| HELP v2 | 사람 복구와 진행·복구 구간을 학습 후보로 선별 | 개입 구간·유용한 수정·정체를 분리 기록 | PhyRC 자동 구간분류·학습 효과는 미구현/미검증 |
| PHIL v1 | 같은 query 상태·길이의 거절 예측/실제 실행 쌍 | 관측·요청·실제 행동·개입 경계 연결 | 다른 replay 상태를 동일 상태의 선호쌍으로 만들지 않음 |
| FEIJOA v1 | 실행 전후 효과 검증과 uncertain 판정 | 명령·운동·천 관계·통과의 분리 검수 | 시각 judge는 착의 참값이 아니며 타 로봇 통계 전용 불가 |

이 원칙들은 설계 제안이다. 다른 과제의 성공률·비용 감소를 PhyRC 예상 개선율로 제시하지 않는다.


## 14. 직접 조작과 사용자 개입은 세 가지 다른 기능

현재 되는 구성요소, 연결 검증이 필요한 경로, 아직 없는 제어권 전환을 구분한다.

근거: [다음 작업 계획](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/COLLECTION_PLAN.md) · [현재 운영 경로](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/OPERATIONS.md) · [미적용 텍스트 개입 후보](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/research/candidates/20261113-actor-feedback/README.ko.md)

| 경로 | 현재 준비 수준 | 다음 검증 |
| --- | --- | --- |
| 사람 단독 키보드 | GUI 경로·키 입력 구성요소·과거 사람 기록 있음. 현재 브라우저 화면은 spectator | 사용자 접속 → 실제 키 입력/해제 → 공개 pose 변화 → 기록/QC |
| decision 경계 텍스트 | CPU 검사를 거친 후보 patch. 미적용이며 실제 모델 전달 미검증 | 최신 소스 회귀 검토 → 한 번 전달/응답 확인 → 실제 행동 비교 |
| Astra ↔ 사람 직접 handoff | 완성된 제어권 전환 경로 미구현 | 현재 행동/정착 완료, 한 제어원, 큐 처리, 인간 구간·재개 관측 기록 |

사람 조작이 됐다고 직접 handoff까지 완료된 것은 아니다. 새 기능·시연은 이번 마감 이후의 별도 작업이다.


## 15. 다음 작업: 전체 개편 대신 조건부 4–8시간

사용자 접속·GUI/브라우저 연결이 준비된 경우의 추정. 연결 장애나 착의 성공을 보장하는 일정은 아니다.

근거: [다음 작업 계획](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/COLLECTION_PLAN.md)

**1–1.5시간 · 근거 표** — E34–E36 전후 관측, 적용 action, 실제 운동, 손·천 관계, unknown을 한 표로 연결.  기존 export 재사용. 원본 수정 없음.

**2–4시간 · 키보드 시험** — 새 run에서 사람 단독 연결·키 해제·포커스·두 로봇 매핑·짧은 실제 움직임 확인.  중간 상태 재생 후 사람 입력 연결은 별도 확인.

**0.5–1시간 · 시험 카드** — 유지할 관계, 바꿀 한 요소, 관측 근거, 중지 조건, 총시간을 기록.  운영 규칙으로 무검토 재시도와 예산 이월을 막음.

검사·실제 입력 확인·마감·정리에 0.5–1.5시간 확보. 연결이 막히면 그날은 재현 가능한 장애 진단까지.


## 16. 사람의 교정이 어떤 가설을 구분해야 하는가

새 시연의 첫 목표는 완전 착의 성공이 아니라 입력·운동·관계 변화의 확인이다.

근거: [E36 공개 리뷰](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [다음 작업 계획](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/COLLECTION_PLAN.md) · [PHIL v1](https://arxiv.org/abs/2611.05667v1) · [허용 관측 규칙](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/competition/RULES.md)

| 질문 | 짧은 비교의 설계 | 남길 증거 |
| --- | --- | --- |
| 자유 구간과 같은 손을 식별할 수 있는가? | 같은 공개 시점에서 사람·모델의 경계/손 해석 비교 | 관측 ID·카메라·판정·대안 설명·unknown |
| 베이스 방향·housing 여유가 핵심인가? | 연결 확인 후 한 요소의 짧은 사람 교정과 결과 관찰 | 요청/실제 action, 전후 pose, 정착, 천·손 관계 |
| 기존 파지에서 유효한 진입이 가능한가? | 허용할 파지 조건과 중지 기준을 사전에 고정 | 진행/복구/실패 구간·제어원·source group |

본 비교는 지정5RGB-D를 사용한다. 자유 viewport 진단 영상은 별도 보관하고 actor·학습 입력·자동 라벨·교사 정보로 쓰지 않는다.


## 17. 이번 마감과 다음 개발의 경계

좋은 부분 동작을 보존하면서, 아직 확인하지 못한 통과를 성공 데이터로 바꾸지 않는다.

근거: [E35 백업 검증](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/project/sessions/20261114-e35-backup-verification.json) · [E36 백업 검증](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/project/sessions/20261114-e36-backup-verification.json) · [다음 작업 계획](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/COLLECTION_PLAN.md) · [전체 경험·설계 근거](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/research/2026-11-14-collection-system-redesign.ko.md)

**완료** — E35·E36 정상 종료 전수 QC·공개 리뷰 고정 백업 재다운로드 검증 원본·GIF·근거 연결 E37 이후 실행 없음

**다음 작은 작업** — 사람 단독 입력 경로 확인 전후 근거와 unknown 정리 같은 실패의 시험 조건 명시  개입은 단계별로 넓힘

**뒤로 미룰 것** — 직접 handoff 구현·검증 검수 전 자동 학습 새 VLA·critic·world model의 동시 도입  현재 학습 승인: unreviewed

채택 기준: 설명이 그럴듯한가보다, 어떤 관계가 바뀌었고 어떤 증거로 다시 확인할 수 있는가.


## 18. 원문과 재검토 경로

슬라이드 하단의 근거 링크와 아래 원문을 클릭해 확인할 수 있다.

근거: [전체 시연](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/EPISODES.md) · [카탈로그](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/collection/catalog/catalog.v1.json) · [연구 검증 범위](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/main/docs/reports/20261114-e36-integrated-review/research-sources.json)

[Encore: Few-Shot Agentic Discovery of Manipulation Strategies](https://arxiv.org/abs/2609.37359v1)

[HELP: Human-Efficient Large-Scale Robot Post-Training with Rollout Segmentation](https://arxiv.org/abs/2607.09776v2)

[Correct Robots Before They Make Mistakes: Proactive Human-in-the-Loop Intervention via Preference Learning](https://arxiv.org/abs/2611.05667v1)

[FEIJOA: Task-Driven Grounding and Execution for Mobile Manipulation](https://arxiv.org/abs/2611.04080v1)

과거 전 영상의 신규 전수 재시청·연구 재현은 하지 않았다. 분석용 개발자와 실행 actor의 접근 범위를 분리했다.
