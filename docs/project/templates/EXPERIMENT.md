# 실험 기록

복사용 템플릿입니다. 실행 전 계획과 측정 결과를 구분해 작성하고, 고유 run ID로 보관합니다.

| 항목 | 값 |
|---|---|
| Run ID / 날짜 | `<UTC-ID>-<name>` / `<UTC 및 UTC+9>` |
| 단계·상태 | `<collect/train/eval/restore/submit>` / `<planned/running/completed/failed>` |
| 질문·가설 | `<이번에 확인할 한 가지>` |
| 기준선과 변경점 | `<한 번에 무엇을 바꾸었는지>` |
| 참가자·upstream commit | `<SHA>` / `<SHA>` |
| Dataset / model revision | `<repo@immutable-commit>` / `<repo@immutable-commit>` |
| 환경·image digest | `<hardware/software 기록 링크>` |

## 실행 조건

- 정확한 명령과 config:
- 관측·state·action 및 전처리 revision:
- 수집 출처: `human` / `gpt` / `human_corrected_gpt` / `learned_policy`
- GPT 수집 시 모델 ID, 프롬프트 revision, 허용 관측, 실행한 도구·행동 기록:
- train/validation episode와 배치 분리:
- 학습 step / 처리 샘플 수 / effective epochs:
- 평가 seed 목록, episode 예산, policy RNG, chunk 실행 설정:

평가 seed·점수·audit 정보를 정책 입력으로 제공하지 않습니다.

## 측정 결과

| 항목 | 값·근거 |
|---|---|
| 유효 episode / 전체 episode | `<실패와 무효 실행도 기록>` |
| raw points / rate points / points/s | `<평균 및 episode별 원본 링크>` |
| success | `<성공 수 / 전체 수, 판정 기준>` |
| 공식·로컬 구분 | `<debug / local evaluation / leaderboard>` |
| wall / simulation / score 시간 | `<각각 측정>` |
| compile / warm step / 추론 지연 | `<측정 범위와 단위>` |
| VRAM·RAM·CPU·GPU·I/O | `<측정 로그>` |
| 서버 사용 시간·비용 | `<실제 요율과 계산 근거>` |

아직 측정하지 않은 값은 `not measured`로 남깁니다. 집기 점수와 완전 착의 성공을 혼동하지 않습니다. 평균에서 실패한 seed를 제외하지 않습니다.

## 시각적 증거

- 원본 영상과 checksum:
- 시작·milestone·실패 프레임 및 simulation timestamp:
- 재생 속도와 카메라 이름:
- 공식 시연 / 자체 인간 시연 / GPT 조작 / 학습 정책 rollout 구분:

## 해석과 다음 실험

- 관찰한 사실:
- 근거가 부족한 해석:
- 실패 원인 후보:
- 다음 변경과 완료 조건:

## 제출·복원

- 제출 후보 ZIP checksum, 자체 검사 명령·결과:
- Codabench ID·제출 시각·상태:
- 주최 측 점수·검증 상태: `<pending이면 명시>`
- 새 서버 복원에 사용한 revision·소요 시간·검증:
- 보관한 params / optimizer·step·RNG / norm stats·tokenizer:

accepted 상태만으로 성능을 주장하지 않습니다. [실험 인덱스](../../../experiments/README.md)에 연결하고 이전 원본을 덮어쓰지 않습니다.
