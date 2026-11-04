# 클린 서버에서 시연 수집 준비하기

[현재 목표와 코드 구조](../../README.md) · [공식 설치 문서](../competition/SETUP.md) · [데이터 규격](../competition/DATA.md) · [관측·행동 규칙](../competition/RULES.md)

이 문서는 새 L40S 서버에서 환경을 구성하고, Codex CLI를 이용한 시연 수집기를 구현·검증하기 위한 실행 순서입니다. **명령을 문서화한 것이며 이번 문서 변경으로 새 서버를 실행하거나 수집에 성공한 것은 아닙니다.** 과거의 날짜별 인계보다 현재 README의 목표를 우선합니다.

기존 브라우저 사람 조작 경로는 사용할 수 있습니다. **Astra의 Codex CLI 세션과 공개 관측·행동 실행기를 연결하는 자동 수집 경로는 추가 구현 대상**입니다. 환경 준비 완료와 자동 시연 수집기 완성을 구분합니다. 기존 모델·과거 데이터 전체 다운로드, 새 학습, 900초 평가는 이번 시작의 선행 조건이 아닙니다.

## 1. 서버와 소스 확인

L40S 한 대가 있는 Linux x86-64 서버에서 시작합니다. GPU뿐 아니라 CPU, RAM, 남은 디스크, 드라이버와 Docker의 GPU 접근을 확인합니다. 공식 권장은 RAM 32 GB 이상, GPU 메모리 12 GB 이상, 빈 SSD 100 GB 이상이며 긴 RGB-D 수집에는 추가 공간이 필요합니다. 설치 디스크의 총 용량과 실제 여유 공간은 다릅니다.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git rev-parse HEAD
nvidia-smi
lscpu
free -h
df -h .
docker info
docker run --rm --gpus all ubuntu:24.04 nvidia-smi
```

이미 checkout이 있으면 변경 내용을 먼저 확인합니다. 기존 작업을 덮어쓰거나 특정 과거 commit으로 자동 되돌리지 않습니다. 실행에 사용한 소스 commit을 기록합니다.

`participant/ops/bootstrap.sh`가 요구하는 호스트 명령은 `git`, `docker`, `nvidia-smi`, `python3`, `curl`, `flock`, `xauth`, `uv`입니다. 드라이버·Docker·NVIDIA Container Toolkit 설치는 [공식 설치 문서](../competition/SETUP.md)를 따릅니다. **bootstrap은 이 호스트 구성 요소, Node/npm, Codex CLI를 설치하지 않습니다.** GPU가 호스트에 보이는 것만으로 컨테이너의 GPU/Vulkan 정상 동작을 확정하지 않습니다.

## 2. 공식 환경 구성과 짧은 동작 검사

```bash
participant/ops/bootstrap.sh --check
# 위 점검에서 빠진 전제 조건을 해결한 뒤 실행합니다.
participant/ops/bootstrap.sh --install
```

`--install`은 호스트 보조 도구용 Python 3.12 `.venv`와 지정된 Python 패키지, HF CLI를 준비하고 다음 순서로 실행합니다.

| 단계 | 실행되는 명령 | 확인 사항 |
|---|---|---|
| 진단 | `./run.sh doctor` | 호스트 도구와 GPU·Docker 정보 |
| 이미지 생성 | `./run.sh build` | 고정 Isaac Sim 6.0.1 기반 이미지 생성 |
| 에셋 준비 | `./run.sh prepare` | 에셋 확인과 실행용 장면 준비 |
| 짧은 동작 검사 | `./run.sh smoke` | 종료 코드 0과 `PHYRC-SMOKE-PASS` |

bootstrap 로그는 `output/sessions/<시각>-bootstrap/doctor.log`와 `output/runs/<실행 ID>/`에 저장됩니다. 보조 실행기 `participant/ops/run.py`는 실제 명령의 출력을 `command.log`로 보내므로, 다른 터미널에서 해당 파일을 확인합니다.

```bash
# 실제 생성된 폴더 이름을 확인합니다.
ls -lt output/runs
# 아래 경로는 실제 smoke 실행 폴더로 바꿉니다.
tail -f "output/runs/<실제-smoke-실행-ID>/command.log"
```

`tail`만 종료하려면 그 터미널에서 Ctrl+C를 누릅니다. 장면이 보이거나 초기화 문구가 나왔다는 이유로 smoke 통과로 기록하지 않습니다. 첫 다운로드와 셰이더 준비 시간은 서버마다 다르며, 과거 준비 시간을 보장 시간으로 사용하지 않습니다. 소스 변경 후에는 필요한 `prepare`를 다시 수행합니다.

## 3. Codex CLI 수집기를 준비할 순서

Codex CLI 설치·로그인과 사용할 모델의 실제 접근 가능 여부를 먼저 확인합니다. 블로그에서 사용한 모델 ID는 `gpt-6-astra`이지만, 새 서버에서 해당 모델이 선택 가능한지는 직접 확인해야 합니다. 별도 유료 API나 다른 모델로 자동 대체하지 않습니다.

```bash
codex --version
codex --help
```

위 명령은 CLI 존재와 사용법 확인용이며 시뮬레이터를 제어하지 않습니다. 현재 저장소에는 **Codex CLI 자동 수집을 바로 시작하는 완성된 명령이 없습니다.** 다음 구현 순서와 완료 기준은 README를 따릅니다.

1. 개발용 Codex 세션이 공개 관측 수집·행동 검증·실행·기록을 연결하는 경계를 구현합니다.
2. 행동 생성용 Astra 세션은 그 제한된 도구만 받습니다. 자유 viewport, 원본 상태 로그, 평가 JSON, 환경 객체, 점수는 읽지 않습니다.
3. 모델 호출 없이 0 명령과 짧은 유효 명령으로 `(2,9)` 형식, 시간 정렬, 정상 종료를 검증합니다.
4. Astra를 연결해 두 로봇의 짧은 명령을 실행하고 새 관측을 받는 순환을 확인합니다. 실제 적용 명령을 20 Hz 경계에서 저장합니다.
5. 접근·파지·들어 올리기의 짧은 시도부터 수집하고, 별도 검수 과정에서 공식 평가와 데이터 검사를 수행합니다.

자동 수집의 첫 비교는 공식 기본 배치·랜덤화 설정에서 시작합니다. 이전 사람 연습의 `STRETCH4_PRACTICE_LAYOUT=garment_side`, `STRETCH4_RANDOMIZE=0`를 자동 수집이나 공식 평가에 그대로 복사하지 않습니다. 훈련용 별도 시작 상태를 사용하면 그 목적과 설정을 데이터에 기록하고, 기본 배치 평가와 구분합니다. GPU 수집·렌더링·학습·평가는 순차 실행합니다.

## 4. 선택 사항: Chrome으로 사람이 관찰·개입하기

이 절은 이미 존재하는 **사람 조작용** WebRTC 경로입니다. 화면 연결이나 키보드 조작이 필요할 때 사용합니다. 자유 이동 viewport와 화면 위 안내 정보를 Astra의 관측 입력으로 넘기지 않습니다. 자동 수집기와 사람 조작기의 동시 명령 충돌을 막는 제어권 전환은 별도 구현·검증 대상입니다.

### 4.1 접속 주소와 포트

새 서버에서 실제 접속 가능한 서버 IPv4와 현재 클라이언트 IPv4를 확인합니다. 외부 조회로 얻은 서버의 송신 IP가 접속 주소와 같다고 가정하지 않습니다. 아래 `<...>`는 모두 실제 값으로 교체합니다. 이전 세션의 주소·포트는 재사용하지 않습니다.

| 내부 포트 | 프로토콜 | 용도 |
|---|---|---|
| 8210 | TCP | 브라우저 화면 페이지 |
| 8211 | TCP | 키보드 입력 전달 |
| 49100 | TCP | WebRTC 연결 설정 |
| 47998 | UDP | 영상 전송 |

직접 접속 또는 클라우드 포트 등록을 준비한 뒤, 호스트의 해당 스트리밍 포트만 클라이언트 IPv4에 제한합니다. 스크립트는 `sudo -n iptables`를 사용하므로 필요한 권한을 먼저 확인합니다.

```bash
python3 participant/streaming/firewall.py --client-ip "<클라이언트-IPv4>"
python3 participant/streaming/firewall.py --client-ip "<클라이언트-IPv4>" --check
```

Brev 중계를 사용하는 경우 CLI 인증과 기존 매핑부터 확인합니다. 외부 포트는 내부 포트와 다를 수 있습니다.

```bash
brev ports ls "<인스턴스>" --json
# 로그인되어 있지 않을 때만 브라우저 인증을 진행합니다.
brev login --skip-browser
# 필요한 매핑이 없을 때만 등록합니다.
brev ports open "<인스턴스>" 8210-8211 --protocol tcp --allow "<클라이언트-IPv4>/32" --json
brev ports open "<인스턴스>" 49100 --protocol tcp --allow "<클라이언트-IPv4>/32" --json
brev ports open "<인스턴스>" 47998 --protocol udp --allow "<클라이언트-IPv4>/32" --json
```

중계 트래픽의 출발지가 클라이언트 IP와 다르면 서버 방화벽에 차단될 수 있습니다. 이 경우 `netbird status -d`와 실제 패킷으로 중계 peer를 확인한 뒤 해당 경로만 허용합니다. 확인 없이 과거 gateway IP를 복사하거나 전체 허용으로 바꾸지 않습니다. HTTP 프록시 접속만으로 UDP 영상 경로까지 검증된 것은 아닙니다.

### 4.2 화면 페이지 준비

Node/npm은 별도로 설치되어 있어야 합니다. `prepare_viewer.py`는 지정된 NVIDIA viewer와 저장된 패키지 잠금을 사용해 화면 페이지를 생성하며, HTTP 서버를 시작하지는 않습니다.

```bash
node --version
npm --version
python3 participant/streaming/prepare_viewer.py
python3 -m http.server 8210 --bind 0.0.0.0 --directory output/webrtc/viewer/dist
```

### 4.3 다른 터미널에서 사람 조작 실행

다음은 **기본 배치**에서의 실행 예입니다. 브라우저 연결 검증 때마다 새로운 실행 ID를 사용합니다.

```bash
cd PhyRC_2027_phase1
export STRETCH4_STREAM_HOST="<접속-가능한-IPv4>"
export STRETCH4_VIEWER_ORIGIN="http://<접속-가능한-IPv4>:<외부-viewer-포트>"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
run_id="$(date -u +%Y%m%dT%H%M%SZ)-human-check"
mkdir -p "output/sessions/$run_id"
chmod g+rwx "output/sessions/$run_id"
export STRETCH4_PERF_LOG="/output/sessions/$run_id/performance.jsonl"
export STRETCH4_DEFER_EXPORT=1
# RAM 제한값은 현재 서버의 여유 RAM을 확인한 뒤 정합니다.
export STRETCH4_MAX_RSS_GIB=40
.venv/bin/python participant/ops/run.py --id "$run_id" -- participant/streaming/start.sh
```

`STRETCH4_MAX_RSS_GIB=40`은 충분한 RAM 서버의 예시입니다. 실제 서버 용량에 맞춥니다. 현재 감시 코드는 호스트 여유 RAM이 16 GiB 미만일 때도 정상 종료를 요청하므로 RAM이 작은 서버에서는 이 조건까지 확인합니다.

Chrome URL 형식은 다음과 같습니다. 직접 접속이면 외부 포트와 내부 포트가 같을 수 있지만, 중계에서는 각 실제 매핑을 사용합니다.

```text
http://<접속-가능한-IPv4>:<외부-viewer-포트>/?keyboardPort=<외부-keyboard-포트>&signalPort=<외부-signal-포트>&mediaPort=<외부-media-포트>
```

`STRETCH4_VIEWER_ORIGIN`은 query를 제외한 위 URL의 origin과 정확히 같아야 합니다. 영상, 두 로봇의 짧은 움직임, 키를 놓았을 때의 정지, 그리퍼, 브라우저 포커스 해제 시 입력 해제를 확인합니다. `P` 초기화와 `Esc` 종료를 구분합니다. 현재 브라우저에는 F1~F5 전달이 없으므로 중간 상태 저장·복원은 연결·검증 없이 사용할 수 있다고 가정하지 않습니다.

## 5. 수집 종료와 학습용 데이터 생성

`STRETCH4_DEFER_EXPORT=1`이면 `Esc` 후 원본을 저장하고 RGB-D 변환을 대기시킵니다. **원본 저장 완료는 학습용 HDF5 생성 완료가 아닙니다.** 명령 로그에 출력된 실제 export request를 사용하고, 수집 프로세스가 끝난 뒤 별도로 변환합니다.

```bash
./run.sh python /scripts/export_policy_dataset.py \
  --request "/output/training_export_requests/<실제-request-파일>.json"
```

이 명령은 기존 사람 수집 경로가 만든 request용입니다. 신규 Astra 수집기는 같은 형식으로 연결됐는지 먼저 검증해야 하며, 기존 exporter와 자동 호환된다고 가정하지 않습니다. `[Dataset export] READY`, `capture.json`의 `status=ready`, `complete=true`, 실제 `policy.hdf5`를 확인합니다.

```bash
./run.sh cpu /scripts/inspect_policy_dataset.py \
  "/output/policy_datasets/<실제-run-id>/policy.hdf5"
./run.sh cpu /scripts/check_deferred_dataset.py \
  "/output/full_teleop/<실제-run-id>" "/output/policy_datasets/<실제-run-id>"
```

저장소의 호스트 `output/`은 컨테이너 내부에서 `/output/`, 저장소는 `/project/`, 스크립트 폴더는 `/scripts/`입니다. `passed=true`는 저장·동기화 검사 통과이며 착의 성공을 뜻하지 않습니다. 점수·성공은 별도 공식 평가 결과로 검수하고 행동 생성 세션에 전달하지 않습니다. 끝난 HDF5는 덮어쓰지 않으며, 불완전 원본의 완료 표시를 강제로 바꾸지 않습니다.

## 6. 서버를 바꾸기 전 남길 것

GitHub에는 코드·실행 명령·공개 검수 요약을 저장하고, 큰 원본·데이터·모델은 선택한 HF 저장소에 보존합니다. `participant/ops/artifacts.py`는 검토한 산출물 디렉터리의 manifest·검사·압축·복원을 돕지만 업로드는 별도입니다. 원격 revision과 checksum을 확인하기 전에는 백업 완료로 기록하지 않습니다.

필수 인계는 실행 commit, 이미지 ID, 에셋 잠금, 모델·프롬프트 버전, 공개 관측 선택, 실행 명령, 원본 및 변환 상태, 검수 결과, 다음 명령입니다. 인증 정보와 서버 접속 주소는 공개 로그에서 제외합니다. 이전 원본이 서버에만 있었다면 새 서버에 남아 있다고 가정하지 않습니다. 프로세스 종료와 클라우드 서버 전원 종료·삭제는 서로 다르며, 서버 종료는 사용자의 실제 요청 범위에 따라 진행합니다.
