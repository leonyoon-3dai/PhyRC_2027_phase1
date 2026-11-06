# 클린 서버에서 시연 수집 준비하기

[현재 목표와 코드 구조](../../README.md) · [상세 수집 과정](../collection/README.ko.md) · [공식 설치 문서](../competition/SETUP.md) · [데이터 규격](../competition/DATA.md) · [관측·행동 규칙](../competition/RULES.md)

이 문서는 새 L40S 서버에서 환경과 구현된 Codex CLI 수집 경로를 복원·검증하는 순서입니다. 명령과 실제 검증 상태를 구분하며, 가장 최근 결과는 [현재 상태](STATUS.md)와 README를 따릅니다. 이전 실행의 통과가 새 서버의 정상 동작을 보장하지 않습니다.

현재 세션은 안정적인 데이터 수집 시스템과 다양한 방법의 과정 기록을 우선합니다. 최신 사용자 피드백에 따라 계측 수정·상주 호출 pilot·짧은 다중 행동을 순차 검증하며, 모델·`ultra` 설정과 첫 5점 리뷰 조건은 유지합니다. 아래 준비 명령을 실행 중인 환경에 무조건 다시 적용하지 않습니다.

기존 브라우저 사람 조작과 별도로 **Astra 자동 수집의 WebRTC는 관찰 전용**입니다. 사람·모델의 제어권 전환은 미구현이며 두 실행기를 동시에 시작하지 않습니다. 기존 모델·과거 데이터 전체 다운로드, 새 학습, 900초 평가는 수집 재개의 선행 조건이 아닙니다.

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

## 3. Codex CLI 수집 경로 준비

검증한 조합은 Linux x86-64, Codex CLI **0.166.0**, `gpt-6-astra`/`ultra`, Docker 29.1.5입니다. 설치·로그인과 모델 접근은 새 서버에서 다시 확인합니다. 별도 API나 다른 모델로 자동 대체하지 않습니다. Node/npm과 전역 설치 권한을 먼저 준비합니다.

```bash
npm install --global @openai/codex@0.166.0
codex --version
codex login --device-auth
codex login status
codex exec --help
docker pull python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
```

`codex_actor.py`는 native CLI 실행 파일, 공개 입력 디렉터리, 새 Codex home만 별도 컨테이너에 연결합니다. 인증 사본은 0600으로 만들고 종료 시 제거하며 호스트 설정·개발 저장소·평가·audit·원시 상태는 연결하지 않습니다. 내부 Docker망에서 허용한 모델·인증 origin의 HTTPS만 프록시로 중계하고 직접 인터넷·호스트 서비스 접근을 차단합니다. 별도 host 포트나 GPU를 actor에 제공하지 않습니다.

모델에 전달하는 것은 RGB 5장, 전체 공개 로봇 상태와 16×16 depth 중앙값 격자입니다. 전체 depth·유효 마스크는 별도 저장하며, 전체 해상도 depth를 모델 영상 입력으로 전달했다고 설명하지 않습니다. 이미지 경로는 턴별로 고정하고 같은 에피소드의 명시적 UUID를 재개합니다. 새 시도는 새 actor 세션을 사용합니다.

아래는 작은 lift·그리퍼 명령 → 정지 → 종료를 확인하는 **연결 시험**입니다. 4.1~4.2절에서 접속 환경과 뷰어를 준비하고 `STRETCH4_STREAM_HOST`, `STRETCH4_VIEWER_ORIGIN`을 현재 값으로 설정합니다. 별도 사람 조작 시뮬레이터가 실행 중이면 먼저 정상 종료합니다.

```bash
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
run_id="$(date -u +%Y%m%dT%H%M%SZ)-codex-wiring"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id "$run_id" --mode wiring --model gpt-6-astra --effort ultra \
  --decisions 3 --max-steps 20 --webrtc
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.validate_capture \
  "output/collections/$run_id" --output "output/collections/$run_id/validation.json"
```

`output/operator-traces/<run-id>/attempt.json`의 종료 상태, 정상 종료 HDF5, `validation.json`과 별도 평가를 함께 확인합니다. 2026-11-06 r5에서 이 wiring 경로의 3개 모델 결정·3전이·정상 종료·전수 검사를 확인했습니다. `--mode wiring`은 `integration_test` 출처이며 성공 시연으로 집계하지 않습니다. 재시도는 새 `--run-id`와 함께 `--parent-attempt`, `--retry-reason`을 지정합니다. 기존 파일을 덮어쓰지 않습니다. `--mode dressing`은 착의 시도용 경로이지만 아직 50점·착의 성공을 검증한 명령은 아닙니다.

기능 설정으로 shell·browser·앱·플러그인 등의 도구를 줄이고, JSONL에 실행 이벤트가 있으면 행동을 거부합니다. 도구 레지스트리가 완전히 비었다고 가정하지 않습니다. 알려진 시작 전 비실행 안내만 예외로 구분하고 일반 오류는 실패로 남깁니다.

자동 수집의 첫 비교는 공식 기본 배치·랜덤화 설정에서 시작합니다. 이전 사람 연습의 `STRETCH4_PRACTICE_LAYOUT=garment_side`, `STRETCH4_RANDOMIZE=0`를 자동 수집이나 공식 평가에 그대로 복사하지 않습니다. 훈련용 별도 시작 상태를 사용하면 그 목적과 설정을 데이터에 기록하고, 기본 배치 평가와 구분합니다. GPU 수집·렌더링·학습·평가는 순차 실행합니다.

## 4. 선택 사항: Chrome으로 사람이 관찰·개입하기

4.1~4.2절의 접속·뷰어 준비는 사람 조작과 자동 수집에서 공유합니다. 4.3절은 별도의 **사람 조작용** 실행입니다. 자동 수집은 3절의 `--webrtc`를 사용하며 키보드·버튼 로봇 입력이 적용되지 않습니다. 자유 이동 viewport와 안내 정보는 Astra 관측으로 전달하지 않습니다. 제어권 전환은 별도 구현·검증 대상입니다.

### 4.1 접속 주소와 포트

새 서버에서 실제 접속 가능한 서버 IPv4와 현재 클라이언트 IPv4를 확인합니다. 외부 조회로 얻은 서버의 송신 IP가 접속 주소와 같다고 가정하지 않습니다. 아래 `<...>`는 모두 실제 값으로 교체합니다. 이전 세션의 주소·포트는 재사용하지 않습니다.

| 내부 포트 | 프로토콜 | 용도 |
|---|---|---|
| 8210 | TCP | 브라우저 화면 페이지 |
| 8211 | TCP | 키보드 입력 전달 |
| 49100 | TCP | WebRTC 연결 설정 |
| 47998 | UDP | 영상 전송 |

직접 접속 또는 클라우드 포트 등록을 준비한 뒤, 호스트의 해당 스트리밍 포트만 클라이언트 IPv4에 제한합니다. 스크립트는 `sudo -n nft`로 전용 `inet phyrc_stream` 테이블을 구성합니다. 다른 서비스의 방화벽 테이블은 변경하지 않습니다. 적용 전 커널 문법 검사를 실행하며, 실제 주소·포트·인터페이스·종료 규칙을 함께 검증합니다.

```bash
python3 participant/streaming/firewall.py --client-ip "<클라이언트-IPv4>"
python3 participant/streaming/firewall.py --client-ip "<클라이언트-IPv4>" --check
```

NetBird 중계가 확인된 경우 실제 gateway 주소를 `--relay-ip "<gateway-IPv4>"`로 함께 지정합니다. 이 주소는 `wt0` 인터페이스에서만 허용하며, 적용과 `--check`에 같은 인자를 사용합니다. `start.sh`는 `--check-installed`가 통과한 뒤 시작합니다. NetBird가 INPUT 체인에 자동 허용 규칙을 추가하는 환경에서는 로컬 목적지의 스트리밍 포트를 prerouting에서 제한합니다. 다른 INPUT 체인의 DROP을 무시하는 설정은 아니므로 실제 패킷 경로도 확인합니다.

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

### 5.1 Codex 자동 수집

자동 수집은 센서를 읽는 즉시 `output/collections/<run-id>/policy.hdf5`에 5개 공개 카메라 RGB-D와 실제 적용된 20 Hz 전이를 저장합니다. `audit.hdf5`, 단계별 시간, 점수·success·획득 이벤트는 별도 검수 자료입니다. 원시 상태 재생을 통한 지연 변환 경로가 아니므로 `check_deferred_dataset.py` 대신 3절의 `validate_capture`를 사용합니다.

해시·완료 상태·전체 전이·0.05초/12 ticks·관측 연속성·평가 라벨 정합성을 통과해도 `training_approval=unreviewed`입니다. 시각적 과제 품질과 승인 구간은 별도로 검수합니다. `attempt.json`의 actor 호출 시간은 준비·Docker/CLI·요청/응답을 포함하며 모델 내부 추론시간은 미제공입니다. 모델을 기다리는 동안 물리는 멈추고 관찰용 렌더링만 수행합니다.

### 5.2 기존 사람 조작 자료

`STRETCH4_DEFER_EXPORT=1`이면 `Esc` 후 원본을 저장하고 RGB-D 변환을 대기시킵니다. **원본 저장 완료는 학습용 HDF5 생성 완료가 아닙니다.** 명령 로그에 출력된 실제 export request를 사용하고, 수집 프로세스가 끝난 뒤 별도로 변환합니다.

```bash
./run.sh python /scripts/export_policy_dataset.py \
  --request "/output/training_export_requests/<실제-request-파일>.json"
```

이 명령은 기존 사람 수집 경로가 만든 request용이며 즉시 센서 저장을 사용하는 Astra 경로에는 적용하지 않습니다. `[Dataset export] READY`, `capture.json`의 `status=ready`, `complete=true`, 실제 `policy.hdf5`를 확인합니다.

```bash
./run.sh cpu /scripts/inspect_policy_dataset.py \
  "/output/policy_datasets/<실제-run-id>/policy.hdf5"
./run.sh cpu /scripts/check_deferred_dataset.py \
  "/output/full_teleop/<실제-run-id>" "/output/policy_datasets/<실제-run-id>"
```

저장소의 호스트 `output/`은 컨테이너 내부에서 `/output/`, 저장소는 `/project/`, 스크립트 폴더는 `/scripts/`입니다. `passed=true`는 저장·동기화 검사 통과이며 착의 성공을 뜻하지 않습니다. 점수·성공은 별도 공식 평가 결과로 검수하고 행동 생성 세션에 전달하지 않습니다. 끝난 HDF5는 덮어쓰지 않으며, 불완전 원본의 완료 표시를 강제로 바꾸지 않습니다.

## 6. 서버를 바꾸기 전 남길 것

GitHub에는 코드·실행 명령·공개 검수 요약을 저장하고, 큰 원본·데이터·모델은 선택한 HF 저장소에 보존합니다. `participant/ops/artifacts.py`는 검토한 산출물 디렉터리의 manifest·검사·압축·복원을 돕지만 업로드는 별도입니다. 원격 revision과 checksum을 확인하기 전에는 백업 완료로 기록하지 않습니다.

필수 인계는 실행 commit, 이미지 ID, 에셋 잠금, 모델·프롬프트 버전, 공개 관측 선택, 실행 명령, 원본 및 변환 상태, 검수 결과, 다음 명령입니다. 상세 폴더·네이밍·피드백·공개 이미지와 영상 규약은 [수집 과정 문서](../collection/README.ko.md)를 따릅니다. 인증 정보와 서버 접속 주소는 공개 로그에서 제외합니다. 이전 원본이 서버에만 있었다면 새 서버에 남아 있다고 가정하지 않습니다. 프로세스 종료와 클라우드 서버 전원 종료·삭제는 서로 다르며, 서버 종료는 사용자의 실제 요청 범위에 따라 진행합니다.
