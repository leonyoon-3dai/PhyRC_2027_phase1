# PhyRC 2027 Phase 1

[![Original README - 공식 참가 가이드](docs/project/assets/original-readme-button.svg)](README.upstream.md)

**RGB-D 관측 처리와 VLA 적응을 활용한 두 Stretch 4의 협동 착의 연구.**

Leonard Yoon, Ph.D. | 윤영호 | 독립 연구 프로젝트  
[English](README.md) / [현재 상태](docs/project/STATUS.md) / [클린 서버 시작](docs/project/START_HERE.ko.md) / [실행 스프린트](docs/project/ENGINEERING_SPRINT.ko.md) / [기술 증거](docs/project/EVIDENCE_MAP.md)

공식 PhyRC Isaac Sim 환경에서 시연 수집, 관측과 행동 검증, π₀.₅ 적응, 정책 평가와 제출 자료 보존을 연결합니다. 저장소만으로 작업의 상태와 근거를 확인하고 새 서버에서 이어갈 수 있도록 기록합니다.

> **2026-10-23 실행 종료:** 사용자 요청으로 테스트를 중단하고 다음 클린 서버를 위한 자료를 보존합니다. 클린 서버 복원·공식 smoke·Chrome 키보드/이동·최소 사람 이동 샘플의 포맷은 검증했습니다. **전체 900초 검사 미완료, Codabench 미제출, 착의 성공 없음.** 실작업 시연 수집과 새 학습은 보류합니다.

## 10월 23일 클린 서버 결과와 인계

상세 근거: [오늘 세션 기록](docs/project/sessions/20261023-clean-start.md) · [현재 상태](docs/project/STATUS.md) · [다음 서버 시작](docs/project/START_HERE.ko.md).

| 항목 | 실제 결과 |
|---|---|
| 서버 | L40S 46,068 MiB ×1, Xeon Platinum 8452Y 12 vCPU, RAM 약 70 GiB, Ubuntu 22.04.5, driver 580.126.09 |
| 실행 코드 | 현재 작업 시작 `5a2ab4ec2b47d907198a171da35c17364e8a185c`; 공식 upstream `4dbbebcf93a06c1bfe12136eadc2e580f30125d6` |
| 복원 | 기존 데이터·전체 모델/train state·제출 ZIP의 고정 revision 다운로드와 checksum 통과. 새 학습·optimizer 재개는 하지 않음 |
| 공식 환경 | build 218.53초, prepare 9.14초, smoke 367.80초. 실제 `PHYRC-SMOKE-PASS`와 exit 0 |
| 정책 실행 | 추가 패키지 이미지 build 68.40초; 짧은 offline 실행 91.11초, 한 번의 action/시뮬레이션 0.05초, 0점·no_contact |
| 복원 총시간 | KST 13:04경 시작, 13:16 공식 환경 검증, 13:18 Chrome 준비. 기본 환경 약 10분, 정책/조작 준비까지 약 14–15분. 다운로드·일부 build 병렬; 각 시간을 단순 합산하지 않음 |
| Chrome | 사용자가 키보드와 로봇 이동 정상 확인. 우하단 13px 동작/키 표, 누른 키·서버 수신/왕복 지연·포커스 해제 표시 추가. 전체 reconnect/gripper checklist 완료를 주장하지 않음 |
| 사람 원본 | ESC 정상 종료, 2,419 transition/120.95 simulation seconds, 수집 wall 1,172.86초, raw capture complete=true |
| 최소 포맷 샘플 | 이미 렌더링된 앞부분에서 이동 입력과 공개 joint/base 변화를 함께 확인한 연속 3구간, 12 transition/0.6초. 전체 이동 구간 314개를 모두 추출한 자료는 아님 |
| 샘플 검사 | 원본 public state/action 일치, 5 RGB-D 카메라 유효성, obs/action/next_obs 연속성, 20Hz, 공식 PolicyDataset 로딩 통과 |
| 전체 export | 긴 대기 때문에 364 transition의 렌더링 prefix 이후 의도적으로 중단. 원본은 유지. 전체 dataset을 READY로 바꾸지 않았으며, 별도 파생 샘플만 완결 검증 |
| 900초 self-check | fresh clone에서 시작 후 사용자 요청으로 중단. **1,460 action/시뮬레이션 73.0초**, 전체 wall **1,814.08초(30분 14초)**. 유효한 최종 점수·통과 없음 |
| 종료 상태 | 평가 GPU 프로세스와 viewer HTTP server 중단, GPU 0 MiB 확인. 서버 자체의 전원 종료·삭제는 수행하지 않음 |

사람 샘플의 출처는 `human`, 목적은 `teleoperation_format_test`, 검수 상태는 `format_only_not_for_sft`입니다. 실제 사람이 입력한 자료지만 **옷 집기/착의 전문가 시연이나 학습 승인 데이터가 아닙니다.** 별도 audit/raw의 privileged state는 정책 입력으로 사용하지 않습니다. 오늘 새 SFT나 성능 비교는 하지 않았습니다.

### 느린 실행과 900초의 의미

공식 주기는 **시뮬레이션 기준** 정책 20Hz/제어 60Hz/물리 240Hz이며, action 하나가 0.05초와 물리 12 step에 해당합니다. 실제 화면/실행이 20 FPS여야 한다는 조건으로 해석하지 않습니다. 공식 runner의 예산은 `누적 simulation seconds + 누적 policy-call wall seconds`입니다. 환경의 물리/렌더링 wall time은 이 합산에 포함되지 않으므로 실제 15분보다 훨씬 오래 걸릴 수 있습니다. [공식 정책/시간 규정](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/docs/competition/POLICY.md)

실측 중 한 지점에서 simulation 19.85초에 평가 wall 379.6초, 이후 simulation 54.85초에 wall 993.5초였습니다. 따라서 당시 평균은 simulation 1분당 실제 약 18–19분입니다. 첫 정책 compile도 포함하며, 고정 처리량의 warm benchmark는 아닙니다. 누적 추론 시간을 별도로 기록하지 않아 **중단 시 900초 예산을 정확히 몇 초 소비했는지는 알 수 없습니다.** 시뮬레이션 73초를 900초 전체 진행률로 쓰지 않습니다. 이전 약 3시간 예상과 이후 약 4시간 15분 보수적 환산은 완료 실측이 아니며, 다음 서버의 ETA로 재사용하지 않습니다.

10초/20Hz py-spy 샘플링(메인 스레드 199개 샘플)은 공식 평가·접촉 계산 41.2%, 물리·제어 39.2%, 카메라 16.1%, 추론 3.5%였습니다. 짧은 구간의 스택 점유 비중이며 정확한 component timer/전체 평균은 아닙니다. 코드에는 매 물리 step의 평가와 GPU→CPU 상태 복사, 5 RGB-D 카메라 동기 렌더링이 있습니다. CPU 순차 처리와 동기화가 유력한 병목 후보이며, GPU 성능 부족으로 단정하지 않습니다.

당시 GPU 약 39%/17,446 MiB/38°C, P0, active thermal/power slowdown 없음; RAM available 약 49 GiB; swap/I/O wait/CPU steal 거의 없음; container CPU·RAM quota 제한, throttling/OOM 없음. 전체 12 vCPU 중 프로세스의 2초 표본 CPU 사용은 약 2.19코어였습니다. VRAM 17GB는 simulator+policy 합계이므로 **정책 12GB hard cap, 심사 RTX 3090 호환성을 증명하지 않습니다.**

### 다음 클린 서버에서 할 일

1. 이 README와 [오늘 보고서](docs/project/sessions/20261023-clean-start.md), `AGENTS.md`, STATUS를 먼저 읽고 [복원 명령](docs/project/RECOVERY.ko.md)을 따릅니다. 아래 과거 스프린트 목표보다 이번 사용자 범위가 우선합니다. **옷 집기 시연·새 학습을 자동 시작하지 않습니다.**
2. 고정 자료를 복원하고 공식 smoke와 짧은 offline 경로부터 확인합니다. 사람 조작 서버/IP는 새로 설정하며 공개 저장소에 주소·토큰을 남기지 않습니다.
3. 장시간 검사 전에 warm-up을 분리한 고정 100–200 step의 짧은 진단을 준비합니다. simulation seconds, policy-call time, 환경 처리 wall, 실제 총 wall, compile, GPU 메모리를 각각 기록합니다. 이 진단을 공식 self-check 통과로 표현하지 않습니다.
4. 스레드 수/CPU affinity/NUMA와 cache 재사용은 후보이며 **아직 적용·효과 검증하지 않았습니다.** 더 많은 RAM/GPU나 CPU 코어가 해결책이라는 근거는 없습니다. 짧은 동일 조건 비교부터 합니다. 물리 주기·solver·형상·평가기·센서 정렬을 바꿔 빠르게 통과시키지 않습니다.
5. 전체 900초 검사는 실행 코드·ZIP·image·예상 wall 예산을 명시한 뒤 별도 슬롯에서 수행합니다. 오늘 helper는 **역사적 simulator `9d97807`**을 선택했습니다. 현재 main 전체 검사가 아닙니다. 새 main을 검사하려면 helper의 source/base 선택을 명시적으로 수정하고 확인해야 합니다.
6. Codabench는 서버와 사용자 Mac 모두 접속 불가였으며 사용자 요청으로 후속 확인을 보류했습니다. 로컬 통과와 실제 업로드/접수/주최 측 점수를 분리합니다.

이미 검증된 최소 샘플은 다음과 같이 복원할 수 있습니다.

```bash
hf download leonayoon/phyrc-2027-phase1-data --type dataset \
  --revision c31241f626c4cbf02c2bd69a10f70a3841fa58a3 \
  --include 'samples/20261023-human-motion-format-test/*' --local-dir output/recovered-human-sample
.venv/bin/python participant/ops/artifacts.py verify \
  output/recovered-human-sample/samples/20261023-human-motion-format-test
```

[E0 복원 근거](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/2234dfd306df355bf8a9f879b6b3aaae4c3b56f8/sessions/20261023-clean-start-e0) · [최소 사람 이동 샘플](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/c31241f626c4cbf02c2bd69a10f70a3841fa58a3/samples/20261023-human-motion-format-test) · 최종 원본/중단 로그 보존 revision과 정확한 복원은 [세션 기록](docs/project/sessions/20261023-clean-start.md)을 확인합니다.

최종 보존: [원본 조작 기록·중단 export archive](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/32fc6d21c5d358caefd17c6aadfc4f25a843e368/captures/20261023-human-source) · [중단된 900초 검사·성능 진단·소스 snapshot](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/93753f568811c5cfcd0235f5d8cb9940c5ce6a23/sessions/20261023-final-evidence). 원본 archive SHA256: `94dfa0238bfab003c255ea6d48f64e7b4b15e9e0e92293e5a360210514a47bd1`. 접속 주소는 보존용 manifest에서만 제거했고 원본 chunk/scene/event bytes는 유지했습니다. 재다운로드/restore 확인 결과와 명령은 세션 보고서에 기록합니다.

원본 archive도 HF 재다운로드→새 디렉터리 restore→샘플 재생성을 완료했으며, 기존 샘플의 public HDF5 배열 **171개가 모두 정확히 일치**했습니다. 이는 같은 서버의 원격 왕복 복원 검사이며, 또 다른 클린 서버 GPU 검증은 아닙니다.

## 다음 클린 서버에서 시작하는 순서

`AGENTS.md`, [STATUS](docs/project/STATUS.md), [START_HERE](docs/project/START_HERE.ko.md), [실행 스프린트](docs/project/ENGINEERING_SPRINT.ko.md)을 먼저 읽습니다. 시작 가이드에 실제 존재하는 명령, 첫 세션의 완료 기준, **Codex에 붙여넣을 인계문**이 있습니다.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git rev-parse HEAD
# 위 문서를 읽고 서버 상태를 확인한 뒤:
participant/ops/bootstrap.sh --check
```

다음 세션은 새 서버 점검, 고정 자료 복원, 공식 smoke, 짧은 정책 실행과 고정 step 성능 진단에 집중합니다. 사람 실작업 시연 수집과 새 학습은 사용자 준비 전까지 보류합니다. 수집, 학습, GPU 평가는 순차 실행합니다. 복원 문서의 과거 commit으로 이동하기 전에 최신 인계 문서를 읽고 실행 revision을 기록합니다.

## 현재 확인한 결과

2026-10-22, L40S 1대, 12 vCPU, 약 70 GiB RAM에서 측정했습니다. 근거: [첫 세션 기록](docs/project/sessions/20261022-bootstrap.md).

| 항목 | 검증 범위 |
|---|---|
| 공식 환경 | build, prepare, 실제 `PHYRC-SMOKE-PASS` |
| 동기화 기록 | scripted 3 episode / 63 transition / 5 RGB-D 카메라, schema와 연속성 검사 |
| π₀.₅ 학습 | JAX LoRA 설정, 30 update / 0.476 effective epochs. 과적합 미확인 |
| 오프라인 실행 | 공식 이미지에서 로딩과 debug 실행, **0점 / no_contact** |
| 보존과 복원 | HF 데이터, 전체 모델/학습 상태, ZIP와 근거 보존. 재다운로드 checksum, CPU step 30 복원 |
| 제출 경로 | 새 clone에 ZIP을 풀어 build와 259 action 실행. **전체 900초 검사 미완료, 미제출** |

데이터는 추가 API 과금 없이 **Codex가 작성한 제한된 고정 명령**으로 수집했고 `integration_test`로 표시했습니다. 사람 또는 live GPT 시연이 아닙니다. 착의 성공이나 정책 성능 향상을 확인한 결과로 쓰지 않습니다. 현재 freeze filter에는 vision/projection 학습 대상도 포함되므로 작은 LoRA 행렬만 학습했다고 표현하지 않습니다.

![실제 recorder 시험의 지정 overview 카메라. 착의 성공 결과 아님](docs/project/assets/first-recorder-test.png)

[실제 3시점 시험 영상](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/resolve/da172805036d5e53daf1834f32baf367820f9183/derived/20261022T0409Z-integration/integration-public-cameras.mp4) / [데이터](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data) / [모델과 학습 상태](https://huggingface.co/leonayoon/phyrc-2027-phase1-pi05) / [고정 복원 자료](docs/project/RECOVERY.ko.md)

## 10월 23–28일: 작은 실험 하나를 완결하기

**실제 사람 수집 → 데이터 검수 → π₀.₅ SFT → 동일 조건 rollout**을 먼저 연결합니다. 날짜·수량은 목표입니다. D0는 사용자가 클린 서버를 실제로 여는 날이며, 10월 23일 개설을 가정하지 않습니다.

| 증거 | 작업 범위 | 완료 기준 |
|---|---|---|
| E0 · 복원 | 고정 자료, 공식 smoke, 짧은 offline 실행 | 새 서버 로그·checksum·복원 시간 |
| E1 · 사람 수집 | Chrome 입력/export 검증, 유용한 짧은 시연 3–5개와 실패 1–2개 목표 | 실제 사람 출처, READY/complete, 검수 데이터 |
| E2 · 데이터와 기하 | 20Hz 정렬, 단위, 유효 depth, camera-local 점군 | QC 보고서, 검수한 RGB-D 사례 2–3개 |
| E3 · 적응과 비교 | 소량 인간 데이터 overfit, 단일 SFT, base/학습 정책 비교 | 재로딩 checkpoint, 같은 practice seed 3개와 실패 포함 결과 |

| 목표 날짜 | 우선순위 |
|---|---|
| 10/23–24, 서버가 준비되면 | E0와 유효한 첫 사람 시연 |
| 10/25 | 데이터 QC와 작은 camera-local RGB-D 진단 |
| 10/26–27 | 사람 데이터 SFT와 짧은 paired 평가, 새 기능 추가 중단 |
| 10/28 | 결과·60–90초 영상·한계·복원 절차 고정 |
| 10/29 이후 | 전체 900초 검사, 제출, 착의 성능 연구 |

집중 작업 **12–18시간에 다운로드·build·compile·export·GPU 대기는 별도**로 측정합니다. 서버 개설이 늦어지면 범위를 줄입니다. Chrome 수정은 우선 2시간으로 제한하고, 막히면 실패 근거를 남긴 뒤 다른 원격 데스크톱 경로를 검토합니다. SAM 2, GPT 자동 조작, FK/IK 확장은 선택 작업입니다.

사람 SFT 전에 loader에 실제 인간 검수 상태를 명세하고 짧은 학습용 LR schedule을 설정해야 합니다. 신규 인간 데이터 학습은 `pi05_base`에서 시작하고 기존 integration checkpoint는 보존합니다. 새 패키지 검사 시 self-check의 역사적 고정 commit과 실제 검사 source를 구분해야 합니다. 이번 문서 갱신에서 코드를 고친 것은 아닙니다.

RGB-D는 우선 **오프라인 진단**입니다. 현재 정책은 RGB 3개와 로봇 상태만 읽습니다. Depth 진단 추가만으로 정책 향상을 주장하지 않습니다. 먼저 두 로봇 인터페이스를 유지하며 접근·집기·짧게 들기를 다룹니다. 전체 착의와 양수 points/s는 다음 성능 목표입니다.

상세 범위: [엔지니어링 스프린트](docs/project/ENGINEERING_SPRINT.ko.md) · [기술 증거와 성과 표현](docs/project/EVIDENCE_MAP.md). 이전 [2주 계획](docs/project/RGBD_TWO_WEEK_PLAN.ko.md)은 보존본이며, 그 일정과 60–70시간 범위는 현재 실행 기준이 아닙니다.

## 데이터와 정책의 현재 형식

| 구분 | 현재 구현 |
|---|---|
| 공식 영상 | overview, robot_0/robot_1 wrist, robot_0/robot_1 head. 원본 256×256 RGB-D |
| Depth | 광축 Z 방향 거리(m), invalid=0과 `depth_valid=false` |
| 정책 영상 | overview와 각 로봇 wrist RGB 3개. depth와 head는 미사용 |
| 정책 상태 | 32D: joint 위치 26 + 손끝 거리 2 + gripper intent 2 + 이전 grip 명령 2 |
| 행동 | 18개 정규화 명령을 모델용 32D로 padding 후 `float32 (2,9)` 복원 |
| 시간 | policy 20Hz, control 60Hz, physics 240Hz. 행동 하나는 simulation 0.05초 |

32D는 로봇 자유도 수가 아닙니다. 그리퍼 0은 이전 의도 유지입니다. RGB-D 분석은 camera-local에서 시작하며, robot/world 변환은 공개 상태의 FK와 static calibration을 검증한 뒤 확장합니다. audit camera matrix, cloth 정답, 물체 pose, seed와 내부 상태를 정책 입력에 사용하지 않습니다.

근거: [DATA](docs/competition/DATA.md), [RULES](docs/competition/RULES.md), [interface 설정](config/policy_interface.json), [공통 전처리](participant/pi05/preprocessing.py).

## 실행과 평가 원칙

- 공식 물리, 행동 제한, reset, evaluator를 유지합니다. SAM 2 분석, JAX 학습, 공식 simulator 환경을 분리합니다.
- base 모델을 보존하고 seed, controller, action rate, adapter, 정규화와 horizon을 맞춰 비교합니다. loss, 구간 성공, raw points, points/s, 전체 착의 성공을 구분합니다.
- 집기에 성공해도 dressing points/s는 0일 수 있습니다. 실패 rollout을 포함하고 평가 표본 수를 함께 적습니다.
- 전체 900초 검사는 simulation+inference 예산입니다. 이전 관측 속도에서는 실제 약 3시간을 예상했으며 새 서버에서 다시 측정합니다.
- L40S 실행은 심사 RTX 3090 24GB와 정책 12GB 예산의 검증을 대신하지 않습니다. 모델, tokenizer, 정규화, 코드를 포함해 offline으로 로드해야 합니다.
- 제한된 Codex/GPT 자동 수집은 선택 확장으로 보존합니다. 추가 과금 API를 계획하지 않으며 주최 측 승인으로 표현하지 않습니다.
- 서버 종료 전 원격 산출물을 검증합니다. 추가 서버 개설과 서버 종료/삭제는 별도 사용자 요청 없이 수행하지 않습니다.

이번 스프린트의 데이터·검수·학습·평가 도구를 그대로 이어 첫 소매 삽입 등 반복 가능한 착의 진행을 목표로 합니다. 기존 내부 제출 목표 11월 16일, 첫 checkpoint 11월 17일은 향후 일정으로 유지합니다.

## 문서 안내

| 문서 | 내용 |
|---|---|
| [START_HERE](docs/project/START_HERE.ko.md) | 현재 클린 서버 진입점과 Codex 인계문 |
| [실행 스프린트](docs/project/ENGINEERING_SPRINT.ko.md) | 현재 우선순위, 일별 기준, 범위 제한과 평가 |
| [기술 증거](docs/project/EVIDENCE_MAP.md) | 엔지니어링 역량, 검증한 주장, 포트폴리오 갱신 |
| [이전 2주 계획](docs/project/RGBD_TWO_WEEK_PLAN.ko.md) | 새 스프린트로 대체된 과거 일정 보존 |
| [STATUS](docs/project/STATUS.md) | 실제 검증과 미해결 항목 |
| [RECOVERY](docs/project/RECOVERY.ko.md) / [TODO](docs/project/TODO.ko.md) | 고정 HF revision, 실제 명령, 남은 작업 |
| [TELEOP](docs/project/TELEOP.ko.md) | 사람 조작과 제한된 AI 수집 설계 |
| [실험 기록](experiments/README.md) | 세션/실험 템플릿과 run 인덱스 |
| [초기 계획 보존본](docs/project/PLAN.ko.md) | 첫 구현 이전의 설계 이력 |
| [출처와 버전](docs/project/SOURCES.md) | 검토한 공식 자료와 revision |

## 과제와 원본 기여

<details>
<summary>주최 측 협동 착의 시연</summary>

![주최 측 teleoperation 시연. 본 프로젝트의 정책 성과 아님](docs/videos/Back_Front_32x.gif)

두 Stretch 4가 앉은 마네킹에 티셔츠를 입히는 공식 시연이며 32배속입니다. 본 저장소에서 학습한 정책의 결과가 아닙니다.

</details>

이 저장소는 Leonard Yoon의 개인 참가 프로젝트이며 주최 측 공식 저장소가 아닙니다. [원본 README](README.upstream.md)는 upstream `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`의 가이드를 보존합니다. 공식 시뮬레이터, 자산, 평가와 시연의 기여는 원저자에게 있습니다. [LICENSE](LICENSE), [NOTICE](NOTICE), [THIRD_PARTY.md](THIRD_PARTY.md)를 따릅니다.

공식 챌린지: https://emprise.cs.cornell.edu/phyrc/challenge-2027/  
공식 코드: https://github.com/rirolab/PhyRC_2027_Challenge  
Codabench: https://www.codabench.org/competitions/18366/  
기존 BEHAVIOR 프로젝트: https://github.com/leonyoon-3dai/behavior-submission-2026
