# VLA 학습과 실행의 실제 계약

[개발 컨텍스트](../CODEX_CONTEXT.ko.md) | [수집과 보존](COLLECTION_AND_RECOVERY_CONTEXT.ko.md) | [입력 및 정책 확장](PERCEPTION_POLICY_CONTEXT.ko.md)

확인 기준: PhyRC `f79f61bccab5ad171b86598ac48dcfd03aef6a4a`, OpenPI `215abfb217dbac7d5f1273282331b9b1866c0479`. 아래 숫자는 이 연결 코드 기준입니다. 논문의 기본 horizon이나 다른 로봇의 차원을 현재 실행 설정과 혼합하지 않습니다.

## 1. 먼저 한 transition을 끝까지 추적

| 순서 | 코드 | 확인할 입력과 출력 |
|---|---|---|
| 저장 | [`training_dataset.py`](../../../src/PhyRC_Sim/Policy/training_dataset.py) | 공개 관측, 적용한 18D 명령, 다음 관측 |
| episode 및 chunk | [`participant/pi05/data.py`](../../../participant/pi05/data.py) | episode 안의 시작 프레임과 길이 10의 action chunk |
| 전처리 | [`participant/pi05/preprocessing.py`](../../../participant/pi05/preprocessing.py) | RGB 3장, state32, action18을 32 폭으로 padding |
| 모델 설정 | [`participant/pi05/config.py`](../../../participant/pi05/config.py) | 공유 transform, π₀.₅, horizon10, LoRA variant |
| 학습 | [`participant/pi05/train.py`](../../../participant/pi05/train.py) | train split 통계, 고정 OpenPI trainer와 checkpoint |
| 추론 | [`participant/policy.py`](../../../participant/policy.py) | local bundle, 모델 청크, 앞 18개 복원과 실행 queue |

실제 샘플 하나의 HDF5 row, 전처리 tensor, 정규화 전후 값, model output과 최종 `(2,9)`를 나란히 저장하면 연결 오류를 재현하기 쉽습니다. 이미지, action과 파일의 출처를 함께 남깁니다.

## 2. 현재 관측과 행동의 정확한 폭

### RGB

| 공개 camera ID | 모델 key | 처리 |
|---|---|---|
| `overview` | `base_0_rgb` | uint8 256×256×3, 공유 transform으로 224×224 resize/pad |
| `robot_0_wrist` | `left_wrist_0_rgb` | 위와 같음 |
| `robot_1_wrist` | `right_wrist_0_rgb` | 위와 같음 |

`left/right` 모델 key는 이 어댑터의 대응 이름입니다. 실제 두 로봇을 한 로봇의 좌우 팔로 오해하지 않습니다. 두 head RGB, depth, 이미지 history는 현재 모델에 들어가지 않습니다.

### State `(B,32)`

| slice | 내용 |
|---|---|
| `[0:13]` | robot 0 joint position |
| `[13:26]` | robot 1 joint position |
| `[26:28]` | 두 로봇의 fingertip-origin distance |
| `[28:30]` | 두 gripper의 close intent, float32로 변환 |
| `[30:32]` | `previous_action[:,8]`, 직전 gripper 명령 |

32는 입력 숫자의 개수이며 물리 자유도 수가 아닙니다. 손끝 원점 간 거리는 접촉면 간격이나 파지 성공이 아닙니다. close intent도 실제 grasp 검출 신호가 아닙니다. 공개된 base pose, twist, joint velocity를 현재 입력이 모두 사용한다고 표현하지 않습니다.

### Action `(B,10,18)`

robot 0의 9개 다음에 robot 1의 9개가 옵니다. 각 로봇은 `base forward, base left, base yaw, lift, arm extension, wrist yaw, wrist pitch, wrist roll, gripper` 순서입니다.

- 앞 8개는 정규화된 **속도 비율**입니다. joint position이나 EEF pose와 다릅니다.
- gripper `>0.5`는 닫기, `<-0.5`는 열기, 나머지는 이전 의도 유지입니다.
- 학습은 뒤에 14개를 더해 `(B,10,32)`를 사용합니다. 추론 뒤 역정규화하고 앞 18개만 `[-1,1]`로 clip한 다음 `(10,2,9)`로 복원합니다.
- 실제 물리 속도는 해당 기록의 runtime scale로 해석합니다. 위치 state를 velocity action에서 빼는 relative-action transform을 적용하지 않습니다.

## 3. 토큰과 Transformer에서 일어나는 일

다음 수는 위 OpenPI 구현의 π₀.₅ 경로를 설명합니다. 실제 실행에서는 shape hook이나 로그로 다시 출력합니다.

| 부분 | 형태와 역할 |
|---|---|
| Vision encoder | 224×224 영상 한 장을 256 patch token으로 변환. RGB 3장으로 768 token |
| Task와 state | 정규화 state를 256개 구간으로 이산화하고 문장과 함께 tokenize. 최대 200 text position |
| VLM prefix | 이미지 768 + 최대 200 text position. Gemma 2B variant, hidden width 2048, 18 layers |
| Action suffix | noisy `(B,10,32)`를 10개 action token으로 projection. Expert width1024, 18 layers |
| 시간 조건 | flow time을 MLP embedding으로 만들고 Action Expert의 adaptive RMS normalization에 사용 |
| 출력 | action token별 32D velocity field. 실제 로봇 속도 자체가 아니라 flow 공간에서 이동할 방향 |

state32가 text token 32개를 뜻하지는 않습니다. text budget에는 prompt와 state 표현, padding이 함께 들어가므로 실제 non-padding 길이를 봅니다.

VLM과 Action Expert는 단순히 “완성된 VLM 답변을 나중에 Expert가 읽는 두 모델”로 보지 않습니다. 층별 attention에서 action suffix가 prefix 맥락을 참조하고, prefix는 noisy action suffix를 보지 못하도록 마스크를 구성합니다. 같은 관측으로 flow 반복을 수행하는 동안 prefix KV를 재사용할 수 있지만 관측, prompt나 state가 바뀌면 다시 계산합니다.

논문의 FAST 이산 action 학습과 현재 참가자 fine-tuning의 flow loss를 구분합니다. FAST action token을 쓰는 사전학습 설명만 보고 현재 trainer에 AR action loss가 있다고 가정하지 않습니다.

## 4. Flow matching: 무엇을 학습하는가

현재 OpenPI 방향은 정답 action 청크를 `A`, 가우시안 노이즈를 `eps`라 할 때 다음과 같습니다.

`x_t = t * eps + (1 - t) * A`

`target = eps - A`

`loss = mean((v_theta(x_t, t, observation) - target) ** 2)`

학습 때 시연 행동과 노이즈를 섞고 그 둘 사이의 방향을 예측합니다. 추론은 noise에서 시작해 **t=1에서 0으로** 이동하므로 Euler step의 `dt`는 음수입니다.

```python
# 원리를 설명하는 PyTorch 의사코드. 이 저장소의 JAX trainer 대체 코드가 아닙니다.
noise = torch.randn_like(actions)                 # [B, H=10, D=32]
t = sample_time(actions.shape[0])[:, None, None] # [B, 1, 1]
x_t = t * noise + (1 - t) * actions
target = noise - actions
velocity = expert(x_t, t, observation)
loss = (velocity - target).square().mean()

# 추론: 고정된 한 관측에 조건화해 같은 청크를 여러 번 보정합니다.
x = torch.randn(B, 10, 32)
dt = -1.0 / num_flow_steps
for i in range(num_flow_steps):
    t = 1.0 + i * dt
    x = x + dt * expert(x, t, observation)
```

교육용 1차원 예: `A=0.4`, `eps=0.2`, `t=0.8`이면 `x_t=0.24`, target은 `-0.2`입니다. `dt=-0.1`인 한 단계는 `0.24 + (-0.1)*(-0.2) = 0.26`으로 정답 0.4 방향에 가까워집니다. 모델의 예측 오차가 없는 예시이며 실제 측정값이 아닙니다.

## 5. 정규화와 마스크: 먼저 검사할 실제 구현 세부

현재 통계는 train split에서만 계산하며 mean/std/q01/q99를 저장하고 실제 transform은 quantile normalization을 사용합니다. 개념식은 `2*(a-q01)/(q99-q01+epsilon)-1`입니다.

**확인된 주의점:**

1. `preprocessing.py`에서 18D 뒤 14개 채널을 0으로 채운 뒤 통계를 계산합니다. 이 채널은 `q01=q99=0`이므로 현재 quantile transform 이후 **-1**이 됩니다. raw padding 0과 모델 입력 0은 같지 않습니다.
2. 고정 OpenPI의 flow loss는 마지막 action 차원 전체를 평균합니다. 현재 참가자 경로에는 14개 padding 차원을 제외하는 loss mask가 없습니다.
3. episode 끝에서 horizon10이 부족하면 마지막 action을 반복합니다. temporal padding loss mask도 없습니다.
4. state 통계는 각 row를 보지만 action 통계는 겹치는 청크와 반복된 tail을 flatten하므로 고유 transition 분포와 가중치가 다릅니다.
5. `image_mask=True`는 영상 존재 여부입니다. attention mask, action-dimension mask, temporal loss mask와 다른 개념입니다.

따라서 처음에는 현행 동작을 기록한 뒤 유효 action 18개와 padding 14개의 loss를 따로 보고, episode tail의 비중을 확인합니다. mask나 통계 방식을 바꾸려면 별도 ablation으로 관리하고 학습 및 추론 transform과 checkpoint 호환성을 함께 검증합니다. 잘못됐다고 단정하고 기존 기준선을 조용히 바꾸지 않습니다.

희소한 gripper 명령은 q01/q99가 같아질 수 있습니다. 명령 `-1/0/+1`별 개수, close intent와 실제 변화, 작은 분모, 역변환 후 임계값 통과를 검사합니다. 길게 유지된 0이 “잡지 않음”을 뜻하지 않으며 드문 open/close를 노이즈로 제거해서는 안 됩니다.

## 6. LoRA와 실제 학습을 확인하는 순서

현재 경로는 JAX/OpenPI이며 VLM과 Action Expert에 LoRA variant를 지정합니다. 하지만 LoRA라는 이름만으로 adapter 행렬만 학습한다고 판단하지 않습니다. [과거 복원 기록](../RECOVERY.ko.md)의 약 4.67억 trainable parameter에는 vision/projection도 포함됐습니다. 새 실행에서는 실제 freeze filter, 파라미터 이름과 수를 다시 출력합니다.

1. 코드 revision, base checkpoint, tokenizer, dtype, optimizer와 trainable filter를 기록합니다.
2. 승인된 실제 시연으로 train/validation을 나누고 train-only 통계를 고정합니다. 현재 loader의 승인 상태를 먼저 확장해야 합니다.
3. 한 batch를 읽어 shape, 유한값, 카메라와 action 순서, padding 및 마스크를 검사합니다.
4. 작은 batch의 반복 학습으로 loss와 파라미터 변화가 생기는지 봅니다. 전체 데이터의 유용한 학습과 구분합니다.
5. 모델과 optimizer를 저장한 뒤 다른 프로세스에서 재로드하고 같은 샘플의 출력과 추론을 확인합니다.
6. held-out episode loss와 미학습 배치의 rollout을 각각 평가합니다. 현재 trainer는 별도 validation 평가 loop를 제공하지 않습니다.

과거 기본 시험은 batch1, 30 update였습니다. warmup1000이 적용된 짧은 시험은 충분한 adaptation을 보여주지 않습니다. `30/63≈0.476`은 요청된 샘플 처리량 비율이며, 복원추출 sampler가 서로 다른 30개 샘플을 모두 봤거나 epoch 절반을 순차 완료했다는 뜻이 아닙니다.

PyTorch 경로를 비교하려면 LeRobot의 π₀.₅/PEFT 지원을 해당 revision에서 확인하고 별도 환경에서 adapter 저장 및 재로드부터 시험합니다. Orbax/JAX checkpoint와 PyTorch/PEFT adapter를 확장자 변경으로 호환시킬 수 없습니다. 새 framework 도입 때문에 공식 simulator의 torch 환경을 덮어쓰지 않습니다.

## 7. 세 가지 길이와 네 가지 시간

| 값 | 현재 의미 |
|---|---|
| Flow step `N` | 한 action 청크를 생성하는 수치 적분 반복 횟수 |
| Horizon `H=10` | 예측하는 행동 10개, 20 Hz에서 0.5 simulation초 |
| Execute prefix `K` | 패키지 기본 5개, 0.25 simulation초. bundle 설정을 확인 |
| `K=1/5/10` 비교 | 각각 0.05/0.25/0.5초마다 새 청크가 필요한 실행 조건 |

현재 adapter는 queue가 남아 있으면 새로 들어온 관측을 사용해 재추론하지 않습니다. 작은 K는 재관측을 빠르게 하지만 호출 비용이 커집니다. 긴 K는 부드럽고 저렴할 수 있지만 접촉 변화와 가림에 늦게 반응할 수 있습니다.

측정할 시간은 camera/observation timestamp, inference wall time, action 적용 simulation time, 전체 run wall time입니다. `scripts/evaluate_policy.py`는 policy-call wall time과 action당 0.05 simulation초를 실행 예산에 더합니다. 이것은 점수의 first-contact~last-award 분모와 다릅니다. 첫 JIT/compile과 warm inference도 분리합니다.

RTC나 비동기 생성은 기준선 이후 비교합니다. 관측 나이, queue 길이, 새 청크와 이전 청크의 연결, stale response, stop 처리부터 검증합니다. 모델의 flow step 10을 로봇을 10번 움직이는 것으로 설명하지 않습니다.

## 8. RL, residual edit와 Q 선택의 역할

현재 PhyRC에 완료된 RL 결과는 없습니다. 다음은 기본 정책이 유용한 단계에 반복적으로 도달하고 평가 및 reset이 준비된 뒤의 실험 설계입니다.

| 요소 | 배우거나 수행하는 것 | 입력과 검증 |
|---|---|---|
| Base policy SFT | 검수된 시연으로 행동 생성 prior 적응 | 공개 관측과 실제 action; flow/BC loss |
| Critic | 현재 상태에서 후보 행동의 기대 return | 공개 관측, action, reward, 다음 관측, terminal |
| Edit policy | base 행동을 제한된 범위에서 보정 | Q 목적과 entropy, 보정량 및 실제 적용 action |
| Q 선택 | 여러 후보 중 학습된 가치가 높은 후보 선택 | 데이터 분포 밖 후보, twin-Q 차이, 실제 return |

EXPO 계열은 큰 base policy의 supervised update와 작은 edit/critic의 RL을 구분합니다. Real-Time EXPO-FT는 느린 생성과 최신 관측을 사용하는 빠른 보정을 결합합니다. **base를 항상 동결해야 한다는 뜻은 아닙니다.** 반대로 Q의 gradient가 자동으로 VLA 전체를 학습하는 것도 아닙니다.

실제 `n`단계 실행 전이의 TD target은 `R_n + gamma^n * m * V(obs[t+n])`이며, `R_n = sum(gamma^j * r[t+j], j=0..n-1)`입니다. `n`은 예측 horizon H가 아니라 실제 실행한 단계 수로, 실행 prefix K 또는 조기 종료까지의 길이입니다. 현재 기본 K=5인 전이에 H=10의 discount나 다음 상태를 조합하지 않습니다. 실제 코드에서는 entropy 항, 다음 action 선택, target network, terminal과 time-limit truncation의 의미를 확인합니다. 무조건 모든 종료에서 bootstrap을 끄거나 chunk reward에 discount를 중복 적용하지 않습니다.

공식 내부 상태는 허용된 reward, termination, reset 계산에만 사용할 수 있습니다. actor, critic, teacher 입력이나 action 정답에 넣지 않습니다. 점수 증가량 reward도 물체 조작의 어느 단계에 신호가 생기는지 분포를 확인합니다. 원래 HDF5의 기본 reward0을 착의 보상으로 쓰지 않습니다.

Q는 성공 확률도 공식 점수도 아닙니다. reward scale과 discount, 데이터 분포에 따라 달라집니다. Q로 argmax 후보를 고르는 것은 GRPO가 아닙니다. GRPO는 그룹 내 상대 보상으로 정책 gradient를 구성하는 다른 학습 방식입니다.

### BEHAVIOR에서 가져올 경험과 가져오지 않을 수치

기존 통합의 최종 구성은 frozen actor와 작업별 edit/critic 보조망을 사용했습니다. base 후보 2개와 보정 후보 1개를 Q로 고르고 비동기 행동 생성을 실행 경로에 연결했습니다. 이를 원 actor 자체의 최종 fine-tuning이나 성능 개선 성공으로 표현하지 않습니다.

- BEHAVIOR의 actor state61/action23, native `30×32`, critic `15×23`은 PhyRC state32/action18과 다른 계약입니다.
- joint delta의 오래된 anchor를 새 관절 상태로 rebase하는 경험은 유용하지만 현재 PhyRC velocity action에 같은 수식을 직접 적용하지 않습니다.
- 15개 실행과 4개 잔여 행동의 비동기 설정도 PhyRC의 20 Hz 및 horizon10에 복사하지 않습니다.
- critic이 보는 정규화, 실제 실행 action, reward 및 next-state 시간축이 일치해야 합니다. downstream rule이 행동을 바꾸면 최종 명령을 기록해야 합니다.
- 기존 모델과 보조망의 가중치가 새 embodiment에서 바로 작동하거나 prior 결과가 개선을 보장하지 않습니다.

참고 코드와 감사 기록:

https://github.com/leonyoon-3dai/behavior-submission-2026

https://github.com/leonyoon-3dai/behavior-submission-2026/blob/main/docs/submission-2026/ILIA-RT-EXPO-INFERENCE-AUDIT.md

### 통제된 비교 순서

기본 actor, task-SFT actor, task-SFT+edit, task-SFT+edit+Q 선택을 분리합니다. 비동기 실행은 별도 변수로 추가합니다. 데이터 split, reward, 초기 배치, reset과 실행 예산을 고정하고 원 기준선을 보존합니다. Q가 올라가는데 실제 점수가 나빠지면 과대평가, reward 정의, 행동 정규화와 지연을 먼저 확인합니다.

## 9. 저장과 제출 경계

`participant/policy.py`는 파일 하나로 독립 실행되지 않습니다. `bundle.json`, Orbax params, normalization assets, tokenizer, 고정 OpenPI/client와 의존성이 필요합니다. BF16 모델 로딩과 float32 최종 action을 구분합니다.

합성 zero 관측으로 돌리는 `pi05_inference_gate.py`는 의존성, 로딩과 메모리의 작은 검사입니다. 실제 장면 동시 실행, 긴 rollout, 공식 자원 한계 검증을 대신하지 않습니다. 현재 `selfcheck.sh`는 과거 source commit을 고정하므로 어떤 revision을 검사하는지 확인한 뒤 사용합니다.

## 10. 핵심 원문

- π₀.₅: https://arxiv.org/abs/2504.16054
- 고정 model: https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/models/pi0.py
- 고정 Transformer: https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/models/gemma.py
- 고정 transforms: https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/transforms.py
- PyTorch 비교 경로: https://huggingface.co/docs/lerobot/pi05
- RTC: https://www.pi.website/download/real_time_chunking.pdf
- EXPO: https://arxiv.org/abs/2507.07986
- Real-Time EXPO-FT: https://arxiv.org/abs/2609.18207
- 구현: https://github.com/pd-perry/expo-ft

외부 main은 변할 수 있습니다. 새 실험을 시작할 때 실제 코드와 모델 리비전을 기록하고 기존 검증 결과의 기준 버전과 구분합니다.
