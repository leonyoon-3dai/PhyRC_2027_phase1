# Codex 작업 지침

**최신 사용자 방향(2026-11-16): 기존 계획은 HOLD한다.** 지금은 연구 방향을 분석하고 계속 기록하는 단계다. **checkpoint 복원**과 **명령 실행 후 실제 변화를 확인해 다음 행동을 바꾸는 피드백**을 우선 검토한다. 분석 정리가 끝난 뒤 사용자가 클린 서버에서 반영할 예정이며, 이번 요청은 저장소 문서 갱신이다. 과거 수집·구현·학습 계획을 자동 실행하지 않는다. [현재 계획](docs/COLLECTION_PLAN.md)과 [누적 분석 기록](docs/collection/research/2026-11-16-checkpoint-effect-feedback.ko.md)을 먼저 읽는다. 사람·Astra·개입·후속 학습 등 다른 선택지는 참고로 보존하며 한 방법을 영구 고정하지 않는다.

**2026-11-14 마감 이력:** E36까지 수집하고 당시 배치를 종료했다. E37–E39는 실행하지 않았다. 원본·QC·백업·공개 GIF·통합 PDF는 보존한다. 당시 사람 조작 우선안은 후보 중 하나이며 2026-11-15의 열린 비교 방향을 대신하지 않는다.


**과거 배치 승인(2026-11-14 09:29 UTC, 현재는 E36 종료):** 정리된 E33/E34 결과와 재정비 계획을 먼저 GitHub에 게시한 뒤, 기존 수집 경로로 옷 아래를 넓게 펼쳐 같은 손목보다 약간 위에서 측면으로 넣는 시연을 **최대5회** 진행한다. 예상 작업 범위는3–4시간이며 매회 마감·QC·공개 검토·고정 백업 뒤 다음 출발점을 선택한다. 사용자의 중간 피드백·중지 지시를 우선한다. 종전 E34 이후 중지는 이 범위에서 해제됐으며 새 시스템 개편·학습은 수행하지 않는다.

## 시작

이 파일은 저장소를 읽는 **개발용 Codex CLI**의 진입점이다. 실제 로봇 행동을 생성하는 격리 actor에는 저장소와 검수 자료를 전달하지 않는다.

1. [메인](README.md)에서 대표 영상과 현재 목표를 확인한다.
2. 새 서버라면 [OPERATIONS](docs/OPERATIONS.md)의 최신 HOLD 안내와 작업 범위를 먼저 읽는다. 설치·복원·검증 명령은 나중에 요청된 적용 범위에서 사용하는 재현 절차다.
3. 수집 변경 전 [COLLECTION_PLAN](docs/COLLECTION_PLAN.md)과 [ASTRA](docs/ASTRA.md)를 읽는다. 시연과 직접 부모는 [EPISODES](docs/EPISODES.md)에서 찾는다.
4. 과거 세션의 “다음”, “재개”, 날짜별 TODO는 현재 지시가 아니다. 고유 실행 근거는 [보관함](docs/ARCHIVE.md)을 통해 확인한다.
5. 시연 수집 방법을 검토할 때 [Agentic Robotics 워크숍 참고](docs/collection/research/2026-11-14-agentic-robotics-workshop.ko.md)를 읽는다. 채택 논문 39편의 조사 범위, Stretch 4+Astra 사례, 현재 코드와의 차이, 다음 비교 제안 및 원문 접근 한계를 기록했다. 개발용 참고이며 actor 입력·구현·재개 명령이 아니다. 최신 상태와 실행 계획은 계속 STATUS/COLLECTION_PLAN이 정본이다.
6. E36 이후를 검토할 때 [2026-11-16 checkpoint·실행 효과 분석](docs/collection/research/2026-11-16-checkpoint-effect-feedback.ko.md)을 우선 읽는다. [이전 다중 방법 설계](docs/collection/research/2026-11-15-e36-continuation-options.ko.md)와 [HolidayFactory 적용 검토](docs/collection/research/2026-11-15-holidayfactory-phyrc.ko.md)는 선행 근거다. 사실·가설·미구현·미실행을 구분하며 분석 중 새 판단과 미결 사항을 기록한다.

## 현재 범위

- **기존 계획 HOLD, 실제 실행 상태는 E36 마감이다.** 현재는 checkpoint 복원과 실행 효과 피드백의 분석·기록을 우선한다. 분석 후 클린 서버에 적용하는 작업은 나중 단계이며 이번 문서 갱신으로 수집·구현·학습을 재개하지 않는다. 닫힌 E36을 실행 중인 환경처럼 취급하지 않으며 새 원본으로 덮어쓰지 않는다.
- **현재 실행·마감 상태는 [STATUS](docs/project/STATUS.md), 후속 방향과 작업 범위는 [COLLECTION_PLAN](docs/COLLECTION_PLAN.md)이 정본이다.** 최신 근거와 미결 사항은 [2026-11-16 누적 분석](docs/collection/research/2026-11-16-checkpoint-effect-feedback.ko.md)에 둔다. 11월14·15일 계획은 선행 설계로 보존한다. 문서를 actor에 주거나 후보 기능을 자동 적용하지 않는다.
- 사람 조작용 state slot과 `initial_slot` 근사 복원 경로는 이미 존재한다. 완전한 FEM 물리 checkpoint나 E36 중간 복원 검증이 완료됐다고 설명하지 않는다. 현재 collector의 행동 재생과 구분하고, 복원 시 초기화되는 상태·정착·평가 재시작을 검토한다. 기존 관측→행동→관측 루프가 전혀 없었다거나 E36까지 모든 명령이 오작동했다고 일반화하지 않는다.
- E36의 추가 재파지0·20결정·review10은 해당 시도의 조건이다. 향후 모든 방법의 고정 규칙으로 일반화하지 않는다. 각 실험에서 제어원, 입력, 재파지·복구 조건, 예산과 종료/검토 방식을 명시하고 공식 물리·관측·행동·평가 계약은 유지한다.
- E33 `20261114-astra-middle-grip264-001`은 E28/264·새 history242/254에서20결정·471전이로 정상 마감했다. QC471/471·고정 백업 검증을 통과했으나0/50·착의0·success=false이며 손 접근은 미실행이다. [E33 기록](docs/project/sessions/20261114-e33-middle-grip-resume.ko.md).
- E34 `20261114-astra-middle-grip470-retain-001`은 E33/470·새 history434/454, 같은 E28 source group의 후속으로20act·24호출·836전이를 정상 마감했다. QC836/836,5/50·픽업5·착의0·success=false이며 새 파지의 들기·운반·짧은 하강을 시험했으나 손목 걸침·소매 통과는 확인하지 못했다. `coordinated-middle-grip-drape-retain`의 추가 재파지0은 정적 actor 지시이며 상태 원장이나 런타임 차단 기능이 아니다. 고정 백업의 재다운로드·236개 manifest 파일·원본234파일 불변 검증도 완료했다. [E34 기록](docs/project/sessions/20261114-e34-retain-resume.ko.md).
- E35·E36은 각각 QC983/983·933/933과 고정 백업 검증으로 정상 마감했다. 최종 raw5/50은 replay의 pickup이며 새 착의점0이다. E36은10act+finish로 종료했다. [통합 분석 PDF](docs/reports/20261114-e36-integrated-review/phyrc-e36-integrated-review.ko.pdf)에 사용자/Codex/연구 분석과 다음 사람 조작 계획을 정리했다.
- E09·E32는 불완전 원본으로 정상 replay·학습 출처에서 제외한다. E32는758전이·전체 QC 실패이며 진단 백업 검증과 수집 완료를 구분한다. [실패 기록](docs/project/sessions/20261114-e32-incomplete.ko.md). 종전 E28/632·중앙 전략 후보와 E27/928 same-arm 후보는 역사적 미실행 계획이며 현재 출발점이 아니다.
- 정상 평가한 시연의 최고 로컬 원점수는5/50, 착의 득점0이며 완전 착의 성공은 확인하지 못했다. E28과 후속 분기·재사용 prefix를 독립 성공 표본으로 세지 않는다. 기술 QC와 학습 승인은 별도이며 최신 시연의 학습 승인은 `unreviewed`다.
- 사용자 예산 지침은 추가 결정의 실제 효과·반복 정체·관측된 진행·호출과 시간을 근거로 분석하는 것이다. 예산만 자동 증액하거나 남은 결정을 새 run에 합산하지 않는다. 종전 최대5회 승인은 E36 뒤 종료 지시로 제한됐으며 남은 횟수를 채우지 않는다.
- [미래 피드백 큐 후보](docs/collection/research/candidates/20261113-actor-feedback/README.ko.md)는 준비·CPU검사·독립 검토를 마친 미적용 패치다. 실제 모델·GPU 연결이나 실시간 사람–Astra handoff가 완료된 기능으로 설명하지 않는다. 초기 π0.5의63전이·30updates 역시 연결 시험이며 새 시연 학습·착의 개선 성과가 아니다.
- 날짜별 세션의 재개·자동 반복·‘다음 시연’ 문구는 당시 이력이다. 과거 중지와 재개 기록은 [보관함](docs/ARCHIVE.md)에 보존하며 최신 E36 종료 지시를 대신하지 않는다.

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
- README 최상단에는 최신 연구 방향·HOLD 상태·누적 분석 링크를 두고 그 바로 아래 기존 통합 분석 PDF 버튼을 보존한다. 최신 실제 시연은 페이지에서 바로 재생되는 GIF로 표시한다. 새 마감에도 GIF·변환 provenance와 별도 gallery 페이지를 만들고 EPISODES에서 연결한다. 고정 manifest에 포함된 기존 attempt README/원본 MP4를 임의 수정하지 않는다. 상세 근거는 링크로 연결한다.
- 실제 관측, 가설, 미실행 계획을 구분한다. 모델이 붙인 stage, 파일 complete, QC 통과, 기본 reward 0은 착의 성공이 아니다. 영상 일부를 독립 시연으로 세지 않는다.
- 과거 세션·실패·provenance·catalog·주최 측 README·LICENSE·NOTICE·THIRD_PARTY는 보존한다. 중복 설명의 이전 본문은 보관함의 고정 Git revision에서 확인한다.
- 새 결과 마감 시 STATUS, EPISODES, catalog, 세션 기록, 백업 receipt를 갱신한다. 현재 계획은 COLLECTION_PLAN 한 곳에 둔다.
- 문서 변경은 링크·경로·코드 예제·현재/계획 구분을 검사한다. CPU 검사, 실제 CLI, GPU 실행, 과제 성능 중 수행하지 않은 검사를 통과했다고 쓰지 않는다.

## 공개 범위

- GitHub에는 코드·문서·선별 이미지·영상만 둔다. 큰 원본, audit·평가, 모델은 비공개 자료 저장소에 고정 revision과 검증 receipt로 남긴다.
- `scripts/preserve_collection.py`의 허용 목록으로 정상 마감·QC 통과 원본을 보존한다. 불완전 E32는 별도 검토한 로컬 허용 목록으로 진단 전용 백업하며 정상 보존 gate를 완화하지 않는다. 분석은 별도 review/session에 두고 collection 원본에 임의 파일을 추가하지 않는다. 신규 의존성이 있으면 소스 보존 목록도 검증한다.
- 인증 파일·키·토큰·개인 접속 주소·원시 CLI reasoning/events·세션 DB·미검수 로그·simulator.log를 게시하지 않는다. 홈이나 저장소 전체를 백업으로 압축하지 않는다.


