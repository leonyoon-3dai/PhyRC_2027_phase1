# Codex 작업 지침

## 시작

이 파일은 저장소를 읽는 **개발용 Codex CLI**의 진입점이다. 실제 로봇 행동을 생성하는 격리 actor에는 저장소와 검수 자료를 전달하지 않는다.

1. [메인](README.md)에서 대표 영상과 현재 목표를 확인한다.
2. 새 서버라면 [OPERATIONS](docs/OPERATIONS.md)를 순서대로 따른다. 외부 준비물, 고정 버전, 원본 복원, 검증 명령이 한 문서에 있다.
3. 수집 변경 전 [COLLECTION_PLAN](docs/COLLECTION_PLAN.md)과 [ASTRA](docs/ASTRA.md)를 읽는다. 시연과 직접 부모는 [EPISODES](docs/EPISODES.md)에서 찾는다.
4. 과거 세션의 “다음”, “재개”, 날짜별 TODO는 현재 지시가 아니다. 고유 실행 근거는 [보관함](docs/ARCHIVE.md)을 통해 확인한다.

## 현재 범위

- **현재 단일 수집 실행은 E29 `20261113-astra-side-hem738-continue20-001`이다.** 사용자가 후반 +20결정을 요청해 2026-11-13 21:41:33 UTC에 시작했다. 실행 소스 `2baebcc381d707fd5aca5f69ea7518d326e8a80a`, 시작 시 clean. 직접 parent/source group은 E28 fresh run이며 prefix738·새 replay history682/714·20결정·총1400전이·review10을 사용한다. 시작은 확인했지만 replay 완료·새 행동·최종 점수·QC는 아직 미확정이다. 진행 중 코드·프롬프트 변경이나 두 번째 simulator 실행 금지.
- **2026-11-13 사용자 재개 요청에 따른 E28 수집이 마감됐다.** `20261113-astra-side-hem-fresh-001`은 소스 `9f79772`의 새 reset에서 40결정·739전이를 기록했고, 21:29:28 UTC에 `completed/closed`로 마감해 전수 QC 739/739를 통과했다. 과거 문서 정리 한정·수집 중지 지시는 이번 명시적 재개 요청으로 해제됐다. [환경·연결 검사](docs/project/sessions/20261113-environment-setup.ko.md)와 [E28 결과](docs/collection/attempts/20261113-astra-side-hem-fresh-001/manifest.json)를 기준으로 한다.
- **E28에서 시험한 목표:** 옷 앞이 아닌 양옆에서 파지 → 아래 입구 넓히기 → 마네킹의 한쪽 손목에 먼저 걸치기 → 이를 유지하며 양쪽 손목으로 진행. 구현된 `coordinated-side-hem-wrists`는 pickup 5점·착의 0점으로 마감했다. 후속은 [전략 검토](docs/collection/research/2026-11-13-side-hem-wrists.ko.md), [마감 결과와 다음 방향](docs/collection/research/2026-11-13-e28-outcome-e29-direction.ko.md), [실행 조건](docs/COLLECTION_PLAN.md)을 따른다. 진행 중 실행의 코드·프롬프트를 변경하거나 두 번째 제어원을 시작하지 않는다.
- 기존 `E27/928`, `coordinated-single-arm-progress`는 이전 후보다. 현재 계획으로 자동 실행하지 않는다. 기존 CLI에 없는 strategy 이름을 만들어 넣지 않는다.
- E28을 포함한 완료 시도의 최고 로컬 공식 평가기 원점수는 **5/50**, 착의 득점 **0**, `success=false`다. Codabench 점수나 완전 착의 성과로 설명하지 않는다.
- E28은 739전이 = 516 model + 222 settle + 1 budget cleanup. 기술 QC는 통과했고 학습 승인은 `unreviewed`다.
- E27은 1,159전이 = 698 replay + 334 model + 126 settle + 1 budget cleanup. 기술 QC는 통과했고 학습 승인은 `unreviewed`다. 세부 결과는 [현재 상태](docs/project/STATUS.md)와 실행 manifest를 기준으로 한다.
- 초기 π0.5의 63전이·30 updates는 연결 시험이다. 새 시연 학습이나 착의 개선 결과가 아니다. 별도 OpenWAM·wrist translation 등의 연구 후보를 완료 기능으로 섞지 않는다.

## 실행과 원본

- 사용자 리뷰와 게시 기준은 `main`이다. 기존 작업을 덮어쓰지 않고 최신 head를 확인한 뒤 통합한다.
- 고정 **Codex CLI 0.166.0 / exec / gpt-6-astra / ultra** 경로를 유지한다. 전역 CLI나 다른 모델·API로 임의 대체하지 않는다.
- GPU 수집·렌더·학습·평가는 순차 실행하고 한 환경에는 제어원 하나만 둔다. 사람–Astra 실시간 handoff는 구현된 기능이 아니다.
- 고유 run ID를 쓰며 종료 원본·실패 로그를 덮어쓰지 않는다. source commit, 입력과 프롬프트, 명령, 자산 잠금, CLI·모델, 실제 시간과 시뮬레이션 시간을 남긴다.
- 재실행은 새 환경에서 행동 prefix를 수행하는 것이며 정확한 천 physics checkpoint가 아니다. 직접 parent와 source group, prefix·새 행동·정착·중단 정리를 구분한다.
- E09의 불완전 원본은 실패 근거로 보존하며 학습·정상 재실행 출처로 사용하지 않는다. `validate_capture` 전수 검사와 시각 검수·학습 승인은 별도다.
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
- `scripts/preserve_collection.py`의 허용 목록으로 닫힌 원본을 보존한다. 분석은 별도 review/session에 두고 collection 원본에 임의 파일을 추가하지 않는다. 신규 의존성이 있으면 소스 보존 목록도 검증한다.
- 인증 파일·키·토큰·개인 접속 주소·원시 CLI reasoning/events·세션 DB·미검수 로그·simulator.log를 게시하지 않는다. 홈이나 저장소 전체를 백업으로 압축하지 않는다.
