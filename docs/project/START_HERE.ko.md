# 다음 클린 서버에서 시작하기

문서 갱신: **2026-10-22**. 오늘은 문서만 정리했고 새로운 GPU 실행 결과는 없다. 다음 실행은 **2026-10-23 클린 서버에서 시작할 예정**이다. 서버가 실제 준비되었는지 먼저 확인한다.

[README](../../README.ko.md) / [현재 상태](STATUS.md) / [2주 계획](RGBD_TWO_WEEK_PLAN.ko.md) / [복원 명령](RECOVERY.ko.md) / [미해결 작업](TODO.ko.md)

## 1. 읽을 순서

1. 루트 [AGENTS.md](../../AGENTS.md): 실행 범위, 관측 제한, 기록 원칙.
2. [STATUS](STATUS.md): 실제 검증과 미완료 항목.
3. 이 문서: 새 서버에서 재개할 순서.
4. [RGBD_TWO_WEEK_PLAN](RGBD_TWO_WEEK_PLAN.ko.md): 14일 목표, 데이터/기하 계약, 평가 기준.
5. [RECOVERY](RECOVERY.ko.md)와 [TODO](TODO.ko.md): 고정 HF revision, checksum, 존재하는 실행 명령.
6. [RULES](../competition/RULES.md), [DATA](../competition/DATA.md), [POLICY](../competition/POLICY.md).

`PLAN.ko.md`는 첫 실행 전 설계의 보존본이다. 현재 우선순위는 이 문서와 2주 계획을 따른다. 이전 세션의 권한이나 살아 있는 서버를 추정하지 않는다.

## 2. 현재 상태를 확인하는 시작 명령

새 위치에 clone한다. 이미 checkout이 있으면 무조건 덮어쓰거나 reset하지 말고 현재 branch와 변경 사항부터 확인한다.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git branch --show-current
git rev-parse HEAD
```

최신 `main`의 인계 문서를 읽은 뒤 사용할 실행 revision을 기록한다. `RECOVERY.ko.md`의 `7c4cfd4...`는 **이전 실험의 고정 코드**다. 인계 문서를 읽기 전에 무조건 해당 commit으로 checkout하지 않는다. 이전 실험을 정확히 재현해야 한다면 별도 worktree/clone에서 수행하고, 새 실험의 source commit과 혼합하지 않는다.

[세션 템플릿](templates/SESSION.md)을 복사해 UTC run ID를 만들고 GPU, CPU, RAM, 디스크, driver, OS, Docker 상태를 기록한다. 공식 [SETUP](../competition/SETUP.md)의 host prerequisite를 확인한다.

```bash
participant/ops/bootstrap.sh --check
# 위 점검에서 빠진 prerequisite를 해결한 뒤 실행:
participant/ops/bootstrap.sh --install
```

`--check`는 prerequisite 명령과 장치를 확인하지만 GPU/Vulkan 정상 동작은 smoke로 확인해야 한다. `--install`은 host helper용 Python 3.12 환경과 HF CLI를 준비하고 공식 doctor/build/prepare/smoke를 실행한다. 오늘은 실행하지 않았고 전체 clean-server 설치 경로도 아직 미검증이다. host driver, Docker, uv와 openpi 학습 환경을 모두 자동 설치하는 도구가 아니다. 이미지 버전을 임의로 `latest`로 바꾸거나 공식 torch/torchvision/NumPy를 교체하지 않는다.

## 3. 첫 실행 세션의 순서와 완료 조건

| 순서 | 작업 | 확인할 증거 |
|---|---|---|
| 1 | 새 서버 환경과 공식 smoke | 실제 `PHYRC-SMOKE-PASS`, 로그와 환경 명세 |
| 2 | 기존 dataset/model 복원 | RECOVERY의 고정 revision 다운로드와 checksum |
| 3 | 기존 정책 짧은 재실행 | offline load, 유효한 `(2,9)` 행동, 결과와 영상 |
| 4 | Chrome 원격 입력 | 두 로봇 움직임, 숫자키 대체, gripper, blur/disconnect의 key release |
| 5 | 짧은 사람 시연 1개 | 정상 종료, READY, complete=true, 데이터 검사 |
| 6 | QC와 다음 실행 기록 | 원본/실패 구분, 다음 실제 명령, 원격 보존 근거 |

새 서버의 다운로드/설치 시간을 따로 기록한다. 이전 서버의 예상 시간을 새 서버에서 측정한 시간처럼 쓰지 않는다. GPU 작업은 하나씩 실행한다. 첫 시연이 준비되지 않으면 대량 수집과 본학습으로 넘어가지 않는다.

기존 정책의 debug 실행 명령은 [첫 세션](sessions/20261022-bootstrap.md)과 현재 `participant/policy.py`, `scripts/evaluate_policy.py`의 CLI를 대조해 복원 경로에 맞춘다. 없는 helper 이름이나 가상의 명령을 실행 지침에 넣지 않는다.

## 4. Chrome과 사람 시연

`participant/streaming/`의 viewer/keyboard/launcher는 구현되어 있으나 실제 Chrome 통합 검증은 미완료다. 새 서버의 주소와 현재 클라이언트 IP로 설정을 갱신한다. 접속 주소, 토큰, 인증 캐시는 공개 저장소에 쓰지 않는다.

공식 GUI 명령만으로 Chrome streaming이 자동 시작되지는 않는다. 현재 `participant/streaming/start.sh`, `prepare_viewer.py`, `firewall.py`와 [TELEOP](TELEOP.ko.md)를 읽고 실제 옵션을 확인한다. 사람이 키를 조작해야 하는 단계에서는 조작 방법과 필요한 확인을 사용자에게 전달한다.

1. 현재 클라이언트 IPv4를 확인한 뒤 `firewall.py --client-ip`로 기존 PhyRC streaming 포트만 제한하고 `--check`로 확인한다. IP를 추측하지 않는다.
2. Node/npm을 별도로 확인하고 `prepare_viewer.py`로 viewer를 build한다. bootstrap은 npm을 검사하지 않는다.
3. 생성한 `output/webrtc/viewer/dist`를 제한된 8210 포트에서 별도 serve한다. build helper는 HTTP server를 시작하지 않는다.
4. 새 서버의 advertised IPv4를 `STRETCH4_STREAM_HOST`로 설정한 뒤 `participant/streaming/start.sh`를 실행한다. 이 경로는 recording과 deferred export를 설정한다.
5. 실제 Chrome에서 키 입력을 확인하고 새 recording을 정상 종료한다. 첫 연결 성공만으로 전체 조작 검증을 완료 처리하지 않는다.

아래 GUI 명령은 로컬 화면 또는 별도 원격 데스크톱 경로를 사용할 때의 공식 수집 예다. Chrome streaming helper와 동시에 두 번째 simulator를 시작하지 않는다.

```bash
# 로컬 GUI / 별도 원격 데스크톱 경로의 공식 수집 명령:
./run.sh gui --training-record 1 --evaluate 1
```

ESC 후 창이 닫혀도 `[Dataset export] READY`까지 기다린다. `capture.json`의 `status=ready`, `complete=true`와 `policy.hdf5`를 확인한다. [DATA](../competition/DATA.md)의 inspect/deferred 검사에 실제 run 경로를 넣는다. 이전 incomplete archive는 실패 근거로 보존하며 강제로 complete로 바꾸지 않는다.

## 5. 이후 연결

- 유효한 사람 시연을 얻으면 [2주 계획의 작업 A](RGBD_TWO_WEEK_PLAN.ko.md#4-작업-a-기록-재생-품질-검증)부터 이어간다.
- checkpoint step 30→31의 재개 시험은 RECOVERY의 명령을 사용하고 별도 run으로 기록한다. 이것이 새로운 사람 시연 학습을 대신하지 않는다.
- RGB-D 분석 도구는 아직 신규 구현 대상이다. 카메라 좌표계 점군부터 시작하고 depth를 현재 정책 입력에 사용한다고 가정하지 않는다.
- 전체 900초 self-check는 짧은 실행과 분리해 시간 슬롯을 배정한다. 기존 부분 실행은 통과가 아니다.
- Codabench 접근이 가능하면 검증된 ZIP을 제출하고 실제 ID/상태를 기록한다. 불가하면 미제출로 남긴다.

## 6. 서버의 Codex에 붙여넣을 요청

```text
이 저장소에서 PhyRC 2027 연구를 새 클린 서버로 이어갑니다.
AGENTS.md, README.ko.md, docs/project/STATUS.md,
docs/project/START_HERE.ko.md, docs/project/RGBD_TWO_WEEK_PLAN.ko.md,
docs/project/RECOVERY.ko.md, docs/project/TODO.ko.md를 순서대로 읽으세요.
공식 RULES, DATA, POLICY와 현재 코드를 확인한 뒤 작업하세요.

이번 세션은 2주 계획의 D1-D2입니다. 현재 서버/checkout을 조사하고,
고정 산출물 복원, 공식 smoke, 기존 정책의 짧은 재실행,
Chrome 키보드 검증과 사람 시연 1개의 정상 export를 우선 진행하세요.
실제 사용자 키 입력이 필요한 시점에는 구체적인 조작 안내를 주세요.
유효 시연 확보 후 QC를 진행하고 다음 단계의 실제 명령을 남기세요.

이전의 3 episode/63 transition은 scripted integration_test이고,
30-update 정책은 debug 0점/no_contact입니다. 사람 시연, full self-check,
Codabench 제출, 새 서버 복원은 증거 없이 완료 처리하지 마세요.
README의 계획 수량을 현재 성과로 옮기지 마세요.

공식 물리/평가/action을 유지하고 공개 관측만 정책과 자동 수집기에 전달하세요.
raw/audit/info/seed/cloth GT/camera world matrix를 입력으로 사용하지 마세요.
SAM 2와 RGB-D 진단은 공식 simulator와 별도 분석 환경에 두세요.
수집, 학습, GPU 평가는 순차 실행하세요.
추가 유료 API나 다른 서버를 열지 말고 서버 종료/삭제도 하지 마세요.

원본 checkpoint와 실패 기록을 보존하고 run별 commit, 설정, 데이터/모델 revision,
실제 명령, 시간, 결과 JSON, 영상과 checksum을 남기세요.
세션 종료 전에 필요한 산출물을 원격 보존하고 STATUS와 양쪽 README를
실제 검증 범위에 맞춰 갱신하세요. 설치/수집/학습/평가가 막히면 실패 근거와
가장 작은 다음 조치를 기록하고, 실행하지 않은 검증을 통과했다고 쓰지 마세요.
```

## 7. 종료 전

export와 checkpoint 저장이 끝났는지 확인하고 선택한 산출물만 HF에 보존한다. 원격 revision/checksum을 확인한 뒤 코드와 세션 기록을 반영한다. 다음 run의 정확한 명령과 blockers를 남긴다. 서버 종료/삭제는 별도의 사용자 요청이 있을 때만 수행한다.
