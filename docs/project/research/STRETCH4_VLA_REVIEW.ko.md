# Stretch 4 학습 정책과 VLM 제어: PhyRC 적용 기록

검토일: **2026-11-04**. 이 문서는 공개 코드와 연구를 분석한 **후속 개발 계획**이다. 이번 문서 작업에서 GPU 실행, 새로운 시연, 학습, 자율 착의 또는 공식 제출 검증을 수행하지 않았다.

현재 시연 수집 방향은 [README](../../../README.ko.md), 서버 재개 순서는 [START_HERE](../START_HERE.ko.md), 최신 실험 상태는 [STATUS](../STATUS.md)를 따른다. 기존 Chrome 버튼·방향 화살표·키보드 UI를 먼저 사용한다. 텍스트 제어, 모델 교체와 새로운 SFT는 다음 UI 테스트의 선행 조건이 아니다.

## 판단 요약

| 참고 대상 | 활용할 부분 | 그대로 복사할 수 없는 부분 |
|---|---|---|
| Hello Robot `stretch4_lerobot` | 데이터/카메라 설정의 보존, 학습과 실행 전처리 일치, 실제 Stretch4 π0.5 LoRA 운영 경험, adapter 로드 확인 | 단일 실기 로봇의 위치·상대위치 명령, LeRobot/PyTorch checkpoint, 실기 비동기 서버 |
| Georgia Tech Astra 연구 | 공개 이미지·로봇 상태를 읽고 짧은 명령을 내린 뒤 다시 관찰하는 제어 구조, 실행 피드백과 실패 기록 | 외부 GPT 호출을 포함하는 실기 실행 경로, 연구의 좌표/명령을 PhyRC에 직접 전달, 가정 작업 결과를 착의 성능으로 해석 |
| 현재 PhyRC 구현 | Chrome 시연 UI, 공개관측 수집 경계, openpi JAX LoRA 경로, 오프라인 제출 adapter | 학습 경로 시험을 착의 baseline 성능으로 해석, raw 저장을 RGB-D 학습 준비 완료로 해석 |

**우선 결정:** 검수된 시연을 확보하고 현재 openpi 경로를 발전시킨다. LeRobot 비교는 필요할 때 별도 환경에서 수행한다. Astra 방식은 추후 자동 수집/보조 제어 연구 옵션으로 남긴다.

## 1. 조사 기준과 검증 수준

기준 사용자 저장소 commit은 [`b4fdde1e966b49f3f1893393f10bd03d61f336f4`](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/commit/b4fdde1e966b49f3f1893393f10bd03d61f336f4), 공식 시뮬레이터 commit은 [`4dbbebcf93a06c1bfe12136eadc2e580f30125d6`](https://github.com/rirolab/PhyRC_2027_Challenge/commit/4dbbebcf93a06c1bfe12136eadc2e580f30125d6)이다. 정책 규격·RULES·POLICY·EVALUATION은 두 저장소의 파일 SHA가 일치했다.

| 항목 | 현재 근거 | 아직 확인하지 않은 것 |
|---|---|---|
| Chrome 직접 조작 | 11월 3일 두 로봇 이동과 사용자 조작 확인 | 충분히 쉬운 조작, 반복 가능한 성공 시연 |
| 최신 raw | 966전이·12,561상태, complete 및 chunk/event/scene 해시 검사 | 최신 RGB-D export/QC와 원격 백업 |
| 중간 복원 | 저장/불러오기 좌표 오차0 smoke | cloth·접촉·파지·제어 상태의 정확한 복원과 계속 조작 |
| π0.5 | 기존 scripted 데이터의 학습/저장/실행 경로 시험 | 인간 성공 시연에서 학습한 자율 착의 성공 |
| 목표 점수 | 첫 50점 시도를 목표로 단계별 연습 | 50점 달성, success=true, 공식 평가 |

11월 3일 L40S 측정 RTF는 약0.1149, 즉 simulation1초에 wall8.70초였다. 같은조건의 짧은 이전표본보다 약10% 빠르지만, 이전 CPU영상편집과 표본차이가 있어 하드웨어의 인과효과나 입력반응 지연으로 해석하지 않는다.

## 2. 가장 중요한 차이: 9개 명령의 의미

| 인덱스 | Hello Robot 실기 데이터 | PhyRC 각 로봇의 행동 |
|---|---|---|
| 0,1,2 | base 선속도/각속도 | 최대속도로 정규화한 forward/left/yaw 명령 |
| 3,4 | lift/arm 위치 | lift/arm 속도 비율 |
| 5,6,7 | wrist yaw/pitch/roll 각도 | wrist 각속도 비율 |
| 8 | 그리퍼 간격 mm | +1 닫기, -1 열기, 0 이전 의도 유지 |

PhyRC는 `(2,9)`이며 두 로봇의18차원 명령을 함께 예측한다. 실기의9차원 배열과 크기가 비슷하다는 이유로 그대로 이식하면 안 된다. 예를 들어 `lift=0.7`은 실기 위치표현에서는0.7m일 수 있지만, PhyRC에서는 최대lift속도의70%라는 뜻이다.

Hello Robot의 relative-action 학습은 해당 위치 표현에 맞춘 방식이다. **현재 PhyRC 속도 action에서 위치 state를 빼는 변환을 적용하지 않는다.** 위치 목표를 사용하는 별도 controller를 도입하려면 현재 위치, 단위, 좌표, 시간간격과 최대속도를 해석하는 새 제어기와 검증이 필요하다.

## 3. 현재 코드 경로와 수정 후보

| 코드 | 현재 역할 | 다음 검토 |
|---|---|---|
| [`participant/pi05/preprocessing.py`](../../../participant/pi05/preprocessing.py) | RGB3개, state32, action18→32padding, 출력32→18→(2,9) | 카메라 순서·색·해상도와 state/action단위 회귀검사 |
| [`participant/pi05/data.py`](../../../participant/pi05/data.py) | SHA·complete·source_group·review검사, horizon10 | 인간 시연용 검수 상태를 명시하고 reset경계/분할 검증 |
| [`participant/pi05/config.py`](../../../participant/pi05/config.py) | openpi JAX π0.5 LoRA, horizon10, shared transforms | 실제 trainable범위, 짧은시험/본학습 학습률 일정 구분 |
| [`participant/pi05/train.py`](../../../participant/pi05/train.py) | train통계, quantile normalization, upstreamtrainer | train-only통계 보존, 학습 데이터/설정/로그 provenance |
| [`participant/policy.py`](../../../participant/policy.py) | offline localbundle, BF16, chunkqueue, reset | 학습/추론 전처리일치, LoRA효과, chunk실행길이 비교 |
| [`scripts/pi05_inference_gate.py`](../../../scripts/pi05_inference_gate.py) | 합성공개입력의 의존성·메모리·추론 시험 | 실제scene 동시메모리·latency, RTX3090평가환경 검증 |
| [`participant/collection/boundary.py`](../../../participant/collection/boundary.py) | 공개관측만복사, action검사, provenance | 자동collector 확장시 정보경계·중지·개입 유지 |
| [`participant/collection/gpt_client.py`](../../../participant/collection/gpt_client.py) | 저빈도API wiringtest | 추후 공개depth조회와짧은행동feedback, human takeover |

현재 state32의 구성은 `26 joint positions + 2 fingertip distances + 2 gripper intents + 2 previous gripper commands`다. base pose/twist, depth, head cameras는 허용되지만 현재 어댑터는 쓰지 않는다. 이동/접근 실패 분석 후 입력 확장을 비교할 수 있다. 지금32차원이 모두 채워져 있으므로 base상태를 단순히 덧붙이는 변경은 새 state설계와 checkpoint호환 검토를 필요로 한다.

`data.py`는 현재 `review == approved_pipeline_test`만 허용한다. 사람 성공 시연을 추가하기 전에 `approved_human_demo` 같은 상태와 검수 근거를 설계하고 코드에서 명시적으로 지원해야 한다. 기존 test데이터를 성공데이터로 재명명하지 않는다.

`train.py`는 무작위 복원추출로 샘플링한다. 30steps×batch1/63전이≈0.476은 처리량 기준이며 서로 다른30샘플을 모두 봤다는 의미가 아니다. checkpoint복원은 dataloader cursor를 복구하지 않으므로 bitwise동일 학습 재개로 설명하지 않는다.

## 4. 외부 자료에서 실제 확인한 결과

### Hello Robot의 공식 Stretch 4 학습 경로

검토한 소스는 [`146efcd2a73b0e2ad7a11c43a5e54fd98cdf7289`](https://github.com/hello-robot/stretch4_lerobot/tree/146efcd2a73b0e2ad7a11c43a5e54fd98cdf7289)이다. README는 **π0.5 LoRA, ACT, Diffusion을 실기 Stretch 4에서 테스트했다**고 명시한다. π0.5는 desktop GPU, ACT/Diffusion은 Jetson에서도 실행한 구성이다. 검토한 README·수집/학습/배포 가이드에는 바로 내려받아 착의에 쓸 작업별 Stretch 4 학습 가중치가 확인되지 않았다. 이는 공개 가중치가 어디에도 없다는 단정이 아니다.

공식 LeRobot recipe는 `lerobot/pi05_base`, BF16, gradient checkpointing, LoRA `all-linear`, `r=32`, `alpha=64`, learning rate `1e-4`, batch 16, 30,000 updates, checkpoint 5,000 간격이다. 이 값은 **실기 데이터용 참고**이며 L40S에서 검증한 PhyRC 설정이 아니다. `use_relative_actions=true`는 위치 표현에 적용하고 `grip`, `base_v`, `base_omega`를 제외한다. 전처리와 학습의 relative 설정·제외 열·chunk size 50이 일치해야 한다.

추가 구현상 주의:

- **동기화:** 기준 카메라 시각에 다른 영상을 20 ms 이내로 짝짓고 관절 상태를 보간한다. observer의 `action[t]=state[t+3]`은 30 Hz에서 약100 ms 미래 상태를 label로 쓰는 실기 방식이다. PhyRC의 실제 적용 action에 덧씌우지 않는다.
- **held joints:** 기본 처리에서 움직인 episode 비율이10% 미만인 관절은 state/action을 median 상수로 변경한다. 착의의 드문 필수 동작을 지울 수 있으므로 초기에는 빈도 보고서만 참고한다.
- **통계:** `stats_floor.py`의 m/rad/mm 하한은 정규화 속도 데이터에 직접 적용하지 않는다. relative 통계는 chunk 전체 `action[t+k]-state[t]`에서 계산한다. 구현상 relative 기본 tail 0.1은 q01/q99라는 키에 실제0.1/99.9 percentile을 담으므로 키 이름만 믿지 않는다.
- **로딩:** `policy_server.py`는 local adapter 설정을 감지해 base를 불러온 뒤 PEFT adapter를 merge한다. LeRobot0.6 async의 LoRA 로딩·관측 history·단위가 다른 similarity filter 문제에 대한 보정이다. 모든 버전이나 현재 OpenPI에 같은 버그가 있다고 확대하지 않는다.
- **복귀:** 실기 start-pose 도구는 arm/wrist/gripper 복귀이며 base·물체·옷 상태 복원이 아니다.
- **시간:** 실기30 Hz의 chunk50은 약1.67초, PhyRC20 Hz에서50명령은2.5 simulation초다. 생성 길이와 실행 길이를 분리한다.

### Georgia Tech Astra: 프롬프트 기반 실기 제어

[Astra Beyond Tabletop](https://www.gt-rail.com/blog/astra-beyond-tabletop/)은 한 대의 Stretch 4로24개 가정 작업을 탐색한 **블로그 실험 보고**다. Codex CLI의 GPT-6 Astra가 카메라·관절 상태·직전 실행 결과를 읽고 상대변위 JSON을 내는 동기식 observe/execute loop다. 학습한 로봇 VLA checkpoint를 공개한 사례로 표현하지 않는다. 원문 페이지에서 완성 실행 코드 repo 링크는 확인하지 못했다.

공개된 정량 비교는 오븐 과제 하나이며 각 조건5회다. 24개 전체 작업의 통합 성공률은 공개하지 않았다.

| 조건 | 성공 | subgoal 완료 | 잘못된 done | 평균 turn | 평균 총 시간 | 추론 비중 |
|---|---:|---:|---:|---:|---:|---:|
| high / depth API |3/5|92%|0/5|49.6|10.3분|82%|
| low |0/5|60%|4/5|57.6|10.5분|81%|
| ultra |1/5|76%|3/5|54.2|10.1분|80%|
| depth image |1/5|61%|3/5|63.8|11.7분|81%|
| no depth |2/5|84%|2/5|66.6|14.6분|84%|

`high`와 `depth API`는 같은 기본5회이므로 합산해10회로 세지 않는다. 작은 한 과제 결과로 모델·추론 설정의 보편적 순위를 주장하지 않는다. 원문의 주요 한계는 미세 접촉, 시야 가림, 앞 단계의 선택이 뒤 단계에 미치는 영향, 주변 충돌과 추론 지연이다. 착의에서는 재파지·천의 걸림·두 로봇 간 간섭을 기록하는 설계 근거로 활용한다.

**모델의 done 선언은 공식 성공 판정과 별개**다. 원문의 wrist depth API도 Euclidean distance(cm)이므로 PhyRC depth와 단위·정의·영상 정합이 같은지 검사한 뒤 구현한다.

## 5. Hello Robot에서 우선 가져올 설계

1. **설정과 데이터의 결합:** 카메라 이름·순서·크롭·회전, RGB 규격, 상태·행동 이름과 단위, 좌표, 정규화, 프레임 속도를 manifest로 저장한다. 학습과 실행이 같은 manifest를 읽게 한다.
2. **시각과 행동 정렬 검사:** 이미지 시각, 관측 시각, 행동 적용 구간의 계약을 고정한다. 실기의 미래 상태 label 생성법을 복사하지 않고, 공식 20Hz 공개 관측과 실제 적용한 정규화 속도 명령을 유지한다.
3. **분포 확인:** 움직이지 않은 관절, 작은 표준편차, 그리퍼 전환, 긴 정지 구간을 검사한다. 통계 하한값이나 고정 관절 처리는 원본 보존과 분리하고 적용 전후를 기록한다.
4. **실행 전 모델 확인:** base와 adapter 경로·해시, 실제 학습 파라미터 변화, 로드 로그를 기록한다. LoRA 옵션만 켠 상태와 학습한 adapter를 실제 불러온 상태를 구분한다.
5. **단계별 독립 검증:** 패키지 로드, 단일 추론, 짧은 폐루프, 여러 seed와 긴 평가를 나누어 확인한다. GUI 수집과 GPU 학습·export를 동시에 돌리지 않는다.

LeRobot을 비교할 경우 `experiments/lerobot/` 같은 별도 영역과 별도 Python 환경에 두고, 공식 Docker의 기존 torch/torchvision을 교체하지 않는다. 기존 Orbax/JAX 체크포인트와 LeRobot/PEFT 체크포인트의 직접 호환은 확인하지 않았다.

## 6. Astra 방식의 PhyRC 적용 경계

현재 자동 조작 코드는 이미 `observe / act / stop / finish_episode` 도구 경계를 갖고 있다. 다만 `gpt_client.py`의 prompt는 작은 lift, 그리퍼 열기·닫기, 정지를 시험하며, 코드도 motion≤0.05와 steps≤10을 강제한다. 이를 성과가 검증된 착의 수집기로 표현하지 않는다.

차후 실험은 지정 공개 RGB-D와 로봇 상태를 읽고, 제한된 2×9 명령을 짧게 수행한 뒤 재관측하는 형태로 설계할 수 있다. 한 명령을 오래 유지하면 두 로봇이 옷을 당기는 동안 접촉 상태가 변할 수 있다. 실행 길이를 작게 시작하고 개입·실패율을 측정한다.

**모델에 전달 가능한 것:** 지정 5개 카메라의 RGB/depth/depth_valid, 공개 로봇 상태, 정적 카메라 보정값, 이전 행동과 시간.

**모델 입력·행동 label로 전달하지 않을 것:** 자유 시점 Chrome 뷰포트 이미지, raw/audit, 옷 입자와 마네킹의 정답 상태, 평가 점수·성공 label·내부 geometry, seed, simulator handle.

공식 RULES는 내부 상태를 학습 reward·termination·reset에 사용하는 것은 허용하지만, actor/critic 등 모델 입력이나 teacher/action label로 사용하는 것은 금지한다. 점수는 수집 후 검수·분석에 분리 사용한다.

공식 제출 안내는 모든 가중치를 ZIP에 포함하고 평가 중에는 다운로드하지 않도록 한다. 현재 우리 adapter도 offline 실행을 강제한다. 외부 API 사용의 별도 허용을 확인한 것은 아니므로, Astra의 외부 서비스 호출 경로는 자동 수집 연구 옵션으로 우선 검토한다.

## 7. 다음 구현 순서와 통과 기준

아래는 앞으로 수행할 작업이며 완료 체크리스트가 아니다.

| 순서 | 작업 | 통과 기준과 남길 자료 |
|---|---|---|
| A | 새 서버의 현재 Chrome UI 복원 | 두 로봇 짧은 동작, release/stop, 정상 종료, run ID와 코드·환경 기록 |
| B | 초기 상태 재시작과 단계 기록 | raw complete와 hash, reset 경계, 실제 관측 점수, 인간 개입 기록 |
| C | 검수된 학습 파일 제작 | RGB-D·공개 관측·행동 개수 일치, 시간 정렬, NaN 0개, 범위 검사, episode 분할, QC 보고서 |
| D | manifest와 공통 전처리 정리 | 학습·실행의 동일 샘플 변환 일치, camera/action 순서 일치, norm/hash 고정 |
| E | 기존 openpi 경로의 짧은 SFT | 체크포인트 재로드, finite 추론, 실제 학습 파라미터 변화, train/val source_group 분리 |
| F | 짧은 로컬 폐루프 비교 | 고정 seed의 raw points/success/rate, 파지 이탈·개입 수, 추론 지연·VRAM, 영상과 로그 |
| G | 장기 검증과 제출 | 공식 환경·offline·shape 검사, RTX3090 자원 내 실행, 공식 900초 self-check와 후속 제출 결과 |

900초 평가를 대신하는 짧은 검사는 adapter와 실행 경로를 빠르게 확인하는 용도다. 긴 시간에 누적되는 문제나 정식 self-check를 완료한 것으로 간주하지 않는다.

chunk 비교는 현재 horizon10을 고정하고 execute_steps 1/5/10부터 시작할 수 있다. 재관측 간격은 각각 0.05/0.25/0.5 simulation초다. 성공률뿐 아니라 policy 호출 시간과 관측 지연, 오래된 명령도 함께 측정한다. 공식 예산은 각 step의 0.05 simulation초와 policy 실제 추론 시간을 더한다.

평가는 RTX3090 24GB 한 대를 사용한다. 시뮬레이터가 약10GB를 사용하므로 정책을 12GB 이내에서 운영하도록 별도 확인한다. L40S의 48GB에서 실행에 성공한 것만으로 충족을 선언하지 않는다.

## 8. 점수와 복원 기록 원칙

누적 raw 50점과 최종 success는 따로 저장한다. 점수는 한 번 얻으면 유지되지만 success는 두 손·머리·정면 방향 조건을 함께 0.5초 충족해야 한다. 공식 rate는 pickup 제외 최대45점을 첫 접촉부터 마지막 착의 득점까지의 simulation 시간으로 나눈 값이다.

`P` reset이나 save-slot 복원은 현재 live 평가 attempt를 invalid 종료하고 새 attempt를 시작한다. 단계별 연습의 서로 다른 점수를 더해서 단일 50점 완주로 보고하지 않는다. checkpoint 파일이 있다는 것과 의복 접촉까지 정확하게 복원된다는 것도 구분한다.

## 9. 원문과 코드

- [Hello Robot Stretch4 LeRobot](https://github.com/hello-robot/stretch4_lerobot)
- [Hello Robot 학습 가이드](https://github.com/hello-robot/stretch4_lerobot/blob/main/docs/2-training-policy.md)
- [Astra Beyond Tabletop](https://www.gt-rail.com/blog/astra-beyond-tabletop/)
- [공식 허용관측·행동 규칙](../../../docs/competition/RULES.md)
- [공식 정책·제출 계약](../../../docs/competition/POLICY.md)
- [공식 평가 정의](../../../docs/competition/EVALUATION.md)
- [공식 인터페이스 JSON](../../../config/policy_interface.json)

자료의 업데이트와 새로운 실험 결과는 이 문서의 검증 수준을 갱신할 근거로 남긴다. 연구자의 실기 결과와 우리 시뮬레이션의 실제 실험 결과는 분리해서 표기한다.

## 10. 출처와 라이선스

Hello Robot 문서·코드: Copyright 2026 Hello Robot Inc., [Apache-2.0](https://github.com/hello-robot/stretch4_lerobot/blob/146efcd2a73b0e2ad7a11c43a5e54fd98cdf7289/LICENSE). 이 문서는 링크와 독립적인 기술 분석을 제공하며 외부 코드를 이 저장소의 실행 코드에 복사하지 않았다.

Astra 원문: Yuchen Zheng 및 공동저자, Georgia Institute of Technology, 2026. 원문 웹사이트는 [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)을 명시한다. 이 문서의 Astra 관련 한국어 요약과 표 재구성은 원문을 변경한 파생 부분이며 같은 CC BY-SA 4.0으로 제공한다. 나머지 저장소 코드의 기존 라이선스를 변경하지 않는다.

**이번 변경 범위:** 문서 분석·계획 기록만 수행. simulator·정책·학습 코드의 동작은 변경하지 않았다. PDF는 별도 분석 자료로 제공하며 공개 README에는 재사용 가능한 텍스트 근거를 남긴다.
