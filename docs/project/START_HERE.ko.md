# 클린 서버 복원·검사·재개 안내

**최신 E24는5/50·착의0·success=false,1,610/1,610전이 검사 통과입니다.** 손–경계 정렬과 진입 시도 뒤 큰 면에 가렸고, 마지막에 틈이 일부 다시 드러났습니다. 22행동 후 감독 종료했으며04:11:53–05:02:19UTC·50분26초,sourceb0513d4 clean·host130/Python130/simulator0입니다. 최고5점·중간목표10점미달성입니다.

[현재 상태·다음 명령](STATUS.md) · [E24 영상](../gallery/20261107-astra-progress1179-named-001.ko.md) · [분석](../collection/reviews/20261107-astra-progress1179-named-001.ko.md) · [전체 일지](sessions/20261106-evening-resume.ko.md)

E25는E18/563·history510/542에서한쪽anchor와테이블지지를유지하며다른경계재파지1cycle·닫힘후검사를비교합니다. M1후보는E24종료후통합했고아직실제시행전입니다. [전체CPU검증](sessions/20261107-opposing-rim-validation.json)과실제옷효과는별도입니다. 모든자료trainingunreviewed이며재실행은정확한천checkpoint가아닙니다.

## 보존 위치와 고정 revision

비공개 dataset 저장소는 `leonayoon/phyrc-2027-phase1-private-backup`입니다. 다음 항목은 모두 **고정 revision에서 별도 재다운로드한 archive·SHA 검증 완료**입니다. 파일 경로·정확한 bytes·SHA256은 링크한 JSON을 기준으로 합니다. GitHub 미리보기만으로 전체 RGB-D·행동·자산을 복원할 수 없습니다.

| 묶음·검증 기록 | 고정 revision | 복원 목적 |
|---|---|---|
| [초기 전체 백업](sessions/20261106-remote-backup-verification.json) | `e1d32f9f9ea82438f90bc379452abf83a150999b` | **실제 assets/custom·downloads와 E07 전체 원본** 포함. 11,779,782,360 bytes |
| [E10](sessions/20261106-e10-backup-verification.json) | `3d474bb724adbb42ac44beaf82de7d216930dc5c` | 750전이 원본 |
| [E11](sessions/20261106-e11-backup-verification.json) | `40a98682caca21222335293cc0947d98537cca66` | 777전이·새 과거 관측 |
| [E12](sessions/20261106-e12-backup-verification.json) | `64659dd24e26b54efe5e3d6b0eac6aef206f1555` | 781전이·몸통 입구 경로 |
| [E13](sessions/20261106-e13-backup-verification.json) | `20a9602acb82ac860ebbf2d039ad593085d5a622` | 810전이·손목 depth |
| [E14](sessions/20261106-e14-backup-verification.json) | `d30808911dba914a87eb3104750e5560e4c00cc5` | 짧은 진단721전이·중단 보존 |
| [E15](sessions/20261106-e15-backup-verification.json) | `ba753c41cf64c361ae91aae9e31f9236106bc4ad` | 초기264 분기·611전이·종료·계측 |
| [E16 이력](sessions/20261106-e16-backup-verification.json) | `1ad0f8ba3cc71ab80962907c713357fbd4005e3f` | 순차 지지·한쪽 재파지516전이. E17의352분기와 E18의470분기 원본 |
| [E17 이력](sessions/20261106-e17-backup-verification.json) | `d5ba6c645232c7674d3861fdf65da3a26e9e1ea9` | 다른 lower-rim 후보 재파지452전이·픽업5 |
| [E18 분기 원본](sessions/20261107-e18-backup-verification.json) | `44d01871f0099f8a537f1bdbfee06a404a95f38c` | 감독자 중단·928전이 정상 마감. E19의801분기·E20/E21의470분기 이력과 E22/E23의787분기 및 **다음 E25의563분기 직접 원본** |
| [E19 원본](sessions/20261107-e19-backup-verification.json) | `a5f9136d1479933b6c026465a8af0321bad1504c` | 명명 명령·세 접근·자율 종료932전이,2,130,731,675 bytes. E20의 직접 부모는 E18 |
| [E20 원본](sessions/20261107-e20-backup-verification.json) | `ad7b94f4dd65115082ad53527a48efbf99a5947d` | 목선 후보 두 재파지·준비 미완료·726전이, 1,721,601,271bytes. E21 직접부모는 E18 |
| [E21 원본](sessions/20261107-e21-backup-verification.json) | `45e6adf8586f935b3ca9f6d19ed3ec97371be44f` | 상방 배치·하강·예산 종료1111전이,2,428,228,014 bytes. 마지막 새 파지는 후속 지지 미검증 |
| [E24 최신 원본](sessions/20261107-e24-backup-verification.json) | `1edca310c1b869a8f4c01b3eeb67b14f6699e12c` | 진입 시도·부분 시야 복구·감독 종료1610전이,3,879,304,287bytes·263member검증. 다음E25직접부모는E18 |
| [E23 원본](sessions/20261107-e23-backup-verification.json) | `c1157513362e30d6a8306e7c8fd2ec0265e5db2c` | 방향반전·팔노출·머리접근,1180전이·2,730,237,231bytes. E24의직접부모 |
| [E22 원본](sessions/20261107-e22-backup-verification.json) | `788a36ece3f606ca06dd0f20224910974dbe270e` | 짧은 탐색·자율 종료813전이,1,854,271,559bytes·92member검증. host143/simulator0구분 보존 |
| [이름 기반 행동·질의 연결 시험](sessions/20261107-named-depth-wiring-backup-verification.json) | `7817a63289250cb40e94a50a9b816eb45a567660` | 실제 GPU·모델 없는 fixture3전이. 실제 source commit과 dirty 작업 트리 상태는 receipt에 기록 |
| [BEHAVIOR 참고 원본](sessions/20261107-champion-reference-backup-verification.json) | `427d3a150b48f2e522bbff30f9177d6a2722788d` | 검토한 제3자 원본19개와 출처/범위6파일,6,879,270bytes. 시연·actor·학습 입력과 분리한 참고자료 |
| [비공개 연구·후보](sessions/20261106-private-research-backup-verification.json) | `3349b6a73bf266cfba015654613e58ae490290b5` | 171개 선별 원본·적용 상태·CPU 근거, 4,600,121 bytes |

E22 원본은 [검증 receipt](sessions/20261107-e22-backup-verification.json)의 고정 revision에서 강제 재다운로드 SHA와 전체92개 archive 파일 해시 일치를03:24:59UTC에 확인했습니다. **다음 E25에는 초기 자산과 E18의563경계까지 재실행할 검증 원본이 필요합니다.** E21 마지막 새 파지는 지지가 미검증이므로 이번 분기의 직접 부모로 사용하지 않습니다.

연구 묶음은 `sessions/20261106-private-research-handoff-v1/` 아래에 있으며 `scope.json`·`handoff.md`가 적용/미적용과 정확한 허용 목록을 설명합니다. phase2 profiler는 미적용입니다. pixel query는 이후 main에 통합돼 E18에서3회·E19에서1회 사용했습니다. 이름 기반 행동은 E19 실제 과제에 적용했고 의도 밖 roll 재발은 관측되지 않았으나 착의 득점은0입니다. 목 우선은 E20에서 실제 비교했고 입구 확인 준비에서 종료했습니다(raw0). 상방 배치·하강은 E21에서 실제 비교했고 raw5·착의0으로 예산 마감했습니다. E21에서는 pixel query를4회 사용했으며 질의 중 물리 진행은0입니다. E22의 `coordinated-entry-probe`는 실제 비교 후5점/no_contact로 종료했습니다. E23의 `coordinated-task-progress`는5점/1180QC로 종료했고, 후속E24도5점/1610QC로 감독 종료했습니다. E25용 `coordinated-opposing-rim`은 E24 종료 후 통합310CPU검사를 통과했으며 아직 실제 시행 전입니다. 옛 후보 파일의 `not_applied`는 당시 상태일 수 있으므로 현재 상태표를 우선합니다. 인증·home·원시 추론·actor 이벤트·세션DB·시뮬레이터 로그는 백업에 넣지 않았습니다. 성능 자원121행은 정제된 수치 증거입니다. 실행 원본의 trusted 평가/audit는 비공개 검수용이고 actor에 연결하지 않습니다.

## 새 서버 준비와 원본 복원

Linux x86-64·NVIDIA 드라이버·Docker GPU 접근과 용량을 먼저 확인합니다. 실제 검증 서버는 L40S 한 대였고 이미지/버전 근거는 [환경 기록](sessions/20261106-l40s-restore.json), [Dockerfile](../../Dockerfile), [공식 설치](../competition/SETUP.md)에 있습니다. 압축·해제본·새 수집을 함께 저장할 공간이 필요합니다. 호스트 도구 `git docker nvidia-smi python3 curl flock xauth uv`와 별도 Node/npm을 준비합니다. bootstrap은 이 도구들을 설치하지 않습니다.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git rev-parse HEAD
participant/ops/bootstrap.sh --check
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python numpy==1.26.4 h5py==3.12.1 pillow==11.0.0 psutil==6.1.1
command -v hf >/dev/null || uv tool install huggingface_hub==2.4.0
hf auth login
```

기존 checkout이나 `.venv`가 있으면 새로 덮어쓰지 않고 먼저 상태를 확인합니다. HF 인증은 새 서버에서 준비하며 토큰을 공개 명령·문서에 넣지 않습니다. 다음 코드는 **먼저 초기 전체 백업**을 새 staging에 복원합니다. 다음 E25 계획에는 초기 자산·E07 백업 뒤 `receipt`를 `docs/project/sessions/20261107-e18-backup-verification.json`으로 바꿔 E18도 별도 새 경로에 복원하고 같은 충돌 거부 병합을 수행합니다. E18 고정 revision은 `44d01871f0099f8a537f1bdbfee06a404a95f38c`입니다. E25는 E18의563경계에서 분기하고 이번 재실행의510/542 관측을 history로 사용할 예정이므로, 다른 시도 원본을 직접 부모로 대신하지 않습니다. 다른 묶음도 필요할 때 같은 방법으로 복원합니다.

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
                '--revision', meta['revision'], '--force-download',
                '--local-dir', str(root/'download')], check=True)
archive = root/'download'/remote
assert archive.stat().st_size == meta['archive_bytes'], 'archive size mismatch'
with archive.open('rb') as stream:
    assert hashlib.file_digest(stream, 'sha256').hexdigest() == meta['archive_sha256'], 'archive SHA mismatch'
subprocess.run([sys.executable, 'participant/ops/artifacts.py', 'restore',
                str(root/'unpacked'), '--archive', str(archive)], check=True)
print('Verified staging:', root/'unpacked')
PY_RESTORE
```

[충돌을 거부하는 검증된 병합 절차](START_HERE.pre-E15-20261106.ko.md#기존-파일을-보존하며-프로젝트에-병합)에 따라 `PHYRC_RESTORE_STAGE`를 위 `unpacked` 경로로 지정하고, 검사된 `assets/**`·`output/**`만 저장소의 같은 상대 경로로 병합합니다. 병합 블록도 준비한 `.venv/bin/python`으로 실행합니다. 이 절차는 기존 파일을 해시가 같을 때만 보존하고 다른 파일·symlink는 쓰기 전에 거부합니다. 연구 후보는 별도 staging에서 검토하며 현재 소스에 자동 복사하지 않습니다. [원본 자산 잠금](../../config/assets.lock.json)은 git clone만으로 공급되지 않는 로컬 USD/texture를 포함합니다.

```bash
python3 scripts/fetch_assets.py --check
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.validate_capture \
  output/collections/20261106-astra-coordinated-fresh-001 \
  --output "output/restores/e07-validation-$(date -u +%Y%m%dT%H%M%SZ).json"
```

E07 기준은1,067/1,067전이·`quality_passed=true`입니다. 새 서버에서 검사를 반복하되 원본 검수 파일을 덮어쓰거나 E09의 불완전 파일을 고쳐 통과시키지 않습니다. 현재 서버에서는 초기 백업5,166개 파일 병합·자산 SHA·E07 전수 검사와 prefix700 입력 검사를 실제 통과했습니다. 이는 미래 서버의 GPU 정상 작동 보장이 아닙니다.

## 환경·고정 CLI·작은 연결 검사

자산 복원 이후 고정 Isaac Sim6.0.1의 build→prepare→smoke를 수행합니다. 기존 bootstrap --install은 HF2.2.0을 지정하므로 이미 설치된 CLI를 덮어쓰지 않도록 아래 명시적인 단계를 사용합니다. 실제 종료 코드0·`PHYRC-SMOKE-PASS`를 확인합니다. 소스에 필요한 CPU 검사는 다음과 같습니다. 현재 서버에서는 build/prepare/smoke·실제 모델 wiring을 검증했습니다. 새 서버에서는 같은 검사를 다시 수행합니다.

```bash
./run.sh doctor
./run.sh build
./run.sh prepare
./run.sh smoke
npm install --prefix .runtime/codex-0.166.0 @openai/codex@0.166.0
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
codex --version
codex login --device-auth
codex login status
docker pull python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
```

`codex --version`이 `codex-cli 0.166.0`인지 확인합니다. 호스트 전역 CLI0.167.0을 그대로 사용하지 않습니다. 최신 CLI로 자동 업그레이드하거나 모델·서비스 등급을 바꾸지 않습니다. actor는 별도 Docker·내부망에서 공개 입력과 전용 인증 사본만 사용하며 host 저장소·평가/audit를 연결하지 않습니다. 인증 파일은 백업에서 복원하지 않습니다.

원본 복원 디렉터리의0700 권한 때문에 simulator UID1234가 공유 trace 부모를 통과하지 못한 이력이 있습니다. `run.sh`는 컨테이너를 `1234:$(id -g)`로 실행합니다. 아래 두 공유 부모에만 현재 그룹 접근을 준비합니다. 하위 원본·actor 인증/runtime의 권한은 바꾸지 않습니다.

```bash
mkdir -p output/operator-traces output/collections
chgrp "$(id -g)" output/operator-traces output/collections
chmod g+x output/operator-traces
chmod g+rwx output/collections
```

기본 연결 검사는 **`--webrtc` 없이** 새 run ID를 사용합니다.

```bash
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
run_id="$(date -u +%Y%m%dT%H%M%SZ)-codex-wiring"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id "$run_id" --mode wiring --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 \
  --decisions 3 --max-steps 20 --model-timeout 180
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.validate_capture \
  "output/collections/$run_id" --output "output/collections/$run_id/validation.json"
```

wiring은 연결 시험이며 성공 시연이 아닙니다. 종료 ACK·정상 파일 완료·전수 검사 이후에만 다음 전략을 선택합니다. 재실행 출처·중복 prefix·새 행동을 구분하고 같은 source group을 유지합니다. 점수 감시나 신뢰된 배치 설정을 actor 입력에 넣지 않습니다.

[과거 시작 안내 전체](START_HERE.pre-E15-20261106.ko.md)는 재현 이력으로 보존했습니다. 그 문서의 “E09부터 수정”, “WebRTC/Chrome 필수”, “다음은700 분기”는 현재 지시가 아닙니다. 다음 과제는 STATUS의 **E23 목표 진전 비교 계획과 실제 시작 여부**를 확인하고 새 run ID로 수행하는 것입니다. E23는03:30:54UTC·source952ec8d clean으로실행중이며, E18 prefix787과 초기 자산 복원이 필요합니다. 설정은 `coordinated-task-progress`·history719/771·named+query·plan1·18판단/max1300/timeout180/settle6/review10입니다. 공유 prefix의 반복 분기를 독립 시연·검증 출처로 세지 않습니다. 사용자에게 이미 받은 재개·main 통합 승인을 반복해서 묻지 않습니다. 과거 E16에서는 독립 지지 진단과 한쪽 재파지를 실제 시행했으며, 국소 지지의 시각적 근거와 연속 입구 미확인을 구분합니다. 픽셀 조회는 보이는 표면 간 거리 질의이며 가림·접촉·입구 위상을 알아내는 기능이 아닙니다.
