# 코드 지도: 관측에서 수집 파일과 정책 실행까지

[챌린지와 전체 흐름](../../README.md) · [현재 상태](STATUS.md) · [새 서버 준비](START_HERE.ko.md) · [연구 계획](RESEARCH_ROADMAP.ko.md) · [수집 기록](../collection/README.ko.md)

**확인 기준: 2026-11-06, 소스 `fb288520bd1109c606e23ca0ced41aa9a38ab9e9`.** E15까지 마감하고 수집을 중지했습니다. 아래 표는 코드의 역할을 설명하며 실행 재개 명령을 대신하지 않습니다.

## 1. 처음 볼 파일

| 알고 싶은 것 | 먼저 읽을 파일 | 핵심 역할 |
|---|---|---|
| 환경을 어떻게 켜는가 | [`run.sh`](../../run.sh), [`Dockerfile`](../../Dockerfile) | 공식 컨테이너 환경의 실행 진입점 |
| 새 서버를 어떻게 확인하는가 | [`participant/ops/bootstrap.sh`](../../participant/ops/bootstrap.sh) | 호스트 점검과 build·prepare·smoke |
| 로봇이 무엇을 보고 어떻게 움직이는가 | [`config/policy_interface.json`](../../config/policy_interface.json) | 공개 관측, 카메라 순서, 행동 채널과 주기 |
| 사람은 어디서 조작하는가 | [`Teleop_TShirt_Stretch4_Env.py`](../../src/PhyRC_Sim/Env_StandAlone/Teleop_TShirt_Stretch4_Env.py) | 장면 구성, 사람 조작과 기록 |
| Astra 수집은 어디서 시작하는가 | [`participant/collection/codex_client.py`](../../participant/collection/codex_client.py) | 관측 준비, 모델 호출, 실행 조율, 기록과 종료 |
| 현재 어디서 멈췄는가 | [E15 종료 검토](../collection/reviews/20261106-astra-opening264-001.ko.md) | 5점·첫 소매0·자율 종료. 각 파지·입구·손 관계가 다음 진단 후보 |

실제 설치·복원·검사 명령은 [새 서버 준비 문서](START_HERE.ko.md)를 기준으로 합니다. 명령을 실행하기 전에 현재 중지 상태와 다음 수정 순서를 확인합니다.

## 2. 자동 수집의 코드 연결

| 순서 | 파일·주요 함수 | 입력과 출력 |
|---|---|---|
| 공개 관측 준비 | [`codex_client.py`](../../participant/collection/codex_client.py)의 `prepare_observation()` | 공개 관측을 RGB 이미지·상태 JSON·depth 요약으로 변환 |
| 선택 입력 추가 | `replay_image_context()`, [`wrist_depth.py`](../../participant/collection/wrist_depth.py) | 같은 새 에피소드의 과거 RGB 또는 현재 양 손목 depth 패널. E15는 패널만 추가 |
| 모델 호출 | [`codex_actor.py`](../../participant/collection/codex_actor.py)의 `Actor.invoke()` | 허용 공개 입력과 JSON schema를 격리된 CLI에 전달하고 최종 응답 수신 |
| 행동 검사 | [`plans.py`](../../participant/collection/plans.py), [`boundary.py`](../../participant/collection/boundary.py) | 형식·로봇 순서·유한값·범위·단계 수 검사 |
| 요청·응답 | `codex_client.py`의 `Simulator.dispatch()` | JSON Lines로 `observe`, `act`, `stop`, `finish_episode` 전달 |
| 환경 적용 | [`scripts/collect_operator.py`](../../scripts/collect_operator.py), [`Policy/environment.py`](../../src/PhyRC_Sim/Policy/environment.py) | 두 로봇 행동 적용, 다음 공개 관측 반환 |
| 선택 중립 대기 | `codex_client.py`의 `--post-action-settle-steps` | 움직임 뒤 중립 전이 추가. `action_source=controller_settle`로 모델 행동과 구분 |
| 단계 시간 계측 | [`step_profile.py`](../../participant/collection/step_profile.py) | capture·그 외 observe·그 외 step의 수치 시간. 기본OFF, E15에 v1 적용 |
| 학습 자료 기록 | [`training_dataset.py`](../../src/PhyRC_Sim/Policy/training_dataset.py) | 매 전이의 관측·실제 적용 행동·다음 관측을 HDF5에 저장 |
| 별도 평가 | [`evaluation.py`](../../participant/collection/evaluation.py) | 공식 점수·획득 이벤트·success를 검수 영역에 기록 |
| 전수 검사 | [`validate_capture.py`](../../participant/collection/validate_capture.py) | 완료 파일·해시·전체 전이·시간·관측·평가 정합성 보고서 |
| 웹 공개 자료 | [`export_report.py`](../../participant/collection/export_report.py) | 선별 이미지·영상·프롬프트·최종 행동·평가 요약 패키지 |

### 두 로봇이 공유하는 행동 계약

| 항목 | 현재 의미 |
|---|---|
| 실행 행동 | `float32 (2,9)`. 행0은 robot_0, 행1은 robot_1 |
| 앞 8열 | 전후·좌우·회전·lift·arm·wrist yaw/pitch/roll의 정규화 속도 비율 |
| 마지막 열 | gripper: `>0.5` 닫기, `<-0.5` 열기, 나머지는 기존 의도 유지 |
| 기록 주기 | 20 Hz. 전이 하나는 simulation 0.05초, physics 12 tick |
| 모델 결정 | 한 결정이 여러 전이에 대응. Astra를 매 0.05초마다 호출하는 구조가 아님 |
| 다중 행동 | 고정 행동 목록을 전체 검사한 뒤 실행. 목록 자체가 조건부 복구 제어기는 아님 |

기본 입력은 RGB5, 전체 공개 로봇 상태, 카메라별 **16×16 depth 중앙값 격자**입니다. E15는 현재 양 손목의 256×256 depth를 고정 회색 범위로 그린 **패널1장**도 받았습니다. 따라서 E15 입력은 RGB5+depth패널1이며 과거 이미지 주입은 없습니다. 원본 depth·유효 마스크도 보존합니다. 패널은 수치 원본이나 가려진 표면을 대신하지 않습니다.

E15의 단일 움직임 결정 뒤 중립6전이(0.3 simulation초)를 추가했습니다. 총21구간·126전이이며 모델 동작221, E07 재실행264와 구분해 기록했습니다. 중립은 그리퍼 의도를 유지하지만 실제 관절·천의 정지나 파지 성공을 보장하지 않습니다. [실제 동작·중립 기록](../collection/reviews/20261106-astra-opening264-001.ko.md)

E09의 미응답 요청 위에 종료 명령을 보내던 문제는 **이미 수정·회귀 검증을 완료**했습니다. 현재 신호 처리는 진행 중 응답을 완료한 경계를 따릅니다. 기존 E09 실패 원본을 고쳐 성공으로 바꾸지는 않았습니다.

### 개발 세션과 행동 세션의 경계

`boundary.py`는 공개 필드·행동 계약을 검사하는 코드입니다. 운영체제 격리는 `codex_actor.py`가 별도 Docker 파일시스템·내부망·제한된 연결로 구성합니다. 행동 세션에는 저장소 전체, audit, 점수, seed, 내부 옷·마네킹 상태를 연결하지 않습니다.

기본 backend는 `exec`입니다. [`codex_app_actor.py`](../../participant/collection/codex_app_actor.py)의 App Server 경로는 실제 2턴 호환성 검증 미통과로 보류합니다. [`gpt_client.py`](../../participant/collection/gpt_client.py)는 별도의 Responses API 연결 시험이며 현재 CLI 수집 경로가 아닙니다.

자동 수집의 WebRTC 코드는 관찰 전용이지만 **현재 운영은 Chrome·WebRTC OFF**입니다. 큰 사건별 GIF/MP4를 [GitHub 갤러리](../gallery/README.ko.md)에서 검토합니다. 사람 조작 화면과 자동 수집 사이의 제어권 전환은 아직 구현 전이며 과거 브라우저 안내를 재개의 필수 조건으로 두지 않습니다.

## 3. 수집이 끝나면 어느 파일을 보는가

| 위치 | 대표 파일 | 확인할 내용 |
|---|---|---|
| `output/collections/<run-id>/` | `policy.hdf5` | 공개 RGB-D·상태·실제 행동·다음 관측 |
| 같은 폴더 | `audit.hdf5`, `evaluation_summary.json` | 시간·검수·공식 평가. 정책 입력으로 사용하지 않음 |
| 같은 폴더 | `capture.json`, `validation.json` | 파일 완료·해시·전수 기술 검사 |
| `output/operator-traces/<run-id>/` | `attempt.json`, `decisions.jsonl` | 시도 관계·결정·실제 실행 구간·오류·종료·시간 |
| 같은 폴더 | `prompt.txt`, `source_snapshot/` | 실제 프롬프트와 실행 코드의 출처 |
| 같은 폴더 | `score_segments.json` | 점수 획득 시각·전이 경계·후속 분기 색인 |
| `output/actors/<run-id>/` | 공개 관측 재현 자료·CLI runtime | actor용 입력과 비공개 세션 자료. 통째로 공개하지 않음 |
| `docs/collection/attempts/<run-id>/` | 공개 README·manifest·이미지·영상 | 웹에서 검토할 수 있도록 선별한 자료 |

**파일 정상 마감, 기술 검사 통과, 학습 승인, 공식 점수와 착의 success는 서로 다른 상태입니다.** `stage`는 모델의 작업 의도이며 공식 해당 항목의 득점을 뜻하지 않습니다. E15는611/611전이 통과·5/50·success=false·학습 승인 unreviewed입니다.

재시도는 새 `run ID`와 `parent_attempt`, 변경 이유를 기록합니다. `source_group`은 같은 복원 출처의 자료가 학습과 검증에 섞이지 않도록 묶는 단위입니다. [세부 폴더·라벨 규약](../collection/README.ko.md)

### 재실행과 분기

[`continuation.py`](../../participant/collection/continuation.py)의 `load_replay_prefix()`는 완결 원본의 전수 검사·SHA를 확인하고 공개 행동을 읽습니다. 신뢰된 수집기가 초기 배치를 구성한 뒤 `iter_action_chunks()`로 실제 명령을 재실행합니다. [`milestones.py`](../../participant/collection/milestones.py)는 점수 구간과 분기 입력의 색인을 지원합니다.

이 과정은 정확한 물리 상태 snapshot 복원이 아닙니다. 원본 점수를 새 시도에 복사하지 않으며 새 관측과 공식 평가를 다시 기록합니다. [재실행·분기 가이드](../collection/guides/continuation-and-branches.ko.md)

## 4. 수집 자료를 정책으로 바꾸는 코드

| 단계 | 파일 | 현재 계약 |
|---|---|---|
| 승인 자료 선택 | [`participant/pi05/data.py`](../../participant/pi05/data.py) | SHA·complete·source group·split 검사. 현재 `approved_pipeline_test`만 허용 |
| 입력 변환 | [`preprocessing.py`](../../participant/pi05/preprocessing.py) | overview와 두 wrist RGB 3장, state32 |
| 행동 변환 | 같은 파일의 `pack_actions()` | 실제 행동18 뒤에 14개를 padding해 모델 폭32 구성 |
| 모델 설정 | [`config.py`](../../participant/pi05/config.py) | OpenPI/JAX π₀.₅, horizon10, VLM·Action Expert LoRA variant |
| 학습 | [`train.py`](../../participant/pi05/train.py) | train 자료 정규화 통계, 고정 OpenPI trainer, 모델·optimizer 저장 |
| 추론 | [`participant/policy.py`](../../participant/policy.py) | 오프라인 bundle 로딩, 행동 청크 생성, 앞18개를 `(2,9)`로 복원 |
| 포장·검사 | [`participant/ops/package.py`](../../participant/ops/package.py), [`selfcheck.sh`](../../participant/ops/selfcheck.sh) | 제출 묶음 생성·검사. selfcheck의 고정 소스 기준 재검토 필요 |

state32는 관절 위치26, 손끝 원점 거리2, 닫기 의도2, 직전 gripper 명령2를 이어 붙인 값입니다. 실제 파지 여부나 32개의 물리 자유도를 의미하지 않습니다.

학생은 길이10 청크를 생성하고 bundle의 `execute_steps`에 따라 앞 **1~10개**를 순서대로 실행합니다. `policy.py` 파일 하나만으로 실행되지 않으며 `bundle.json`, 모델 파라미터, tokenizer, 정규화 통계와 고정 OpenPI 코드가 필요합니다.

현재 수집 교사는 RGB5·depth 요약·과거 문맥을 사용하지만 기존 학생은 RGB3·state32를 사용합니다. 이번 실제 시연의 학습 승인과 입력 차이 검토가 선행되어야 합니다. 과거 30 update는 연결 시험이며 이번 자료로 새 기준선을 학습한 결과는 아직 없습니다.

## 5. 연구 코드와 실행 코드 구분

[`participant/research/`](../../participant/research/)의 `depth_backprojection.py`, `color_depth_roi.py`, `color_pair_comparison.py`, `action_encoding.py`는 공개 기록의 사후 비교와 변환 시험에 사용했습니다. 현재 Astra actor에 자동 적용되는 모듈로 설명하지 않습니다.

픽셀 depth 조회·통합 초안과 단계 계측v2는 **미적용 후보**로 비공개 인계에 보존했습니다. 실제 CLI2턴·수집 통합 검증을 마친 기능으로 쓰지 않습니다. 기존 실행 기록의 전체208 CPU 통과와 모델 없는 GPU6/6전이 검사는 계측v1 등의 당시 검사 근거이며, 이번 문서 정리에서 재실행한 검사가 아닙니다. [범위와 수치](performance/20261106-speedup-plan.ko.md)

연구별 실제 검사 범위와 다음 실험은 [연구 계획](RESEARCH_ROADMAP.ko.md), 데이터·영상 근거는 [수집 기록](../collection/README.ko.md)에서 찾습니다. 과거 소스 기준의 [개발 컨텍스트](CODEX_CONTEXT.ko.md)는 기술 참고 자료이며 현재 실행 상태는 [STATUS](STATUS.md)를 따릅니다.
