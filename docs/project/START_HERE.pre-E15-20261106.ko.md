> **과거 안내 보존본 — 현재 실행 지시가 아닙니다.** 2026-11-06 E15 마감 전 START_HERE 원문입니다. 아래 E07 중심 상태, E09 미수정, WebRTC/Chrome 필수라는 지시는 모두 이후 변경됐습니다. 현재는 [최신 시작 안내](START_HERE.ko.md)를 따릅니다. 원본 복원·충돌 방지 병합 절차만 최신 안내가 지정한 범위에서 참고합니다.

# 클린 서버에서 시연 수집 준비하기

[세션 정리·다음 목표](SESSION_WRAPUP_20261106.ko.md) · [현재 목표와 코드 구조](../../README.md) · [상세 수집 과정](../collection/README.ko.md) · [공식 설치 문서](../competition/SETUP.md) · [데이터 규격](../competition/DATA.md) · [관측·행동 규칙](../competition/RULES.md)

**현재는 사용자 요청으로 수집을 일시 중지했습니다. 아래 명령은 다음 클린 서버에서 재개를 요청한 뒤 사용할 안내이며, 현재 서버에서 설치·수집을 시작하는 지시가 아닙니다.**

| 인계 핵심 | 확인한 상태와 다음 조건 |
|---|---|
| 남긴 결과 | E07 협력 들기·운반, 공식 부분 점수 5/50·착의 success=false·rate 0점/초. 80결정·1,067전이 전수 검사 통과 |
| 보존할 실패 | E08 스트림 설정 누락으로 시작 전 실패. E09 사용자 중지 뒤 종료 응답 불일치·불완전 파일·전수 검사 실패 |
| 다음 원본 후보 | `20261106-astra-coordinated-fresh-001`의 완결 자료, 운반 경계 **700전이**. E09의 미완료 자료를 정상 재개 출처로 쓰지 않음 |
| 다음 한 가지 과제 | 종료 처리 수정·CPU 회귀 검증, 환경·원본 복원 확인 후 운반 구간을 재실행하고 **소매 통과** 시도 |
| 재개 방식의 한계 | 저장 행동을 다시 실행하며 천·접촉 상태를 새로 관측. 정확한 물리 checkpoint 복원이 아님 |
| 보존 확인 | GitHub 공개 패키지와 비공개 원본 백업은 별개. 로컬 새 경로 복원·전체 SHA·E07 prefix700 입력 검사 06:32:32 UTC 통과. 비공개 HF 고정 revision의 재다운로드·SHA 검증 06:37:37 UTC 완료 |

[현재 종료 상태](STATUS.md) · [E07 종료 검토](../collection/reviews/20261106-astra-coordinated-fresh-001.ko.md) · [정확한 5점·700전이 원본 프레임](../collection/milestones/20261106-astra-coordinated-fresh-001/README.ko.md) · [당일 실패·중지 기록](../collection/sessions/2026-11-06.md) · [행동 재실행과 분기](../collection/guides/continuation-and-branches.ko.md)

[E09 종료 검토](../collection/reviews/20261106-astra-coordinated-branch700-002.ko.md): 재실행 도중 SIGTERM을 받은 뒤 진행 중 행동 응답과 종료 요청이 충돌했습니다. ACK 재실행 120전이와 저장 141전이(원본 재실행 140 + 중립 1)를 구분하고 모델 호출·결정은 0입니다. 파일 미완료 오류 3개를 보존했습니다. **다음 GPU 실행 전에 이 종료 프로토콜을 수정하고, 진행 중 요청·중단·중립 정리·파일 마감을 CPU 회귀 검사로 확인해야 합니다. 아직 수정 완료로 기록하지 않습니다.**

| 복원 순서 | 통과 기준 |
|---|---|
| 1. 소스·자산·서버 | 검증한 commit, 자산 SHA, NVIDIA 드라이버·Docker GPU 접근·여유 공간 |
| 2. 환경 | 고정 Isaac Sim 이미지의 build·prepare·smoke, 실제 종료 코드 0·`PHYRC-SMOKE-PASS` |
| 3. CLI·작은 연결 시험 | CLI 0.166.0·Astra/ultra·exec, CPU 검사·공개 입력 격리·작은 wiring 전수 검사 |
| 4. 관찰 화면 | 새 서버의 실제 매핑과 필수 환경 변수 사전 검사, 제어 주체 한 개 |
| 5. 원본 검수 | E07 전체 자료 복원·manifest·SHA·1,067전이 재검사 |
| 6. 후속 분기 | 새 run ID, 같은 source group, 중복 700전이와 새 행동 분리, 새 관측·평가로 소매 통과 확인 |

자동 수집의 WebRTC는 **관찰 전용**이며 사람 제어권 전환은 미구현입니다. E02 상주 App Server는 실제 2턴 호환성 실패로 보류하고 CLI `exec`를 유지합니다. 색 후보·명명 행동·OpenWAM 연구를 복원 과정에서 자동 적용하지 않습니다. 과거 모든 데이터·모델의 다운로드, 새 학습, 긴 평가는 수집 재개의 선행 조건이 아닙니다.

<details>
<summary>1. 서버와 소스 확인</summary>

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

이미 checkout이 있으면 변경 내용을 먼저 확인합니다. 기존 작업을 덮어쓰거나 특정 과거 commit으로 자동 되돌리지 않습니다. 인계 기록에서 검증된 코드 revision을 고르고 새 checkout에 적용한 뒤 `git rev-parse HEAD`를 남깁니다. E07 당시 `source_snapshot/`과 현재 복원 코드는 서로 다른 재현 근거이며 수정된 종료 처리는 별도 commit과 검사 결과로 기록합니다.

| 고정한 구성 | 소스 근거 |
|---|---|
| Isaac Sim 6.0.1 | `nvcr.io/nvidia/isaac-sim:6.0.1@sha256:783444c706538aa76cf5126e911ddc5e618779e6105305ad4af4260362a30aa9` — [Dockerfile](../../Dockerfile) |
| 보조 Python | 3.12, numpy 1.26.4·h5py 3.12.1·Pillow 11.0.0·psutil 6.1.1 — [bootstrap](../../participant/ops/bootstrap.sh) |
| CLI·actor | Codex CLI 0.166.0, `gpt-6-astra`/`ultra`·exec. 별도 Python 이미지 digest는 3절 |
| 자산 | [assets.lock.json](../../config/assets.lock.json)의 파일별 SHA·출처 |

**로컬 입력 자산 4개는 잠금 파일에 정확한 공개 다운로드 경로가 확립되지 않았다고 기록돼 있습니다.** `assets/custom/`의 옷·사람·사람 texture·로봇 USD 및 참조 파일을 기존 검증 자료에서 복원하고 해시를 확인합니다. `git clone`과 build만으로 모든 자산이 생긴다고 가정하지 않습니다. 원격 revision·다운로드 검증은 인계 근거에 실제로 남은 값만 사용합니다.

```bash
# 잠긴 자산을 복원한 뒤 검사합니다. 파일을 내려받거나 수정하지 않습니다.
python3 scripts/fetch_assets.py --check
```

`participant/ops/bootstrap.sh`가 요구하는 호스트 명령은 `git`, `docker`, `nvidia-smi`, `python3`, `curl`, `flock`, `xauth`, `uv`입니다. 드라이버·Docker·NVIDIA Container Toolkit 설치는 [공식 설치 문서](../competition/SETUP.md)를 따릅니다. **bootstrap은 이 호스트 구성 요소, Node/npm, Codex CLI를 설치하지 않습니다.** GPU가 호스트에 보이는 것만으로 컨테이너의 GPU/Vulkan 정상 동작을 확정하지 않습니다.

</details>

<details>
<summary>2. 공식 환경 구성과 짧은 동작 검사</summary>

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

</details>

<details>
<summary>3. Codex CLI 수집 경로 준비</summary>

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

아래는 재개 이후 작은 lift·그리퍼 명령 → 정지 → 종료를 확인하는 **연결 시험**입니다. 먼저 종료 처리 회귀 검증을 마치고 4.1~4.2절에서 새 접속 환경·뷰어를 준비합니다. 실제 값을 비공개 환경에 설정한 뒤 다음 사전 검사에서 값 자체를 출력하지 않습니다. E08은 이 설정 누락으로 환경 초기화 전에 실패했습니다. 별도 사람 조작 시뮬레이터와 동시에 시작하지 않습니다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python - <<'PY_CHECK'
import os
from participant.streaming.collector_stream import CollectorStream
for name in ('STRETCH4_STREAM_HOST', 'STRETCH4_VIEWER_ORIGIN'):
    if not os.environ.get(name):
        raise SystemExit(f'{name} 설정 필요')
CollectorStream.from_environment()
print('stream configuration check passed')
PY_CHECK
```

이 검사는 값의 형식과 필수 설정만 확인합니다. 포트 등록·방화벽·브라우저 영상 수신은 별도로 검증하며 접속 주소나 인증 값을 공개 파일에 저장하지 않습니다.

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

`--plan-size` 기본값은 1이며 최대 3개의 고정 행동 목록을 받을 수 있습니다. 모든 구간을 실행 전에 검사하고 중간 관측을 저장하지만, 같은 목록의 후속 구간을 위해 모델을 재호출하지 않습니다. 조건부 복구 기능은 아닙니다. E03은 `--plan-size 3`으로 한 호출의 3구간을 실제 검증했습니다.

E05에서 첫 공식 누적 5점 감시는 client에 내장되어 이전 외부 watch를 대체했습니다. 중지 요청 이후 재개할 때 후속 50점 목표에 맞는 종료 설정을 다시 기록합니다. 행동 응답 경계에서 점수를 읽고 미실행 목록을 폐기한 뒤 종료·리뷰하며, 점수는 모델 입력에 넣지 않습니다. wiring에서는 이 감시를 비활성화합니다. usage v2는 thread 누계의 차분과 미확정 호출을 보존하고, actor 시간은 입력 준비·프로세스·결과 해석으로 분해합니다. 내부 모델 추론 시간은 별도로 제공되지 않습니다.

기능 설정으로 shell·browser·앱·플러그인 등의 도구를 줄이고, JSONL에 실행 이벤트가 있으면 행동을 거부합니다. 도구 레지스트리가 완전히 비었다고 가정하지 않습니다. 알려진 시작 전 비실행 안내만 예외로 구분하고 일반 오류는 실패로 남깁니다.

자동 수집의 첫 비교는 공식 기본 배치·랜덤화 설정에서 시작합니다. 이전 사람 연습의 `STRETCH4_PRACTICE_LAYOUT=garment_side`, `STRETCH4_RANDOMIZE=0`를 자동 수집이나 공식 평가에 그대로 복사하지 않습니다. 훈련용 별도 시작 상태를 사용하면 그 목적과 설정을 데이터에 기록하고, 기본 배치 평가와 구분합니다. GPU 수집·렌더링·학습·평가는 순차 실행합니다.

</details>

<details>
<summary>4. Chrome 관찰 화면과 별도 사람 조작 경로</summary>

## 4. Chrome 관찰 화면과 별도 사람 조작 경로

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

</details>

<details>
<summary>5. 수집 종료와 학습용 데이터 생성</summary>

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

</details>

<details>
<summary>6. 원본을 복원·검증하고 소매 통과를 이어갈 준비</summary>

## 6. 원본을 복원·검증하고 소매 통과를 이어갈 준비

### 6.1 자료와 인증을 구분해 인계

GitHub에는 코드·공개 프롬프트·선별 관측·영상·검수 요약이 있습니다. 이것만으로 전체 RGB-D와 행동을 재실행할 수 없습니다. 사용자 승인으로 **비공개 HF dataset 저장소** `leonayoon/phyrc-2027-phase1-private-backup`을 만들고 `private=true`를 확인했습니다. 고정 revision에서 새 로컬 경로로 강제 재다운로드한 압축 파일의 크기·SHA와 부속 metadata 4개의 바이트 일치를 **2026-11-06 06:37:37.501918 UTC**에 확인했습니다. 기존 공개 HF 데이터 저장소에는 이번 신뢰된 원본을 올리지 않았습니다.

| 비공개 전송 묶음 | 확인한 값 |
|---|---|
| 저장소 유형·ID | dataset · `leonayoon/phyrc-2027-phase1-private-backup` |
| 저장소 안 파일 경로 | `sessions/20261106-session-close-v1/20261106-session-close-v1.tar.gz` |
| 압축 파일 크기 | 11,779,782,360 bytes |
| 압축 파일 SHA256 | `d087a7899f60fffd7e9541d13215585ef6b462f3e0d71c66e0649fd0172ed34b` |
| 고정 revision | `e1d32f9f9ea82438f90bc379452abf83a150999b` |
| 로컬 복원 검증 | 2026-11-06 06:32:32 UTC, 새 경로에 복원·전체 SHA 검사·E07 `load_replay_prefix(..., 700)` 통과. CPU만 사용 |
| 원격 파일 검증 | 2026-11-06 06:37:37.501918 UTC, private=true·고정 revision·새 경로 재다운로드 압축 SHA·부속 4파일 바이트 일치. [세션 정리](SESSION_WRAPUP_20261106.ko.md) |

로컬 전체 복원·입력 검사와 원격 파일 재다운로드 검증을 각각 확인했습니다. 새 서버의 설치·물리 재실행·소매 통과는 아직 수행하지 않았습니다. 압축 파일·staging·최종 복사본을 동시에 보관할 디스크 여유를 확보하고 아래 고정 revision을 사용합니다.

| 복원 대상 | 사용 목적과 경계 |
|---|---|
| 잠긴 자산과 참조 파일 | `assets/custom/`, `assets/downloads/`와 `config/assets.lock.json`. 원본 파일 복원 후 해시 확인 |
| `output/collections/20261106-astra-coordinated-fresh-001/` 전체 | `policy.hdf5`, `audit.hdf5`, capture·run metadata·evaluation·validation. 신뢰된 수집·검수 영역에만 보관 |
| `output/operator-traces/20261106-astra-coordinated-fresh-001/` 전체 | attempt·원본 프롬프트·실행 JSONL·source_snapshot·점수 구간 색인과 부모 출처 확인 |
| E07 공개 관측 원본 | `output/actors/<run-id>/observations/`의 RGB·public_depth.npz·공개 상태. actor runtime·인증·원시 세션은 복원 묶음에 섞지 않음 |
| E08·E09 및 다른 시도 원본 | 실패·중단·시계·프로토콜 분석 근거. E09를 정상 checkpoint나 학습 승인 자료로 바꾸지 않음 |
| 환경 재현 근거 | git revision·변경 목록, Docker digest, 자산 잠금, 라이브러리/CLI 버전·명령·검사 결과 |

검수 자료의 배치 설정·평가·audit는 신뢰된 재실행 절차에서만 읽으며 actor에 연결하지 않습니다. 새 서버의 CLI/HF/클라우드 인증은 해당 서버에서 별도로 준비하고, 호스트 home·토큰·접속 설정·개발 로그 전체를 압축하지 않습니다. 원본 서버 전원 종료·삭제는 이 문서 정리와 별도 작업입니다.

### 고정 revision에서 다운로드하고 새 경로에 복원

HF CLI **2.2.0**의 `hf download --help`에서 `--type dataset`, `--revision`, `--local-dir` 지원을 확인했습니다. 인증은 새 서버에서 `hf auth login`으로 준비하며 토큰을 명령 인자나 공개 파일에 쓰지 않습니다. 아래는 원격 검증을 마친 commit SHA입니다. 계속 변하는 `main`을 재현 기준으로 사용하지 않습니다.

```bash
# 사용자 재개 요청 이후, 새 서버의 저장소 루트에서 실행합니다.
phyrc_backup_revision="e1d32f9f9ea82438f90bc379452abf83a150999b"
phyrc_restore_id="$(date -u +%Y%m%dT%H%M%SZ)-phyrc-restore"
export PHYRC_RESTORE_ROOT="$(realpath ..)/$phyrc_restore_id"
mkdir -m 700 "$PHYRC_RESTORE_ROOT"
hf download leonayoon/phyrc-2027-phase1-private-backup \
  sessions/20261106-session-close-v1/20261106-session-close-v1.tar.gz \
  --type dataset --revision "$phyrc_backup_revision" --force-download \
  --local-dir "$PHYRC_RESTORE_ROOT/download"
export PHYRC_RESTORE_ARCHIVE="$PHYRC_RESTORE_ROOT/download/sessions/20261106-session-close-v1/20261106-session-close-v1.tar.gz"
```

다음 명령은 11.78GB 압축 파일의 바이트 수·SHA256을 확인한 뒤, 존재하지 않는 새 staging 경로로만 복원합니다. [산출물 도구](../../participant/ops/artifacts.py)는 archive 내부의 경로·일반 파일 여부와 `SHA256.json`을 검사합니다. 검증 실패 시 원본 서버 자료를 지우거나 기존 경로에 덮어쓰지 않습니다.

```bash
export PHYRC_RESTORE_STAGE="$PHYRC_RESTORE_ROOT/unpacked"
python3 - <<'PY_ARCHIVE'
import hashlib
import os
from pathlib import Path
import subprocess
archive = Path(os.environ['PHYRC_RESTORE_ARCHIVE'])
expected = 'd087a7899f60fffd7e9541d13215585ef6b462f3e0d71c66e0649fd0172ed34b'
if archive.stat().st_size != 11779782360:
    raise SystemExit('archive size mismatch')
with archive.open('rb') as stream:
    if hashlib.file_digest(stream, 'sha256').hexdigest() != expected:
        raise SystemExit('archive SHA256 mismatch')
print('archive size and SHA256 verified')
stage = os.environ['PHYRC_RESTORE_STAGE']
subprocess.run(['python3', 'participant/ops/artifacts.py', 'restore', stage,
                '--archive', str(archive)], check=True)
subprocess.run(['python3', 'participant/ops/artifacts.py', 'verify', stage],
               check=True)
PY_ARCHIVE
```

### 기존 파일을 보존하며 프로젝트에 병합

압축 내부의 `assets/**`와 `output/**`를 저장소 루트의 같은 상대 경로에 복사합니다. `SHA256.json`과 인계 부속 기록은 staging에 남깁니다. 아래 코드는 **먼저 전체 목적 경로를 검사하고**, 기존 파일은 해시가 같을 때만 그대로 유지합니다. 서로 다른 기존 파일·symlink·일반 파일이 아닌 목적 경로가 있으면 쓰기 전에 멈춥니다. 누락 파일만 배타적으로 생성하므로 기존 파일을 덮어쓰거나 삭제하지 않습니다. 병합 중에는 다른 수집기·복원 작업을 실행하지 않습니다.

```bash
python3 - <<'PY_MERGE'
import hashlib
import json
import os
from pathlib import Path
import shutil

os.umask(0o077)
source = Path(os.environ['PHYRC_RESTORE_STAGE']).resolve()
target = Path.cwd().resolve()
if not (target / 'config/assets.lock.json').is_file():
    raise SystemExit('run from the repository root')
manifest = json.loads((source / 'SHA256.json').read_text())

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

selected = []
for name, spec in manifest.items():
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise SystemExit('unsafe manifest path')
    if not relative.parts or relative.parts[0] not in ('assets', 'output'):
        continue
    src, dst = source / relative, target / relative
    for base, candidate in ((source, src), (target, dst)):
        for node in (candidate, *candidate.parents):
            if node == base:
                break
            if node.is_symlink():
                raise SystemExit(f'symlink rejected: {relative}')
            if node != candidate and node.exists() and not node.is_dir():
                raise SystemExit(f'parent is not a directory: {relative}')
    if not src.is_file() or digest(src) != spec['sha256']:
        raise SystemExit(f'source checksum mismatch: {relative}')
    if dst.exists() and (not dst.is_file() or digest(dst) != spec['sha256']):
        raise SystemExit(f'existing file differs; preserved: {relative}')
    selected.append((src, dst, spec['sha256']))
if not selected:
    raise SystemExit('no asset or output files selected')

copied = 0
for src, dst, expected in selected:
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        with src.open('rb') as reader, dst.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
        copied += 1
    if digest(dst) != expected:
        raise SystemExit('post-copy checksum mismatch; retain evidence')
print({'verified_files': len(selected), 'new_files': copied,
       'existing_files_preserved': len(selected) - copied})
PY_MERGE
python3 scripts/fetch_assets.py --check
```

이 병합 절차는 임시 합성 파일로 동일 파일 보존·새 파일 추가·충돌 거부·symlink 거부·손상 원본 거부를 확인했습니다. 전체 원본을 새 서버 프로젝트에 병합하거나 GPU로 재실행한 결과는 아직 없습니다. 실제 원본으로 확인한 것은 로컬 새 경로 복원·전체 SHA·E07 prefix 입력 검사와 원격 고정 revision의 재다운로드 파일 일치입니다. 신뢰된 평가·audit·배치 metadata가 포함된 복원 폴더는 공개 게시나 actor mount 대상으로 사용하지 않습니다. 원본 파일의 종료·품질 표시도 수정하지 않습니다.

### 6.2 E07 전체 원본을 재검사

아래 명령은 **재개한 새 서버에 E07 전체 자료를 복원한 뒤** 실행합니다. 기존 검수 결과를 덮어쓰지 않고 새 검수 보고서를 만듭니다. 모델·GPU를 호출하지 않습니다.

```bash
restore_check_id="$(date -u +%Y%m%dT%H%M%SZ)-restore-e07-check"
mkdir -p "output/sessions/$restore_check_id"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.validate_capture \
  output/collections/20261106-astra-coordinated-fresh-001 \
  --output "output/sessions/$restore_check_id/validation-restored-e07.json"
```

E07 기준은 `quality_passed=true`, 오류 없음, 전체 **1,067전이**입니다. source SHA와 복원 후 SHA가 일치하는지 확인합니다. 검사가 실패하면 원본을 수정해서 통과시키지 말고 복원 누락·손상·버전 차이를 먼저 해결합니다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python - <<'PY_PREFIX'
from pathlib import Path
from participant.collection.continuation import load_replay_prefix
prefix = load_replay_prefix(
    Path.cwd(), '20261106-astra-coordinated-fresh-001', steps=700)
print({'replay_steps': len(prefix.actions),
       'resume_kind': prefix.public_lineage['resume_kind']})
PY_PREFIX
```

이 입력 검사는 원본 완료 상태·검수·정책 파일 SHA·행동/시계/연속성·출처 그룹을 확인합니다. **prefix 객체 전체나 trusted metadata를 출력하지 않습니다.** 재실행을 수행하거나 천 상태가 정확히 같아졌다는 검사는 아닙니다. E09의 `new_recorded_suffix_steps=21`은 미확인 재실행 20전이와 중립 1전이이며 새 모델 행동이 아닙니다.

### 6.3 조건이 충족된 뒤의 후속 실행 예

**현재 일시 중지 중에는 실행하지 않습니다.** 사용자의 재개 요청, 종료 프로토콜 수정·CPU 회귀 검사, 새 서버 smoke·wiring, E07 복원 검사, 관찰 스트림 사전 검사를 모두 확인한 뒤 사용할 예입니다. 원본과 다른 새 run ID를 쓰고, 같은 source group에 포함해 중복 700전이를 독립 시연으로 세지 않습니다.

```bash
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
run_id="$(date -u +%Y%m%dT%H%M%SZ)-astra-sleeve-branch700"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id "$run_id" --mode dressing --strategy coordinated \
  --actor-backend exec --model gpt-6-astra --effort ultra \
  --replay-prefix-run 20261106-astra-coordinated-fresh-001 \
  --replay-prefix-steps 700 \
  --parent-attempt 20261106-astra-coordinated-fresh-001 \
  --retry-reason clean_server_resume_from_verified_transport_prefix \
  --source-group 20261106-coordinated-demo-methods \
  --plan-size 2 --plan-step-budget 40 --review-points 50 \
  --decisions 80 --max-steps 2400 --model-timeout 180 --webrtc
```

최대 전이 예산에는 재실행 prefix도 포함합니다. 모델 설정·기존 행동 형식·공식 물리·평가를 유지하고 새 actor는 최신 공개 관측에서 이어갑니다. 원본 5점은 새 평가로 다시 측정하며 소매 통과나 최종 50점을 미리 보장하지 않습니다. 행동 재실행 이후의 천·양측 파지·마네킹 위치 관계를 공개 카메라로 재확인하고, 실패·복구·지연·점수 획득을 새 시도에 기록합니다.

</details>
