# Codex 작업 지침

**현재 사용자 지시(2026-11-16): 최신 전략으로 시연을 시작하고, 판단 지점에서5카메라를 저장소에 게시해 사용자 텍스트를 기다린다.** 개발 대화의 Astra 전환과 HF 로그인 확인 후 클린 서버 복원·필수 기능 구현/검증에 착수했다. E36/933을 우선 검증하고 M1 현재 파지 유지·국소 교정으로 첫 소매 새5점을 시도한다. [현재 계획](docs/COLLECTION_PLAN.md)과 [실행 인계서](docs/collection/research/2026-11-16-user-guided-resume.ko.md)가 정본이다. 실제 실행·검증 상태는 [STATUS](docs/project/STATUS.md)에서 확인한다.

**문서 관리:** [기전·판단 기준](docs/MECHANISMS.ko.md)과 [과거 결과 요약](docs/HISTORY_SUMMARY.ko.md)을 중심으로 현재 전략과 최근 분석을 관리한다. 시간별 초기 시행착오를 활성 문서에 반복하지 않는다. 세션·원본·실패·provenance·GIF·PDF는 보존하고, 현재 판단을 바꾼 근거에서 상세 이력으로 연결한다. 과거 분석-only HOLD·최대5회 배치·날짜별 TODO는 현재 지시가 아니다.

## 시작

이 파일은 저장소를 읽는 **개발용 Codex CLI**의 진입점이다. 실제 로봇 행동을 생성하는 격리 actor에는 저장소와 검수 자료를 전달하지 않는다.

1. [메인](README.md)에서 대표 영상과 현재 목표를 확인한다.
2. 새 서버라면 [실행 인계서](docs/collection/research/2026-11-16-user-guided-resume.ko.md)와 [OPERATIONS](docs/OPERATIONS.md)를 읽고 고정 원본·자산·모델 환경을 복원한다. 필요한 HOLD·checkpoint·게시·피드백 연결을 검증하기 전 기존 즉시 종료 수집기로 본 시연을 시작하지 않는다.
3. 수집 변경 전 [COLLECTION_PLAN](docs/COLLECTION_PLAN.md)과 [ASTRA](docs/ASTRA.md)를 읽는다. 시연과 직접 부모는 [EPISODES](docs/EPISODES.md)에서 찾는다.
4. 과거 세션의 “다음”, “재개”, 날짜별 TODO는 현재 지시가 아니다. 고유 실행 근거는 [보관함](docs/ARCHIVE.md)을 통해 확인한다.
5. 시연 수집 방법을 검토할 때 [Agentic Robotics 워크숍 참고](docs/collection/research/2026-11-14-agentic-robotics-workshop.ko.md)를 읽는다. 채택 논문 39편의 조사 범위, Stretch 4+Astra 사례, 현재 코드와의 차이, 다음 비교 제안 및 원문 접근 한계를 기록했다. 개발용 참고이며 actor 입력·구현·재개 명령이 아니다. 최신 상태와 실행 계획은 계속 STATUS/COLLECTION_PLAN이 정본이다.
6. [현재 계획](docs/COLLECTION_PLAN.md)의 M1/M2/M3와 사용자 HOLD 절차를 따른다. [checkpoint·실행 효과 분석](docs/collection/research/2026-11-16-checkpoint-effect-feedback.ko.md), [최신 착의 연구](docs/collection/research/2026-11-16-recent-dressing-resources.ko.md), 이전 다중 방법·HolidayFactory 문서는 선행 근거다. 조사 자체를 다시 확대하지 않는다.

## 현재 범위

- **최신 정상 과제 시연은 E36 마감이며 클린 서버 착수 작업을 진행한다.** 필요한 최소 구현·검증 뒤 새 고유 run으로 M1을 시도한다. 닫힌 E36 원본을 덮어쓰지 않으며 구현 준비·CPU 검사·실제 연결·과제 실행을 구분한다.
- **실제 실행·점수·백업은 [STATUS](docs/project/STATUS.md), 현재 방향은 [COLLECTION_PLAN](docs/COLLECTION_PLAN.md), 복원·구현 계약은 [실행 인계서](docs/collection/research/2026-11-16-user-guided-resume.ko.md)가 정본이다.** 이전 문서의 HOLD·재개·날짜별 TODO보다 최신 사용자 결정을 우선한다. 연구 문서 전체를 actor에 전달하지 않는다.
- 사람 조작용 state slot과 `initial_slot` 근사 복원 경로는 이미 존재한다. 완전한 FEM 물리 checkpoint나 E36 중간 복원 검증이 완료됐다고 설명하지 않는다. 현재 collector의 행동 재생과 구분하고, 복원 시 초기화되는 상태·정착·평가 재시작을 검토한다. 기존 관측→행동→관측 루프가 전혀 없었다거나 E36까지 모든 명령이 오작동했다고 일반화하지 않는다.
- E36의 추가 재파지0·20결정·review10은 해당 시도의 조건이다. 향후 모든 방법의 고정 규칙으로 일반화하지 않는다. 각 실험에서 제어원, 입력, 재파지·복구 조건, 예산과 종료/검토 방식을 명시하고 공식 물리·관측·행동·평가 계약은 유지한다.
- E33–E36의 핵심 결과와 계보는 [과거 결과 요약](docs/HISTORY_SUMMARY.ko.md), 원본·검사·백업은 [보관함](docs/ARCHIVE.md)에 보존한다. E36은10act+finish·933전이·QC933/933·raw5/50·새 착의점0이다. E09·E32는 불완전 원본으로 정상 replay·학습 출처에서 제외한다. E32의 진단 백업 검증을 수집 완료로 바꾸어 설명하지 않는다.
- 정상 평가한 시연의 최고 로컬 원점수는5/50, 착의 득점0이며 완전 착의 성공은 확인하지 못했다. E28과 후속 분기·재사용 prefix를 독립 성공 표본으로 세지 않는다. 기술 QC와 학습 승인은 별도이며 최신 시연의 학습 승인은 `unreviewed`다.
- 모델 stop/finish, 정체, 관리 예산, 목표 득점은 종료 dispatch 전에 사용자 HOLD로 바꾼다. 물리0 대기와 기록기·프로세스 유지,5카메라 README 게시·원격 확인, 텍스트 재개를 검증한다. 사용자 무응답은 재개 승인이 아니며 구간 예산을 자동 증액하지 않는다. 실제 하드 horizon·장애는 정상 HOLD와 구분한다.
- [미래 피드백 큐 후보](docs/collection/research/candidates/20261113-actor-feedback/README.ko.md)는 준비·CPU검사·독립 검토를 마친 미적용 패치다. 실제 모델·GPU 연결이나 실시간 사람–Astra handoff가 완료된 기능으로 설명하지 않는다. 초기 π0.5의63전이·30updates 역시 연결 시험이며 새 시연 학습·착의 개선 성과가 아니다.
- 날짜별 세션의 재개·자동 반복·‘다음 시연’ 문구는 당시 이력이다. 과거 배치 남은 횟수는 이어받지 않는다. 최신 사용자 피드백 시연 계획에 따른 새 run만 수행한다.

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
- README 최상단의 `PHYRC_USER_REVIEW:START/END`에는 현재 서버/시연 상태와 최신 사용자 검토를 둔다. HOLD마다 같은 관측의 overview+양쪽 head/wrist5장·원본 링크·관측 ID·사유·질문을 push한다. 과거 이미지를 live로 표시하지 않는다. 기존 통합 PDF 버튼·공식 데모·E36 GIF는 보존하며 새 마감에도 gallery·provenance를 연결한다.
- 실제 관측, 가설, 미실행 계획을 구분한다. 모델이 붙인 stage, 파일 complete, QC 통과, 기본 reward 0은 착의 성공이 아니다. 영상 일부를 독립 시연으로 세지 않는다.
- 과거 세션·실패·provenance·catalog·주최 측 README·LICENSE·NOTICE·THIRD_PARTY는 보존한다. 중복 설명의 이전 본문은 보관함의 고정 Git revision에서 확인한다.
- 새 결과 마감 시 STATUS, EPISODES, catalog, 재현용 run 기록, 백업 receipt를 갱신한다. 현재 계획은 COLLECTION_PLAN 한 곳에 두고, 기전·가설·판별 근거는 MECHANISMS에, 과거 핵심 교훈은 HISTORY_SUMMARY에 요약한다. 실행 시각·hash는 상세 provenance에 보존하되 활성 문서에 시간순 로그를 복제하지 않는다.
- 문서 변경은 링크·경로·코드 예제·현재/계획 구분을 검사한다. CPU 검사, 실제 CLI, GPU 실행, 과제 성능 중 수행하지 않은 검사를 통과했다고 쓰지 않는다.

## 공개 범위

- GitHub에는 코드·문서·선별 이미지·영상만 둔다. 큰 원본, audit·평가, 모델은 비공개 자료 저장소에 고정 revision과 검증 receipt로 남긴다.
- `scripts/preserve_collection.py`의 허용 목록으로 정상 마감·QC 통과 원본을 보존한다. 불완전 E32는 별도 검토한 로컬 허용 목록으로 진단 전용 백업하며 정상 보존 gate를 완화하지 않는다. 분석은 별도 review/session에 두고 collection 원본에 임의 파일을 추가하지 않는다. 신규 의존성이 있으면 소스 보존 목록도 검증한다.
- 인증 파일·키·토큰·개인 접속 주소·원시 CLI reasoning/events·세션 DB·미검수 로그·simulator.log를 게시하지 않는다. 홈이나 저장소 전체를 백업으로 압축하지 않는다.
