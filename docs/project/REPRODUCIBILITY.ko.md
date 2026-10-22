# 클린 서버 작업과 실험 재현

2026-10-22 기준 운영 설계입니다. 아직 GPU 서버를 개설하거나 복원 시험을 수행하지 않았습니다. 아래의 자동 설치·백업·재개 도구는 **구현 예정**이며, 존재하는 실행 명령으로 간주하지 않습니다.

첫 목표는 데이터 수집, π₀.₅ 학습, 정책 실행, 제출을 연결하고, 서버를 삭제한 뒤에도 같은 코드와 산출물을 복원하는 것입니다. 착의 성능과 복원 속도는 실제 측정 후 보고합니다.

## 보관 위치

| 위치 | 보관 내용 |
|---|---|
| GitHub | 코드, 설정, 의존성 명세, 작업 상태, 실험 인덱스, 요약 결과, 대표 이미지, 재현 명령 |
| Hugging Face Dataset | 원본 수집 기록, 완결된 `policy.hdf5`, 변환 데이터, 영상, 대용량 로그와 체크섬 |
| Hugging Face Model | 전체 모델 params, tokenizer, 정규화 통계, 설정, 학습 재개용 상태 |
| 서버 로컬 SSD | 다운로드·렌더·학습 캐시와 작업 중인 파일. 유일한 원본을 두지 않음 |

HF 저장소는 연결 계정과 공개 범위를 확인한 후 생성합니다. GitHub와 HF의 링크를 미리 완료된 자산처럼 표시하지 않습니다. 원본 assets와 NVIDIA 이미지의 재배포는 해당 구성 요소의 조건을 따릅니다. [THIRD_PARTY.md](../../THIRD_PARTY.md)

## 실험마다 고정할 정보

모든 run은 UTC 기반의 고유 ID를 사용합니다. 예: `YYYYMMDDTHHMMSSZ-short-name`. 사람이 읽는 요약에는 KST/JST(UTC+9)도 병기하고, 날짜만으로 다른 실행을 덮어쓰지 않습니다.

| 구분 | 기록할 값 |
|---|---|
| 소스 | 참가자 Git commit, upstream commit, dirty 여부, 변경 diff 또는 patch |
| 환경 | GPU·CPU·RAM·SSD, OS, driver, Docker, Python·학습 라이브러리 버전 |
| 이미지·assets | Dockerfile revision, 실제 image digest, `config/assets.lock.json` revision과 검증 결과 |
| 데이터 | HF repo ID와 **불변 commit revision**, episode 목록, 필터, train/validation 분리, 변환 코드 revision |
| 모델 | base 모델 출처·revision, 전체 params checksum, 학습 설정, 정규화 통계, tokenizer·processor 파일 |
| 학습 재개 | optimizer를 포함한 `train_state`, step, RNG, 학습률 상태, 가능한 sampler 상태 |
| 실행 | 정확한 명령, 카메라·state·action schema, chunk 실행 설정, 평가 seed 목록과 종료 조건 |
| 결과 | 원본 결과 JSON, 로그, 영상·대표 프레임, 제출 ZIP checksum과 Codabench ID |

`main`, `latest` 또는 HF 저장소 이름만으로 데이터·모델 버전을 식별하지 않습니다. 사람이 선택한 배치 seed는 재현 기록에 보관하되 정책 입력에는 제공하지 않습니다.

LoRA 학습도 adapter 행렬만 보관하지 않습니다. 실제 학습된 전체 params와 부속 파일을 저장합니다. openpi의 현재 checkpoint 복원은 데이터 로더 cursor까지 복원하지 않으므로, **같은 checkpoint 복원**과 **비트 단위로 동일한 학습 순서 재개**를 구분합니다. 후자가 필요하면 sampler 상태 저장을 추가하고 별도로 검증합니다.

## 작업 시작·재개

1. 최신 작업 상태와 직전 [세션 기록](templates/SESSION.md)을 읽고, 이어갈 단계와 필요한 산출물을 확인합니다.
2. 고정된 Git commit과 환경 명세로 설치합니다. upstream 업데이트는 기존 run에 섞지 않고 변경 내용을 기록한 뒤 검증합니다.
3. 지정한 HF revision의 필요한 파일만 받고 체크섬을 검증합니다. 인증 정보는 별도로 제공하며 저장소에 넣지 않습니다.
4. 공식 `./run.sh doctor`, `build`, `prepare`, `smoke` 경로를 사용합니다. 준비·실행 완료를 로그로 확인하고 `PHYRC-SMOKE-PASS`를 기다립니다.
5. 모델을 로드하고 고정된 허용 관측·RNG에서 출력 shape, 범위, 수치 차이를 확인합니다. 실제 허용 오차와 비교 환경을 기록합니다.
6. 짧은 실행으로 관측·행동·기록 경로를 확인한 뒤 수집·학습·평가를 이어갑니다.

위 명령의 근거는 [공식 설치 가이드](../competition/SETUP.md)입니다. 원격 GUI, Chrome streaming, π₀.₅ 학습과 제출 adapter는 이 fork에서 추가 검증할 대상입니다. GPU·driver가 달라지면 기존 shader cache를 그대로 신뢰하지 않습니다.

## 서버 중단·삭제 전

1. 인간 teleop은 `ESC`로 정상 종료합니다. 창이 닫힌 것만으로 완료로 판단하지 않고 **`[Dataset export] READY`**와 `capture.json`의 `status=ready`, `complete=true`를 확인합니다.
2. episode와 HDF5를 검사합니다. 자동 수집기는 별도 종료·완결성 검증을 구현하며, 기존 deferred 검사까지 자동 지원한다고 가정하지 않습니다.
3. 학습을 중단할 때 추론 파일뿐 아니라 학습 재개용 상태를 저장합니다. 파일 작성 중인 checkpoint를 완결된 모델로 업로드하지 않습니다.
4. GitHub에 코드와 설정을 반영하고, HF에 데이터·모델·영상·로그를 업로드합니다. 반환된 revision, 파일 수·크기와 SHA-256을 확인합니다.
5. [실험 인덱스](../../experiments/README.md), 세션 기록, 현재 상태 문서에 성공·실패와 **다음 실행 명령 및 기대 결과**를 남깁니다.
6. 복원에 필요한 원격 파일을 확인한 뒤 서버를 종료·삭제합니다. 업로드 실패나 불완전 export가 있으면 먼저 복구합니다.

원본 raw archive와 audit 파일은 검증용으로 보관합니다. 학습 loader와 조작 agent에는 허용된 관측·행동만 전달합니다. `obs`와 함께 반환되는 `info` 전체를 전달하지 않습니다. [데이터 가이드](../competition/DATA.md) · [규칙](../competition/RULES.md)

## 시간을 나누어 기록

| 시간 | 용도 |
|---|---|
| Wall time | 서버 과금, 사람 작업, 다운로드, compile, export, 학습, API 대기, 평가, 업로드 시간 |
| Simulation time | 행동·영상·상태 정렬. 정책 20Hz, 제어 60Hz, physics 240Hz |
| 공식 score 시간 | 최초 shirt–manikin 접촉부터 마지막 착의 점수 획득까지의 simulation time |
| Episode budget | 공식 평가에서는 simulation time에 policy call의 실제 추론 시간을 더함 |

서버 발급부터 첫 smoke, 첫 모델 로딩, 첫 유효 rollout까지의 시간을 각각 측정합니다. 첫 compile과 정상 학습 step 시간, checkpoint 저장·업로드 시간을 분리해 복원 속도의 병목을 찾습니다. 서버 요금은 선택한 인스턴스의 실제 요율과 사용 시간으로 계산합니다.

## 결과와 시각적 증거

- `raw_points`, pickup 제외 `rate_points`, `points/s`, `success`, 유효성, 실패 상태를 함께 남깁니다. 집기 5점은 양수 points/s를 뜻하지 않습니다.
- 고정한 같은 배치·예산에서 기준선과 변경 모델을 비교합니다. 실패한 seed를 제외하지 않고, 짧은 디버그 실행과 공식 조건 평가를 구분합니다.
- 영상에는 run ID, 카메라 이름, simulation time과 실제 재생 속도를 표시합니다. 시작·milestone·실패 시점 프레임을 원본 영상의 timestamp와 연결합니다.
- 데이터 episode 수, 처리 샘플 수, effective epochs, 학습 step 수를 함께 기록합니다. 데이터만 늘리고 학습 노출량이 줄어드는지 확인합니다.
- GPU 사용률·VRAM, CPU 코어별 사용률·RAM·I/O, real-time factor, 추론 지연을 기록합니다. GPU 증설은 병목 측정 후 결정합니다.

공식 점수의 근거는 [EVALUATION.md](../competition/EVALUATION.md), 제출 제약은 [POLICY.md](../competition/POLICY.md)를 따릅니다.

## 공개 기록 원칙

`planned`, `implemented`, `measured`, `verified`를 구분하고 근거 링크를 붙입니다. 초기에는 실행 결과가 없음을 명시합니다. Codabench **accepted는 업로드·형식 승인 상태**이며 착의 성공, leaderboard 점수 또는 주최 측의 최종 검증을 뜻하지 않습니다.

성공 사례뿐 아니라 실패 원인과 다음 가설을 공개합니다. 기존 원본과 제출 ZIP을 덮어쓰지 않고 후속 revision으로 수정합니다. 공식 시연, 자체 인간 시연, GPT 조작, 학습 정책 rollout을 구분해 작성자의 성과를 과장하지 않습니다.

공개 문서에는 토큰·SSH key·로그인 세션·인증 cookie를 포함하지 않습니다. 실험 이해에 필요한 사실은 공개하되 접속 자격 증명과 재사용 가능한 인증 URL은 제외합니다.
