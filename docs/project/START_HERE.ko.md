# 첫 클린 서버에서 시작하기

현재는 실행 전 문서 단계입니다. 아래 명령은 공식 설치 흐름을 안내하며, 이 프로젝트 서버에서 검증한 결과가 아닙니다. 원격 화면·AI 수집·π₀.₅ 도구는 아직 구현되어 있지 않습니다.

[현재 상태](STATUS.md) · [초기 계획](PLAN.ko.md) · [원격 수집](TELEOP.ko.md) · [보존·복원](REPRODUCIBILITY.ko.md)

## 서버가 준비된 뒤

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git rev-parse HEAD
```

`AGENTS.md`와 `docs/project/STATUS.md`를 먼저 읽습니다. [세션 템플릿](templates/SESSION.md)으로 새 기록을 만들고 GPU·CPU·RAM·디스크·드라이버·OS·Docker 상태를 남깁니다. 처음부터 학습 패키지를 공식 simulator 환경에 한꺼번에 설치하지 않습니다.

1. [공식 SETUP](../competition/SETUP.md)에 따라 host driver, Docker, NVIDIA Container Toolkit을 점검합니다. host에 Isaac Sim·ROS·Conda·CUDA Toolkit 전체를 추가하는 것으로 시작하지 않습니다.
2. Docker가 GPU를 확인하면 아래 공식 순서를 진행합니다. 장면이 보이는 것과 smoke 통과를 구분합니다.

```bash
./run.sh doctor
./run.sh build
./run.sh prepare
./run.sh smoke
```

`PHYRC-SMOKE-PASS`와 로그·소요 시간을 저장합니다. 공식 runner는 Isaac Sim 6.0.1을 고정하므로 `latest`로 교체하지 않습니다.

## 첫 세션의 범위

| 단계 | 진행할 일 | 다음 단계 조건 |
|---|---|---|
| 1 | 공식 환경 점검·smoke | 실제 PASS와 환경 기록 |
| 2 | Chrome WebRTC 입력 연결 또는 GPU 원격 데스크톱 | 두 로봇·그리퍼·키 해제·ESC 확인 |
| 3 | 짧은 인간 시연 기록·export | READY, complete, 데이터 검사 |
| 4 | 소량 관측으로 π₀.₅ 추론·의존성·메모리 검증 | 공식 이미지에서 offline adapter 가능성 확인 |
| 5 | AI 도구·수집 wrapper 구현 | 공개 관측만 전달, 시간 정렬된 transition 저장 |

GUI가 확보된 후 공식 수집 명령은 다음과 같습니다. **이 명령이 Chrome 스트리밍을 자동으로 켜 주지는 않습니다.**

```bash
./run.sh gui --training-record 1 --evaluate 1
```

ESC 후 창이 닫혀도 `[Dataset export] READY`까지 기다립니다. 실제 run ID를 확인한 뒤 [DATA.md](../competition/DATA.md)의 inspect/deferred 검사 명령에 적용합니다. 수집 시작 전부터 원격 업로드와 세션 종료 기록 경로를 정합니다.

## 서버의 Codex에 전달할 시작 요청

아래 요청은 앞으로 서버에서 사용할 인계문입니다. API key나 다른 인증 값을 넣지 않습니다.

```text
이 저장소의 AGENTS.md, README.ko.md, docs/project/STATUS.md,
START_HERE.ko.md, PLAN.ko.md, TELEOP.ko.md, REPRODUCIBILITY.ko.md를 읽고
현재 코드와 실제 서버 상태를 비교해주세요.

이번 첫 세션은 공식 환경 smoke, 원격 조작과 짧은 데이터 저장,
π0.5의 공식 제출 환경 추론 가능성 검증부터 시작합니다.
기존에 설치되거나 동작한다고 가정하지 말고 상태와 근거를 기록해주세요.
아직 없는 streaming/AI 수집/변환 도구는 구현 상태를 확인하고 추가해주세요.

물리·평가·공식 action 규격을 바꾸지 마세요.
AI operator에는 허용된 카메라와 public robot observation만 전달하고,
info/raw/audit/seed/정답 위치를 노출하지 마세요.

작업마다 실제 명령·버전·소요 시간·검증 결과와 다음 작업을 남겨주세요.
정상 저장·원격 업로드·checksum 확인을 마친 뒤 세션을 종료해주세요.
문서의 계획을 실제 성공으로 표시하지 말고 증거가 있는 항목만 갱신해주세요.
```

## 종료 전에

export·학습 저장이 끝났는지 확인하고 데이터·모델·증거를 HF에 업로드합니다. 원격 revision과 checksum을 검증한 뒤 코드·실험 보고서·STATUS를 GitHub에 반영합니다. 새 서버에서 바로 실행할 다음 명령과 아직 해결하지 못한 문제를 기록합니다. GPU 서버 종료·삭제는 이 확인 뒤에 진행합니다.
