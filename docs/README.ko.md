# 문서 지도

[메인 README](../README.md) · [5점→10점 가이드 PDF](guide/PhyRC_2027_Repository_Guide_KR.pdf)

## 먼저 읽을 문서

| 질문 | 기준 문서 | 더 자세한 근거 |
|---|---|---|
| 어떤 챌린지이고 어떻게 점수를 얻는가 | [챌린지·점수·시간](project/CHALLENGE_GUIDE.ko.md) | [공식 평가](competition/EVALUATION.md), [규칙](competition/RULES.md) |
| 데이터를 어떻게 수집·검수하는가 | [수집 안내](collection/README.ko.md) | [공개 시연 갤러리](gallery/README.ko.md), [시도별 기록](collection/attempts/) |
| 지금 어디서 멈췄는가 | [현재 상태](project/STATUS.md) | [11월 6일 종료 인계](project/SESSION_WRAPUP_20261106.ko.md) |
| 클린 서버에서 무엇부터 실행하는가 | [새 서버 준비](project/START_HERE.ko.md) | [재실행과 분기](collection/guides/continuation-and-branches.ko.md) |
| 왜 5점에 머물렀고 10점으로 어떻게 가는가 | [진단 가이드](project/FIVE_TO_TEN.ko.md) | [E15 원인 검토](collection/reviews/20261106-astra-opening264-001.ko.md) |
| 어떤 연구를 어떤 순서로 적용하는가 | [연구 로드맵](project/RESEARCH_ROADMAP.ko.md) | [방법별 비교](collection/experiments/2026-11-06-method-comparison.ko.md) |
| 코드는 어디에 있는가 | [코드 길잡이](project/CODE_MAP.ko.md) | [수집 코드](../participant/collection/), [학습 코드](../participant/pi05/) |
| 지금까지 어떻게 진행했는가 | [개발 이력](project/HISTORY.ko.md) | [수집 일지](collection/sessions/), [초기 세션](project/sessions/) |

## 문서의 역할

- `README.md`: 목표, 점수, 데이터 흐름, 현재 상태, 다음 작업의 짧은 입구.
- `project/STATUS.md`: 중지 위치와 재개 조건. 실행 명령은 `START_HERE.ko.md`에 연결.
- `collection/attempts/`: 시도별 공개 패키지. `reviews/`는 종료 평가와 품질 상태.
- `collection/experiments/`: 방법별 실험의 조건·결과·한계. 여러 조건이 달라진 탐색은 통제 비교와 구분.
- `collection/research/`: 연구 검토. 현재 actor 적용·성능 개선으로 해석하지 않음.
- `collection/sessions/`, `project/sessions/`: 날짜별 실제 작업 원문.
- `gallery/`: 영상·이미지 중심 탐색. 원본 HDF5 백업을 대신하지 않음.
- `competition/`: 공식 문서. 제출 전 해당 버전의 규칙을 다시 확인.

## 갱신할 때

1. 새 실행에는 고유 run ID를 부여하고 원본을 덮어쓰지 않습니다.
2. 원점수, 착의 success, 파일 완료, 기술 검사, 학습 승인을 따로 기록합니다.
3. 새 결과는 시도별 문서와 검토 결과에 남기고, 현재 상태는 `STATUS.md`에 반영합니다.
4. README에는 변화한 목표·핵심 지표·다음 한 가지 작업만 반영합니다.
5. 과거 기록을 새 상태에 맞춰 소급 수정하지 않습니다. 잘못된 수치는 정정 이유와 원본을 함께 보존합니다.

## 보존한 기존 문서

[개편 전 메인 README](../README.before-reorganization-20261106.ko.md), [개편 전 상태 문서](project/STATUS.before-reorganization-20261106.ko.md), [개편 전 수집 목차](collection/README.before-reorganization-20261106.ko.md)는 2026-11-06 재구성 직전 스냅샷입니다. 이전 명령이나 우선순위보다 현재 상태와 재개 안내를 따릅니다.
