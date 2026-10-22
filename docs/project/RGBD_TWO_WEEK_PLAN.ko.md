# RGB-D 관측 처리와 VLA 적응: 2주 실행 계획

작성일: 2026-10-22. **오늘은 문서 정리만 수행한다.** 새 클린 서버 작업은 2026-10-23 시작 예정이며, 날짜는 목표 일정이다. 서버 개설 지연 시 D1부터 같은 순서로 이동한다. 이 문서의 목표 수량과 완료 기준은 실험 결과가 아니다.

[README](../../README.ko.md) / [클린 서버 시작](START_HERE.ko.md) / [실제 상태](STATUS.md) / [고정 산출물 복원](RECOVERY.ko.md) / [미해결 작업](TODO.ko.md)

## 1. 목적과 범위

공식 PhyRC 시뮬레이터의 두 Stretch 4를 대상으로 사람 시연을 수집하고, RGB-D 관측의 품질을 확인한 뒤 π₀.₅ 정책을 적응하고 비교한다. 로봇 조작의 첫 구간인 **접근, 의복 집기, 짧게 들어 올리기**부터 시작한다. 두 로봇의 입력과 행동 형식은 유지하되, 초기 시연에서는 각 로봇의 역할을 단순하게 고정한다.

핵심 산출물은 다음과 같다.

| 산출물 | 완료 기준 |
|---|---|
| 사람 시연 데이터 | 실제 원격 키 입력, 정상 종료, READY와 complete, episode 검증 결과 |
| RGB-D 진단 | 영상과 상태의 정합 검사, 의복 mask, 카메라 좌표계의 가시 표면 점군 |
| VLA 적응 | 단일 π₀.₅ LoRA 설정, checkpoint 재로딩, 동일 조건 baseline 비교 |
| 재현과 전달 | 데이터와 모델 revision, 결과 JSON, 원본 영상, 복원 절차, 짧은 시연 영상 |

예상 집중 작업량은 약 60-70시간이다. 설치, export, 학습, 전체 평가의 벽시계 대기는 별도로 잡는다. 단일 L40S에서 수집, 학습, GPU 평가는 순차 실행한다.

전체 착의 성공, 새로운 RL 알고리즘, 여러 VLA 모델 비교, 5개 카메라의 정밀 3D 융합, 실로봇 전이는 이 2주의 필수 완료 조건에 넣지 않는다. 시연과 SFT 기준선을 확보한 뒤 residual policy adaptation 등 후속 연구를 판단한다.

## 2. 현재 구현과 이번 계획의 구분

근거: [2026-10-22 세션 기록](sessions/20261022-bootstrap.md), [STATUS](STATUS.md), [RECOVERY](RECOVERY.ko.md).

| 항목 | 2026-10-22에 확인한 범위 | 다음 검증 |
|---|---|---|
| 공식 환경 | L40S에서 build, prepare, 실제 smoke PASS | 새 클린 서버 복원 |
| 수집 | scripted integration_test 3 episode / 63 transition | 사람 시연, 정상 export, 반복 수집 |
| 브라우저 | viewer와 keyboard 코드 존재 | 실제 Chrome 조작, 키 해제, reconnect |
| 학습 | JAX LoRA 30 update / 0.476 effective epochs | optimizer 재개, 작은 overfit, 유효 시연 학습 |
| 정책 실행 | 공식 이미지 offline load, debug 0점 / no_contact | 고정 조건 rollout과 공식 full self-check |
| 보존 | HF 재다운로드 checksum, CPU state step 30 복원 | 새 서버 GPU에서 재실행 |
| 제출 | ZIP와 fresh-clone 부분 실행 259 action | 전체 검사, 제출 ID와 accepted 확인 |

사람 또는 live GPT 시연은 아직 없다. 기존 63 transition은 학습 경로 연결용이며, 조작 성공 데이터셋으로 바꾸어 표기하지 않는다. 자동 GPT 조작은 기존 설계를 보존하되, 이번 핵심 경로를 막지 않는 선택 확장으로 둔다. 추가 과금 API는 별도 요청 없이 사용하지 않는다.

## 3. 현재 데이터 계약

구현 기준: [policy_interface.json](../../config/policy_interface.json), [preprocessing.py](../../participant/pi05/preprocessing.py), [공식 DATA](../competition/DATA.md).

| 구분 | 현재 값과 의미 |
|---|---|
| 공식 카메라 | overview, robot_0_wrist, robot_1_wrist, robot_0_head, robot_1_head |
| RGB / depth | 카메라별 256×256, uint8 RGB / float32 optical-Z depth(m) |
| 유효 깊이 | invalid depth=0, depth_valid=false. 유효 mask와 함께 처리 |
| 시간 | policy 20Hz, control 60Hz, physics 240Hz. action 하나가 simulation 0.05초 |
| 로봇 관절 관측 | `(2,13)` 위치. 회전과 직선 관절의 단위 및 이름 확인 |
| 공식 행동 | 정규화된 float32 `(2,9)`, 범위 [-1,1]. 저장 시 `(N,18)` |
| 그리퍼 | <-0.5 open, >0.5 close, 그 외 이전 intent 유지. 0은 open이 아님 |
| 현재 정책 영상 | overview와 각 로봇 wrist의 RGB 3개. head RGB와 depth는 미사용 |
| 현재 정책 상태 | 32D = 26 joint positions + 2 fingertip distances + 2 gripper intents + 2 previous grip commands |
| 모델 행동 형식 | 18D에 14D padding, 출력의 첫 18D를 두 로봇 `(2,9)`로 복원 |

32D는 로봇 자유도 수가 아니다. 모델 슬롯의 left_wrist/right_wrist는 한 로봇의 양손목이 아니라 robot_0/robot_1의 wrist에 대응한다. 기존 속도 명령을 position/delta-action으로 임의 변환하지 않는다.

## 4. 작업 A: 기록, 재생, 품질 검증

공식 recorder/exporter를 재사용하고 참가자 검수 도구를 추가한다. 기존 `scripts/inspect_policy_dataset.py`, `scripts/check_deferred_dataset.py`의 실제 CLI는 [DATA](../competition/DATA.md)를 따른다. 다음 산출물 이름은 설계 항목이며 아직 실행 가능한 신규 명령이 아니다.

- `obs[t]`, `action[t]`, `next_obs[t]`의 길이, 순서, boundary와 simulation timestamp 확인.
- action은 t부터 t+0.05까지 적용되고 next observation은 t+0.05에 대응하는지 확인.
- shape, dtype, NaN/Inf, action bounds, 카메라 순서, joint 이름과 단위 검사.
- RGB, depth, state, action을 같은 시간축에서 보는 replay viewer 구성.
- 원본, 제외 구간, 검수 결과를 분리. 저속 구간과 접촉 유지 구간을 일괄 삭제하지 않음.
- `human`, `integration_test` 등 실제 출처 기록. 실패/중단 기록은 그대로 보존.
- episode와 layout/source group 단위로 train/validation 분리. 동일 원본 clip을 양쪽에 섞지 않음.

목표 파일: dataset manifest, episode별 QC JSON/CSV, replay 영상, 제외 사유표. 기존 `capture.json`이 incomplete이면 metadata를 고쳐 유효 시연으로 만들지 않는다.

## 5. 작업 B: RGB-D와 가시 표면 분석

### 오프라인 mask와 점군

1. SAM 2의 첫 프레임 prompt로 의복 mask를 지정하고 영상에서 추적한다.
2. 소수 수동 검수 프레임으로 mask IoU와 가림 이후 재등장을 확인한다.
3. mask를 native 256×256 좌표로 맞춘 뒤 depth_valid와 교차한다.
4. 원본 해상도의 intrinsics K로 카메라 좌표계의 점군을 만든다.
5. 유효 depth 비율, 깊이 분포, mask 이탈과 점군 변화를 기록한다.

```text
X = (u - cx) * Z / fx
Y = (v - cy) * Z / fy
Z = optical-axis depth in metres
```

카메라 optical frame은 X right, Y down, Z forward다. depth를 ray length로 해석하지 않는다. 모델용 224×224 resize와 기하 검수용 원본 좌표를 섞지 않는다. resize가 필요하면 K와 mask도 함께 변환하고 invalid depth를 유효 표면과 평균내지 않는다.

같은 K를 사용한 역투영/재투영 round trip은 구현 점검이며 독립적인 정확도 검증이 아니다. mask의 가시 표면 중심은 의복 전체 중심, 물리적 파지점, 강체 6D pose가 아니다. depth 유효 비율을 calibrated uncertainty로 표현하지 않는다.

### 좌표 변환의 범위

- 필수 범위는 camera-local 점군과 품질 진단이다.
- robot/world frame 확장은 고정 로봇 geometry, 공개 joint state, public base pose로 계산한 FK와 static camera mount를 검증한 뒤 진행한다.
- overview는 human reset에 따라 위치가 달라진다. config의 기준 eye/target을 hidden layout의 실제 world pose로 가정하지 않는다.
- audit의 camera matrix, simulator 내부 link transform, cloth/object ground truth를 정책이나 자동 시연 생성기에 전달하지 않는다.
- `grasp_pose_base`를 wrist camera optical pose로 대체하지 않는다.

SAM 2는 공식 simulator와 분리된 분석 환경에서 실행한다. 이 단계의 사람 prompt 기반 도구를 autonomous online perception으로 쓰지 않는다. depth 진단이 현재 RGB/state 정책 입력에 연결되지 않았다면 정책 성능 향상을 그 모듈의 효과로 주장하지 않는다.

## 6. 작업 C: 시연 학습과 비교 평가

### 데이터 목표

- 짧고 유효한 사람 시연 8-12개와 실패 사례 3-5개를 목표로 한다. 이는 확보한 수량이 아니다.
- 초기 위치와 의복 접근 조건에 작은 변화를 주고, 두 로봇의 역할과 제어 조건을 기록한다.
- 관측 영상에서 의복이 gripper 움직임을 따라 이동하고 잠시 유지되는지 보조 구간 기준으로 판정한다. 내부 grasp anchor flag는 사용하지 않는다.
- 성공/실패 기준을 실험 전에 고정하고 SFT에 포함한 episode와 제외 사유를 남긴다.
- 정규화 통계는 train 데이터만으로 생성한다.

### 단일 학습 설정

1. 복원한 checkpoint에서 optimizer step 30→31을 별도 run으로 확인한다. 원본 checkpoint는 보존한다.
2. 유효한 시연 1-2개로 작은 overfit 시험을 진행한다.
3. 학습 대상 parameter, gradient, 저장 전후 weight, 실제 로드한 checkpoint를 확인한다.
4. 기존 30-step 시험의 warmup=1,000과 데이터 노출을 검토한다. 짧은 학습에 맞춘 schedule은 별도 설정으로 기록한다.
5. 단일 본학습 설정의 중간/최종 checkpoint를 저장하고 공식 이미지에서 재로딩한다.

현재 openpi freeze filter는 LoRA 외 vision/projection parameter도 학습 대상으로 둘 수 있다. [복원 기록](RECOVERY.ko.md)의 trainable count를 확인하고 실제 parameter 목록을 다시 남긴다. 순수 adapter 행렬만 학습했다고 가정하지 않는다. dataloader cursor나 physics의 bitwise 복원도 검증 없이 주장하지 않는다.

### 비교 조건과 지표

같은 adapter, train-derived normalization, controller, action rate, horizon과 시작 조건에서 base π₀.₅와 하나의 LoRA checkpoint를 비교한다. 먼저 같은 seed 3개, 자원에 여유가 있으면 5개로 확대한다. 짧은 구간 비교와 공식 전체 평가를 구분한다. 고정 검증 seed를 학습 튜닝에 반복 사용했다면 held-out test로 부르지 않는다.

| 대상 | 기록할 지표 |
|---|---|
| 데이터 | 검수 통과 episode, 누락/정합 오류, invalid action, 제외 사유 |
| 인식 | 수동 표본 mask IoU, depth valid 비율, 추적 이탈, 대표 영상 |
| 행동 | 보조 구간 완료, raw points, 공식 points/s, full-dressing success |
| 실행 | inference p50/p95, peak VRAM, simulation time, inference time, wall time |
| 학습 | loss, steps, batch size, 처리 샘플 수/effective epochs, checkpoint |

pickup raw milestone과 공식 dressing points/s는 다르다. 집기에 성공해도 points/s는 0일 수 있다. loss 감소만으로 조작 성공을 판단하지 않는다. 실패를 포함해 모든 평가 episode를 보고한다. 적은 seed 수는 초기 기술 검증 범위이며 일반적인 성능 우위를 입증하지 않는다.

## 7. 일정과 완료 기준

| 날짜 목표 | 단계 | 수행 내용 | 다음 단계 조건 |
|---|---|---|---|
| 10/23-24, D1-2 | 복원과 사람 조작 | 최신 문서 확인, 고정 산출물 복원, smoke, 기존 정책 짧은 재실행, Chrome 키 입력 | 사람 시연 1개 정상 export 또는 구체적 blocker |
| 10/25-26, D3-4 | 관측 QC | 시간 정합, replay, depth 역투영 | QC 보고서와 RGB-D viewer |
| 10/27-28, D5-6 | 시각 분석 | SAM 2 mask, camera-local 점군, 정상/가림 비교 | 실제 데이터의 검수 화면 |
| 10/29-30, D7-8 | 데이터 고정 | 시연/실패 수집, 검수, 분할, train 통계 | 버전이 고정된 dataset manifest |
| 10/31-11/01, D9-10 | 모델 적응 | 작은 overfit, 단일 LoRA 설정, 공식 환경 재로딩 | 유효한 정책 행동과 checkpoint |
| 11/02-03, D11-12 | 비교 평가 | 3-5개 동일 seed, 시간/메모리 profiling | 원본 영상과 비교 결과표 |
| 11/04-05, D13-14 | 패키지와 기록 | full self-check, ZIP, 가능 시 Codabench, 복원 기록, 90초 영상 | 재현 절차와 결과, 미해결 항목 |

전체 900초 평가에는 별도 실행 시간을 배정한다. 이전 관측 속도에서 약 3시간이 예상되었으나 새 서버에서 다시 측정한다. 900초는 simulation+inference 예산이며 실제 대기 15분을 뜻하지 않는다. L40S 실행은 RTX 3090 24GB 및 정책 12GB 예산의 하드웨어 검증을 대신하지 않는다.

## 8. 막혔을 때의 우선순위

- D3까지 유효한 사람 시연이 없으면 Chrome/입력/READY를 먼저 해결하고 SFT 범위를 줄인다. 기존 scripted integration data를 사람 시연으로 바꾸지 않는다.
- 좌표/시간/행동 매핑이 맞지 않으면 수집량을 늘리기 전에 수정한다.
- D10에서 행동이 잘못되면 checkpoint, normalization, action 복원부터 확인한다. 학습 step만 늘리지 않는다.
- GPU 메모리가 부족하면 작업을 순차 실행하고 분석 환경을 분리한다. 공식 dependency 교체로 해결하지 않는다.
- Codabench가 열리지 않으면 검증된 ZIP, checksum, 로컬 결과를 보존하고 제출 상태를 미완료로 둔다.
- 양수 점수나 개선이 없으면 그 결과를 보고한다. 구현과 재현성이 확인된 범위는 별도 성과로 정리한다.

## 9. 세션 종료와 지원 자료

[SESSION](templates/SESSION.md), [EXPERIMENT](templates/EXPERIMENT.md) 형식으로 code commit, dirty state, image/asset revision, dataset/model revision, 명령, seed, hardware, 결과와 다음 명령을 연결한다. 실행 후 STATUS와 한국어/영어 README의 검증 범위를 함께 갱신한다.

90초 영상은 과제/관측 20초, RGB-D/mask 25초, 정책 비교 25초, 결과와 한계 20초로 구성한다. 포트폴리오 2장은 실제 데이터 처리 화면과 평가/복원 근거를 담는다. CV에는 완료한 구현만 추가하며, 공식 recorder와 공개 모델을 활용한 통합 기여를 원천 개발과 구분한다.

면접 준비 질문: optical-Z와 invalid depth, 공개 관측으로 가능한 좌표 변환, observation-action 시간 정합, 32D state와 18D action, 학습 loss와 task score의 차이, 새 서버에서의 복원 방법.

## 10. 참고 주소

- 공식 챌린지: https://emprise.cs.cornell.edu/phyrc/challenge-2027/
- 공식 코드: https://github.com/rirolab/PhyRC_2027_Challenge
- 데이터 계약: https://github.com/rirolab/PhyRC_2027_Challenge/blob/main/docs/competition/DATA.md
- 규칙: https://github.com/rirolab/PhyRC_2027_Challenge/blob/main/docs/competition/RULES.md
- 제출: https://github.com/rirolab/PhyRC_2027_Challenge/blob/main/docs/competition/POLICY.md
- openpi: https://github.com/Physical-Intelligence/openpi
- SAM 2: https://github.com/facebookresearch/sam2
- 기존 BEHAVIOR 결과: https://github.com/leonyoon-3dai/behavior-submission-2026
- ROS 2 인터페이스 참고: https://github.com/Holiday-Robot/friday_ros2
- RL 구현 참고: https://github.com/Holiday-Robot/rsl_rl_flashsac

마지막 두 저장소는 기술 연결을 위한 참고다. 전체 재현이나 PhyRC에 그대로 이식하는 작업은 이번 2주 범위에 포함하지 않는다.
