# 문서 지도

[메인 화면](../README.md) · [시간순 시각 갤러리](gallery/README.ko.md) · [12장 기술 발표](project/PRESENTATION.ko.md)

처음에는 그림으로 흐름을 보고, 그다음 수집 구현과 원본 근거로 내려갑니다. **현재 실제 실행은 E27까지, 최고 로컬 공식 평가기5/50·착의0이며 E28은 미실행입니다.**

## 1. 처음 읽는 순서

| 순서 | 문서 | 여기서 이해할 것 |
|---|---|---|
| 1 | [메인 README](../README.md) | 어떤 챌린지이고 무엇을 만들었는가 |
| 2 | [시간순 갤러리](gallery/README.ko.md) | 직접 조작→Astra→첫5점→재파지·운반의 실제 변화 |
| 3 | [챌린지·점수·시간](project/CHALLENGE_GUIDE.ko.md) | 픽업5, 착의 항목, 점수율과 성공의 차이 |
| 4 | [수집·검수 안내](collection/README.ko.md) | 자료의 종류, 파일 위치, QC와 학습 승인 |
| 5 | [Astra end-to-end](collection/guides/astra-end-to-end.ko.md) | 관측→CLI→명령검사→실행→전이저장→검수·백업 |
| 6 | [코드 지도](project/CODE_MAP.ko.md) | 실제 파일·함수·인터페이스의 연결 |
| 7 | [기술 발표 가이드](project/PRESENTATION.ko.md) | 5분·15분 동선과12장 설명, 기술 질문 |

## 2. 질문별 바로 가기

| 질문 | 기준 자료 | 상세 근거 |
|---|---|---|
| 사람이 조작한 것과 GPT가 한 것을 어떻게 구분하나 | [수집 경로 비교](collection/README.ko.md) | [사람 시연](gallery/20261026-human-pickup-transport.ko.md), [자동 수집 전체 과정](collection/guides/astra-end-to-end.ko.md) |
| 날짜순으로 어떤 일이 있었나 | [전체 이력](project/HISTORY.ko.md) | [초기 세션](project/sessions/), [수집 일지](collection/sessions/) |
| 어느 방법에서 무엇이 달라졌나 | [시각 갤러리](gallery/README.ko.md) | [개별 리뷰](collection/reviews/), [방법 비교](collection/experiments/) |
| 파지·입구·가림 때문에 어디서 막혔나 | [E27 최신 검토](collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md) | [E25 재파지](collection/reviews/20261107-astra-opposing563-named-001.ko.md), [E26 접근·시점](collection/reviews/20261107-astra-hand-swap787-named-001.ko.md) |
| 기록·출발점·방법을 어떻게 찾나 | [catalog 설명](collection/catalog/README.ko.md) | [정본 JSON](collection/catalog/catalog.v1.json), [출발점 화면](gallery/20261107-support-startpoints.ko.md) |
| 지금 어디서 멈췄나 | [현재 상태](project/STATUS.md) | [11월7일 마감](project/SESSION_WRAPUP_20261107.ko.md) |
| 클린 서버에서 어떻게 이어가나 | [복원 안내](project/START_HERE.ko.md) | [재실행·분기](collection/guides/continuation-and-branches.ko.md) |
| 다음에 무엇을 검증할까 | [최신 마감의 전략 질문](project/SESSION_WRAPUP_20261107.ko.md) | [E28 후보·미실행](collection/research/2026-11-07-e27-single-arm-continuation.ko.md), [장기 구간 조합](collection/research/2026-11-07-composable-scoring-data-plan.ko.md) |
| 학습·알고리즘 적용 범위는 어디까지인가 | [수집 자료의 학습 전환](collection/README.ko.md) | [π0.5 어댑터](../participant/pi05/), [연구 로드맵](project/RESEARCH_ROADMAP.ko.md) |

## 3. 주제와 날짜를 나누는 폴더 역할

| 경로 | 분류 기준 | 보존하는 내용 |
|---|---|---|
| `gallery/` | 시간순·주제별 시각 탐색 | 실제 장면, MP4, 변화 설명, 영상 provenance |
| `collection/attempts/<run-id>/` | 개별 실행 | 공개 manifest·최종 결정·선별 관측·영상 |
| `collection/reviews/` | 실제 실행에 대한 검토 | 점수·실제 행동·가설·오류·복구·승인 상태 |
| `collection/catalog/` | 실행·출발점·방법의 관계 | 실제·계획·계보·검사·학습 승인 색인 |
| `collection/guides/` | 반복해서 읽는 기술 설명 | 자동 수집 전체 과정, 재실행과 분기 |
| `collection/experiments/` | 비교 질문 | 조건·변경점·결과·비교 한계 |
| `collection/research/` | 연구·후속 후보 | 외부 방법, 적용 검토, 미실행 제안 |
| `project/sessions/`, `collection/sessions/` | 날짜별 원문 | 실제 명령·시간·작업·검증 영수증·인계 |
| `project/performance/` | 성능 계측 | 모델 호출·환경·재실행 비용, 자원 표본과 한계 |
| `competition/` | 주최 측 문서 | 규칙·설치·데이터·평가·정책 계약 |

실행 원본·파일 경로·기존 갤러리 주소는 유지합니다. 같은 내용을 여러 첫 화면에 복제하지 않고 **README는 요약, 갤러리는 그림, HISTORY는 이력, STATUS는 현재, 기술 문서는 구현**을 담당합니다.

## 4. 현재 자료와 당시 자료

| 자료 | 해석 기준 |
|---|---|
| STATUS·11월7일 마감·최신 catalog | E27 완료·수집 중지·E28 미실행이라는 현재 상태 |
| 개별 review·gallery·session | 해당 실행 당시의 조건과 결과. “다음”은 당시 계획일 수 있음 |
| [11월6일 마감](project/SESSION_WRAPUP_20261106.ko.md), [당시5→10 가이드](project/FIVE_TO_TEN.ko.md) | E15 시점의 진단. 이후 E16–E27은 HISTORY·최신 리뷰로 확인 |
| [기존 시각 가이드 PDF](guide/PhyRC_2027_Repository_Guide_KR.pdf) | 과거 버전 설명. 최신 실행의 근거로 대체하지 않음 |
| [초기 연구 로드맵](project/RESEARCH_ROADMAP.ko.md) | 알고리즘 후보·학습 계획. 실제 적용·성과는 실행별 근거로 확인 |

[개편 전 README](../README.before-reorganization-20261106.ko.md), [개편 전 STATUS](project/STATUS.before-reorganization-20261106.ko.md), [개편 전 수집 목차](collection/README.before-reorganization-20261106.ko.md)는 당시 스냅샷입니다. 원문을 최신 상태처럼 소급 수정하지 않습니다.

성능 세부 근거는 [E13–E15 계측](project/performance/20261106-performance-review.ko.md), [단계 계측과 속도 후보](project/performance/20261106-speedup-plan.ko.md), [E23 시간 분석](project/performance/20261107-e23-stage-timing.ko.md), [E24 재실행·질의 비용](project/performance/20261107-e24-stage-timing.ko.md)에 남겨둡니다.

## 5. 새 기록을 추가할 때

1. 고유 run ID로 실행하고 기존 원본·실패 로그를 덮어쓰지 않습니다.
2. 직접 부모·source group·재실행 prefix·새 행동·정착·정리를 분리합니다.
3. 파일 완료·QC·원점수·점수율·success·시각 검토·학습 승인을 각각 기록합니다.
4. 개별 실행과 리뷰를 먼저 쓰고 catalog·HISTORY·갤러리에 한 줄의 변화와 대표 장면을 연결합니다.
5. README에는 대표 변화와 최신 결과만, STATUS에는 현재 중단·재개 조건만 반영합니다.
6. 연구 후보·CPU검사·실제 CLI/GPU 적용·과제 성능을 구분합니다. 링크·이미지·날짜를 확인한 문서 변경을 runtime 검사 통과로 세지 않습니다.
