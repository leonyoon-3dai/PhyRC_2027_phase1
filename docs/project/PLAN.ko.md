# 초기 실행 계획

[프로젝트 README](../../README.md) · [원격 조작 설계](TELEOP.ko.md) · [공식 정책·제출 가이드](../competition/POLICY.md)

기준일: **2026-10-22**. 이 문서는 서버 개설 전의 실행 계획이다. 이 프로젝트에서 설치, 원격 조작, 학습, 평가, 제출은 아직 수행하지 않았다.

공식 환경 검토 기준은 [`rirolab/PhyRC_2027_Challenge@4dbbebc`](https://github.com/rirolab/PhyRC_2027_Challenge/tree/4dbbebcf93a06c1bfe12136eadc2e580f30125d6), openpi 검토 기준은 [`215abfb`](https://github.com/Physical-Intelligence/openpi/tree/215abfb217dbac7d5f1273282331b9b1866c0479)이다. 실제 시작 시 변경 사항을 확인하고 사용할 commit을 기록한다.

## 첫 실행에서 확인할 것

**작은 데이터로 수집 → π₀.₅ 학습 → closed-loop 실행 → Codabench 제출 → 새 서버 복원이 연결되는지 확인한다.** 완전 착의나 양수 점수는 첫 파이프라인 시험의 완료 조건이 아니다.

| 단계 | 완료 증거 |
|---|---|
| 환경 | 실제 장면을 사용하는 공식 smoke의 `PHYRC-SMOKE-PASS`, 환경 명세와 로그 |
| 인간 수집 | Chrome 키보드로 두 로봇을 조작한 짧은 시연, 정상 export된 `policy.hdf5` |
| 자동 수집 | 허용 관측만 받는 Codex/GPT가 관측·행동·재관측을 반복한 기록 |
| 학습 | 소량 episode에 대한 과적합 점검, 저장한 checkpoint와 학습 곡선 |
| 실행 | 학습한 정책이 공식 관측을 받아 유효한 `(2,9)` 명령을 반환하는 rollout |
| 제출 | fresh clone에서 공식 self-check 통과, ZIP 체크섬과 Codabench accepted 기록 |
| 복원 | 새 클린 서버에서 같은 코드·데이터·모델 revision을 복원한 검증 로그 |

`accepted`는 형식 승인이다. 주최 측 점수 평가나 착의 성능 검증과 구분한다.

## 자원과 모델 선택

| 항목 | 초기 선택과 근거 |
|---|---|
| GPU | Brev L40S 48GB 한 대. 수집·학습·평가는 순차 실행 |
| CPU·메모리·디스크 | 16–32 vCPU 후보, RAM 64GB, SSD 300–500GB를 운영 권장 사양으로 제안. 실제 후보의 CPU·I/O 성능을 먼저 측정 |
| 시뮬레이터 | 공식 Docker와 Isaac Sim **6.0.1** 고정. 환경의 물리·행동 제한·평가 함수 유지 |
| 기준 모델 | `pi05_base`에서 **JAX π₀.₅ LoRA SFT** 시작 |
| 비교 기준 | SFT 기준선과 데이터·전처리·평가 조건을 보존한 뒤 개선 실험 진행 |

[openpi 공식 요구사항](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/README.md#requirements)은 추론 `>8GB`, LoRA 학습 `>22.5GB`, 전체 파인튜닝 `>70GB`를 추정한다. 이는 PhyRC 구성의 실측값이 아니다. 현재 공식 openpi의 PyTorch LoRA는 미지원이므로 첫 학습 경로로 가정하지 않는다. π₀.₅ LoRA용 PhyRC 설정은 추가 구현 대상이다.

## 학습을 늘리기 전의 제출 가능성 점검

공식 [POLICY.md](../competition/POLICY.md)에 따르면 심사 GPU는 **RTX 3090 24GB**이며 simulator가 약 10GB를 사용한다. 정책은 **12GB 이내**로 준비해야 한다. L40S에서 실행된다는 사실만으로 심사 장비에서의 실행을 보장하지 않는다.

1. 공식 이미지에서 π₀.₅ 의존성과 모델이 함께 로드되는지 확인한다. 제출 Dockerfile은 `FROM phyrc-2027:isaac-6.0.1`로 시작하며, 기존 `torch`·`torchvision`을 재설치하거나 기존 패키지 버전을 변경하지 않는다.
2. 실제 입력 크기로 모델 로드·추론 peak VRAM과 지연을 측정한다. JAX의 기본 메모리 선점도 확인한다. 24GB 하드웨어를 사용하지 않았다면 그 한계를 결과에 표시한다.
3. 모델뿐 아니라 tokenizer, 정규화 통계, 설정, 코드도 번들에 넣고 **네트워크 없이** 로드·추론한다. openpi의 자동 다운로드 경로가 남아 있지 않은지 확인한다.
4. 작은 LoRA 학습·저장·재로드까지 확인한 뒤 본수집과 학습량을 늘린다.

첫 배포 후보는 학습과 같은 JAX·LoRA 경로다. 다른 framework로 내보내야 한다면 LoRA merge, 누락된 parameter, 동일 입력·noise에서의 행동 수치 일치를 검증한다. 기존 변환 스크립트만 실행하고 변환 완료로 처리하지 않는다.

## 데이터와 정책 연결

| 항목 | 초기 설계 |
|---|---|
| 카메라 | 허용된 overview RGB와 두 로봇 wrist RGB를 openpi의 세 영상 입력에 매핑 |
| 상태 | 공개 joint state부터 형식을 확인. 필요한 base 상태는 의미·좌표·차원을 명세한 뒤 추가 |
| 행동 | robot_0의 9개 다음 robot_1의 9개인 **18차원 정규화 명령**을 함께 예측 |
| padding | 모델의 32차원 규격에 맞춰 padding하고 실제 출력 18개를 복원. 상태나 행동을 묵시적으로 잘라내지 않음 |
| 전처리 | 학습·추론이 같은 카메라 순서·크기 변환·상태 선택·정규화·행동 복원 코드를 사용 |
| 실행 | 공식 20Hz 호출에서 한 step 명령 반환. chunk 실행량은 지연과 rollout을 측정해 조정 |

PhyRC 행동은 position/delta-action이 아니라 공식 속도·그리퍼 명령이다. LIBERO 등의 행동 변환을 그대로 복사하지 않는다. 그리퍼는 **`+1` 닫기, `−1` 열기, `0` 이전 의도 유지**다. `reset()`에서 chunk buffer와 episode 메모리를 비운다.

원본은 보존하고 `human`, `gpt`, `human_corrected_gpt` 출처를 남긴다. train/validation은 episode와 배치 단위로 나누며, 같은 원본에서 나온 부분 clip·수정본을 양쪽에 섞지 않는다. 정규화 통계는 train 데이터로만 계산한다. 실패 데이터를 자동으로 성공 시연과 함께 SFT에 넣지 않는다.

공식 score·success는 시연 선택·분석에 사용하되 정책 입력이나 행동 정답 생성에 사용하지 않는다. raw archive와 audit는 검증용으로 보관하고 학습 loader는 허용 관측·행동만 읽는다. [RULES.md](../competition/RULES.md), [DATA.md](../competition/DATA.md)

## 첫 서버 세션의 순서

서버 개설일을 **D0**로 둔다. 아래 날짜는 목표 작업 단위이며 하루 안에 모두 끝난다는 약속이 아니다.

| 순서 | 작업 | 다음 단계로 넘어갈 조건 |
|---|---|---|
| D0 | 코드·규칙 revision 고정, 서버·Docker 점검, 공식 build·prepare·smoke | smoke 통과 및 설치 시간·환경 로그 저장 |
| D1 | Chrome 원격 조작, 짧은 인간 시연 한 개 export | 두 로봇 키 입력과 데이터 완결성 확인 |
| D2 | 인간 시연 변환, 공식 이미지에서 π₀.₅ 추론·오프라인 패키징 | 의존성·메모리·전처리 문제 해결 |
| D3 | public-observation bridge와 자동 수집기, 짧은 Codex/GPT 시도 | 입력 allowlist·행동·0.05초 시간 정렬과 공통 데이터 형식 확인 |
| D4 | 2–3개 episode 과적합 점검 후 작은 SFT | checkpoint 저장·재로드와 실제 rollout 확인 |
| D5 | 제출 ZIP 구성, fresh clone에서 공식 self-check, Codabench 제출 | ZIP 체크섬·실행 로그·accepted 상태 기록 |
| D6 | 업로드 검증 후 서버 교체, 복원 시험 | 같은 artifact 복원과 재검증, 재개 시간 기록 |

Chrome가 막히면 GPU 원격 데스크톱 등 대체 경로로 인간 수집을 계속한다. 자동 조작의 착의 성공을 기다리느라 전체 파이프라인 검증을 미루지 않는다. 제출 의존성·메모리가 막히면 학습량을 늘리기 전에 그 문제를 해결한다.

## 첫 제출 이후의 성능 목표

첫 checkpoint는 **2026-11-17 23:59 AoE**다. 내부 목표는 **11월 16일까지 검증된 후보를 제출**하는 것이다. 서버 개설 시점과 검증 결과에 따라 일정은 갱신한다. [공식 일정](https://emprise.cs.cornell.edu/phyrc/challenge-2027/)

파이프라인이 연결된 뒤에는 리셋부터 집기·팔 정렬·첫 소매 삽입이 이어지는 시연을 확보하고, 별도 고정 배치에서 반복 달성을 목표로 한다. [현재 점수 규칙](../competition/EVALUATION.md)은 pickup을 분자에서 제외하므로 **집기 5점만으로 points/s는 0**이다. raw points, points/s, `success`는 각각 보고하고 실패한 episode도 평균에 포함한다.

BEHAVIOR에서의 경험을 반영해 다음을 기록한다.

- GPU 증설 전에 CPU·렌더·저장 병목과 simulation real-time factor를 측정한다.
- 데이터가 늘면 step 수뿐 아니라 처리 샘플 수·effective epochs도 확인한다.
- 짧은 디버그와 동일 시간 제한의 성능 평가를 구분한다.
- 기준선을 보존하고 같은 배치·예산으로 개선 효과를 비교한다.
- EXPO·FlashSAC 등 RL 확장은 수집·SFT·제출·복원 기준선을 확보한 뒤 검토한다.

## 공개 기록 원칙

계획, 소스 검토로 확인한 사실, 실제 실행 결과를 분리한다. 각 run은 코드 commit, 데이터·모델 revision, 실행 명령, wall time·simulation time·추론 시간, 결과 JSON, 대표 영상, 실패 이미지, 다음 행동을 연결해 남긴다. 서버 비용에는 설치·대기·export·업로드 시간도 포함한다.

GitHub에는 코드·설정·요약·실험 인덱스를, Hugging Face에는 대용량 데이터·모델·영상·로그를 보관한다. 학습 재개용으로 전체 params와 optimizer·step·RNG 등 학습 상태를 저장한다. 공식 openpi는 data-loader cursor까지 자동 복원하지 않으므로, 첫 복원 목표는 같은 모델·데이터·설정의 정확한 복원이다. 학습 순서까지 동일한 재개가 필요하면 sampler 상태 저장을 추가한다.

현재는 설계와 문서 준비 단계다. 성능 수치, 자체 데모, 학습 모델, 제출 결과는 실행 증거가 생긴 뒤 추가한다.
