# 원격 조작과 자동 수집 설계

> 2026-10-22 실행 단계로 전환했습니다. 아래는 초기 설계·계획을 보존한 문서입니다. 실제 구현·측정·실패·미검증 항목은 [STATUS](STATUS.md), [첫 세션 기록](sessions/20261022-bootstrap.md), [실제 복원 명령](RECOVERY.ko.md)을 따릅니다. API 과금 없는 Codex 작성 제한 명령 데이터로 첫 경로를 검증하며 live GPT API는 사용하지 않습니다.

[프로젝트 README](../../README.md) · [초기 실행 계획](PLAN.ko.md) · [공식 수집 가이드](../competition/DATA.md)

기준일: **2026-10-22**. 두 경로를 준비하되 **현재 프로젝트에서 실행·검증한 기능은 없다.** 아래 연결 도구와 launcher는 추가 구현 대상이다.

## 두 조작 방식

| 항목 | Chrome 키보드 | Codex/GPT 자동 조작 |
|---|---|---|
| 판단 주체 | 사람이 화면을 보고 조작 | 모델이 허용 관측을 보고 다음 행동 결정 |
| 연결 | 브라우저 스트리밍 → 공식 키 입력·teleop | public observation → 조작 agent → 공식 `(2,9)` 행동 |
| 초기 목적 | 짧고 신뢰할 수 있는 인간 시연 확보 | 관측·행동·재관측과 자동 저장 경로 검증 |
| 주요 검증 | 키 release·동시 입력·numpad·포커스·지연 | 정보 allowlist·행동 유효성·지연·수집 정렬 |
| 첫 성공 기준 | 두 로봇 조작과 시연 한 개 정상 export | 짧은 이동·그리퍼 행동을 반복하고 정상 저장 |

완전 착의를 두 경로의 첫 기능 시험에 요구하지 않는다. 수집이 연결된 뒤 π₀.₅ 학습·실행·제출을 먼저 검증한다.

## Chrome에서 사람이 조작

[Isaac Sim 6.0.1 공식 스트리밍 문서](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/manual_livestream_clients.html)는 Chromium 기반 WebRTC viewer를 지원한다. 그러나 현재 [PhyRC `run.sh`](../../run.sh)에는 `web`·`webrtc` 모드가 없다. [SETUP.md](../competition/SETUP.md)도 원격 GUI를 공식 검증 범위 밖으로 명시한다.

공식 teleop Python 환경을 유지하면서 스트리밍을 연결하는 얇은 launcher를 만든다. 일반 Isaac Sim streaming 앱만 띄운 것을 PhyRC teleop 실행으로 간주하지 않는다. 환경의 물리·제어 주기·평가 방식은 유지한다.

| 점검 | 완료 기준 |
|---|---|
| 화면·GPU | 공식 장면과 두 로봇이 표시되고 실제 RTX 렌더링·NVENC 동작 확인 |
| 네트워크 | WebRTC signaling·media·viewer 경로 확인. 접속은 인증된 경로나 클라이언트 IP 제한으로 구성 |
| 키 입력 | key-down/up, 두 로봇 동시 입력, 그리퍼 toggle, reset·ESC 전달 |
| Mac 키보드 | robot_1의 `NUMPAD_n`을 실제로 보내거나 별도 키 매핑 사용. 일반 숫자열과 numpad를 구분 |
| 연결 전환 | 포커스 이탈·재접속·연결 종료 시 눌린 키와 대기 명령 해제 |
| 저장 | 짧은 시연 후 export·schema·시간 정렬 검사 통과 |

Isaac Sim의 기본 스트리밍은 인스턴스당 클라이언트 한 명용이다. 첫 Chrome 옵션은 운영자 한 명의 조작·관람으로 한정한다. 여러 명의 동시 방송은 초기 범위에 넣지 않는다.

처음에는 기존 recorder와 deferred rendering을 재사용한다. GUI가 닫힌 뒤에도 `[Dataset export] READY`를 기다리고, `capture.json`의 `status=ready`, `complete=true`를 확인한다. 라이브 스트리밍 화면과 학습용 5개 카메라의 live export는 다른 기능이다.

WebRTC 연동이 막히면 GPU 기반 원격 데스크톱을 대체 경로로 검증한다. Chrome 기능 때문에 수집·학습 일정 전체를 멈추지 않는다.

## Codex/GPT가 자동 조작

자동 경로는 브라우저의 키를 오래 누르는 방식보다 **허용된 관측과 공식 action을 연결하는 방식**으로 만든다. 화면 부하에 따라 wall-time key hold의 실제 이동량이 달라지는 문제와 포커스 의존성을 줄일 수 있다.

| 제안 도구 | 역할 |
|---|---|
| `observe()` | 지정된 카메라 이미지와 허용된 로봇 상태만 반환 |
| `act(actions, steps)` | 정규화된 `float32 (2,9)` 행동을 제한된 simulation step만큼 실행 |
| `stop()` | 대기 queue를 비우고 이동축에 중립 명령 적용. 그리퍼의 `0`은 이전 의도 유지 |
| `finish_episode()` | episode 종료·저장·검증 처리 |

이 도구들은 현재 저장소에 구현된 명령이 아니다. 최초 구현은 범위·dtype·NaN/Inf·step 수를 검사하고 공식 `DressingEnv.step()`으로만 로봇을 움직인다. 물체·옷·로봇 state를 직접 설정하는 조작 도구는 제공하지 않는다.

GPT는 저빈도 행동 결정자로 사용한다. 로컬 실행기가 매 0.05초 simulation step에서 관측·명령·기록을 담당하고, 짧은 행동 묶음 뒤 새 관측을 반환한다. 예를 들어 10 step은 시뮬레이션 시간 0.5초다. GPT가 20Hz로 응답하거나 처음부터 착의를 성공한다고 가정하지 않는다.

학습 수집은 환경의 step 호출과 외부 모델 응답 대기를 구분해 구현할 수 있다. API 대기·요청량·wall time은 따로 기록한다. 최종 제출 평가에서는 공식 runner의 시간 예산을 그대로 적용한다.

Codex는 [MCP 연결](https://developers.openai.com/codex/mcp/)로 전용 도구를 사용할 수 있다. GPT API의 [이미지 입력](https://developers.openai.com/api/docs/guides/images-vision)과 [함수 호출](https://developers.openai.com/api/docs/guides/function-calling)도 대안이다. 실제 사용할 연결과 모델은 첫 서버에서 확정하고 기록한다.

## 조작 agent에 전달하는 정보

[RULES.md](../competition/RULES.md)는 허용 관측에서 위치·특징을 추정하는 모델·제어기를 허용하고, 내부 정답 정보를 이용한 자동 시연·teacher·행동 label 생성을 금지한다. 따라서 public observation만 사용하는 자동 수집은 가능한 방향으로 해석한다. **이는 규정 문구에 따른 해석이며 GPT 자동 시연에 대한 주최 측의 명시적 승인으로 표현하지 않는다.**

| 전달 가능 | 조작 모델에 전달하지 않음 |
|---|---|
| 지정된 overview·두 wrist·두 head의 RGB·depth·valid mask | 자유롭게 움직인 GUI viewport·inspector 화면 |
| 공개 joint·base·gripper·fingertip 상태 | 옷·마네킹·의자 정답 pose, cloth particle/vertex |
| 공개 controller target·이전 행동·simulation time | seed·spawn·audit·평가 JSON·성공 판정 내부 정보 |
| 공개 정적 calibration과 행동 규격 | 물체 위치를 드러내는 동적 camera world matrix |

특히 [`DressingEnv`](../../src/PhyRC_Sim/Policy/environment.py)는 공개 `obs` 외에 내부 정보가 포함된 `info`도 반환한다. **`(obs, info)` 전체를 직렬화하지 않는다.** 허용 필드 목록으로 새 입력 객체를 만들고, 화면에도 점수·seed·spawn·정답 정보를 섞지 않는다. `env.render()`는 지정된 overview RGB를 반환하므로 자유 viewport 없이 관측 이미지를 얻을 수 있다.

구현용 Codex와 조작용 agent의 도구 범위를 구분한다. 조작 agent가 코드·파일·simulator API를 통해 내부 정보를 우회해서 읽지 않도록 구성한다. score·success는 별도의 결과 분석과 데이터 선별에만 사용하며 다음 행동을 정하는 관측에 넣지 않는다.

## 공통 데이터와 조작권 전환

두 경로는 공식 `obs → action → next_obs` 형식으로 기록한다. [현재 평가 실행기](../../scripts/evaluate_policy.py)는 점수·measurement를 저장하지만 자동으로 학습용 `policy.hdf5`를 만들지는 않는다. AI 경로에는 별도 수집 wrapper가 필요하다.

기존 [`DatasetWriter`](../../src/PhyRC_Sim/Policy/training_dataset.py)를 재사용해 `(2,9)` 행동, 12 physics tick, 0.05초 시간 정렬, `next_obs.previous_action` 일치를 확인한다. 새 수집기가 기존 deferred raw recorder의 모든 검증까지 자동으로 제공한다고 가정하지 않는다. raw 기록·재생·export 지원 범위는 실제 구현에 맞춰 명시한다.

| 기록 | 내용 |
|---|---|
| 조작 출처 | `human`, `gpt`, `human_corrected_gpt`와 전환 step |
| AI 추적 | 모델 식별자·프롬프트 버전·전달한 허용 관측·실제 명령·지연·오류 |
| 데이터 추적 | run/episode ID, 코드·데이터 revision, 시간 정렬 검증 결과 |
| 시각 기록 | 대표 카메라 영상과 전환·실패 시점 이미지 |

동일 세션에서 조작권은 한쪽만 가진다. 사람이 인계받으면 AI queue를 비우고 전환 지점을 기록한다. 인간 수정본과 원본이 서로 다른 train/validation split으로 흩어지지 않게 관리한다.

## 첫 기능 시험의 순서

1. 공식 smoke를 통과한다.
2. Chrome에서 두 로봇 이동·그리퍼·reset·종료를 확인하고 짧은 인간 시연을 저장한다.
3. 자동 경로에 허용 관측만 노출되는지 확인한다.
4. Codex/GPT로 짧은 이동·그리퍼 시도를 1–3회 실행하고 공통 데이터 형식을 검사한다.
5. 사람이 검토한 소량 데이터를 변환해 π₀.₅ 과적합 학습·rollout을 확인한다.
6. 외부 GPT·Chrome·개인 서버 없이 실행되는 제출 ZIP을 검증한다.

첫 단계는 파이프라인 시험이며 좋은 착의 시연 확보와 구분한다. 이후 인간 시연과 자동·수정 시연의 품질을 비교해 데이터 수집 비중을 결정한다.
