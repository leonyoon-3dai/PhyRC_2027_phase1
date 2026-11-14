# 클린 서버 재개: 가운데 파지와 위에서 내려 걸치기

2026-11-14 사용자가 HF CLI 설치, 마지막 시연 제안1회 재개, 새 에이전틱 시스템 연구의 수집 시스템 적용 분석을 요청했다. 과거 중지 지시는 이 단일 실행 범위에서 해제됐다. 이 기록은 준비 상태이며 시작·결과는 실제 확인 후 갱신한다.

- 시작 checkout: `112cc5145dda4203ddce478473ddd70e7f17b3bb`, 최초 clean.
- HF CLI: 독립 `uv tool` 환경에 huggingface_hub2.4.0 설치; 사용자 터미널 로그인 확인.
- 호스트: NVIDIA L40S46,068MiB, 드라이버580.126.09, Docker29.1.5, Python3.12.16. 고정 numpy1.26.4/h5py3.12.1/Pillow11.0.0/psutil6.1.1 별도 `.venv`.
- 전역 Codex0.169.0을 유지하고 프로젝트 `.runtime/codex-0.166.0`에0.166.0 별도 설치. ChatGPT 로그인 상태 확인은 실제 actor 모델 연결 검사와 구분한다.
- 초기 CPU 검사는 shallow clone의 과거 test oracle commit 누락으로12개 import 오류가 났다. 전체 Git 이력을 fetch해 해결했다. 새 전략6개 회귀 검사를 포함한 전체 CPU352개가48.542초에 통과했고 독립 검토의 신규+central13개도 통과했다.
- 초기 자산과 E28은 인계 receipt의 고정 HF revision·archive SHA·전체 내부 manifest를 검증해 누락 파일만 복원했다. E28 전수 QC739/739·오류0을 새 서버에서 다시 확인했다. 잠금 자산8개와 Docker build/prepare도 통과했다. E32 원본은 복원 대상이 아니다.
- detached launcher는 게시된 원본과 byte-identical로 복사했고 CPU9개 검사 통과. 기존143 발신 원인은 미확정이며 process-session 분리는 host/cgroup 종료 생존 보장이 아니다.

실행 조건의 정본은 [COLLECTION_PLAN](../../COLLECTION_PLAN.md#이번-e33-실행-조건)이다. E28/264, 새 history242/254, `coordinated-middle-grip-drape`, 최대20새 결정. 새 원본은 `20261114-astra-middle-grip264-001`에만 기록한다.

새 전략은 현재 공개 관측에서 더 가운데의 접근 가능한 밑단 위치를 선택하고 실제 닫힘·천 동행을 확인한 뒤 세로 공간을 만든다. 같은 마네킹 손 위에 접근해 짧게 내려 걸치는 관계를 시험한다. 위치·속도 정답, 숨은 기하, 평가 결과는 actor에 전달하지 않는다. 구동·스키마·물리·평가기는 유지하고 기존 전략의 프롬프트도 보존한다. 위에서 내리는 단계에 도달하지 못하면 수행한 것으로 기록하지 않는다.

마감 시 실제 시작/종료, source snapshot, replay/model/settle/cleanup 전이, 모델 호출·시간, 파일 complete, 전수 QC, 별도 점수와 영상, 고정 백업을 각각 기록한다. 단계별 시각적 진행과 착의 득점은 별개이며 학습 승인은 자동 부여하지 않는다.

[검증된264 CPU 분기 계획](../../collection/retry-plans/20261114-e33-e28-264-middle-grip.json)과 [추가 에이전틱 연구 제안](../../collection/research/2026-11-14-agentic-collection-proposal.ko.md)을 보존한다. 연구 제안의 구간 sampler·실패 기억·교정쌍 학습은 구현하지 않았다.

## 같은 세션의 추가 수집 요청과 연결 검사

사용자가 “기존 방법으로 시연 몇번 수집을 더 진행보면서 다른 연구나 시스템의 장점을 어떻게 적용할지 함께 고민”하도록 요청했다. 우선3회를 기존 Astra 방식으로 순차 수집하고 각 결과를 근거로 다음 경계·조작을 선택한다. 새 연구 시스템 기능의 동시 도입은 하지 않는다. 이후 E34/E35의 출발점은 E33 결과 전에 확정하지 않는다.

실제 GPU smoke는 종료0과 `PHYRC-SMOKE-PASS`를 확인했다. 첫 초기화 약256초이며 착의 성공 검사가 아니다. wiring001은 detached supervisor의 umask077을 상속해 prompt 파일을 simulator UID1234가 읽지 못했다. 모델 호출0·물리전이0에서 실패했고 원본을 보존했다. launcher 원본은 유지하고 검토된 명령 스크립트에 `umask 027`을 넣어 같은 작업 그룹의 trace 접근/프롬프트 읽기를 허용한다. actor 인증 디렉터리700·인증파일600은 그대로다. 재검사는 새 wiring002로 진행한다.
