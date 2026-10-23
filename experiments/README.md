# Experiment index

Latest runtime: [October 23 clean-server session](../docs/project/sessions/20261023-clean-start.md), preceded by [October 22 baseline](../docs/project/sessions/20261022-bootstrap.md). Restore/smoke and minimal human-motion format checks passed; full 900-second checks were interrupted and no submission is established. Current scope is format/submission verification, with task demos/new training deferred.

`index.csv` may retain historical coverage; the linked session reports contain the detailed run IDs and evidence. Use the following process for future experiments.

1. [실험 템플릿](../docs/project/templates/EXPERIMENT.md)을 복사하여 `experiments/<run-id>/README.md`에 작성합니다. 이 경로는 각 실험 때 생성합니다.
2. 참가자·upstream commit, HF 데이터·모델의 불변 revision, 정확한 실행 조건을 고정합니다.
3. 실행 후 인덱스 한 행에 상태와 원본 보고서·영상·결과 위치를 연결합니다. 계획 행을 넣는 경우에도 `planned`로 표시하고 성능 값을 비워 둡니다.
4. 중단·재개 정보는 [세션 템플릿](../docs/project/templates/SESSION.md)으로 별도 남기고, 다음 실행 명령과 기대 결과를 기록합니다.

| 구분 | 공개할 근거 |
|---|---|
| 수집 | 인간/GPT/수정 시연 출처, 허용 관측, episode 완결성, 영상 |
| 학습 | 데이터 분리, step·샘플 수·effective epochs, 설정·checkpoint |
| 평가 | 같은 seed·예산의 기준선 비교, 전체 실패, episode별 점수·success |
| 복원 | 새 서버에서 사용한 revision, 복원 시간, 검증 결과 |
| 제출 | ZIP checksum, self-check, 제출 ID, accepted와 실제 점수의 구분 |

작은 요약·대표 이미지는 GitHub에, 큰 영상·데이터·가중치·로그는 HF에 저장합니다. 결과는 원본을 보존한 새 revision으로 갱신합니다. 공식 제공 영상과 자체 rollout은 명확히 구분합니다.

`raw_points`, pickup 제외 `rate_points`, `points/s`, `success`는 서로 다른 값입니다. 무효·실패 실행을 감추거나 실패 seed를 평균에서 제외하지 않습니다. 로컬 점수를 leaderboard 점수로 표시하지 않습니다.

CSV의 빈 수치는 미측정이며 0점이라는 뜻이 아닙니다. `report_path`는 저장소 기준 경로, artifact 열은 확인된 URL 또는 불변 revision 링크를 사용합니다. 개행·쉼표가 있는 값은 CSV 규칙에 따라 인용합니다.

[클린 서버·저장·재현 절차](../docs/project/REPRODUCIBILITY.ko.md)
