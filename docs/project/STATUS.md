# 현재 상태

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [다음 수집](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

**2026-11-13 사용자 재개 요청으로 E28 수집 진행 중입니다.** `20261113-astra-side-hem-fresh-001`은 20:43:30 UTC에 소스 `9f79772`의 새 reset에서 시작했습니다. replay prefix·직접 parent 없이 측면 파지와 밑단 펼침부터 시도하며, 최종 점수·종료·전수 QC는 아직 미확정입니다. 과거 same-arm/E27-928 후보는 이전 이력으로 보존합니다.

E28은 `coordinated-side-hem-wrists`, Codex CLI 0.166.0 / exec / gpt-6-astra / ultra, named actions·pixel depth query·wrist depth panel·plan-size 1을 사용합니다. 최대 40판단·1,400전이, 동작 후 중립 정착 최대 6전이, 10점 검토 종료 기준과 단계별 시간 계측을 적용했습니다. **10점은 실행의 검토 기준이며 달성 기록이 아닙니다.** [환경·연결 검사 receipt](sessions/20261113-environment-setup.json) / [전략 검토](../collection/research/2026-11-13-side-hem-wrists.ko.md) / [수집 계획](../COLLECTION_PLAN.md)

아래는 **마지막 마감 시연 E27**의 보존된 결과입니다. 완료된 시도의 최고 기록은 여전히 5/50점입니다.

| 구분 | 확인된 상태 |
|---|---|
| 마지막 마감 시연 | `20261107-astra-regrasp698-progress-named-001` (E27) |
| 수집 | 1,159전이 / 57.95 시뮬레이션초 / 2,450.624초 실제 경과 |
| 구성 | 698 재실행 + 334 모델 행동 + 126 정착 + 1 예산 종료 |
| 모델 | 23호출, 22 act, depth 질의 1회. `decision_budget` 종료 |
| 기술 검사 | 1,159 / 1,159, 오류 0, capture complete |
| 공식 평가기 | raw 5/50, pickup 5, dressing 0, success false, final_score 0 |
| 학습 승인 | unreviewed. 새 시연을 학습한 성능 결과 없음 |
| 원본 백업 | 고정 revision, 재다운로드와 254개 member 검증 완료 |

[실행 manifest](../collection/attempts/20261107-astra-regrasp698-progress-named-001/manifest.json) / [장면 리뷰](../collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md) / [백업 receipt](sessions/20261107-e27-backup-verification.json)

`capture complete`와 `operator_finished`는 모델의 자율 완수나 착의 성공을 뜻하지 않습니다. 위 E27 결과는 과거 보존 기록입니다. 2026-11-13 새 환경에서는 CPU 335개 검사, 실제 GPU smoke, 별도 wiring 3/3전이 QC를 통과했으며 wiring 원본은 [고정 백업 revision과 62개 member 검증](sessions/20261113-wiring-backup-verification.json)을 완료했습니다. 이 연결 시험은 E28 착의 결과가 아닙니다.

과거 시연 원본은 보존합니다. 새 서버의 준비·검사는 [OPERATIONS](../OPERATIONS.md), 실험 목표와 분기는 [COLLECTION_PLAN](../COLLECTION_PLAN.md), 이전 상세 상태는 [보관함](../ARCHIVE.md)을 따릅니다. E28은 마감·검수 후 결과와 보존 receipt를 추가합니다.
