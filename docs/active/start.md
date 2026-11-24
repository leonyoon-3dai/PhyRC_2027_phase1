# 새 서버에서 시연 1–6 복원과 다음 회차 준비

시연 1–6은 종료됐다. 갤러리는 CPU만으로 복원할 수 있다. GPU 시뮬레이터와 행동 모델은 사용자가 다음 회차를 요청할 때 준비한다. [여섯 회차의 비공개 백업 확인서](20261124-private-backup.json)

## 저장소와 지난 갤러리 열기

새 서버에서는 아래와 같이 저장소를 받는다. 이미 clone이 있으면 그 루트에서 복원한다.

```bash
git clone --filter=blob:none --sparse https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git sparse-checkout init --cone
git sparse-checkout set assets config docs/active docs/competition examples participant scripts sitecustomize src tests tools
git rev-parse HEAD
```

리뷰 브랜치를 병합하기 전에 복원하려면 위 checkout에서 `git switch review/20261124-dressing-series-closeout`을 실행한다.

Hugging Face 비공개 데이터셋에 읽기 권한이 있는 계정으로 인증한다. 아래 명령은 여섯 회차가 담긴 SQLite 저널과 각 회차의 검토 ZIP만 고정 revision에서 내려받는다. 회차별 파일과 각 영상의 SHA-256을 확인한 뒤 새 `output/segment-review`를 만든다. 기존 갤러리가 있으면 `--destination`으로 새 경로를 지정하고 게시할 때 같은 경로를 `--review-dir`에 전달한다.

```bash
command -v hf >/dev/null || uv tool install huggingface-hub==2.4.0
hf auth whoami || hf auth login
python3.12 scripts/restore_review_gallery.py --receipt docs/active/20261124-private-backup.json
python3.12 tools/publish_review_gallery.py --review-dir output/segment-review --destination "$HOME" --once
```

Jupyter 파일 루트가 사용자 홈이면 같은 서버의 Brev Jupyter 주소 뒤에 `/view/PhyRC-review.html`을 붙인다. 다른 파일 루트에서는 그 경로를 게시 명령의 `--destination`에 사용한다. 첫 화면에는 시연 6의 마지막 구간이 나온다. 특정 구간의 주소는 `/view/PhyRC-gallery/<run>/<hold>.html`이다. 새 회차를 수집하는 동안에는 같은 게시 명령에서 `--once`를 빼고 상시 실행하면 새로고침할 때 최신 구간이 선택된다.

HDF5·최종 평가·구간 프레임을 분석하려면 확인서의 해당 `run_id`에서 `archive.path`, `review_frames.path`와 SHA-256을 찾는다. `hf download`에 확인서의 `repo_id`, 해당 파일 경로, `--repo-type dataset --revision <revision>`을 지정한다. 내려받은 원본 아카이브는 `python3.12 participant/ops/artifacts.py restore 새_디렉터리 --archive 받은_파일.tar.gz`로 내부 목록과 파일 해시까지 검증하며 복원할 수 있다.

## 1. 환경 준비

다음 회차를 시작할 때는 Ubuntu x86-64, RTX 렌더링을 지원하는 NVIDIA GPU, Docker·NVIDIA Container Toolkit, Node/npm, Python 3.12와 uv, FFmpeg(libx264), `xauth`, `tmux`를 준비한다. Docker의 isolated bridge 기능이 필요하다. [공식 설치 절차와 GPU 요건](../competition/SETUP.md)

```bash
uv venv --python 3.12 .venv
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

`--segment-review-dir`는 새 출발 검사를 자동으로 켠다. 공식 샘플러로 고정 테이블을 선택하는 seed를 CPU에서 찾고, 실제 장면은 **한 번만** reset한다. 첫 회차의 seed 43은 그대로 사용된다. 다른 연습 seed를 지정해도 같은 테이블에 놓이도록 요청 seed와 실제 seed를 감독 기록에 함께 남긴다. 공식 제출의 초기화 경로는 주최 측의 배치 규칙을 따른다.

새 서버에서 아직 확인할 항목은 실제 모델 권한, 5카메라 입력, 의도한 물리 조건의 장면, GPT의 첫 실제 행동과 구간 영상 게시, 그리고 유효한 최종 점수다. 수집 명령으로 시작한 회차와 점수만 새 데이터셋에 집계한다.
