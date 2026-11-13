# L40S와 RTX PRO 6000의 수집 비용 검토

**2026-11-13 문헌·기존 기록 분석이다. 인스턴스 교체, 새 GPU 벤치마크 또는 비교 rollout은 수행하지 않았다.** 시간당 가격은 사용자가 제시한 L40S **$1.07**, RTX PRO 6000 **$2.63**을 사용하며, 현재 판매 가격을 별도로 검증한 값은 아니다.

현재 원격 Astra 호출을 포함한 시연 수집에서는 **L40S 유지가 비용 면에서 유리할 근거가 강하다.** Blackwell GPU가 환경 실행 일부를 단축할 가능성은 있지만, 동일 수집량당 비용이 같아지려면 전체 처리 속도가 **2.63 / 1.07 = 2.458배**가 되어야 한다. 실제 PhyRC 장비 간 속도 차이는 아직 측정하지 않았다.

## 기존 수집에서 확인한 시간

[E27 백업 검증 기록](../../project/sessions/20261107-e27-backup-verification.json)의 `recorded_wall_fields`가 계산의 입력이다. 새 서버의 벤치마크나 현재 진행 중 시도의 측정으로 해석하지 않는다.

| 필드 | 실제 기록 | 전체 비중 |
|---|---:|---:|
| `wall_s` | 2450.624435922초 / 40.84분 | 100% |
| `actor_call_wall_s` | 1348.905617475004초 / 22.48분 | 55.0% |
| `environment_dispatch_wall_s` | 1046.465704732018초 / 17.44분 | 42.7% |
| 위 두 경로 밖 잔여 | 55.253113714978초 / 0.92분 | 2.3% |

actor 호출 시간은 순수 추론 시간이 아니다. Docker·CLI 실행, 통신, 원격 서비스 대기와 생성 등이 포함되며 로컬 GPU 교체로 같은 배율의 개선을 기대할 수 없다. [호출 시간의 정의](../../ASTRA.md#4-시간과-실행-길이)를 따른다.

환경 실행 왕복만 `s`배 빨라지고 actor·기타 시간이 그대로라는 가정에서 새 시간은 `2450.624435922 - 1046.465704732018 + 1046.465704732018 / s`초다. 같은 전이·모델 호출을 수행한다고 가정하며 초기 설치, 저장소 비용, 모델 이용 비용은 제외한다.

| 조건 | 전체 시간 | 전체 속도 배율 | 인스턴스 비용 |
|---|---:|---:|---:|
| E27 원래 시간 × L40S 요금 | 40.84분 | 1.00배 | $0.73 |
| 환경 왕복 전체가 2배 빨라진다고 가정 × PRO 6000 요금 | 32.12분 | 1.27배 | $1.41 |
| 환경 왕복 시간이 0인 불가능한 제거 상한 × PRO 6000 요금 | 23.40분 | 1.75배 | $1.03 |

이는 **병목 설명용 가정 계산이며 PRO 6000의 측정 성능이나 예상 완료 시간은 아니다.** CPU·스토리지·네트워크·모델 응답 시간이 달라지면 결과도 달라진다.

## GPU 사양이 주는 단서와 한계

다음은 NVIDIA 공식 제품 사양이다. 최대 연산량·대역폭 비율을 PhyRC 속도 배율로 사용하지 않는다.

| 항목 | L40S | RTX PRO 6000 Blackwell Server Edition | 사양 비율 |
|---|---:|---:|---:|
| FP32 | 91.6 TFLOPS | 120 TFLOPS | 1.31배 |
| RT core 처리량 | 212 TFLOPS | 355 TFLOPS | 1.67배 |
| 메모리 대역폭 | 864 GB/s | 1597 GB/s | 1.85배 |
| GPU 메모리 | 48 GB | 96 GB | 2배 |

출처: [NVIDIA L40S 사양](https://www.nvidia.com/en-sg/data-center/l40s/), [NVIDIA RTX PRO 6000 Blackwell Server Edition 사양](https://www.nvidia.com/en-us/data-center/rtx-pro-6000-blackwell-server-edition/).

상품명이 `RTX PRO 6000`인 것만으로 위 Server Edition 사양을 확정할 수 없다. Blackwell **Server / Workstation / Max-Q**는 전력·클럭 조건이 다르다. Workstation은 공식 자료에서 96 GB·1792 GB/s·600 W, Max-Q는 96 GB·1792 GB/s·300 W로 구분한다. [Workstation 공식 자료](https://www.nvidia.com/content/dam/en-zz/Solutions/data-center/rtx-pro-6000-blackwell-workstation-edition/workstation-blackwell-rtx-pro-6000-workstation-edition-nvidia-us-3519208-web.pdf), [Max-Q 공식 사양](https://www.nvidia.com/en-us/products/workstations/professional-desktop-gpus/rtx-pro-6000-max-q/).

이전 세대 **RTX 6000 Ada**라면 48 GB·FP32 91.1 TFLOPS·RT 210.6 TFLOPS로 L40S와 유사한 등급이다. 이름이 비슷한 Blackwell 제품의 개선 폭을 적용하지 않는다. [RTX 6000 Ada 공식 자료](https://www.nvidia.com/content/dam/en-zz/Solutions/design-visualization/rtx-6000/proviz-print-rtx6000-datasheet-web-2504660.pdf).

[E18 기존 계측](2026-11-07-e18-capture-timing.ko.md)에서는 environment step 평균 750.927 ms 중 camera capture가 161.157 ms, 약 21%였다. observe 바깥에는 제어·물리·평가·동기화 등이 섞이며, 이는 GPU kernel별 분해가 아니다. 따라서 렌더 처리량만으로 전체 개선을 설명할 수 없다. NVIDIA도 GPU·physics·app frame time을 구분해 병목을 판단하도록 안내한다. [Isaac Sim 공식 벤치마크 해석](https://docs.isaacsim.omniverse.nvidia.com/latest/reference_material/benchmarks.html#interpreting-results).

## 다음 비교 방향 — 미실행

원격 Astra 호출이 없는 **순수 prefix replay 또는 로컬 정책 rollout**에는 E27의 actor 55% 비중을 적용하지 않는다. 그 작업은 GPU 개선 효과가 더 클 수 있지만, 2.458배 비용 분기점을 넘는지는 미측정이다. 향후 비교 시 정확한 GPU 변형·전력 제한과 CPU·RAM·디스크를 기록하고, 동일 prefix·카메라·공식 물리·평가·기록 조건에서 준비 시간을 분리한 전이/초와 전이/달러를 비교한다. actor 루프에서는 호출 경과와 환경 경과도 별도로 비교한다.

이번 분석은 공식 물리·카메라·평가기 변경이나 새 비교 실행을 수행한 기록이 아니다. 장비 속도 향상 자체를 착의 득점 또는 50점 달성으로 해석하지 않는다.
