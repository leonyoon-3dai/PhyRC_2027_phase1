# PhyRC 2027 · Phase 1

[![Original README — 공식 참가 가이드](docs/project/assets/original-readme-button.svg)](README.upstream.md)

**두 대의 Stretch 4로 옷을 입히는 정책을 개발하고, 시연 수집부터 학습·제출·서버 복원까지 공개합니다.**

Leonard Yoon, Ph.D. · 윤영호 · 독립 연구 프로젝트  
[English](README.md) · [현재 상태](docs/project/STATUS.md) · [첫 서버 작업](docs/project/START_HERE.ko.md) · [공식 챌린지](https://emprise.cs.cornell.edu/phyrc/challenge-2027/) · [Codabench](https://www.codabench.org/competitions/18366/)

이 저장소는 공식 PhyRC 환경을 바탕으로 진행하는 개인 참가 프로젝트입니다. 원격으로 시연을 수집하고, L40S 한 대에서 π₀.₅를 LoRA로 학습해 공식 평가와 제출까지 연결합니다. 작업할 때만 서버를 사용하고, 새 클린 서버에서 정확하게 이어갈 수 있도록 코드와 실험 자료를 기록합니다.

> **2026-10-22 현재: L40S 서버에서 구현·검증을 시작했습니다.** 공식 smoke, 실제 센서 기반 scripted 시험 3 episode, π₀.₅ JAX LoRA 30-step 학습, 공식 환경의 첫 debug action을 확인했습니다(0점). Fresh clone 900초 검증은 진행 중입니다. Chrome 사람 조작·Codabench 승인·착의 성능·새 서버 복원은 아직 검증되지 않았습니다. [세션 증거](docs/project/sessions/20261022-bootstrap.md).

## 첫 목표

첫 실행은 **데이터 수집 → π₀.₅ 학습 → 정책 rollout → Codabench 제출 → 클린 서버 복원**이 연결되는지 확인합니다. 완전 착의나 양수 점수를 첫 실행의 필수 조건으로 요구하지 않습니다.

| 단계 | 확인할 결과 | 현재 상태 |
|---|---|---|
| 공식 환경 | 버전 기록과 `PHYRC-SMOKE-PASS` | L40S에서 통과 |
| Chrome 사람 조작 | 두 로봇 키보드 조작, 정상 저장된 짧은 시연 | 미구현·미검증 |
| 자동 수집 | 허용 관측·공식 action·실제 transition 저장 | Codex 작성 고정 명령 시험 3 episode 검증 |
| π₀.₅ SFT | 소량 데이터 학습, checkpoint, closed-loop 실행 | 30-step 연결 시험·첫 debug action 완료, 0점 |
| 제출 | 오프라인 self-check와 accepted 제출 ID | 미실행 |
| 재개 | 새 서버 복원 후 동일 자료로 재검증 | 미실행 |

이 경로가 확인된 후에는 첫 소매 삽입 등 실제 착의 점수를 여러 배치에서 반복 달성하는 것을 목표로 합니다. 내부 제출 목표는 **2026년 11월 16일**, 첫 leaderboard checkpoint는 **11월 17일 AoE**입니다. 이는 향후 목표이며 현재 실적이 아닙니다.

## 두 가지 데이터 수집 방식

| 방식 | 구성 | 먼저 확인할 항목 |
|---|---|---|
| 사람이 Chrome으로 조작 | Isaac Sim WebRTC 화면과 키보드 입력을 공식 teleop에 연결 | 두 로봇, 숫자 키패드 대체, key-down/up, 포커스·접속 종료 |
| Codex/GPT 자동 조작 | 지정 카메라·공개 로봇 상태를 관측하고 공식 행동을 짧게 실행 | 관측 허용 목록, 명령 검증, 20Hz 기록, 자동 수집 HDF5 |

자동 조작은 자유 GUI 화면을 보고 키를 누르는 구조보다 **허용 관측 → 모델 판단 → 공식 action → 재관측** 방식으로 준비합니다. GPT는 저빈도로 행동을 결정하고 로컬 실행기가 20Hz 시뮬레이션 시간에 맞춰 실행합니다. 사람이 인계받아 수정한 구간도 출처를 구분합니다.

공식 저장소의 물리·평가는 유지하고 참가자 경로에 수집기·학습·adapter를 구현했습니다. Chrome 연결은 시험 중이며 실제 원격 인간 시연을 완료했다고 주장하지 않습니다. 자세한 조건은 [원격 수집 설계](docs/project/TELEOP.ko.md)에 정리했습니다.

## 초기 학습과 운영 선택

- **L40S 한 대:** 수집·학습·평가를 순차 실행하고 CPU·GPU·렌더링·I/O 병목부터 측정합니다.
- **π₀.₅ JAX LoRA:** 기본 모델에서 자체 데이터로 SFT 기준선을 만듭니다. EXPO·FlashSAC은 기준선 이후 검토합니다.
- **두 로봇 공동 예측:** 18차원 정규화 행동을 한 모델에서 예측하고 공식 `(2,9)`로 복원합니다.
- **초기 3시점 RGB:** 허용된 overview와 두 wrist 카메라를 사용하며 학습·추론 전처리를 공유합니다.
- **GitHub + Hugging Face:** 코드·설정·작은 보고서는 GitHub, 데이터·모델·영상은 HF에 revision과 checksum으로 연결합니다.

제출 심사는 RTX 3090 24GB에서 수행되며 정책은 12GB 예산을 지켜야 합니다. 대규모 수집·학습에 앞서 공식 이미지의 의존성과 오프라인 추론을 확인합니다. L40S에서 실행된 것만으로 심사 장비 검증을 완료했다고 표시하지 않습니다.

## 기록과 공개 방식

구현·실패·실험·영상·다음 계획을 공개하고, 면접이나 연구 소개에서 실제 증거를 따라갈 수 있게 관리합니다. 계획, 구현 완료, 로컬 측정, 제출 승인, 주최 측 평가를 구분합니다. 실행 증거는 [세션 보고서](docs/project/sessions/20261022-bootstrap.md)에 기록했습니다. [원본 시험 데이터](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data)와 [전체 학습 checkpoint](https://huggingface.co/leonayoon/phyrc-2027-phase1-pi05)를 checksum과 함께 보존했습니다. 착의 성공 결과는 아직 없습니다.

각 실험에는 코드 commit, 데이터·모델 revision, 환경, 실행 명령, 비교 배치, 소요 시간과 비용, 점수, 실패 영상, 다음 행동을 남깁니다. 시뮬레이션 시간과 실제 작업 시간을 구분하며 성공한 episode만 골라 평균을 높이지 않습니다.

[BEHAVIOR 2026 경험](https://github.com/leonyoon-3dai/behavior-submission-2026)을 바탕으로 GPU 확장 전 CPU·I/O 측정, 수정 전 기준선 보존, 데이터 증가에 따른 학습 노출량 기록, 제출 승인과 성능 확인의 구분을 적용합니다.

## 문서 안내

| 문서 | 내용 |
|---|---|
| [STATUS](docs/project/STATUS.md) | 완료 사항, 미검증 항목, 다음 작업 |
| [초기 계획](docs/project/PLAN.ko.md) | 첫 실행의 단계와 완료 기준 |
| [원격 수집](docs/project/TELEOP.ko.md) | Chrome과 Codex/GPT 방식 비교·설계 |
| [첫 서버 세션](docs/project/START_HERE.ko.md) | 나중에 clone한 뒤 시작할 순서와 Codex 인계 |
| [보존·복원](docs/project/REPRODUCIBILITY.ko.md) | 종료·업로드·복원·시간·시각 기록 |
| [조사 자료](docs/project/RESEARCH.md) | Stretch 4 공개 사례와 모델 재사용의 한계 |
| [실험 기록](experiments/README.md) | 실험·세션 템플릿과 인덱스 |
| [출처와 버전](docs/project/SOURCES.md) | 검토한 공식 자료와 revision |

## 원본과 기여 구분

공식 [rirolab/PhyRC_2027_Challenge](https://github.com/rirolab/PhyRC_2027_Challenge)의 참가자 fork입니다. 공식 시뮬레이터·평가·자산·시연은 원저자의 작업이며, 이 저장소의 개인 계획과 향후 구현은 별도로 기록합니다. 공식 주최 측 저장소가 아닙니다.

상단 버튼의 [원본 README](README.upstream.md)는 upstream `4dbbebc`의 참가 가이드를 보존합니다. 공식 문서는 `docs/competition/`, 개인 프로젝트 문서는 `docs/project/`에 둡니다. [LICENSE](LICENSE), [NOTICE](NOTICE), [THIRD_PARTY.md](THIRD_PARTY.md)의 구성 요소별 조건을 따릅니다.
