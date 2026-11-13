# 현재 상태

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [다음 수집](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

**현재 진행 중: E29 `20261113-astra-side-hem738-continue20-001`.** 사용자의 후반 +20결정 요청으로 **2026-11-13 21:41:33 UTC**에 시작했습니다. 실행 소스는 `2baebcc381d707fd5aca5f69ea7518d326e8a80a`의 clean snapshot입니다. 직접 parent와 source group은 E28 `20261113-astra-side-hem-fresh-001`입니다.

E29는 E28의738전이를 새 환경에서 재실행하고, 새 replay 중682·714의 공개 관측을 기록한 뒤 기존 `coordinated-side-hem-wrists` 전략으로 최대20개 새 결정을 수행하도록 시작했습니다. 총1,400전이·10점 검토 기준, exec/gpt-6-astra/ultra·named actions·depth query·wrist panel·settle6·시간 계측을 유지합니다. **replay 완료나 새 득점·최종 QC는 아직 확인하지 않았습니다.** 이전5점을 복사하거나 정확한 천 checkpoint를 복구하는 방식이 아닙니다. 아래는 마지막 마감 시연 E28의 결과입니다.

**2026-11-13: E28을 마감했습니다. 로컬 공식 평가기는 5/50점, 픽업 5점·착의 0점, success=false입니다.** 측면 접근 전략으로 파지·들기·운반과 손 접근을 수행했지만 소매 통과는 확인되지 않았습니다. 50점 목표는 아직 달성하지 못했습니다.

| 구분 | 확인된 상태 |
|---|---|
| 마지막 마감 시연 | `20261113-astra-side-hem-fresh-001` (E28) |
| 시작·출처 | 새 reset, parent 없음, replay 0, 별도 source group. 실행 소스 `9f797722acdb0f8d35001175e3aaa7e07a8dd2f8`, 시작 시 clean |
| 실행 시각 | 2026-11-13 20:43:30–21:29:28 UTC |
| 수집 | 739전이 / 36.95 시뮬레이션초 / 2,758.774초 실제 경과 |
| 구성 | 516 모델 행동 + 222 정착 + 1 예산 종료 중립. 재실행 없음 |
| 모델 | 40판단·46호출, depth 질의 6회와 후속 응답 6회. 질의 중 물리 진행 0 |
| 종료·기술 검사 | 결정 예산 종료, completed·closed·finished, simulator 반환값 0, capture complete, 739/739 전수 QC 통과·오류 0 |
| 공식 평가기 | valid=true, raw 5/50, pickup 5, dressing 0, success=false. 첫 픽업 경계 371 |
| 학습 승인 | unreviewed. QC 통과와 학습·착의 성공은 별도 |
| 원본 백업 | 고정 revision `230c90a5d7abe76216311590f7764a65c19a946d` 재다운로드, archive SHA256·크기·402개 member 검증 완료 |

[실행 manifest](../collection/attempts/20261113-astra-side-hem-fresh-001/manifest.json) / [장면 리뷰](../collection/reviews/20261113-astra-side-hem-fresh-001.ko.md) / [전체 영상](../collection/attempts/20261113-astra-side-hem-fresh-001/overview.mp4) / [백업 receipt](sessions/20261113-e28-backup-verification.json) / [마감 기록](sessions/20261113-e28-close.ko.md)

별도 host exec session의 최종 반환값은 **143**이었습니다. simulator 반환값0·완료 파일·유효한 평가·전수 QC·원격 백업 검증을 각각 구분하며, host까지0이라고 주장하지 않습니다.

E28은 `coordinated-side-hem-wrists`, Codex CLI 0.166.0 / exec / gpt-6-astra / ultra, named actions·pixel depth query·wrist depth panel·plan-size 1을 사용했습니다. 최대 40판단·1,400전이, 이동 동작 후 중립 정착 최대 6전이, 10점 검토 종료 기준과 단계별 시간 계측을 적용했습니다. **10점은 검토 기준이며 실제 도달하지 않았습니다.**

E29는 **E28/738**에서 분기를 시작했으며, **E28/682**는 미실행 비교 후보입니다. 738은 마지막 새 행동·정착이 끝나고 종료 중립 1전이가 추가되기 전입니다. 380의 들어 올린 입구 후보와 264의 닫기 전 준비도 보존합니다. 이들은 같은 E28 계보의 상관된 경계이며 독립 성공 시연이 아닙니다. 원본 QC·백업과 공개 관측 검토 후 새 run ID로 분기하며, 정확한 천 상태 복원이나 이전 점수 복사는 아닙니다. [다음 수집 계획](../COLLECTION_PLAN.md) / [출발점 목록](../collection/catalog/README.ko.md)

과거 E27/928 same-arm 후보는 당시 미실행 계획으로 보존하며 실제 E28의 출발점이 아닙니다. E27의 1,159전이·픽업 5점 원본은 [과거 manifest](../collection/attempts/20261107-astra-regrasp698-progress-named-001/manifest.json), [리뷰](../collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md), [백업 receipt](sessions/20261107-e27-backup-verification.json)에 남습니다.

새 환경의 CPU 335개 검사, 실제 GPU smoke, 별도 wiring 3/3전이 QC와 [62개 member 백업 검증](sessions/20261113-wiring-backup-verification.json)은 환경 연결 근거입니다. 이 검사를 착의 성공으로 합산하지 않습니다. 과거 원본을 보존하고 시연 영상·분석·백업은 각각 실제 완료한 범위를 기록합니다.
