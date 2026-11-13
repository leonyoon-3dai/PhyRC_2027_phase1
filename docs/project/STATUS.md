# 현재 상태

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [다음 수집](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

**E30을 마감했고 E31은 준비 단계입니다.** E30의 유효한 로컬 공식 평가기 원점수는 **5/50·픽업5·착의0·success=false**이며 **새 구간 득점은0**입니다.50점 목표는 달성하지 못했습니다. E31은 E28/682·새 history632/668에서 같은 대각선 진입 전략·최대20결정을 비교할 계획이며 아직 시작하지 않았습니다. [E31 계획](sessions/20261113-e31-plan.ko.md)

| 구분 | 확인된 E30 상태 |
|---|---|
| 마지막 마감 시연 | `20261113-astra-diagonal738-001` |
| 시작·출처 | clean source `7eaae3e6b56ce938237b873bcb1540470a449b79`; 직접 parent/source group 모두 E28 `20261113-astra-side-hem-fresh-001` |
| 재실행 | prefix738 완료, 새 replay 관측682·714 사용. 정확한 천 checkpoint 복원 아님 |
| 실행 시각 | 2026-11-13 22:31:59–23:02:50 UTC |
| 수집 | 915전이 /45.75시뮬레이션초 /1,850.453초(약30.84분) 실제 경과 |
| 구성 | 738 replay +87 model +90 settle; 새 구간177전이·8.85시뮬레이션초, 종료 중립0 |
| 모델 | 최대20결정 중19결정=18 act+1 finish_episode,20호출=질의 후속1회 포함. 질의 중 물리 진행0 |
| 종료 | D18 actor `finish_episode`; 예산 소진·10점 도달·timeout 아님. 국소 판단이며 불가능성 증명 아님 |
| 기술 검사 | completed·closed·finished, simulator 반환0, capture complete,915/915 전수 QC·오류0 |
| 공식 평가기 | valid=true, raw5/50, pickup5 at371(`replayed_parent`), 새 구간 득점0, dressing0, success=false |
| 시간 | actor1,035.999초; 환경764.021초= replay617.940 +새146.081초. 전체 경과에는 초기화 포함 |
| 학습 승인 | unreviewed. QC·기록 완료·단계 이름은 학습 승인이나 착의 성공이 아님 |
| 원본 백업 | 고정 revision `6b259ab4e34103286c30235640a434c7ee74f60c` 강제 재다운로드·archive SHA256/크기·227개 member 검증 완료 |

[실행 manifest](../collection/attempts/20261113-astra-diagonal738-001/manifest.json) / [공개 리뷰](../collection/reviews/20261113-astra-diagonal738-001.ko.md) / [추가 구간 영상](../gallery/20261113-e30-diagonal-738-915/event.mp4) / [전체 영상](../collection/attempts/20261113-astra-diagonal738-001/overview.mp4) / [백업 receipt](sessions/20261113-e30-backup-verification.json) / [마감 기록](sessions/20261113-e30-close.ko.md) / [결정·시간 분석](../collection/reviews/20261113-decision-budget/E30/README.ko.md)

host exec session 반환값은143입니다. simulator0·완료 파일·유효한 평가·전수 QC를 구분하며 host까지0이라고 주장하지 않습니다. `coordinated-diagonal-entry`, 고정CLI0.166.0 / exec / gpt-6-astra / ultra, named/query/wrist-panel/plan1/settle6/profile을 사용했습니다. 실시간 사람 피드백 큐는 미적용입니다.

E30은 같은 손의 낮춤·회전·올림을 나누어 시험했으나 확인된 통과나 추가 득점이 없었습니다. 다음 E31은 전략·기본20결정을 유지하고 더 이른 E28/682로 출발점만 바꿉니다. E30/886·915는 진단 자료이며 새로운 출발점으로 승격하지 않습니다. 사용자 승인에 따라 단일 시연→전수 QC·고정 백업→공개 관측·별도 점수/시간 분석→다음 시연을 자동 반복하며 매번 확인을 요청하지 않습니다. 중지·방향 변경 요청은 우선합니다.

E28·E29·E30은 같은 source group이며 독립 성공 표본이 아닙니다. E28은 clean source `9f797722acdb0f8d35001175e3aaa7e07a8dd2f8`의 새 reset에서40결정·739전이로 마감했습니다. [E28 백업](sessions/20261113-e28-backup-verification.json)은 고정 revision230c90a5·402members, [E29 백업](sessions/20261113-e29-backup-verification.json)은4a470053·155members 검증을 완료했습니다. 과거 E27/928 same-arm은 실제 E28의 출발점이 아닌 역사적 미실행 계획입니다.

새 환경의 CPU335개 검사·GPU smoke·별도 wiring3/3 QC와 [62members 백업](sessions/20261113-wiring-backup-verification.json)은 연결 근거입니다. E30 방법의17개 focused CPU 검사는 [방법 기록](../collection/research/2026-11-13-e30-diagonal-entry.ko.md)에 있습니다. 미적용 피드백 후보의353개 CPU 검사는 실행된 E30 코드의 전체 검사로 혼합하지 않습니다.
