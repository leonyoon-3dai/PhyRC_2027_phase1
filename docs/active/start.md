# 새 서버에서 첫 회차 시작하기

사용자가 README를 리뷰하고 새 서버에서 시작을 지시한 뒤 실행한다. 첫 수집 조건은 **새 장면의 0전이, 세 번째 테이블(+X 중앙), 셔츠–마네킹 마찰 0.35, GPT-6.2 Astra Ultra**다. 개인 시연 백업이나 과거 서버의 세션 복원 없이 시작할 수 있다.

## 1. 환경 준비

Ubuntu x86-64, RTX 렌더링을 지원하는 NVIDIA GPU, Docker·NVIDIA Container Toolkit, Node/npm, Python 3.12와 uv, 호스트의 FFmpeg(libx264)를 준비한다. Ubuntu 패키지로 `ffmpeg`, `xauth`, `tmux`를 준비한다. Docker의 isolated bridge 기능이 필요하다. [공식 설치 절차와 GPU 요건](../competition/SETUP.md)

아래 부분 체크아웃은 시뮬레이터 소스·자산·수집 코드·활성 문서를 받는다. 이전 영상은 열 때 가져올 수 있다. 이미 전체 clone이 있다면 해당 저장소 루트에서 환경 준비로 이어간다.

```bash
git clone --filter=blob:none --sparse https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git sparse-checkout init --cone
git sparse-checkout set assets config docs/active docs/competition examples participant scripts sitecustomize src tests tools
git rev-parse HEAD
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

## 3. 시연 4의 검토 화면과 시작

[시연 4 인계](20261124-handoff.ko.md#새-서버에서-시작하기)에 따라 한 번만 새 실행과 브라우저 갤러리를 준비한다. `--gpt-only`에서는 새 reset 영상을 게시한 뒤 첫 행동부터 GPT가 선택한다. 구간별 승인을 원하는 경우 사용자 피드백 모드를 쓴다. [GPT 단독 실험](autonomous.md) · [실험 계획](experiment.md)

`--segment-review-dir`는 새 출발 검사를 자동으로 켠다. 공식 샘플러로 고정 테이블을 선택하는 seed를 CPU에서 찾고, 실제 장면은 **한 번만** reset한다. 첫 회차의 seed 43은 그대로 사용된다. 다른 연습 seed를 지정해도 같은 테이블에 놓이도록 요청 seed와 실제 seed를 감독 기록에 함께 남긴다. 공식 제출의 초기화 경로는 주최 측의 배치 규칙을 따른다.

새 서버에서 아직 확인할 항목은 실제 모델 권한, 5카메라 입력, 의도한 물리 조건의 장면, GPT의 첫 실제 행동과 구간 영상 게시, 그리고 유효한 최종 점수다. 수집 명령으로 시작한 회차와 점수만 새 데이터셋에 집계한다.
