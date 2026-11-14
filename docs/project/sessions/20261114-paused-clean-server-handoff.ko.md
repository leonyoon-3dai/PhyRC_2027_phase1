# 2026-11-14 중지와 클린 서버 인계

**[이번 세션 영상·실패 분석 모음](../../collection/reviews/20261114-session-review.ko.md)**에서 E28–E32 영상과 시도별 판단을 바로 검토할 수 있습니다.

사용자가 “여기까지 하고 잠깐 정리 하고 나중에 다시 클린 서버로 시작합니다.”라고 요청했다. **시연·분석 자동 반복을 중지했고 E33은 시작하지 않았다.** E32 실패 원본의 고정 비공개 백업 검증과 공개 기록 정리만 완료한다. 명시적 재개 전에는 새 시연·GPU 검사·모델 호출을 하지 않는다. 서버 전원 종료를 요청하거나 수행한 기록은 아니며 수집 프로세스 종료와 구분한다.

마지막 정상 마감·전체 QC 통과는 E31: 로컬5/50·픽업5·착의0·새 득점0·success=false다. E32는20 act·21호출,758전이를 남겼으나 capture/두 HDF5 root의 complete=false로 전체 QC 실패다. 원본을 고치지 않고 진단 전용으로 보존한다. [현재 상태](../STATUS.md) / [E32 실패 기록](20261114-e32-incomplete.ko.md) / [공개 리뷰](../../collection/reviews/20261113-astra-central380-001.ko.md) / [시간 분석](../../collection/reviews/20261113-decision-budget/E32/README.ko.md).

## 2026-11-14 추가 시연 참고

사용자는 파지 위치를 더 가운데 쪽으로 조정해 노란 경계가 위아래로 길게 늘어지고 공간이 충분히 보이는 상태에서, 마네킹 손 위에서 시작해 살짝 내려오며 걸치는 방향을 요청했다. [다음 시연 메모](../../COLLECTION_PLAN.md#2026-11-14-다음-시연-메모)에 상세 순서를 기록했다. **문서만 업데이트했으며 실제 시연·서버 재시작·코드·actor 프롬프트 변경은 수행하지 않았다.** 다음 클린 서버 재개 때 먼저 읽고 종전 E28/632·같은 중앙 전략 유지안의 적합성을 다시 검토한다.

## 새 서버에서 읽을 기준

[Agentic Robotics 워크숍 참고](../../collection/research/2026-11-14-agentic-robotics-workshop.ko.md)에는 39편 조사 목록, 수상 데모의 Stretch 4+Astra 사례, 현재 코드 대응, 파지 변경·위에서 내려 걸치기 검토안을 보존했다. 새 서버의 개발용 Codex가 읽는 연구 문서이며, actor에 전달하거나 중지 상태를 해제하는 지시가 아니다.

[AGENTS](../../../AGENTS.md)와 [OPERATIONS](../../OPERATIONS.md)를 먼저 읽고 `main`의 실제 clone commit과 clean 상태를 기록한다. 이 문서를 포함한 게시 commit은 Git 이력에서 고정할 수 있다. 과거 E32의 실행 source는 `0421f8b3c45fd0291455fb278144ce279682dd98`이며 새 개발 checkout의 commit과 혼동하지 않는다. 현재 정적 전략 client SHA256은 `4797a5d010ffb8b0d8d6faf127aabdc57431b34be8ee78f4bcd59524dcae2899`다. E32 실행 이후 정책·actor·simulator·평가 코드는 변경하지 않았다.

| 구성 | 유지할 기준 |
|---|---|
| Actor | Codex CLI0.166.0 /exec /gpt-6-astra /ultra; named·pixel query·wrist panel·plan1 |
| Python |3.12 계열, 호스트 numpy1.26.4·h5py3.12.1·pillow11.0.0·psutil6.1.1 |
| HF CLI |검증 환경 huggingface_hub2.4.0, `hf auth login`; 기존 다른 버전은 덮어쓰기 전에 확인 |
| Simulator |Isaac Sim6.0.1, Dockerfile base digest `sha256:783444c706538aa76cf5126e911ddc5e618779e6105305ad4af4260362a30aa9` |
| Actor container |`python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54` |
| 자산·의존성 |[`assets.lock.json`](../../../config/assets.lock.json), [`requirements-runtime.txt`](../../../requirements-runtime.txt), [`Dockerfile`](../../../Dockerfile) 고정 값 |
| 인증 |새 서버에서 HF와 Codex에 별도 로그인. 토큰·auth.json·세션 DB는 저장소/백업에 없음 |

[이 서버의 환경 검증](20261113-environment-setup.json)은 과거 L40S·Docker29.1.5·NVIDIA Toolkit1.20.1 환경의 결과이며 새 서버 검사를 대신하지 않는다. 실제 실행 재개를 요청받으면 자산 해시, doctor/build/prepare/smoke, actor 격리와 고정 CLI를 다시 확인한다. GPU 작업은 한 번에 하나만 실행한다.

## 다음 후보에 필요한 비공개 원본

HF dataset은 `leonayoon/phyrc-2027-phase1-private-backup`이다. 가변 main 대신 아래 receipt의 고정 revision·경로를 사용하고 `--force-download`로 별도 staging에 받는다. archive bytes/SHA256과 내부 manifest 전체를 확인한 뒤 누락 파일만 병합한다. 기존 다른 내용의 파일·symlink가 있으면 중단하며 덮어쓰지 않는다. 구체적인 다운로드·안전 restore·누락만 병합 코드는 [OPERATIONS 3절](../../OPERATIONS.md#3-원본과-자산-복원)에 있다.

| 목적 | 고정 HF revision | 크기 / SHA256 / receipt |
|---|---|---|
| 초기 자산 |`e1d32f9f9ea82438f90bc379452abf83a150999b`|11779782360bytes /`d087a7899f60fffd7e9541d13215585ef6b462f3e0d71c66e0649fd0172ed34b` /[초기 receipt](20261106-remote-backup-verification.json)|
| **다음 후보의 직접 원본 E28** |`230c90a5d7abe76216311590f7764a65c19a946d`|1687186946bytes /`b38a8136991b6a851c4b4dfabbb9f98a1549b8f56cd7d2586228c823101bfdfc` /[E28 receipt](20261113-e28-backup-verification.json),402members 검증|

E28 archive 경로는 `sessions/20261113-astra-side-hem-fresh-001-close-v1/20261113-astra-side-hem-fresh-001-close-v1.tar.gz`다. 전체402members를 검증하고 그 아래 `output/collections/20261113-astra-side-hem-fresh-001/`과 `output/operator-traces/20261113-astra-side-hem-fresh-001/`를 원래 구조로 복원한다. `policy.hdf5`, `capture.json`, `validation.json`, `run_metadata.json`, trace의 `attempt.json`이 prefix 로더의 필수 근거다. 전체 소스·audit·평가·공개 관측도 archive에 보존됐으므로 일부 PNG만으로 replay를 준비하지 않는다. 과거 actor 세션은 복사하지 않으며 history는 새 replay에서 생성한다.

E28 policy SHA는 `03b0c37fc67737ed88af83e2400ff5a5d04e0778319ec3c3bac09906999b4ce9`,capture SHA는 `22de85a2b55100af158d4fec208be76b09f34aed3bf0ab3f5aed9ac83a45d1d2`,validation SHA는 `bf7bd85edd3dc009bc2f164997996a2948949e4787326636f15e1c0145b650e6`다. 전체739전이 QC·해시를 확인한다. 종전632 후보를 다시 선택하는 경우에만 `[0,632)` 행동 prefix를 새 환경에서 수행하며, 파지 위치 변경에 필요한 더 이른 유효 경계나 새 reset 여부를 먼저 검토한다. 정확한 천 physics checkpoint가 아니다. [검증된 CPU 분기 계획](../../collection/retry-plans/20261114-e33-e28-632-central-span.json).

**E32 diagnostic archive는 다음 실행의 필수 원본이 아니며 replay·학습 출처에서 제외한다.** [진단 백업 receipt](20261114-e32-backup-verification.json)의 고정 revision `91f91b06e39bb8257b8c888675b74d747261edd4`,1665375739bytes·SHA`eadd08aff5ab09a93828bf3f2177d28efcedde8d3a7f4d9d927cb62202a1889d`,234members와 원본233파일 불변 검증을 마쳤다. 진단 검토로 복원하더라도 별도 staging에 두고 원래 complete=false/756·758 차이를 유지한다. 원본 없는 상태나 정확한 천 상태 복원을 약속하지 않는다.

## 최신 시연 메모와 함께 재검토할 종전 후보

[E33 계획](20261114-e33-plan.ko.md)은 `20261114-astra-central632-001`, 직접 parent/source group E28, prefix632·새 history588/614, **같은 `coordinated-central-span-entry`, 최대20새 결정/1400총전이/review10**, motion-only settle6·timeout180·시간 계측이다. 이는 추가 파지 변경 제안 전의 미실행 후보이며 새 서버에서 출발점·전략·ID 중복과 조건을 다시 확인한다.632+20×(20+6)+1=1153으로 전이 예산에 들어간다.

긴 운반보다 첫 손 접촉 전 중앙 자유 구간의 폭·깊이·정렬에 판단을 쓰는 목적이다. U자 외형이나 가림을 삽입 성공으로 세지 않고 같은 손과 연결 전완의 실제 상대 진행을 확인한다. [선택 근거](../../collection/research/2026-11-14-e33-central632-direction.ko.md). 최신 E32 경계를 재사용하거나 결과를 독립 성공 표본으로 세지 않는다.

[별도 process session launcher 준비](20261114-detached-launch-preparation.ko.md)는9개 합성 CPU 검사를 통과했지만 실제 GPU/모델에 적용하지 않았다. 검토한 source·9개 검사·당시 사용 설명을 [미적용 인계 artifact](../../collection/research/candidates/20261114-detached-launcher/README.ko.md)에 byte-identical로 보존했다. 게시가 설치·활성화나 실제 수집 검증을 뜻하지 않으며 명시적 재개 뒤 원본 해시·실행 명령을 다시 검토한다.143 발신 원인은 미확정이고 세션 분리가 모든 host/cgroup 종료에서 생존을 보장하지 않는다. 미적용 실시간 피드백 큐 패치도 활성화하지 않는다.

