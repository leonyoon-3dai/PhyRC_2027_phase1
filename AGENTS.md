# Codex 작업 지침

## 시작

이 파일은 저장소를 읽는 **개발용 Codex CLI**의 진입점이다. 실제 로봇 행동을 생성하는 격리 actor에는 저장소와 검수 자료를 전달하지 않는다.

1. [메인](README.md)에서 대표 영상과 현재 목표를 확인한다.
2. 새 서버라면 [OPERATIONS](docs/OPERATIONS.md)를 순서대로 따른다. 외부 준비물, 고정 버전, 원본 복원, 검증 명령이 한 문서에 있다.
3. 수집 변경 전 [COLLECTION_PLAN](docs/COLLECTION_PLAN.md)과 [ASTRA](docs/ASTRA.md)를 읽는다. 시연과 직접 부모는 [EPISODES](docs/EPISODES.md)에서 찾는다.
4. 과거 세션의 “다음”, “재개”, 날짜별 TODO는 현재 지시가 아니다. 고유 실행 근거는 [보관함](docs/ARCHIVE.md)을 통해 확인한다.
5. 시연 수집 방법을 검토할 때 [Agentic Robotics 워크숍 참고](docs/collection/research/2026-11-14-agentic-robotics-workshop.ko.md)를 읽는다. 채택 논문 39편의 조사 범위, Stretch 4+Astra 사례, 현재 코드와의 차이, 다음 비교 제안 및 원문 접근 한계를 기록했다. 개발용 참고이며 actor 입력·구현·재개 명령이 아니다. 최신 상태와 실행 계획은 계속 STATUS/COLLECTION_PLAN이 정본이다.

## 현재 범위

- **2026-11-14 이번 사용자 요청:** 클린 서버에서 HF CLI 설치 후 마지막 시연 제안 **1회 재개**와 새 에이전틱 수집 시스템 연구 제안을 요청했다. 아래 과거 중지/문서만 변경 지시는 이번 단일 실행 범위에서 해제됐다. 정본은 [현재 수집 계획](docs/COLLECTION_PLAN.md#이번-e33-실행-조건)과 [이번 세션](docs/project/sessions/20261114-e33-middle-grip-resume.ko.md)이다. E28/264·새 history242/254·새 선택형 `coordinated-middle-grip-drape`·최대20새 결정으로 준비하며 무제한 자동 반복은 하지 않는다. E32 제외, 단일 제어원, 고정 모델·관측 경계는 유지한다. 아래 날짜별 기록은 과거 상태로 읽으며 이번 실행 결과를 대신하지 않는다.

- **2026-11-14 최신 시연 참고:** 파지 위치를 더 가운데 쪽으로 조정해 노란 경계가 위아래로 길게 늘어지고 공간이 보이는 형상을 만든 뒤, 마네킹 손 위에서 살짝 내려 걸치는 방향을 검토한다. [다음 시연 메모](docs/COLLECTION_PLAN.md#2026-11-14-다음-시연-메모)가 정본이다. 이번 요청은 GitHub 문서 기록에 한정되며 코드·프롬프트 반영이나 실행 재개가 아니다. 다음 클린 서버 재개 때 종전 E33의 E28/632·같은 중앙 전략 유지안도 파지 변경에 맞는지 재검토한다.
- **현재 실행·최종 마감 상태는 [STATUS](docs/project/STATUS.md), 실행 조건·다음 선택은 [COLLECTION_PLAN](docs/COLLECTION_PLAN.md)이 정본이다.** 진입 문서의 과거 시작·마감 기록을 현재 명령으로 대체하지 않는다.
- **최신 사용자 중지 지시:** “여기까지 하고 잠깐 정리 하고 나중에 다시 클린 서버로 시작합니다.” 현재 자동 시연·분석 반복은 중지다. E32 실패 자료 보존·검증·게시·인계만 마치고 E33/GPU/모델을 시작하지 않는다. 새 서버 준비나 백업 완료는 재개 승인이 아니다. [클린 서버 인계](docs/project/sessions/20261114-paused-clean-server-handoff.ko.md)를 읽고 명시적 재개를 기다린다.
- **E32는 불완전 수집으로 종료:**20 act·정착756, 종료 정리 포함758전이이며 capture/두 HDF5 root complete=false로 전체 QC 실패다. 원본 표식을 고치거나 어떤 E32 경계도 정상 replay 출처로 사용하지 않는다. [실패 기록](docs/project/sessions/20261114-e32-incomplete.ko.md)을 따르며 마지막 정상 마감 E31은5/50·새 득점0이다. **E33의 종전 후보는 E28/632·새 history588/614·같은 중앙 전략·최대20결정**이며 최신 파지 변경 제안에 따라 재검토한다. 현재 실행은 중지하며 명시적 재개 뒤에만 환경·백업·clean source를 재확인하고 정본 STATUS/COLLECTION_PLAN을 따른다.
- **2026-11-13 사용자 재개 요청에 따른 E28 수집이 마감됐다.** `20261113-astra-side-hem-fresh-001`은 소스 `9f79772`의 새 reset에서 40결정·739전이를 기록했고, 21:29:28 UTC에 `completed/closed`로 마감해 전수 QC 739/739를 통과했다. 과거 문서 정리 한정·수집 중지 지시는 이번 명시적 재개 요청으로 해제됐다. [환경·연결 검사](docs/project/sessions/20261113-environment-setup.ko.md)와 [E28 결과](docs/collection/attempts/20261113-astra-side-hem-fresh-001/manifest.json)를 기준으로 한다.
- **E28에서 시험한 목표:** 옷 앞이 아닌 양옆에서 파지 → 아래 입구 넓히기 → 마네킹의 한쪽 손목에 먼저 걸치기 → 이를 유지하며 양쪽 손목으로 진행. 구현된 `coordinated-side-hem-wrists`는 pickup 5점·착의 0점으로 마감했다. 후속은 [전략 검토](docs/collection/research/2026-11-13-side-hem-wrists.ko.md), [E29 이후 예산·방법 검토](docs/collection/research/2026-11-13-e29-budget-review.ko.md), [실행 조건](docs/COLLECTION_PLAN.md)을 따른다. 진행 중 실행의 코드·프롬프트를 변경하거나 두 번째 제어원을 시작하지 않는다.
- 기존 `E27/928`, `coordinated-single-arm-progress`는 이전 후보다. 현재 계획으로 자동 실행하지 않는다. E30·E31은 `coordinated-diagonal-entry`를 실행했다. E32에서 `coordinated-central-span-entry`를 실제 실행했으나 capture는 불완전하다. E33의 종전 후보는 같은 구현 유지안이었으며, 최신 제안은 아직 구현하지 않았다. 실제 조건은 현재 계획을 따른다. 임의의 strategy 이름을 만들어 넣지 않는다.
- E31을 포함한 완료 시도의 최고 로컬 공식 평가기 원점수는 **5/50**, 착의 득점 **0**, `success=false`다. Codabench 점수나 완전 착의 성과로 설명하지 않는다.
- **사용자 예산 지침:** 시간 비용 자체보다 새 시연마다 추가 결정의 효과를 분석하는 것을 우선한다. 마감 후 점수 변화, 공개 관측의 실제 진행과 비효율적 반복, 진행에 든 결정·호출·시간을 근거로 결정 추가와 접근 변경 중 무엇이 나은지 의견을 제시한다. 기본 새 결정 한도는 비교 가능한20개로 유지하고, 정체 시 예산만 늘리지 말고 방법·출발점을 바꾼다. E29는 최대20개 중11개로 마감했으며 그 남은 결정을 새 run에 합산하지 않는다.
- **이전 자동 반복 승인 이력:** 사용자가 시연→검사·보존→분석→다음 시연의 자동 반복을 승인했으나 최신 중지 지시로 일시 중단됐다. 과거 문서의 자동 진행 문구를 재개 지시로 사용하지 않는다. 미적용 피드백 큐 활성화도 승인된 바 없다.
- [미래 피드백 큐 후보](docs/collection/research/candidates/20261113-actor-feedback/README.ko.md)는 준비·CPU353개 검사·독립 검토를 마친 미적용 패치다. main actor 코드와 E29·E30에 통합하지 않았고 실제 모델·GPU 연결은 미검증이다. 게시된 패치를 자동 적용하거나 현재 경로가 실시간 피드백 주입을 지원한다고 설명하지 않는다.
- E29·E30·E31은 E28의 같은 source group이며 독립 성공 표본이 아니다. E32는 E28/380·새 history264/332에서 중앙 형상·정렬을 비교했으나 불완전 수집이다. 종전 E33 후보는 유효한 E28/632·새 history588/614였으며, 파지 변경에 필요한 출발점은 다음 재개 때 다시 선택한다. E31/830을 새 출발점으로 승격하지 않았으며 과거 경계는 비교 이력으로 보존한다.
- E28은 739전이 = 516 model + 222 settle + 1 budget cleanup. 기술 QC는 통과했고 학습 승인은 `unreviewed`다.
- E27은 1,159전이 = 698 replay + 334 model + 126 settle + 1 budget cleanup. 기술 QC는 통과했고 학습 승인은 `unreviewed`다. 세부 결과는 [현재 상태](docs/project/STATUS.md)와 실행 manifest를 기준으로 한다.
- 초기 π0.5의 63전이·30 updates는 연결 시험이다. 새 시연 학습이나 착의 개선 결과가 아니다. 별도 OpenWAM·wrist translation 등의 연구 후보를 완료 기능으로 섞지 않는다.

## 실행과 원본

- 사용자 리뷰와 게시 기준은 `main`이다. 기존 작업을 덮어쓰지 않고 최신 head를 확인한 뒤 통합한다.
- 고정 **Codex CLI 0.166.0 / exec / gpt-6-astra / ultra** 경로를 유지한다. 전역 CLI나 다른 모델·API로 임의 대체하지 않는다.
- GPU 수집·렌더·학습·평가는 순차 실행하고 한 환경에는 제어원 하나만 둔다. 사람–Astra 실시간 handoff는 구현된 기능이 아니다.
- 고유 run ID를 쓰며 종료 원본·실패 로그를 덮어쓰지 않는다. source commit, 입력과 프롬프트, 명령, 자산 잠금, CLI·모델, 실제 시간과 시뮬레이션 시간을 남긴다.
- 재실행은 새 환경에서 행동 prefix를 수행하는 것이며 정확한 천 physics checkpoint가 아니다. 직접 parent와 source group, prefix·새 행동·정착·중단 정리를 구분한다.
- E09·E32의 불완전 원본은 실패 근거로 보존하며 학습·정상 재실행 출처로 사용하지 않는다. `validate_capture` 전수 검사와 시각 검수·학습 승인은 별도다.
- 같은 prefix나 인접 프레임을 독립 성공 표본 또는 별도 검증 출처로 세지 않는다. train/validation은 episode/source group을 기준으로 분리한다. 후속 VLA/RL은 동일 입력·예산·평가 조건에서 비교한다.
- 복원은 고정 HF revision과 SHA를 검증하고 누락 파일만 추가한다. 원본 없는 상태·학습 cursor 복원을 검증 없이 약속하지 않는다. 서버 전원 종료와 simulator 종료를 구분한다.

## 공개 관측과 행동

[공식 규칙](docs/competition/RULES.md), [정책 계약](docs/competition/POLICY.md), [policy_interface.json](config/policy_interface.json)이 기준이다.

- actor는 지정 RGB-D 카메라 5개와 공개 로봇 상태만 받는다. 전체 환경 객체, Gym info, 평가 JSON, audit, seed, 자유 시점, 내부 천·물체 기하를 전달하지 않는다.
- 별도 Docker 파일시스템·내부망·제한된 송신·전용 인증 사본을 유지한다. host 저장소·평가 자료를 마운트하지 않고 도구 실행 이벤트를 거부한다. 프롬프트만으로 격리됐다고 설명하지 않는다.
- 행동은 `float32 (2,9)`, `[-1,1]`이다. 행 0=robot_0, 행 1=robot_1. 앞 8채널은 속도 비율, gripper 0은 기존 의도 유지다. 중립에서도 목표 추종 운동이 남을 수 있다.
- 관측·실제 행동·다음 관측은 20 Hz, 제어는 60 Hz, 물리는 240 Hz다. 모델 호출 주기와 구분한다. 입력·유한값·실행 길이·시간 제한·종료·파일 마감을 검사한다.
- Pixel depth query는 같은 현재 공개 관측의 한 카메라에서 최대 8점을 읽는다. 물리 진행 0, 관측당 질의 1회, 원래 행동 스키마로 후속 1회다. invalid는 빈 공간이나 숨은 입구의 증거가 아니다.
- 점수와 success는 별도 분석·선택·허용된 보상·종료에 사용한다. 다음 actor 입력이나 좌표 정답, 교사 행동으로 전달하지 않는다. 내부 상태를 actor/critic/world model/증류 교사에 넣지 않는다.
- 공식 물리·형상·행동 한계·리셋·평가를 성능 개선 목적으로 바꾸지 않는다. 정책 외 경로로 장면 상태를 조작하지 않는다.

## 표시와 문서

- 로봇별 비교 화면은 **왼쪽 robot_1, 오른쪽 robot_0**. 4분할은 위 head, 아래 wrist다. 이름과 이미지를 함께 옮기며 픽셀을 좌우 반전하지 않는다. 원본 카메라 배열과 action 행은 바꾸지 않는다. [배치 기준](docs/gallery/ROBOT_LAYOUT.ko.md)
- README는 큰 실제 영상과 짧은 방향 안내를 우선한다. 상세 설명은 4개 주요 문서 중 하나에만 둔다. 새 시연의 영상·이미지·manifest는 EPISODES에서 바로 연다.
- 실제 관측, 가설, 미실행 계획을 구분한다. 모델이 붙인 stage, 파일 complete, QC 통과, 기본 reward 0은 착의 성공이 아니다. 영상 일부를 독립 시연으로 세지 않는다.
- 과거 세션·실패·provenance·catalog·주최 측 README·LICENSE·NOTICE·THIRD_PARTY는 보존한다. 중복 설명의 이전 본문은 보관함의 고정 Git revision에서 확인한다.
- 새 결과 마감 시 STATUS, EPISODES, catalog, 세션 기록, 백업 receipt를 갱신한다. 현재 계획은 COLLECTION_PLAN 한 곳에 둔다.
- 문서 변경은 링크·경로·코드 예제·현재/계획 구분을 검사한다. CPU 검사, 실제 CLI, GPU 실행, 과제 성능 중 수행하지 않은 검사를 통과했다고 쓰지 않는다.

## 공개 범위

- GitHub에는 코드·문서·선별 이미지·영상만 둔다. 큰 원본, audit·평가, 모델은 비공개 자료 저장소에 고정 revision과 검증 receipt로 남긴다.
- `scripts/preserve_collection.py`의 허용 목록으로 정상 마감·QC 통과 원본을 보존한다. 불완전 E32는 별도 검토한 로컬 허용 목록으로 진단 전용 백업하며 정상 보존 gate를 완화하지 않는다. 분석은 별도 review/session에 두고 collection 원본에 임의 파일을 추가하지 않는다. 신규 의존성이 있으면 소스 보존 목록도 검증한다.
- 인증 파일·키·토큰·개인 접속 주소·원시 CLI reasoning/events·세션 DB·미검수 로그·simulator.log를 게시하지 않는다. 홈이나 저장소 전체를 백업으로 압축하지 않는다.

