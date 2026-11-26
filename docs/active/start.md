# 새 서버에서 시연 복원과 다음 회차 준비

시연 1–25와 별도 기술 시험을 종료했다. 갤러리는 CPU만으로 복원할 수 있다. GPU 시뮬레이터와 행동 모델은 사용자가 다음 회차를 요청할 때 준비한다. [시연 24–25 결과](20261126-demo24-25-closeout.ko.md) · [시연 26 계획](20261126-demo26-plan.ko.md) · [시연 24–25 비공개 백업 확인서](20261126-demo24-25-private-backup.json) · [시연 19–23 백업](20261126-demo19-23-private-backup.json) · [시연 1–18 백업](20261125-demo1-18-private-backup.json)

## 저장소와 지난 갤러리 열기

새 서버에서는 아래와 같이 저장소를 받는다. 이미 clone이 있으면 그 루트에서 복원한다.

```bash
git clone --filter=blob:none --sparse https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git sparse-checkout init --cone
git sparse-checkout set assets config docs/active docs/competition examples participant scripts sitecustomize src tests tools
git rev-parse HEAD
```

Hugging Face 비공개 데이터셋에 읽기 권한이 있는 계정으로 인증한다. 아래 명령은 확인서가 지정하는 실행의 SQLite 저널과 검토 ZIP을 고정 revision에서 내려받는다. 파일과 각 영상의 SHA-256을 확인한 뒤 새 `output/segment-review`를 만든다. `--frames-destination`은 누적 GIF용 0전이부터 종료 전이까지의 JPEG를 복원한다. 기존 갤러리와 프레임 디렉터리가 있으면 새 경로를 선택한다.

```bash
command -v hf >/dev/null || uv tool install huggingface-hub==2.4.0
hf auth whoami || hf auth login
test -x .venv/bin/python || uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python pillow==11.0.0
python3.12 scripts/restore_review_gallery.py \
  --receipt docs/active/20261126-demo24-25-private-backup.json \
  --frames-destination output/operator-traces
.venv/bin/python tools/publish_review_gallery.py --review-dir output/segment-review \
  --traces output/operator-traces --destination output/published-gallery --min-demo 24 --gif-only --once
python3.12 -m http.server 8766 --bind 127.0.0.1 --directory output/published-gallery
```

게시에는 아래 환경 준비 절의 Pillow와 FFmpeg가 필요하다. 위 명령은 시연 24–25의 최신 GIF를 `output/published-gallery`에 쓴다. 이전 시연은 해당 확인서와 새 출력 경로를 사용해 복원한다. 로컬 컴퓨터에서 `ssh -N -L 8766:127.0.0.1:8766 SSH_HOST`를 열고 Chrome에서 `http://127.0.0.1:8766/PhyRC-review.html`을 연다. `SSH_HOST`는 새 서버에 연결할 때 쓰는 SSH 별칭이다. 시연별 최신 GIF는 `/PhyRC-gallery/<run>/index.html`에 있다. 상세 화면과 고정 구간 주소가 필요할 때는 게시 명령에서 `--gif-only`를 뺀다. Brev 같은 인증된 HTTP 경로를 쓰는 경우 같은 출처에서 갤러리 폴더만 제공한다. 수집 중에는 게시 명령에서 `--once`를 빼고 실행한다.

HDF5·최종 평가·구간 프레임을 분석하려면 확인서의 해당 `run_id`에서 `archive.path`, `review_frames.path`와 SHA-256을 찾는다. `hf download`에 확인서의 `repo_id`, 해당 파일 경로, `--repo-type dataset --revision <revision>`을 지정한다. 내려받은 원본 아카이브는 `python3.12 participant/ops/artifacts.py restore 새_디렉터리 --archive 받은_파일.tar.gz`로 내부 목록과 파일 해시까지 검증하며 복원할 수 있다.

## 1. 환경 준비

다음 회차를 시작할 때는 Ubuntu x86-64, RTX 렌더링을 지원하는 NVIDIA GPU, Docker·NVIDIA Container Toolkit, Node/npm, Python 3.12와 uv, FFmpeg(libx264), `xauth`, `tmux`를 준비한다. Docker의 isolated bridge 기능이 필요하다. [공식 설치 절차와 GPU 요건](../competition/SETUP.md)

```bash
test -x .venv/bin/python || uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python numpy==1.26.4 h5py==3.12.1 pillow==11.0.0 psutil==6.1.1
ffmpeg -hide_banner -encoders 2>/dev/null | grep libx264
./run.sh doctor
./run.sh build
./run.sh prepare
python3 scripts/fetch_assets.py --check
```

셸에 오래된 접촉이나 배치 설정이 남아 있으면 해제한다. 사용하려는 소스가 런타임에 복사됐는지 확인한다. [공식 변경과 물리 조건](upstream.md)

```bash
unset STRETCH4_RANDOMIZE STRETCH4_PRACTICE_LAYOUT STRETCH4_LOAD_SLOT
unset STRETCH4_HUMAN_CONTACT_FRICTION STRETCH4_GRIPPER_CONTACT_FRICTION STRETCH4_TABLE_CONTACT_FRICTION
cmp src/PhyRC_Sim/Env_Config/Garment/ZeroSceneFriction.py .runtime/PhyRC_Sim/Env_Config/Garment/ZeroSceneFriction.py
umask 027
mkdir -p output/operator-traces output/collections
chmod g+rx output/operator-traces
chmod g+rwx output/collections
```

## 2. 모델과 영상 경로 확인

격리 actor는 저장소에 고정된 Codex CLI 0.166.0으로 모델 ID를 명시한다. 개발자가 접속하는 Codex와 로봇 행동을 만드는 actor는 별도 세션이다. 계정 로그인과 해당 모델 호출을 각각 확인한다.

```bash
npm install --prefix .runtime/codex-0.166.0 @openai/codex@0.166.0
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
codex --version
codex login status
# 로그인이 필요한 서버에서만 실행
# codex login --device-auth
docker pull python:3.12-slim@sha256:4840d514c583a4d3d8cad3940e68dee6f0f6f3635c12fcd0a3d74c21a5b93a54
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -p 'test_segment*.py'
```

`./run.sh smoke`로 실제 GPU에서 `PHYRC-SMOKE-PASS`를 확인한다. 아래 연결 검사는 같은 새 출발 조건에서 실행하고 기술 검사로 기록한다. 새 데이터셋의 본시연은 다음 절의 별도 ID를 사용한다.

```bash
phyrc_probe_id="$(date -u +%Y%m%dT%H%M%SZ)-astra62-wiring"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id "$phyrc_probe_id" --mode wiring --nearest-table --seed 43 \
  --actor-backend exec --model gpt-6.2-astra --effort ultra --plan-size 1 \
  --decisions 3 --max-steps 20 --model-timeout 180
```

기술 검사 결과는 `output/operator-traces/RUN/attempt.json`에서 실제 호출과 마감, `output/collections/RUN/run_metadata.json`의 `collection_start`에서 seed, table_index=2, start_step=0, shirt_manikin_friction=0.35, verified_after_reset=true를 확인한다. 모델 접근 또는 출발 조건에서 실패하면 오류를 기록하고 그 조건을 먼저 해결한다.

## 3. 다음 회차의 검토 화면과 시작

사용자가 새 회차의 목표와 시작을 지시하면 기존 실행과 중복되지 않는 ID로 실행한다. `participant/ops/collect_autonomous.sh NEW_RUN_ID`는 새 장면의 0전이에서 시작하며 공식 50점 또는 사용자 피드백으로 종료한다. 시연 5의 카메라 설명은 `--camera-briefing`, 시연 6의 손목·접근 제한은 `--gentle-wrist-dressing` 옵션이다. 두 옵션은 함께 사용할 수 있다. 구간별 승인을 원하는 경우 사용자 피드백 모드를 쓴다. [GPT 단독 실험](autonomous.md) · [수집과 갤러리 운영](collection.md)

시연 7–13의 본 실행 구성은 `--sol-ultra --camera-briefing`이다. 사용자가 특정 영상 경계를 분기점으로 고르면 종료되고 전수 검증된 원본 수집 기록과 운영 추적을 새 서버로 복원한다. 위의 JPEG 복원 결과와 원본 아카이브의 운영 추적을 같은 `output/operator-traces/RUN`에 서로 다른 파일로 배치한다. 원본의 `output/collections/RUN`과 검증 파일도 필요하다. `--wrist-transfer-from SOURCE_RUN END_STEP`은 원본의 시드와 허용 행동을 사용해 선택 전이까지 재실행한다. `--cover-right-wrist`는 현재의 끝 파지 지시를 선택한다. 재실행은 새 시뮬레이터 관측을 만들므로, 그 지점의 밑단과 손목 관계를 다시 확인한다.

`--segment-review-dir`는 새 출발 검사를 자동으로 켠다. 공식 샘플러로 고정 테이블을 선택하는 seed를 CPU에서 찾고, 실제 장면은 **한 번만** reset한다. 첫 회차의 seed 43은 그대로 사용된다. 다른 연습 seed를 지정해도 같은 테이블에 놓이도록 요청 seed와 실제 seed를 감독 기록에 함께 남긴다. 공식 제출의 초기화 경로는 주최 측의 배치 규칙을 따른다.

새 서버에서 아직 확인할 항목은 실제 모델 권한, 5카메라 입력, 의도한 물리 조건의 장면, GPT의 첫 실제 행동과 구간 영상 게시, 그리고 유효한 최종 점수다. 수집 명령으로 시작한 회차와 점수만 새 데이터셋에 집계한다.
