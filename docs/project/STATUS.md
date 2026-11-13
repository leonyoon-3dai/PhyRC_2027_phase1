# 현재 상태

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [다음 수집](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

**E27까지 마감. 새 수집은 중지 상태입니다.** E28 이후는 옷 양옆에서 아래 입구를 펼쳐 마네킹의 한 손목부터 양 손목으로 이어가는 [새 계획](../COLLECTION_PLAN.md)입니다. 과거 same-arm/E27-928 후보는 미실행 이력으로 보존합니다.

| 구분 | 확인된 상태 |
|---|---|
| 마지막 실행 | `20261107-astra-regrasp698-progress-named-001` (E27) |
| 수집 | 1,159전이 / 57.95 시뮬레이션초 / 2,450.624초 실제 경과 |
| 구성 | 698 재실행 + 334 모델 행동 + 126 정착 + 1 예산 종료 |
| 모델 | 23호출, 22 act, depth 질의 1회. `decision_budget` 종료 |
| 기술 검사 | 1,159 / 1,159, 오류 0, capture complete |
| 공식 평가기 | raw 5/50, pickup 5, dressing 0, success false, final_score 0 |
| 학습 승인 | unreviewed. 새 시연을 학습한 성능 결과 없음 |
| 원본 백업 | 고정 revision, 재다운로드와 254개 member 검증 완료 |

[실행 manifest](../collection/attempts/20261107-astra-regrasp698-progress-named-001/manifest.json) / [장면 리뷰](../collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md) / [백업 receipt](sessions/20261107-e27-backup-verification.json)

`capture complete`와 `operator_finished`는 모델의 자율 완수나 착의 성공을 뜻하지 않습니다. 위 결과는 보존 기록이며 이번 문서 개편에서 서버·모델·GPU 검사를 다시 수행하지 않았습니다.

시연 원본과 실행 코드는 변경하지 않았습니다. 새 서버의 준비·검사는 [OPERATIONS](../OPERATIONS.md), 실험 목표와 분기는 [COLLECTION_PLAN](../COLLECTION_PLAN.md), 이전 상세 상태는 [보관함](../ARCHIVE.md)을 따릅니다.
