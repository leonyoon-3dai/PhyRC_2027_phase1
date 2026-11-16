> **사용자 피드백 실행 경로는 구현·실행 검증됐습니다.** 옵션·checkpoint 준비·게시/답변 형식은 [GUIDED_RUNTIME](collection/GUIDED_RUNTIME.ko.md)을 따릅니다. 이번 시연은 종료됐으며, 다음 출발점과 방향은 [현재 계획](COLLECTION_PLAN.md), 고정 백업과 실제 검증 범위는 [STATUS](project/STATUS.md)를 확인합니다.

# 클린 서버 시작 안내

**2026-11-16 세션 마감:** 사용자 교정 M1 120전이와 R0 단독 접근 분기135전이를 정상 마감했다. 다음 사용자 재개 지시가 오면 **R0 단독 접근 전110전이의 저장slot을 검증·복원**하고, 두 로봇을 마네킹 왼손 쪽으로 함께 이동시켜 양손에 옷을 걸치는 방향을 시험한다. 저장slot의 복원은 아직 시험하지 않았다. 이번 마감 지시만으로 새 실행을 시작하지 않는다. [현재 계획](COLLECTION_PLAN.md)이 정본이다.

[메인](../README.md) | [시연 목록](EPISODES.md) | [다음 수집](COLLECTION_PLAN.md) | [Astra 코드](ASTRA.md) | [클린 서버](OPERATIONS.md)

이 문서는 **새 Ubuntu GPU 서버에서 저장소와 보존 자료를 복원하고, 작은 연결 검사까지 준비하는 순서**입니다. 모든 프로젝트 명령은 저장소 루트에서 실행합니다. 2026-11-13 사용자 재개 요청으로 아래 복원·build·prepare·GPU smoke와 작은 wiring을 실제 완료했습니다. [환경 검사 receipt](project/sessions/20261113-environment-setup.json) / [세션 기록](project/sessions/20261113-environment-setup.ko.md)

실제 진행·마감·점수·백업은 [현재 상태](project/STATUS.md), 실행 조건·후속 판단은 [수집 계획](COLLECTION_PLAN.md)을 기준으로 합니다. 과거 결과는 [E30 마감](project/sessions/20261113-e30-close.ko.md)에 보존합니다.

2026-11-14에는 HF CLI2.4.0 설치·로그인과 고정 모델/환경 연결을 확인한 뒤 E33을 정상 마감했습니다. detached launcher를 적용한 첫 wiring은 umask077 때문에 simulator UID1234가 prompt를 읽지 못해 모델0회·물리0전이에서 실패했습니다. 검토한 명령 스크립트의 `umask 027`로 공유 trace/프롬프트 접근을 허용한 새 wiring은 통과했습니다. actor 인증 디렉터리700·파일600은 유지했습니다. [검사와 E33 마감](project/sessions/20261114-e33-middle-grip-resume.ko.md).

E09·E32의 불완전 원본은 정상 replay 출처로 사용하지 않습니다. E30/E31의 host143은 simulator0·complete·QC통과와 공존했으므로 host 반환값만으로 마감을 판정하지 않습니다. 별도 process session은 host/cgroup 종료 생존을 보장하지 않으며 E32의143 발신 원인은 미확정입니다. [E32 실패 기록](project/sessions/20261114-e32-incomplete.ko.md) / [launcher 검토](project/sessions/20261114-detached-launch-preparation.ko.md).

아래는 클린 서버 환경 재현 절차다. checkpoint·물리0 HOLD·5카메라/GIF·텍스트 재개는 이미 구현했고 slot+prefix 확장까지 CPU399개와 실제 GPU replay를 검증했다. 기능을 다시 구현하지 말고 해당 코드·자산·선택 출발slot을 확인한다. 다음110전이slot의 복원 품질은 새 run에서 별도 검증한다. 과거 배치의 남은 횟수·예산을 이어받지 않는다.

## Codex CLI 시작 프롬프트

새 서버의 개발용 Codex에 아래 내용을 전달하면 됩니다. 별도 대화 이력 없이 이 저장소의 현재 안내를 기준으로 시작합니다.

시연 수집 방법의 연구 근거는 [Agentic Robotics 워크숍 참고](collection/research/2026-11-14-agentic-robotics-workshop.ko.md), [E36 후속 분석](collection/research/2026-11-15-e36-continuation-options.ko.md), [HolidayFactory 적용 검토](collection/research/2026-11-15-holidayfactory-phyrc.ko.md)에 보존했습니다. 이 채팅을 보지 못한 Codex CLI도 현재 사실·선택지·미구현 부분을 구분할 수 있도록 연결합니다.

```text
AGENTS.md, docs/project/STATUS.md, docs/COLLECTION_PLAN.md, docs/OPERATIONS.md를 읽어라.
현재 세션은 종료됐다. 사용자 재개 요청이 있을 때 아래 절차로 새 run을 시작하라.
고정 Codex CLI0.166.0 / exec / gpt-6-astra / ultra와 actor 격리·단일 GPU 제어원을 유지하라.
최신 고정 백업에서 초기 자산, 선택한110전이 출발slot·receipt·원본을 SHA 검증해 복원하라.
마지막 R0 단독 접근 전인 새 분기 hold-0001/110의 slot은 저장·해시 확인만 됐고 복원은 미검증이다.
복원·정착을 별도 기록하고 과거5카메라와 새 관측을 비교·게시하라. 정확한 물리 복원으로 주장하지 마라.
다음 방향은 두 로봇을 마네킹 왼손 쪽으로 함께 옮긴 뒤 옷을 양손에 모두 걸치는 것이다.
R0=오른손 쪽, R1=왼손 쪽이며 양쪽의 실제 운동과 천의 동행을 짧은 구간마다 확인하라.
구간별 GIF와 같은 경계의5카메라를 README에 게시하고 판단 지점에서 사용자 텍스트를 기다려라.
모델 종료 제안·관리 예산·득점 검토는 물리0 HOLD로 전환하라. 무응답은 재개 승인이 아니다.
사용자 종료 때 정상 마감·QC·고정 백업 검증·각 움직임 기록을 완료하라. 과거 배치는 이어받지 마라.
```

## 1. 먼저 준비할 것

| 항목 | 필요한 상태 |
|---|---|
| 서버 | Ubuntu 22.04/24.04, Linux x86-64, RTX 렌더링 지원 NVIDIA GPU와 정상 드라이버. 이 fork는 L40S 1대로 실행했습니다. [Isaac Sim 6.0.1 요건](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/requirements.html)을 확인합니다. |
| 자원 | 공식 권장 RAM 32 GB 이상, GPU 메모리 12 GB 이상, SSD 100 GB 이상. 압축본·해제본·최종 복사본과 새 RGB-D 기록을 함께 둘 여유가 더 필요합니다. |
| 컨테이너 | Docker Engine과 NVIDIA Container Toolkit. actor 격리 경로는 Docker 29.1.5에서 검증됐으며 `gateway_mode_ipv4=isolated`, `--gw-priority` 지원이 필요합니다. |
| 비공개 원본 | HF dataset `leonayoon/phyrc-2027-phase1-private-backup`을 읽을 수 있는 본인 계정. 코드 clone만으로 잠긴 로컬 자산과 전체 시연을 복원할 수 없습니다. |
| 모델 인증 | `gpt-6-astra`에 접근할 수 있는 ChatGPT 계정으로 새 서버의 Codex CLI에 로그인. HF 인증과 별개입니다. |
| 외부 제공 사항 | 서버 접속 권한, HF 저장소 읽기 권한, 모델 로그인, 선택 시 브라우저 접속 주소. 인증 파일과 토큰은 GitHub나 백업에 없습니다. |

큰 원본의 `audit`, 평가, 배치 정보는 신뢰된 검수·재실행 영역에만 둡니다. actor는 지정 카메라와 공개 로봇 상태만 받습니다. 공식 입력·행동 규격은 [policy_interface.json](../config/policy_interface.json), 이용 조건은 [LICENSE](../LICENSE), [NOTICE](../NOTICE), [THIRD_PARTY](../THIRD_PARTY.md)를 따릅니다.

### 호스트 도구

GPU 드라이버가 이미 준비된 서버에서는 다음부터 확인합니다. `nvidia-smi`가 실패하면 드라이버를 먼저 해결합니다. 호스트에 Isaac Sim을 별도로 설치하지 않습니다.

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates gnupg python3 xauth util-linux unzip xz-utils
nvidia-smi
```

Docker와 NVIDIA Container Toolkit이 없다면 저장소에 보존한 [공식 설치 가이드의 2–3절](competition/SETUP.md#2-docker-engine)에 있는 설치 명령을 실행합니다. Docker 그룹 적용 후에는 다시 로그인합니다. 두 검사가 모두 통과해야 다음 단계로 갑니다.

```bash
docker run --rm hello-world
docker run --rm --gpus all ubuntu:24.04 nvidia-smi
```

`uv`가 없으면 [공식 설치 방법](https://docs.astral.sh/uv/getting-started/installation/)으로 준비합니다. 설치된 도구는 덮어쓰지 말고 버전을 기록합니다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

## 2. 저장소와 호스트 Python

새 작업 디렉터리에서 clone합니다. 기존 checkout을 다시 사용할 때는 변경 파일을 먼저 확인하고 덮어쓰지 않습니다. `main`의 실제 commit을 기록하며 과거 시연 소스와 현재 개발 소스를 구분합니다.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
export PHYRC_ROOT="$PWD"
git status --short
git rev-parse HEAD
participant/ops/bootstrap.sh --check
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python numpy==1.26.4 h5py==3.12.1 pillow==11.0.0 psutil==6.1.1
uv tool install huggingface_hub==2.4.0
hf --version
hf auth login
```

인증은 대화형 로그인으로 준비합니다. 토큰·로그인 URL·`auth.json` 내용을 출력하거나 문서에 붙이지 않습니다. HF CLI가 다른 버전으로 이미 설치되어 있으면 자동으로 강제 교체하지 않고 현재 버전과 `hf download --help`를 먼저 확인합니다. 아래 복원은 `--type dataset`, `--revision`, `--force-download`, `--local-dir`을 사용합니다.

`bootstrap.sh --install`은 HF CLI 2.2.0을 설치하고 곧바로 build/prepare/smoke까지 수행합니다. 이 안내에서는 **원본 자산 복원 후 환경을 검사하기 위해 `--check`와 명시적인 단계를 사용**합니다.

### Node와 npm

Codex 패키지 설치에 Node/npm이 필요합니다. 브라우저 viewer의 잠금 파일은 Node 20 이상, npm 10 이상을 요구합니다. 이미 맞는 버전이 있으면 유지합니다. 없다면 다음은 [공식 Node 22.23.4 배포본](https://nodejs.org/en/blog/release/v22.23.4)을 저장소의 무시된 `.runtime/`에 설치하는 예입니다. 이 버전을 과거 시연의 측정 환경이라고 주장하지 않습니다.

```bash
mkdir -p .runtime/host-tools
curl -fL https://nodejs.org/dist/v22.23.4/node-v22.23.4-linux-x64.tar.xz \
  -o .runtime/host-tools/node-v22.23.4-linux-x64.tar.xz
curl -fL https://nodejs.org/dist/v22.23.4/SHASUMS256.txt \
  -o .runtime/host-tools/SHASUMS256.txt
(cd .runtime/host-tools && grep '  node-v22\.23\.4-linux-x64\.tar\.xz$' SHASUMS256.txt | sha256sum -c -)
tar -xJf .runtime/host-tools/node-v22.23.4-linux-x64.tar.xz -C .runtime/host-tools
export PATH="$PHYRC_ROOT/.runtime/host-tools/node-v22.23.4-linux-x64/bin:$PATH"
node --version
npm --version
```

## 3. 원본과 자산 복원

첫 서버는 초기 자산 묶음이 필요합니다. 특정 시연에서 분기하려면 그 시연의 receipt도 선택합니다. **이번 기본 복원 대상은 초기 자산과 E36입니다. E34는 이전 출발 대안을 준비할 때 추가합니다.** 전체 백업 목록은 [보존 자료](ARCHIVE.md)에서 찾습니다.

| 용도 | receipt | 고정 HF revision |
|---|---|---|
| 초기 자산과 E07 원본 | [초기 백업](project/sessions/20261106-remote-backup-verification.json) | `e1d32f9f9ea82438f90bc379452abf83a150999b` |
| 최신 출발 E36 원본 | [E36 백업](project/sessions/20261114-e36-backup-verification.json) | `dcf059881e4e6c103dc8206438a70eb1b8ccb26f` |
| 이전 대안 E34 원본 | [E34 백업](project/sessions/20261114-e34-backup-verification.json) | `ba71dd6a07e2b05202c3dcaa5b0c9a3c17997b1d` |

아래 코드는 초기 묶음을 새 staging에 받아 **크기·SHA256·archive 내부 파일**을 검사합니다. 초기 묶음을 복원·병합한 뒤 `receipt`를 `docs/project/sessions/20261114-e36-backup-verification.json`으로 바꿔 별도로 반복합니다. E34 대안이 필요하면 E34 receipt로 같은 절차를 수행합니다. receipt의 `main` 같은 가변 참조 대신 고정 revision을 사용합니다.

```bash
.venv/bin/python - <<'PY_RESTORE'
import datetime, hashlib, json, pathlib, subprocess, sys
receipt = pathlib.Path('docs/project/sessions/20261106-remote-backup-verification.json')
meta = json.loads(receipt.read_text())
assert meta['private'] and meta['remote_download_verified']
remote = meta.get('archive_path') or meta['path']
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
root = pathlib.Path('output/restores') / stamp
root.mkdir(parents=True, mode=0o700)
subprocess.run(['hf', 'download', meta['repo_id'], remote, '--type', 'dataset',
    '--revision', meta['revision'], '--force-download', '--local-dir', str(root/'download')], check=True)
archive = root/'download'/remote
assert archive.stat().st_size == meta['archive_bytes'], 'archive size mismatch'
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == meta['archive_sha256'], 'archive SHA mismatch'
subprocess.run([sys.executable, 'participant/ops/artifacts.py', 'restore',
    str(root/'unpacked'), '--archive', str(archive)], check=True)
print('Verified staging:', root/'unpacked')
PY_RESTORE
```

### 검증된 파일만 병합

출력된 실제 staging 경로를 지정합니다. 아래 명령은 전체 대상을 먼저 검사하고, `assets/`와 `output/`의 **누락 파일만 추가**합니다. 다른 내용의 기존 파일이나 symlink가 있으면 쓰기 전에 중단합니다. 실패 원본과 검수 결과를 덮어쓰지 않습니다.

```bash
export PHYRC_RESTORE_STAGE='output/restores/<위에서-출력된-시각>/unpacked'
.venv/bin/python - <<'PY_MERGE'
import hashlib, json, os, pathlib, shutil
os.umask(0o077)
source = pathlib.Path(os.environ['PHYRC_RESTORE_STAGE']).resolve()
target = pathlib.Path.cwd().resolve()
assert (target/'config/assets.lock.json').is_file(), 'run from repository root'
manifest = json.loads((source/'SHA256.json').read_text())
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
selected = []
for name, spec in manifest.items():
    relative = pathlib.Path(name)
    assert not relative.is_absolute() and '..' not in relative.parts, 'unsafe path'
    if not relative.parts or relative.parts[0] not in ('assets', 'output'):
        continue
    src, dst = source/relative, target/relative
    for base, candidate in ((source, src), (target, dst)):
        for node in (candidate, *candidate.parents):
            if node == base:
                break
            assert not node.is_symlink(), f'symlink rejected: {relative}'
            assert node == candidate or not node.exists() or node.is_dir(), 'invalid parent'
    assert src.is_file() and digest(src) == spec['sha256'], f'source mismatch: {relative}'
    assert not dst.exists() or (dst.is_file() and digest(dst) == spec['sha256']), f'existing file differs: {relative}'
    selected.append((src, dst, spec['sha256']))
assert selected, 'no assets/output files selected'
for src, dst, expected in selected:
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        with src.open('rb') as reader, dst.open('xb') as writer:
            shutil.copyfileobj(reader, writer)
    assert digest(dst) == expected, 'post-copy mismatch'
print('Verified files:', len(selected))
PY_MERGE
python3 scripts/fetch_assets.py --check
```

이 작업은 데이터 복사와 검사입니다. 시뮬레이터 상태를 복구하거나 로봇을 움직이지 않습니다. `assets/custom/`의 로봇·사람·옷 원본은 [잠금 파일](../config/assets.lock.json)과 일치해야 합니다. 다운로드 주소가 없는 자산을 다른 파일로 대체해 검사를 우회하지 않습니다.

## 4. 환경과 GPU 검사

[Dockerfile](../Dockerfile)은 Isaac Sim **6.0.1** 이미지 digest `783444c706538aa76cf5126e911ddc5e618779e6105305ad4af4260362a30aa9`에 고정되어 있습니다. `latest`로 교체하지 않습니다. 컨테이너 Python 의존성은 [requirements-runtime.txt](../requirements-runtime.txt)가 설치하며 호스트 `.venv`와 별개입니다.

```bash
./run.sh doctor
./run.sh build
./run.sh prepare
./run.sh smoke
```

`smoke`는 실제 GPU 물리를 실행하는 작은 검사입니다. 서버 사용과 검사 실행을 요청받은 뒤 수행합니다. **종료 코드 0과 `PHYRC-SMOKE-PASS`를 모두 확인**합니다. 장면 초기화 메시지만으로 통과로 기록하지 않습니다. 첫 shader compile 시간은 환경마다 다릅니다.

| 호스트 경로 | 시뮬레이터 컨테이너 경로 |
|---|---|
| 저장소 루트 | `/project` 읽기 전용 |
| `output/` | `/output` |
| `scripts/` | `/scripts` 읽기 전용 |
| `.runtime/PhyRC_Sim/` | `/workspace/PhyRC_Sim` |

복원 staging의 0700 권한과 simulator UID 1234 때문에 공유 디렉터리를 통과하지 못한 이력이 있습니다. `run.sh`는 `1234:현재그룹`으로 실행합니다. 아래 **공유 부모 두 개만** 조정하고 원본·actor 인증 폴더 전체에 재귀 chmod를 하지 않습니다.

```bash
mkdir -p output/operator-traces output/collections
chgrp "$(id -g)" output/operator-traces output/collections
chmod g+x output/operator-traces
chmod g+rwx output/collections
```

## 5. 고정 Codex CLI와 연결 검사

```bash
npm install --prefix .runtime/codex-0.166.0 @openai/codex@0.166.0
export PATH="$PHYRC_ROOT/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
codex --version
codex login --device-auth
codex login status
docker pull python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
```

정확히 `codex-cli 0.166.0`인지 확인합니다. [actor 코드](../participant/collection/codex_actor.py)는 Linux x64 native 실행 파일과 `gpt-6-astra` / `ultra` 조합을 검사합니다. 전역 CLI, 다른 모델, API backend로 자동 대체하지 않습니다. 인증 파일은 개인 권한으로 존재해야 하며 actor가 전용 사본을 만들어 종료 시 제거합니다. 실제 모델 접근 가능 여부는 로그인 상태만으로 확정되지 않습니다.

다음은 재개 승인 후의 **작은 실제 연결 시험**입니다. 옷입히기 실험이나 E28이 아닙니다. 기본 경로에 WebRTC가 필요하지 않습니다. 다른 GPU 수집기·학습·평가를 동시에 실행하지 않습니다.

```bash
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
phyrc_wiring_id="$(date -u +%Y%m%dT%H%M%SZ)-codex-wiring"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id "$phyrc_wiring_id" --mode wiring --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 \
  --decisions 3 --max-steps 20 --model-timeout 180
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.validate_capture \
  "output/collections/$phyrc_wiring_id" --output "output/collections/$phyrc_wiring_id/validation.json"
```

확인할 것은 종료 응답, 파일 완결성, 실제 `obs/action/next_obs` 정렬입니다. `quality_passed=true`는 착의 성공이나 학습 승인이 아닙니다. 모델 호출 중 물리는 멈추며, 20 Hz는 기록·행동 경계입니다. 모델의 실제 응답 주파수로 설명하지 않습니다.

## 6. 다음 세션: 단독 접근 전110전이에서 양손 걸침 시도

**사용자 재개 지시 후** [현재 계획](COLLECTION_PLAN.md)과 [GUIDED_RUNTIME](collection/GUIDED_RUNTIME.ko.md)의 구현된 경로를 사용한다. 이번 세션은 마감됐으므로 살아 있는 HOLD를 재개하는 것이 아니다.

1. 초기 자산과 [최신 백업 receipt](collection/reviews/20261116-right-hand-hold10-backup-verification.json)의 원본·출발slot·receipt를 위3절로 복원·검증한다. M1 앞110행동 replay가 필요하면 [parent 백업](collection/reviews/20261116-m1-checkpoint-backup-verification.json)도 복원한다.
2. 새 분기 hold-0001/110에서 저장한slot의 SHA·코드·자산 계보를 확인하고 고유 새 run에서 복원한다. 이 slot은 저장·해시 검증만 마쳤고 복원 품질은 미검증이다.
3. 복원 정착을 별도 기록하고 당시 공개5카메라와 새 관측을 비교·게시한다. 정확한 FEM 물리 되감기로 주장하지 않는다.
4. 적합한 출발에서 **두 로봇을 마네킹 왼손 쪽으로 함께 이동한 뒤 옷을 양손에 걸치는 방향**을 짧게 시험한다. R0=오른손 쪽/R1=왼손 쪽, 실제 양쪽 이동과 천의 동행을 확인한다.
5. 판단 지점·모델 stop/finish·관리 예산·득점 검토에서는 물리0 HOLD하고 구간 GIF와5카메라를 README 상단에 게시한 뒤 사용자 텍스트를 기다린다.
6. 사용자 종료 때 정상 마감·전수 QC·고정 백업 검증과 개별 움직임 장부를 갱신한다.

collector/client의 opt-in `--user-guided`와 초기slot+선택 prefix 경로는 이미 구현·검증됐다. M1/M2/M3는 guided 방법 이름이며 실제 최신 작업 지시는 현재 계획과 사용자 텍스트다. 과거 E27/E28 또는 E36 최초 준비 명령을 그대로 시작 명령으로 복사하지 않는다.

같은 live HOLD에서 계속할 때는 환경을 reset하지 않는다. 다른 checkpoint 선택이나 마감 후 복원은 **새 run**으로 기록한다. 과거 점수·시간을 이월하거나 동일 source group을 독립 성공으로 세지 않는다.

## 7. 사람 조작과 브라우저

현재 `prepare_viewer.py`는 **읽기 전용 spectator**를 만듭니다. 과거 `LIVE.ko.md`의 같은 명령이 키보드 조작 화면을 만든다는 설명을 현재 기능으로 복사하지 않습니다. 과거 사람 시연과 키 매핑은 보존되어 있으며 브라우저 조작 화면 복원은 별도 확인 대상입니다.

로컬 Linux 데스크톱에서 현재 공식 사람 조작 경로는 다음과 같습니다. GUI는 DISPLAY/Xauthority와 모니터가 필요합니다. headless 서버의 Astra 수집과 구분합니다.

```bash
./run.sh gui --training-record 1 --evaluate 1
```

`ESC`로 종료한 뒤 `[Dataset export] READY`, `capture.json`의 `status=ready`, `complete=true`, `policy.hdf5`까지 확인합니다. 현재 `run.sh gui`는 종료 후 export를 자동 수행합니다. 과거 스트리밍 launcher의 `STRETCH4_DEFER_EXPORT=1` 경로는 별도 기능이며, GUI 명령에도 적용된다고 가정하지 않습니다. 대기 중인 export request를 처리할 때는 출력된 실제 경로를 사용하고 exporter와 다음 simulator를 동시에 실행하지 않습니다.

## 8. 마감과 인계

1. 수집기를 정상 종료하고 host/client/simulator 반환값과 capture 완결성을 확인합니다. 창이 닫힌 것과 정상 마감은 다릅니다.
2. 닫힌 원본에 전수 QC를 수행합니다. 원점수, 착의 점수, 점수율, `success`, 시각 검토, 학습 승인 상태를 따로 기록합니다.
3. 새 run ID의 원본과 실행 소스·모델·프롬프트·명령·직접 부모를 보존합니다. 원본 수정 대신 별도 review 파일에 분석을 씁니다.
4. [보존 도구](../scripts/preserve_collection.py)의 허용 목록으로 묶고 비공개 저장소의 고정 revision에서 재다운로드·SHA 검증합니다. 공개 GitHub에는 선별 관측과 검토 자료만 둡니다.
5. 실제 새 시연을 수행한 경우 시연 목록에 변화와 결과를 한 줄로 추가하고 현재 계획을 갱신합니다. 선택한 시험 카드의 예산·중지 조건과 사용자 피드백을 반영하며 과거 최대5회 배치를 자동 재개하지 않습니다. 세부 명령·검사 receipt는 기존 `project/sessions/`와 실행별 기록 경로에 남깁니다.
6. 수집 프로세스가 없는지 확인한 뒤 요청받은 서버 종료를 별도로 수행합니다. **시뮬레이터 종료와 클라우드 인스턴스 정지는 다른 작업**입니다.

인증·원시 reasoning·CLI 이벤트·세션 DB·미검수 simulator 로그를 공개하거나 홈 전체를 압축하지 않습니다. GPU 검사·모델 호출·과제 성능·문서 링크 검사는 각각 실제 수행한 범위로 기록합니다.

### 문제가 생기면

| 증상 | 먼저 확인할 곳 |
|---|---|
| 자산 해시/파일 누락 | 초기 비공개 백업과 `config/assets.lock.json`. E36/E34 archive만으로 초기 잠금 자산을 대체할 수 없음 |
| Docker `invalid tar header` | [공식 설치 가이드의 Docker 29 설명](competition/SETUP.md#troubleshooting). 기존 daemon 설정을 통째로 덮어쓰지 않음 |
| actor의 CLI/인증 오류 | 고정 PATH, `codex-cli 0.166.0`, private 권한의 본인 auth 파일, 모델 접근 권한 |
| actor network 생성 실패 | Docker의 isolated gateway와 `--gw-priority` 지원. 격리 설정을 끄고 우회하지 않음 |
| 공유 폴더 permission denied | simulator UID1234와 공유 부모의 현재 그룹 접근, launcher가 상속한 umask와 prompt 권한. 인증 폴더까지 재귀 chmod하지 않음 |
| `active prepare/run` | `cache/runtime.lock`을 보유한 이전 실행의 정상 종료 여부. 실행 중 잠금 삭제 금지 |
| 파일 complete=false / 중간 종료 | 실패 원본 보존. 완료 표시를 수정하지 말고 새 run ID로 재시도 |
| 영상은 보이지만 점수 미확인 | 공식 evaluator의 별도 결과 확인. 단계 이름·그리퍼 닫힘·QC 통과를 착의 성공으로 해석하지 않음 |
