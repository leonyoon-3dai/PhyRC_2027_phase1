# 첫 실행 자료 복원

**10월 23일 추가 복원 자료:** [오늘 세션](sessions/20261023-clean-start.md)에 최소 사람 이동 샘플, 원본/중단 export와 최종 검사 근거의 고정 revision·복원 명령을 추가했습니다. 공식 클린 서버 smoke와 짧은 정책 실행은 새 서버에서 통과했으나, 전체 900초 검사는 다시 사용자 요청으로 중단했습니다. 아래 10월 22일 고정 모델/데이터 자료는 그대로 보존합니다.

새 서버의 현재 진입점은 [START_HERE](START_HERE.ko.md)다. 아래 commit과 revision은 이전 실험 재현용 고정 자료다. 최신 인계 문서를 먼저 읽고, 과거 실행을 재현할 때는 별도 checkout에서 이 snapshot을 사용한다. 새 run의 코드/데이터/정규화와 과거 실험을 섞지 않는다.

현재까지 **같은 서버의 새 디렉터리**에서 HF 다운로드 checksum, snapshot pack/restore를 검증했다. 별도의 클린 서버 전체 복원과 학습 step 재개는 아직 검증되지 않았다. 서버 삭제·종료 전에 원격 자료를 확인해야 하며 이번 요청으로 서버를 종료하지 않는다.

## 고정된 자료

- 코드: 공개 `7c4cfd41f1b17bcdc5031a61997a6df5834564d9`. 로컬 `5dd4227`과 Git tree가 동일함을 확인했다. 로컬 이전 구현 commit은 별도 Git bundle로 보존한다.
- 공식 upstream: `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`.
- openpi: `215abfb217dbac7d5f1273282331b9b1866c0479`.
- 원본 dataset: `leonayoon/phyrc-2027-phase1-data`, revision `057b59b1099407b20fe25dafa080285b34ab3aaa`.
- 전체 params·train state: `leonayoon/phyrc-2027-phase1-pi05`, revision `cadbc22798387e4217497f61a196a801854853b2`.
- 각 HF run 폴더의 `SHA256.json`을 실제 다운로드 후 검사했다. 모델 카드 변경 revision과 weight revision은 별개다.

## 현재 존재하는 복원 명령

최신 인계 문서를 읽은 뒤, 이전 실험을 정확히 재현하는 별도 checkout에는 위 공개 commit을 사용한다. 새 작업은 선택한 source commit을 명시하고 공식 SETUP의 Docker/NVIDIA prerequisites를 준비한다. 아래 helper는 호스트 prerequisite 확인을 현재 서버에서 시험했다. `--install` 전체를 두 번째 클린 서버에서 실행했다고 주장하지 않는다.

```bash
participant/ops/bootstrap.sh --check
# Prerequisite 준비 후 공식 build / prepare / smoke를 기록하며 실행:
participant/ops/bootstrap.sh --install
```

HF CLI 로그인은 서버에 별도로 설정한다. 토큰을 저장소나 채팅에 넣지 않는다.

```bash
hf download leonayoon/phyrc-2027-phase1-data --type dataset \
  --revision 057b59b1099407b20fe25dafa080285b34ab3aaa \
  --include 'runs/20261022T0409Z-integration/*' --local-dir output/recovered-data
.venv/bin/python participant/ops/artifacts.py verify \
  output/recovered-data/runs/20261022T0409Z-integration

hf download leonayoon/phyrc-2027-phase1-pi05 --type model \
  --revision cadbc22798387e4217497f61a196a801854853b2 \
  --include 'runs/20261022T0420Z-overfit/*' --local-dir output/recovered-model
.venv/bin/python participant/ops/artifacts.py verify \
  output/recovered-model/runs/20261022T0420Z-overfit
```

`participant/ops/artifacts.py manifest|verify|pack|restore`는 명시적으로 선택한 산출물 폴더만 취급한다. 심볼릭 링크·인증 파일처럼 보이는 경로를 거부하며 기존 restore 디렉터리를 덮어쓰지 않는다. 전체 HOME/cache를 백업하지 않는다. 학습 재개에는 checkpoint `29` 안의 **params와 train_state 둘 다** 필요하다. 폴더명 29는 학습 상태 step 30을 의미한다.

현재 학습 실행기는 dataset manifest·정규화·tokenizer·설정과 deterministic seed/step 기반 RNG를 사용한다. dataloader cursor를 보존하지 않으므로 중단 전후 학습 순서의 완전한 일치를 약속하지 않는다. 물리 solver의 비트 단위 복원도 약속하지 않는다.

## 정확한 제출 ZIP과 실행 증거

- ZIP/model repo revision: `1ff737e560e7f4b2c9a29534ff4f907dc01a6a98`.
- ZIP path: `submissions/20261022T0429Z-pi05-release.zip` (6,340,722,353 bytes).
- ZIP SHA256: `611ec928e35c4c446098de2e645cf4d7e332dc95b74e3fbeb54b14663df64871`.
- Session evidence/dataset revision: `69234efea487f083f37bd062835ced8f99e6e9f0`, path `sessions/20261022-bootstrap/`.
- 위 자료는 원격에서 다시 받아 checksum을 확인했다. ZIP의 full 900초 검증은 사용자 요청으로 중단했으므로 통과가 아니다.

현재 호스트에서 사용한 uv는 `0.13.5`이며 helper는 작동하는 `uv`, Docker, NVIDIA runtime 등을 prerequisite로 확인한다. prerequisite 설치까지 자동 완료하는 스크립트로 과장하지 않는다. 작업 당시 실제 `uv sync --frozen`이 openpi의 Python 3.11 환경을 생성했고 host helper는 별도의 Python 3.12 환경을 사용했다.

## 학습 환경과 다음 optimizer-step 시험 준비

아래는 존재하는 코드로 재개를 준비하는 명령이다. **이번 세션은 CPU에서 전체 state 복원까지만 확인했다.** 다음 GPU optimizer step은 TODO다. 초기 checkpoint `29`를 보존하고 새 output 디렉터리에 복사하여 시험한다.

```bash
mkdir -p output/deps
git clone https://github.com/Physical-Intelligence/openpi.git output/deps/openpi
git -C output/deps/openpi checkout --detach 215abfb217dbac7d5f1273282331b9b1866c0479
(cd output/deps/openpi && GIT_LFS_SKIP_SMUDGE=1 uv sync --frozen)

mkdir -p output/recovered-training/phyrc_pi05_lora/pipeline
cp -a output/recovered-model/runs/20261022T0420Z-overfit/checkpoint \
  output/recovered-training/phyrc_pi05_lora/pipeline/29
```

원본과 같은 3 episode로 pipeline-only manifest를 새 서버 경로에 맞춰 생성한다. source group 전체가 train이며 **validation 성능을 보고하는 split이 아니다**.

```bash
.venv/bin/python - <<'PY'
import hashlib, json
from pathlib import Path
path = Path('output/recovered-data/runs/20261022T0409Z-integration/policy.hdf5').resolve()
with path.open('rb') as stream:
    checksum = hashlib.file_digest(stream, 'sha256').hexdigest()
assert checksum == '75cb6d3a952f8ba6af1e1d3b307b7dc22e905dde99588204f230a9eb9202fe0e'
spec = {'purpose': 'pipeline-only resume test; no validation claim', 'episodes': [
    {'path': str(path), 'episode': f'demo_{i}', 'split': 'train',
     'source_group': '20261022T0409Z-integration', 'sha256': checksum,
     'review': 'approved_pipeline_test'} for i in range(3)]}
Path('output/recovered-training/manifest.json').write_text(json.dumps(spec, indent=2) + '\n')
PY
```

GPU 작업이 없는지 확인한 뒤 다음 optimizer step을 시험한다. 이 명령이 성공하면 checkpoint step·optimizer·고정 입력 출력·새 checksum을 새 run으로 기록한다. 동일 dataloader 순서가 자동 복원되었다고 주장하지 않는다.

```bash
XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH="$PWD" \
  output/deps/openpi/.venv/bin/python participant/pi05/train.py \
  --openpi output/deps/openpi \
  --manifest output/recovered-training/manifest.json \
  --base-params output/recovered-training/phyrc_pi05_lora/pipeline/29/params \
  --tokenizer output/recovered-model/runs/20261022T0420Z-overfit/tokenizer.model \
  --output output/recovered-training --steps 31 --batch-size 1 --resume
```

Upstream의 freeze filter는 language/action expert LoRA 외에도 vision/projection을 trainable로 둔다. 이번 복원에서 전체 3,403,421,456 parameter 중 466,957,072개가 trainable임을 확인했다. 순수 adapter 행렬만 학습·보관했다고 표현하지 않는다. 원본 30-step 설정의 LR warmup은 1,000이므로 짧은 overfit 시험 설정은 다음에 별도 run으로 수정하고 비교한다.

