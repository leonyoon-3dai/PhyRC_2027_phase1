# PhyRC 2027: 두 로봇의 협력 착의 챌린지

[공개 시연 갤러리](docs/gallery/README.ko.md) · [수집 과정·일지](docs/collection/README.ko.md) · [공식 원본 안내](README.upstream.md) · [새 서버 준비](docs/project/START_HERE.ko.md) · [다음 작업 상태](docs/project/STATUS.md) · [공식 대회](https://emprise.cs.cornell.edu/phyrc/challenge-2027/)

두 대의 Stretch 4가 앉아 있는 마네킹에 티셔츠를 입히는 시뮬레이션 과제입니다. 이 저장소는 공식 시뮬레이터에 시연 수집, 브라우저 조작, 데이터 검수, π₀.₅ 학습 및 제출 도구를 추가한 참가자 저장소입니다.

## 직접 수집한 시연 화면

**[공개 시연 갤러리](docs/gallery/README.ko.md)**에서 사람 부분 시연, Astra의 접근·파지 시도, 작은 움직임 연결 시험의 영상·원본 화면·짧은 행동 응답을 볼 수 있습니다.

맥북 Chrome에서 두 로봇을 직접 조작한 **접근 → 파지·들기 → 마네킹 쪽 운반** 장면입니다. 아래 화면은 실제 기록을 재생해 렌더링한 것으로, AI로 합성한 성공 장면이 아닙니다.

| ① 옷에 접근·정렬 | ② 양쪽 파지 후 들어 올리기 | ③ 마네킹 쪽으로 운반 |
|:---:|:---:|:---:|
| [![옷 양옆에서 두 로봇을 정렬하는 직접 시연](docs/project/assets/visual-20261027/human-demo-t08.jpg)](docs/project/assets/visual-20261027/human-demo-t08.jpg) | [![두 로봇이 옷을 잡아 들어 올린 직접 시연](docs/project/assets/visual-20261027/human-demo-t20.jpg)](docs/project/assets/visual-20261027/human-demo-t20.jpg) | [![옷을 유지하며 마네킹 쪽으로 운반하는 직접 시연](docs/project/assets/visual-20261027/human-demo-t29.jpg)](docs/project/assets/visual-20261027/human-demo-t29.jpg) |

**[▶ 33초 편집 시연 영상 보기](docs/videos/20261026-human-pickup-transport.mp4)** · [기록과 화면의 출처](docs/project/DEMO_20261026.ko.md)

고정 연습 배치에서 수집한 부분 시연입니다. **이 시연의 공식 점수, 소매·목 통과와 전체 착의 성공은 확인하지 않았습니다.** 화면의 각 단계에 임의의 점수를 붙이지 않습니다.

## 후속 확장: 0점에서 50점까지

아래 그림은 첫 5점 검토 이후의 확장 목표와 공식 평가 항목을 연결한 **설명용 점수 지도**입니다. 현재 득점 검토 기준은 5점이며, 그림은 직접 달성한 점수 기록이나 성공 시뮬레이션 화면이 아닙니다.

[![0점 준비부터 픽업 5점, 첫 소매 10점, 반대 어깨 15점, 두 번째 소매 20점, 왼쪽 위팔 25점, 오른쪽 위팔 30점, 목 통과 40점, 앞면 방향 50점까지의 누적 예시](docs/project/assets/score-roadmap-20261104/score-roadmap.ko.svg)](docs/project/assets/score-roadmap-20261104/score-roadmap.ko.svg)

**각 항목을 그림 순서로 획득할 때의 누적 예시**이며 실제로는 순서가 달라지거나 여러 항목이 함께 인정될 수 있습니다. 누적 점수는 유지되므로 **50점과 성공 판정은 별도**입니다. 성공은 두 손·머리·옷 앞면 조건을 동시에 0.5초 유지했는지 확인합니다. [공식 평가 정의](docs/competition/EVALUATION.md)

다음 수집에서는 먼저 **접근·파지·들기의 반복 가능한 시연**을 확보하고, 실제 점수를 확인하면서 소매·어깨·목·방향 단계로 확장합니다.

**오늘의 우선순위는 빠른 득점보다 안정적인 시연 데이터 수집 시스템과 다양한 방법의 과정 기록입니다.** Codex CLI의 Astra로 단계별 실험을 이어가며 첫 공식 누적 5점에서 과정을 리뷰합니다. 50점·다양한 완주 경로·검수한 시연을 이용한 로컬 정책 학습은 이후 목표입니다.

## 현재 기술 상태

**2026-11-06:** 기존 L40S에서 환경 복원과 WebRTC 연결을 확인하고, 격리된 Codex CLI `gpt-6-astra`/`ultra`의 실제 로봇 wiring을 완료했습니다. 첫 착의 시도는 SIGTERM으로 중단됐으며 167전이를 정상 보존·검사했습니다. **공식 평가는 0점·success=false로 현재 목표 5점에 도달하지 못했습니다.**

| 확인한 것 | 결과와 한계 |
|---|---|
| 공식 환경 | build·prepare·smoke 통과, 맥북 Chrome 실시간 영상 확인 |
| Codex CLI | 0.166.0, Astra `ultra`, 실제 이미지 2턴·JSON·동일 UUID 재개 통과 |
| 실제 로봇 wiring | 3개 모델 결정·3전이·0.15 simulation초, 정상 종료·전체 전이 검사 통과 |
| wiring 공식 평가 | 유효 평가 0점·success=false·no_contact. 성공 시연으로 집계하지 않음 |
| 기술 검사 | 계측·계획 실행·공개 패키지 도구를 포함해 CPU 85개 통과. 과제 시연 승인과 구분 |
| 행동 입력·격리 | 공개 RGB 5장·전체 공개 로봇 상태·16×16 depth 요약. 저장소·평가·audit·원시 상태와 actor의 파일·네트워크 경계를 분리 |
| 관찰·개입 | 자동 수집 WebRTC는 관찰 전용. 사람과 모델의 제어권 전환은 미구현 |
| 실제 착의 시도 | `20261106-astra-dressing-001`: 15개 완료 결정·167전이·8.35 simulation초, SIGTERM 중단 후 정상 파일 마감. 점수0·success=false |

## 수집 과정을 자세히 읽기

**[시연 데이터 수집 과정 목차](docs/collection/README.ko.md)**에서 폴더 구조·네이밍·공개/비공개 자료·프롬프트·최종 행동·이미지·영상·점수·시간·피드백 기준을 확인할 수 있습니다.

**[2026-11-06 수집 일지](docs/collection/sessions/2026-11-06.md)**에는 환경 복원부터 실제 모델 호출, 실패 원인 분리, r1~r5 재시도, 정상 wiring과 첫 착의 시도까지의 과정·명령·측정 근거를 기록합니다. 성공·부분 성공·실패·중단을 모두 보존하고, 같은 physics tick의 점수 획득은 동시 batch로 다룹니다. 수집 중 피드백과 반영 내용도 이 일지에 갱신합니다.

[실제 wiring 이미지·영상·프롬프트·행동 기록 보기](docs/collection/attempts/20261106-codex-robot-wiring-r5/README.ko.md)

[첫 착의 시도 전체 기록·33.4초 관측 영상](docs/collection/attempts/20261106-astra-dressing-001/README.ko.md) · [종료·검수 결과](docs/collection/reviews/20261106-astra-dressing-001.ko.md) · [토큰 집계 정정](docs/collection/corrections/20261106-token-accounting.ko.md)

[첫 착의 시도의 속도·난도 분석](docs/collection/sessions/2026-11-06-initial-review.md)은 완료된 첫 10개 판단만 고정해 검토한 중간 기록입니다.

**[5점 수집을 위한 호출 지연 개선 가이드](docs/collection/guides/call-latency-options.ko.md)**는 조건부 계획·로컬 피드백·상주 프로세스 등의 비교 근거입니다. 최신 피드백에 따라 계측 수정·상주 호출 pilot·짧은 다중 행동을 순차 실험하며 각 변경과 결과를 기록합니다.

메인 README는 기술 상태와 문서 입구를 유지합니다. 상세 개발·수집 과정은 별도 페이지에 한국어로 기록하고, 인증·개인 접속 주소·내부 상태·숨겨진 모델 추론은 게시하지 않습니다.

## 코드 길잡이

| 경로 | 역할 |
|---|---|
| [`codex_actor.py`](participant/collection/codex_actor.py) | 별도 Docker에서 CLI·공개 이미지·구조화 응답·명시적 세션 재개·timeout 처리 |
| [`codex_client.py`](participant/collection/codex_client.py) | 관측 전달·행동 검사·실행, 단계·재시도·시간·출처 기록 |
| [`collect_operator.py`](scripts/collect_operator.py), [`boundary.py`](participant/collection/boundary.py) | 공식 행동 경계와 실제 20 Hz 관측·행동·다음 관측 저장 |
| [`evaluation.py`](participant/collection/evaluation.py) | 같은 시도의 공식 점수·획득 이벤트·success를 행동 문맥 밖에 저장 |
| [`validate_capture.py`](participant/collection/validate_capture.py) | 파일 해시·전체 전이·시간·연속성·평가 라벨 검사. 학습 승인은 별도 |
| [`collector_stream.py`](participant/streaming/collector_stream.py) | 물리 시간을 진행하지 않는 관찰용 WebRTC 렌더링 |
| [`participant/pi05/`](participant/pi05/), [`policy.py`](participant/policy.py) | 후속 π₀.₅ 학습·로컬 정책 실행. 실제 승인 시연으로 새 학습을 수행한 상태는 아님 |

기존 [`gpt_client.py`](participant/collection/gpt_client.py)는 별도 Responses API의 작은 시험 코드이며 현재 Codex CLI 경로를 대신하지 않습니다. API나 다른 모델로 자동 전환하지 않습니다.

## 재현과 다음 작업

[새 서버 준비](docs/project/START_HERE.ko.md)에 고정 CLI·actor 이미지, 공식 환경, WebRTC와 `--mode wiring` 실행·검사 명령을 정리했습니다. [현재 상태](docs/project/STATUS.md)에서 이어갈 한 가지 작업을 확인합니다. 실패 run ID와 완료 파일을 덮어쓰지 않습니다.

현재는 **안정적인 수집 시스템·다양한 방법의 비교·자주 공유하는 과정 기록**을 우선합니다. Astra와 `ultra`를 유지하며 계측 수정 → 상주 호출 pilot → 짧은 다중 행동을 순차 검증합니다. 계획과 실행·통과를 구분하고 첫 5점 리뷰 조건은 유지합니다. 이후 50점과 다양한 경로 수집, 여러 VLA baseline의 공통 조건 비교, RL·world model 활용을 검토합니다. 이 후속 학습·평가는 아직 실행하지 않았습니다. [세부 데이터·실험 계획](docs/collection/README.ko.md)

## 참고 문서

- [공식 공개 관측 규칙](docs/competition/RULES.md), [데이터 구조](docs/competition/DATA.md), [정책 연결](docs/competition/POLICY.md), [공식 평가](docs/competition/EVALUATION.md)
- [기술 배경과 후속 실험 검토](docs/project/CODEX_CONTEXT.ko.md), [Stretch 4·Astra 조사](docs/project/research/STRETCH4_VLA_REVIEW.ko.md): 과거 계획보다 현재 README·수집 일지의 실행 상태를 우선합니다.
- [이전 세션 기록](docs/project/sessions/), [이전 결과](docs/project/RESULTS.ko.md), [이전 README](README.history.ko.md)
- [공식 시뮬레이터](https://github.com/rirolab/PhyRC_2027_Challenge), [원본 안내](README.upstream.md), [출처와 라이선스](THIRD_PARTY.md)
