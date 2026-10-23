# 로봇 학습 엔지니어링 스프린트

갱신일: **2026-10-23**. 검토한 코드·문서 snapshot은 `ee7e8912a653855a862ae9bcb8372c2b357aae7e`다. 공개 실험 계획이며, 아래 목표 수량·시간·날짜는 실행 결과가 아니다. 이번 갱신에서는 서버·데이터·정책을 실행하지 않았다.

[현재 상태](STATUS.md) · [새 서버 진입점](START_HERE.ko.md) · [산출물 복원](RECOVERY.ko.md) · [기술 증거](EVIDENCE_MAP.md) · [기술 TODO](TODO.ko.md) · [이전 계획 보존본](RGBD_TWO_WEEK_PLAN.ko.md)

## 1. 짧은 실험을 먼저 완결한다

10월 23–28일에는 **복원 → 실제 사람 시연 → 데이터·기하 검수 → 작은 π₀.₅ SFT → 동일 조건 rollout**을 우선한다. 10월 28일에는 결과·한계·재현 자료를 고정한다. 전체 착의와 양수 points/s는 이 스프린트의 필수 조건이 아니다.

**D0는 소유자가 다음 클린 서버를 실제로 연 날**이다. 10월 23일에 서버를 열었다고 가정하지 않는다. 날짜가 늦어지면 동일 순서를 유지하고 실험 규모를 줄인다. 후반 날짜에 맞추려고 검증을 생략하거나 예정 기능을 완료로 표시하지 않는다.

기존 [2주 계획](RGBD_TWO_WEEK_PLAN.ko.md)의 RGB-D 진단·학습·평가를 모두 확대하기보다, 실제 자료로 작은 실험 하나를 끝내고 확장한다. 단일 L40S에서 GPU 수집·학습·평가는 순차 실행한다. 집중 작업 예산은 **12–18시간**을 제안하며 다운로드·빌드·compile·export·학습·평가 대기는 별도 측정한다. 이는 새 서버의 실측 완료 시간이나 과금 견적이 아니다.

## 2. 출발점과 구현 전 수정할 항목

실제 근거는 [2026-10-22 세션](sessions/20261022-bootstrap.md), [측정 기록](sessions/20261022-bootstrap-metrics.json), [복원 문서](RECOVERY.ko.md)에 있다.

| 현재 자료·코드 | 이번 스프린트에서의 처리 |
|---|---|
| scripted `integration_test` 3 episode / 63 transition | 통합 fixture로 보존한다. 사람 시연·성공 데이터로 이름을 바꾸지 않는다 |
| 30-update checkpoint, 0.476 effective epochs | 복원과 optimizer step 30→31 시험에 사용한다. overfit·착의 expert로 취급하지 않는다 |
| [Episodes loader](../../participant/pi05/data.py)는 `review=approved_pipeline_test`만 허용 | 사람 데이터용 검수 상태와 목적을 새로 명세하고 loader 허용 조건·manifest·검증을 함께 수정한다. 사람 데이터를 기존 fixture 상태로 위장하지 않는다 |
| 기존 30 steps에 기본 warmup 1,000 | [학습 설정](../../participant/pi05/config.py)의 실제 LR schedule을 확인하고, 짧은 학습에 맞는 별도 설정을 기록한다. 사용한 step별 LR·학습 대상·가중치 변화로 유효 update를 확인한다 |
| [selfcheck helper](../../participant/ops/selfcheck.sh)는 checkout을 `9d97807`로 고정 | 역사적 ZIP 재현과 새 패키지 검사를 구분한다. 새 검사에는 선택한 source/base commit·ZIP·image를 명시적으로 연결하고 실제 검사 대상을 확인한다 |
| 현재 정책은 RGB 3개 + public state 32D | depth 진단을 추가한 것만으로 RGB-D 정책 학습이나 성능 개선을 주장하지 않는다 |

사람 데이터 SFT는 **`pi05_base`에서 새 run**으로 시작한다. 기존 integration checkpoint와 원본 train state는 보존한다. train-only 정규화, dataset revision, base model revision, 학습된 parameter 목록을 기록한다. 32D 상태는 로봇의 자유도 수가 아니며, 18D 행동을 임의의 position/delta-action으로 변환하지 않는다.

## 3. P0: 네 가지 증거 묶음

| 실험 | 할 일 | 완료 증거 | 집중 작업 예산 제안 |
|---|---|---|---|
| E0. 새 서버 복원 | 고정 자료 checksum, 공식 smoke, offline 정책 짧은 실행. optimizer step 재개는 별도 선택 run | 환경·revision·원본 로그·복원 시간·checkpoint step | 1–2시간 + 다운로드·빌드·compile 대기 |
| E1. 실제 원격 수집 | Chrome 입력·release·numpad·ESC 검증, 짧은 인간 시연과 실패 수집 | 실제 사용자 입력 영상, READY/complete, public HDF5, 출처와 검수표 | 3–4시간 + export 대기 |
| E2. 동기화·RGB-D 기하 | 실제 수집 자료의 obs/action/next_obs 정렬과 camera-local depth 검수 | QC JSON/CSV, 동일 시점 RGB·depth·가시 표면 점군, 오류 사례 | 2–3시간 |
| E3. 작은 SFT·paired 평가 | 사람 데이터 overfit 확인, 하나의 LoRA 설정, base와 학습 정책의 같은 3개 practice seed 짧은 실행 | loss·LR·노출량·checkpoint, 전체 rollout 결과, 성공·실패 원본 영상 | 3–5시간 + 학습·평가 대기 |

나머지 3–4시간은 문제 수정·산출물 저장·짧은 보고서에 배정한다. 예산을 초과하면 선택 확장을 줄인다. 완결된 실패·진단 보고서도 결과이며, 시간 제한을 피하려고 물리나 evaluator를 바꾸지 않는다.

### E0. 설치를 반복하지 않고 복원 근거를 남긴다

[START_HERE](START_HERE.ko.md)에서 실제 서버·checkout·인증 상태를 조사하고 [RECOVERY](RECOVERY.ko.md)의 고정 자료를 구분해 복원한다. 같은 서버 새 디렉터리에서 통과한 것을 새 클린 서버 통과로 표시하지 않는다.

복원 시간은 download, dependency/build, shader/compile, model load, smoke로 나눈다. 선택적인 optimizer 재개 시험은 원본 step-30 checkpoint를 보존하고 새 output에서 30→31을 확인한다. 모델·optimizer state 복원, data-loader 순서 복원, physics solver의 비트 단위 복원은 서로 다른 주장이다.

### E1. 짧은 실제 사람 시연부터 확보한다

첫 수집은 두 로봇 조작과 정상 export가 목표다. 이어 접근·집기·짧게 들기를 시도한다. 목표는 **실제 시연 3–5개, 실패 1–2개**이며 확보량이 아니다. 같은 원본·수정 clip은 같은 source group에 둔다. 학습용 recording과 별도 검수용 recording을 구분해 무작위 프레임 분할을 피한다.

Chrome 화면 표시, 실제 키 입력, 데이터 저장을 각각 검증한다. Chrome 수정에 첫 2시간을 사용해도 실제 조작이 되지 않으면 원인·재현 로그를 보존하고 GPU 원격 데스크톱 등 다른 경로로 수집을 진행한다. 대체 경로의 성공을 Chrome 성공으로 바꾸지 않는다.

사람 시연은 새로운 검수 상태와 포함 사유를 기록하고 loader가 그 목적을 명시적으로 허용하게 한다. 실패 데이터는 분석용으로 보존하며 초기 SFT에 자동 혼합하지 않는다. `complete=false`를 수동 수정하지 않는다. GPT 수집은 기존 도구 설계를 유지하되 이 핵심 경로를 막지 않는 선택 작업이다. 추가 유료 API는 별도 요청 없이 사용하지 않는다.

### E2. camera-local RGB-D는 작은 필수 작업으로 끝낸다

필수 범위는 실제 자료의 2–3개 대표 시점에서 다음을 확인하는 것이다.

- 20Hz의 `obs[t] → action[t] → next_obs[t]`, 카메라 순서·joint 단위·행동 범위·reset boundary를 검사한다.
- native 256×256 RGB, optical-axis Z depth(m), `depth_valid`와 공개 정적 intrinsics의 출처를 기록한다.
- valid depth만 camera optical frame의 가시 표면 점군으로 역투영한다. 축은 X right, Y down, Z forward다.
- 224×224 모델 resize와 원본 기하 좌표를 구분하고, resize하면 K도 함께 변환한다.
- depth 유효 비율·깊이 분포와 가림/invalid 사례를 보여준다. 같은 K로 한 역투영·재투영 round trip은 구현 검사이며 독립적인 정확도 측정이 아니다.

SAM 2 설치·추적은 필수 선행 조건이 아니다. 수동으로 표시한 작은 image ROI를 진단에 사용하면 사람 보조 분석임을 명시하고 autonomous 파지점으로 표현하지 않는다. SAM을 추가할 경우 공식 simulator와 분리된 환경에서 prompted offline 분석으로 실행한다. 가시 표면 중심을 의복 전체 중심·6D pose·물리적 grasp point로 부르지 않는다.

현재 π₀.₅가 depth를 읽지 않는다면 결과는 **RGB-D 관측 처리**와 **RGB/state 정책 적응**으로 각각 설명한다. depth의 정책 효과는 후속 대조 실험에서 검증한다.

### E3. 실제 데이터의 새 기준선을 비교한다

1. 검수한 사람 시연 1–2개로 작은 overfit 시험을 한다. 의도한 parameter가 업데이트되고 실제 checkpoint가 로드되는지 확인한다.
2. 짧은 학습용 LR schedule과 학습 노출량을 기록한다. step만 늘리는 방식으로 행동·normalization 오류를 덮지 않는다.
3. 하나의 본학습 설정을 고정한다. train 통계만 사용하며 base와 LoRA는 같은 adapter·전처리·상태·정규화·action rate·horizon으로 평가한다.
4. 같은 **3개 practice seed**를 두 조건에 적용한다. 예를 들어 각 run의 simulation+inference 예산 30–60초 중 하나를 실행 전에 고정해 두 조건에 똑같이 적용한다. 실제 simulation seconds, policy-call time, wall time과 cold load/compile을 구분해 기록한다. 공식 시간 측정 방식을 바꾸거나 짧은 검사를 전체 self-check로 표시하지 않는다. 튜닝에 쓴 seed를 untouched test로 부르지 않는다.
5. 모든 episode의 raw points, 공식 points/s, full-dressing success와 보조 구간 완료 기준을 보고한다. 집기 성공만으로 points/s가 양수가 되는 것은 아니다.

loss 감소, 유효 action 출력, 관측에 따른 행동, 보조 동작 성공, 공식 착의 성공은 각각 확인한다. 적은 seed 수의 초기 비교를 일반적 성능 우위로 확대하지 않는다. 인간 시연이 확보되지 않았다면 기존 fixture로 실행 경로만 진단하고 **실제 시연 학습은 미완료**로 남긴다.

이 단계는 행동 시연을 감독 신호로 쓰는 SFT다. 공식 환경의 placeholder reward 0을 학습 보상으로 쓰는 RL로 설명하지 않는다. 종료/시간 제한/착의 성공을 구분하고, 기존 공식 reset·randomization을 유지한다. 새로운 보상·환경 설계는 평가 규칙과 별도로 검토할 후속 연구다.

## 4. P1: 선택 가능한 FK·Jacobian 실험

E0–E3의 핵심 경로를 막지 않을 때 **최대 2시간**으로 제한한다. 로봇 자체의 공개 geometry·public joint state·public base pose와 검증한 static camera mount만 사용하여 wrist camera의 관측 목표를 robot frame으로 변환한다. 이어 작은 Cartesian 목표를 Jacobian/DLS 기반 속도 명령으로 바꾸고 공식 `(2,9)` action을 통해 실행한다.

실험에는 목표 좌표계·단위·제어 주기·joint limit·추종 오차를 기록한다. `grasp_pose_base`를 camera optical pose로 대체하지 않고, overview의 기준 eye/target을 임의 배치의 실제 world pose로 사용하지 않는다. audit의 camera world matrix, cloth/object 정답 pose, 내부 grasp state를 목표 생성·teacher 입력으로 쓰지 않는다.

검증한 extrinsic/FK가 없으면 camera-local 진단으로 종료한다. 새 IK 라이브러리나 전체 collision-aware motion planner를 만들기 위해 SFT·실제 시연·보고서를 미루지 않는다. 작은 DLS 실험을 전체 loco-manipulation planner나 실로봇 배포로 부르지 않는다.

## 5. 날짜별 의사결정과 범위 고정

| 목표 날짜 | 우선 작업 | 완료 또는 축소 판단 |
|---|---|---|
| 10/23–24 | 서버가 준비되면 E0, 실제 인간 시연 한 개 | 서버 미개설이면 문서·검수 도구 준비만 하고 실행 완료를 주장하지 않음 |
| 10/25 | E1/E2, 소량 데이터 고정 | 수집 지연 시 SAM·자동 조작·IK 확장을 제외 |
| 10/26–27 | E3, 같은 조건의 3개 paired 짧은 rollout | **10/27부터 새 기능 추가 중단**. 실패하면 가장 작은 원인을 진단 |
| 10/28 | 결과·영상·재현 문서·다음 명령 고정 | 미완료 항목과 한계를 그대로 기록. 새 학습 규모 확장보다 증거 보존 우선 |
| 10/29 이후 | 전체 검사·제출·성능 연구 | 아래 후속 경로로 같은 데이터·도구·실험 기록을 이어감 |

## 6. 다음 챌린지 실험으로 연결

10월 29일 이후에는 고정된 기준선을 유지하며 다음을 진행한다.

1. 실제 제출할 ZIP과 source/base commit을 고정하고 fresh clone의 **전체 900초 self-check**를 완료한다. 현재 helper의 역사적 commit 고정을 새 코드 검사로 오해하지 않는다. marker뿐 아니라 exit 상태·valid 최종 JSON·설정·ZIP SHA256을 확인한다.
2. Codabench 접근을 재확인하고 검증된 ZIP을 제출한다. 접근이 안 되면 패키지와 근거를 보존하고 미제출로 표시한다. accepted/Scoring은 성능 평가 완료가 아니다.
3. 3–5개 고정 배치에서 baseline을 재평가하고, 집기부터 첫 소매까지 연속된 시연의 수와 다양성을 늘린다. 평가 조건과 학습 노출량을 맞춰 비교한다.
4. **한 가지 depth 대조 실험**을 선택한다. 같은 RGB 기반 detector/mask와 controller에서 RGB 평면·크기 피드백 조건과 depth 거리 피드백 조건을 비교할 수 있다. 초기 사람 prompt가 필요하면 두 조건 모두 동일하게 제공하고 사람 초기화 시스템으로 표시한다. 접근 오차·overshoot·재시도·집기/들기 비율·시간을 비교한다. 점군을 그리기만 한 것을 depth의 인과적 효과로 주장하지 않는다.
5. 수집 조건이 다른 데이터로 정책을 비교할 때는 episode/배치·전처리·학습 노출량을 통제한다. 실제 depth-conditioned VLA 입력을 추가하는 선택은 별도 모델·학습·12GB 배포 검증을 요구한다.

내부 제출 목표는 **2026-11-16**, 첫 공식 checkpoint는 **11-17 23:59 AoE**다. 초기 파이프라인 검증과 이후 양수 착의 점수·완전 성공은 별도 milestone으로 유지한다. 목표 시점이 가까워져도 공식 물리·geometry·actuation·reset·evaluator를 변경해 점수를 만들지 않는다.

## 7. 결과를 남기는 형식

각 실험은 [실험 템플릿](templates/EXPERIMENT.md), 각 세션은 [세션 템플릿](templates/SESSION.md)을 사용한다. code/upstream commit, dirty state, dataset/model revision, normalization, image digest, 실행 명령, 하드웨어, 시간·비용, 결과 JSON과 원본 영상 checksum을 연결한다. 데이터가 늘면 처리 샘플 수·effective epochs도 갱신한다.

10월 28일 결과 묶음은 다음으로 제한한다.

- 한 페이지 결과표: E0–E3의 실제 완료 범위, 수량, 실패와 한계.
- 60–90초 영상: 실제 원격 입력, 동기화/RGB-D 검수, base/LoRA rollout, 결과·한계.
- 재현 입구: 복원 artifact와 정확한 다음 명령, 남은 문제.
- 관측·행동 인터페이스 명세: 카메라·상태·행동의 이름·차원·단위·좌표계·제어 주기·latency·reset/종료 조건.

공식 recorder·공개 모델·시뮬레이터를 활용한 통합 기여와 새로 구현한 코드를 구분한다. 구현, 로컬 측정, 제출, 주최 측 평가를 별도 상태로 유지한다. 실로봇을 사용하지 않았다면 실로봇 평가나 Sim-to-Real 성공으로 표현하지 않는다. 자료를 HF/GitHub에 보존하고 검증한 뒤 세션을 정리하며, 서버 종료·삭제는 별도 사용자 요청 없이 수행하지 않는다.
