# RGB-D 인식과 정책 확장: 기준선을 만든 뒤 비교할 것

[개발 컨텍스트](../CODEX_CONTEXT.ko.md) | [수집과 보존](COLLECTION_AND_RECOVERY_CONTEXT.ko.md) | [현재 VLA 경로](VLA_TRAINING_CONTEXT.ko.md)

2026-11-06까지 검토한 기술 방향을 정리합니다. 아래는 **후속 실험의 선택지**이며 구현 완료나 성능 개선 결과가 아닙니다. 문헌의 벤치마크 수치를 PhyRC의 점수로 옮기지 않습니다. 첫 작업은 README에 적힌 CLI 수집 연결과 유효한 시연 확보입니다.

## 1. 문제에 따라 다른 부분을 바꾼다

| 관측된 문제 | 먼저 볼 증거 | 비교할 한 가지 변경 |
|---|---|---|
| 옷이나 그리퍼가 가려짐 | 카메라별 가시성, 시간 정합, 가림 직전 행동 | 추가 head RGB 또는 관측 선택 |
| 앞뒤 거리나 소매 진입 위치가 틀림 | depth 유효 비율, 좌표계, 동일 프레임의 RGB-D | 깊이 보조 표현이나 기하 기반 목표 추정 |
| 시연에서는 되지만 정책이 잘못 움직임 | action 순서, 단위, 정규화, 학습 출처, 실제 적용 명령 | 변환 수정 또는 데이터 구성 변경 |
| 접촉 후 오래된 행동을 계속 실행 | 관측 나이, 추론 p95, queue 길이, K | 실행 청크 단축. 그 다음 비동기 비교 |
| 학습 손실은 낮지만 새 배치에서 실패 | collection 단위 split, 시작 조건과 단계별 진행도 | 시연 다양성, 실패 주변의 사람 보정 |
| Q는 높아지는데 실제 진행은 나빠짐 | reward, terminal, 행동 분포, edit 크기, twin-Q 차이 | 보상 및 critic 검증. 더 큰 edit부터 시도하지 않음 |

수집 UI 개선, 모델 아키텍처 변경, 보상 변경을 한 번에 적용하면 원인을 구분하기 어렵습니다. 실패를 재현한 짧은 구간과 비교 조건을 먼저 고정합니다.

## 2. 3 RGB에서 5 RGB와 depth로

현재 저장 가능한 센서는 overview, 두 wrist, 두 head의 **5개 RGB-D**입니다. 현재 π₀.₅는 overview와 두 wrist의 RGB만 사용합니다. 데이터는 가능하면 전체 공개 스트림을 보존하고 학습 입력은 실험 설정으로 선택합니다. 수집 원본에서 미사용 센서를 삭제하지 않습니다.

| 조건 | 변경 | 기대하는 역할 | 비용 또는 위험 |
|---|---|---|---|
| A: 현재 기준선 | 3 RGB + state32 | 기존 연결 재현 | 가려진 영역과 깊이 모호성 |
| B: 추가 시점 | 5 RGB + 동일 state/action | 머리 시점의 옷과 신체 관계 | 중복 영상, token 증가, 사전학습 camera 구성과 차이 |
| C: 깊이 보조 | B + depth encoder 또는 기하 feature | 거리, 형상, 접근 방향 | 유효성 mask, 보정, 새로운 encoder 학습 |
| D: 별도 기하 정책 | RGB-D에서 얻은 point cloud | 공간 표현의 효용 비교 | 좌표계, 샘플링, 계산 비용, 다른 정책 구조 |

### RGB를 늘릴 때

- 먼저 모델이 임의 camera key를 실제로 읽는지 확인합니다. 사전에 정한 세 key 외의 입력을 조용히 버리지 않는지 tensor와 mask를 출력합니다.
- RGB encoder 가중치를 공유하더라도 camera identity와 순서를 명시합니다. 학습 및 실행에서 동일하게 유지합니다.
- camera dropout은 누락 mask와 함께 적용하고, 검은 영상을 유효 관측으로 표시하는 방식과 구분합니다.
- 현재 224×224, patch size 14의 경로는 16×16 grid로 영상당 256 token입니다. 3 RGB는 768, 5 RGB는 1,280 image token입니다. text 최대 200을 포함하면 prefix는 각각 최대 968과 1,480 position입니다.
- 단순한 dense attention의 prefix 길이 제곱 비율은 약 2.34배지만 **전체 추론 지연이나 VRAM이 그만큼 늘어난다는 측정 결과는 아닙니다.** encoder, KV cache, batch, kernel과 action expert 비용을 별도로 측정합니다.

### Depth를 추가할 때

1. 공식 depth 정의, 단위, 유효 mask와 RGB 대응을 확인합니다. 현재 문서의 depth는 meter 단위의 카메라 Z 깊이입니다. 유효하지 않은 0을 가까운 표면으로 해석하지 않습니다.
2. 같은 시각의 RGB, depth, intrinsics와 허용된 extrinsics를 묶습니다. resize/crop 시 intrinsics도 일관되게 변환합니다.
3. 작은 depth encoder와 projection을 별도 conditioning token으로 붙이는 방식부터 비교할 수 있습니다. 사전학습 RGB encoder에 네 번째 채널을 붙인다고 즉시 동작하는 것은 아닙니다.
4. 또는 depth를 public camera frame의 point cloud로 바꿔 접근 거리와 가시성 같은 보조 feature를 만들 수 있습니다. feature 추가도 입력 계약과 normalization을 바꾸는 실험입니다.
5. 센서 추가 전후에 같은 시연, split, 학습 예산, 시작 배치와 K를 사용합니다. 단계 진행도, 전체 성공, 지연과 peak VRAM을 함께 봅니다.

카메라 Z 깊이를 사용할 때 `X=(u-cx)*Z/fx`, `Y=(v-cy)*Z/fy`로 camera-frame 좌표를 만들 수 있습니다. RGB-depth 정렬, 축 방향과 pixel convention을 먼저 확인합니다. base/world로 옮길 때는 허용된 static mount와 공개 robot state로 구한 변환만 사용합니다. **audit/info에 있는 동적 camera pose나 hidden spawn 정보가 곧 허용 입력인 것은 아닙니다.** 특히 overview의 숨겨진 배치 의존 정보를 모델이나 자동 시연 생성기에 넘기지 않습니다.

## 3. 옷에는 하나의 6D pose만으로 부족하다

강체 물체의 위치와 회전을 추정하는 방법은 유용한 출발점이지만, 옷은 변형되므로 한 개의 pose로 조작 상태가 충분히 설명되지 않습니다.

| 필요한 정보 | 공개 영상에서 검토할 표현 | 동작과 연결 |
|---|---|---|
| 잡을 곳 | 옷 영역, grasp 후보, 양쪽 대응점, 가시성 | 두 로봇의 접근과 집기 |
| 소매 입구 | 경계와 opening 후보, 위치 불확실성 | 손과 소매의 상대 정렬 |
| 목과 앞뒤 | collar 후보, 관측 가능한 외관과 방향 | 머리 통과와 방향 정렬 |
| 변형과 미끄러짐 | 연속 프레임의 추적, gripper intent와 영상의 불일치 | 멈춤, 재관측, 재파지 |

표현의 정확도는 pixel/point 오차만으로 끝내지 않습니다. 실제 접근 거리, 잘못된 파지, 소매 진입, 충돌과 복구 가능성까지 확인합니다. 보이지 않는 상태에는 불확실성을 남기고 관측을 더 확보하는 행동을 고려합니다.

별도 센서가 없는 상태에서 force나 tactile 기반 결과를 현재 구현 성과로 설명하지 않습니다. 허용 관측에 없는 contact force, cloth vertex, 평가기의 sleeve 판정은 모델 입력이나 행동 정답으로 사용할 수 없습니다.

## 4. End-to-end와 모듈형 제어의 비교

| 구성 | 역할 | 이 저장소에서의 검증 과제 |
|---|---|---|
| 직접 VLA 정책 | 공개 영상과 state에서 `(2,9)` 생성 | 시연 품질, normalization, 청크 실행 |
| 인식 + 계획 + 제어 | 관측 기반 목표, IK/경로, 제한된 속도 명령 | 프레임과 FK, 관측 오차, 충돌 및 제어 안정성 |
| 혼합 | 상위 단계/목표와 하위 정책 또는 제어기 결합 | 전환 조건, 실패 복구, 실제 적용 action 기록 |

현재 API에서 각 로봇의 앞 8개는 정규화된 속도 명령이며, 마지막 gripper 값은 열기/닫기/유지 의도입니다. 자연어의 “손끝을 조금 위로”를 지원하려면 EEF frame, FK/Jacobian, 관절 한계, 최대 속도와 도달 오차를 정의한 bounded controller가 추가로 필요합니다. 기존 action 열을 EEF 좌표라고 재해석하지 않습니다. 두 로봇 목표를 하나의 동기화된 step으로 적용하고 각 로봇의 제어권이 중복되지 않게 합니다.

모션 플래닝의 숨겨진 객체 pose를 이용해 시연을 자동 생성하는 것은 이 대회의 공개 관측 원칙과 충돌할 수 있습니다. IK에 필요한 로봇 기구학과 영상에서 추정한 목표는 구분해서 다룹니다. 계획 방법을 도입할 때 입력의 출처와 허용 여부를 먼저 검증합니다.

## 5. 정책 후보를 고르는 기준

아래 링크는 최근 스터디의 재현 후보입니다. 모델을 전부 설치하라는 목록이 아니며 현재 PhyRC 연동이나 GPU 적합성을 검증했다는 뜻도 아닙니다. 학습 가능한 가중치, 라이선스, 버전, 입력 수, 행동 표현, 저장/재로드와 전체 메모리를 확인한 뒤 하나를 선택합니다.

| 후보 | 비교 목적 | 먼저 확인할 부분 |
|---|---|---|
| 현재 π₀.₅ / OpenPI | 이미 있는 연결의 SFT와 rollout 기준선 | 실제 trainable 범위, stats, bundle와 JAX 환경 |
| ACT | 작은 모방학습 정책으로 데이터 효용 분리 | 18D 양로봇 동기화, 시퀀스와 실행 주기. 언어 prior와 별개 |
| SmolVLA | 비교적 작은 flow 기반 VLA | LeRobot 변환, camera key, 18D/state 계약과 실제 메모리 |
| LeRobot π₀.₅ | PyTorch 학습 및 PEFT 경로 비교 | 지원 revision과 pretrained 변환, adapter 저장/재로드 |
| GR00T, LingBot-VLA | 다른 표현과 사전학습 prior 비교 | embodiment adapter, 배포 자원, 학습 데이터와 사용 조건 |
| 3D Diffusion Policy | point-cloud 입력의 기하 효용 | 보정과 좌표계, point sampling. 언어 VLA와 동일 모델 아님 |
| X-VLA SoftFold, DeMaVLA | 변형 물체와 협응 조작 prior 검토 | cloth task 차이와 EEF/action 표현. checkpoint 직접 호환 가정 금지 |

https://github.com/Physical-Intelligence/openpi

https://huggingface.co/docs/lerobot/act

https://huggingface.co/docs/lerobot/smolvla

https://huggingface.co/docs/lerobot/pi05

https://github.com/NVIDIA/Isaac-GR00T

https://github.com/Robbyant/lingbot-vla-v2

https://github.com/YanjieZe/3D-Diffusion-Policy

https://github.com/2toinf/X-VLA

https://huggingface.co/2toINF/X-VLA-SoftFold

https://huggingface.co/Midea-AIRC/DeMaVLA

## 6. 최근 기술 방향을 실험 질문으로 바꾸기

| 방향 | PhyRC에서 묻는 질문 | 적용 전 조건 |
|---|---|---|
| World/action model | 미래 관측이나 실패를 예측하면 후보 선택에 도움이 되는가 | 실제 rollout과 예측의 오차, 허용 입력과 학습 출처 |
| Video 기반 추론/agent | 짧은 history가 가림과 단계 전환을 설명하는가 | 과거 프레임의 시각, 문맥 비용, 실제 실행 지연 |
| 적은 flow step | 생성 반복을 줄여도 양로봇 동작이 유지되는가 | 같은 checkpoint에서 품질과 latency 곡선 |
| 양자화 | 모델 메모리 감소가 환경 동시 실행을 가능하게 하는가 | 행동 오차, gripper 임계값, flow 누적 오차와 rollout |
| RTC/비동기 | 느린 생성 중 실행을 이어갈 수 있는가 | stop 우선권, stale 응답 폐기, queue 연결과 관측 나이 |
| residual RL | 시연 정책의 접촉 이후 약점을 작은 보정으로 개선하는가 | 유용한 기본 정책, reward/reset, 새로운 critic 학습 |

가장 먼저 재현할 대상은 실제 병목 하나입니다. 큰 모델 도입 자체를 목표로 삼지 않습니다. 학습률, mixture, camera 구성, 실행 K, 모델 종류를 동시에 바꾸지 않습니다.

연구 연결점:

- World/action: https://openwam.stanford.edu/
- Video/agent: https://chicychen.github.io/VoLo/
- Flow 생성 효율: https://zuo-kuangji.github.io/delta-flow/
- 양자화: https://quantvla.github.io/
- 실시간 청크: https://www.pi.website/download/real_time_chunking.pdf
- 기하 표현: https://point2pose.github.io/
- 파지 후보: https://github.com/NVlabs/GraspGenX

공식 simulator 버전은 challenge 호환성이 우선입니다. 새 physics engine이나 다른 Isaac Sim/Lab 버전은 분리된 연구 환경의 후보이며 수집 서버의 공식 환경을 즉시 업그레이드할 이유가 아닙니다.

## 7. 데이터 확장과 학습 전략

**시연 수보다 먼저 출처와 유효 구간을 확인합니다.** 전체 성공 시연, 부분 성공, 사람 수정, 실패 및 연결 시험을 구분합니다. 실패를 무조건 삭제하지 않되 초기 SFT의 정답 행동으로 모두 섞지도 않습니다. 어떤 단계가 부족한지 확인한 뒤 mixture와 sampling을 조절합니다.

- 단계 균형: 무동작과 긴 접근 구간이 드문 파지, 소매 통과와 gripper 전환을 압도하는지 확인합니다.
- Curriculum: 쉽게 도달하는 단계에서 시작할 수 있지만 복원 상태의 학습과 시작 배치부터의 평가를 따로 보고합니다.
- 사람 보정: 정책이 방문한 실패 상태에서 수정 행동을 수집합니다. 이를 DAgger 스타일이라고 부를 수 있어도 정식 집계/재학습 알고리즘을 구현했다고 주장하지 않습니다.
- 영상 증강: 조명, 색과 가림을 바꿀 때 action 의미와 RGB-D 기하 일관성을 유지합니다. 생성 영상이 물리적으로 맞는 행동 라벨을 보장하지 않습니다.
- 궤적 확장: 새 배치에 시연을 옮기려면 관측 기반 대응, 기구학, 접촉 가능성과 실행 검증이 필요합니다. 단순 복사, 구간 연결, 내부 정답 기반 자동 라벨을 사용하지 않습니다.
- 같은 원본, 복원 branch, 증강본은 같은 `source_group`에 묶어 검증 누출을 막습니다.

시뮬레이션 시연 확장 방법의 구조를 참고할 수 있으나, 객체의 내부 pose로 자동 정답을 만드는 기능을 그대로 가져올 수는 없습니다. 각 방법의 입력을 공개 관측으로 대체할 수 있는지 별도로 검토합니다.

https://docs.nvidia.com/isaaclab/features/synthetic-data-generation-and-imitation-learning-with-isaac-lab-mimic

https://docs.nvidia.com/isaaclab/features/skill-gen-for-automated-demonstration-generation

## 8. 한 실험에 남길 최소 비교표

아래는 새로 채울 템플릿입니다. 아직 측정된 결과가 아닙니다.

| 항목 | 기준선 | 변경안 |
|---|---|---|
| 코드/모델/stats revision | 기록 | 기록 |
| 시연과 split, 승인 기준 | 고정 | 동일 또는 변경 이유 |
| camera/depth/state/action | 기록 | 바꾼 부분만 표시 |
| trainable 수, update와 sampling | 기록 | 기록 |
| H / K / flow steps | 기록 | 기록 |
| 시작 배치, 시도 수와 예산 | 고정 | 동일 |
| 전체 착의 성공 / 유효 시도 | 측정 | 측정 |
| raw score 및 단계별 도달 | 측정 | 측정 |
| 공식 rate와 success 검증 상태 | 측정 | 측정 |
| policy p50/p95, 관측 나이 | 측정 | 측정 |
| policy process peak VRAM | 측정 | 측정 |
| simulator 포함 전체 peak VRAM | 측정 | 측정 |
| 실패 유형과 개입 횟수 | 기록 | 기록 |

평가 시도 수가 작으면 차이를 일반적 우월성으로 설명하지 않습니다. 평균만 남기지 말고 episode별 원본 결과, 영상, 실제 명령, 실행 시각과 설정을 연결합니다. 다음 실험은 점수와 실패 기록에서 가장 분명한 병목 한 가지를 선택합니다.
