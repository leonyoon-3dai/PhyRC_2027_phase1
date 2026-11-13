# 현재 상태

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [다음 수집](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

**현재 E30 `20261113-astra-diagonal738-001`이 2026-11-13 22:31:59 UTC에 시작해 진행 중입니다.** clean source `7eaae3e6b56ce938237b873bcb1540470a449b79`, E28/738 prefix·새 replay history682/714, `coordinated-diagonal-entry`, 최대20개 새 결정·총1400전이·review10을 적용했습니다. 실제 attempt의 시작·초기화는 확인했지만 replay 완료·새 구간 득점·최종 QC는 미확정입니다. [시작 기록](sessions/20261113-e30-start.ko.md)

**마지막 마감 시연은 E29입니다.** 로컬 공식 평가기의 유효한 원점수는 **5/50점·픽업5·착의0·success=false**입니다. E29의 픽업은 앞 행동 재실행 중 얻었으며 **새 구간 득점은0**입니다. 50점 목표는 달성하지 못했습니다.

| 구분 | 확인된 상태 |
|---|---|
| 마지막 마감 시연 | `20261113-astra-side-hem738-continue20-001` (E29) |
| 시작·출처 | clean source `2baebcc381d707fd5aca5f69ea7518d326e8a80a`; 직접 parent/source group은 E28 `20261113-astra-side-hem-fresh-001` |
| 재실행 | E28 prefix738 완료, 새 replay 관측682·714 사용. 정확한 천 checkpoint 복원 아님 |
| 실행 시각 | 2026-11-13 21:41:33–22:07:44 UTC |
| 수집 | 834전이 / 41.70시뮬레이션초 / 1,571.539초(약26.19분) 실제 경과 |
| 구성 | 738 replay +42 model +54 settle; 새 구간96전이·4.8시뮬레이션초, 종료 중립0 |
| 모델 | 최대20결정 중11결정=10 act+1 finish_episode,12호출=질의 후속1회 포함. 질의 중 물리 진행0 |
| 종료 | D10의 actor `finish_episode`; 예산 소진·10점 도달·timeout 종료 아님. 국소 판단이며 불가능성 증명 아님 |
| 기술 검사 | completed·closed·finished, simulator 반환0, capture complete,834/834 전수 QC 통과·오류0 |
| 공식 평가기 | valid=true, raw5/50, pickup5 at371(`replayed_parent`), 새 구간 득점0, dressing0, success=false |
| 시간 계측 | actor 경로775.837초, 환경 요청·응답747.066초. 전체 경과에는 초기화와 replay 포함 |
| 학습 승인 | unreviewed. QC·기록 완료·단계 이름은 학습 승인이나 착의 성공이 아님 |
| 원본 백업 | 고정 revision `4a4700539b5abcd8e5e9a0a93a3824916f1ca7e3` 재다운로드·archive SHA256/크기·155개 member 검증 완료 |

[실행 manifest](../collection/attempts/20261113-astra-side-hem738-continue20-001/manifest.json) / [공개 리뷰](../collection/reviews/20261113-astra-side-hem738-continue20-001.ko.md) / [추가 구간 영상](../gallery/20261113-e29-extra-decisions-738-834/event.mp4) / [전체 영상](../collection/attempts/20261113-astra-side-hem738-continue20-001/overview.mp4) / [백업 receipt](sessions/20261113-e29-backup-verification.json) / [시작 기록](sessions/20261113-e29-start.ko.md) / [마감 기록](sessions/20261113-e29-close.ko.md)

별도 host exec session의 최종 반환값은 **143**이었습니다. simulator 반환값0·완료 파일·유효한 평가·전수 QC를 각각 구분하며 host까지0이라고 주장하지 않습니다.

E29는 기존 `coordinated-side-hem-wrists`, Codex CLI0.166.0 / exec / gpt-6-astra / ultra, named actions·pixel depth query·wrist depth panel·plan-size1·motion-only settle6·시간 계측을 유지했습니다. 사용자 조작 피드백을 실시간 actor 입력에 전달하지 않았습니다. 최대20결정·총1,400전이·review10은 한도였으며,20개 행동을 모두 수행한 것이 아닙니다.

**다음에는 같은 방법의 예산 증액보다 진입 방식 변경을 우선 권합니다.** 방향과 높이 변화는 관측했지만 확인된 통과나 새 득점은 없었습니다. 다른 방법의 우선 비교점은 **E28/738**, 중간 방향 상태를 보존할 선택적 비교점은 **E29/784**입니다. 마지막834를 최신이라는 이유로 우선하지 않습니다. 사용자가 당분간 시연·분석의 자동 반복을 승인했습니다. E30부터 기본20결정·단일 실행으로 마감·QC·백업·분석을 거쳐 다음 방법·출발점을 정하며 매 시도 확인을 요청하지 않습니다. [수집 계획](../COLLECTION_PLAN.md) / [출발점 목록](../collection/catalog/README.ko.md)

E28과 E29는 같은 source group이며 독립 성공 표본이 아닙니다. 원래 E28은 source `9f797722acdb0f8d35001175e3aaa7e07a8dd2f8`의 새 reset에서40결정·739전이로 마감했고,5/50·착의0·success=false였습니다. E28의 고정 백업 `230c90a5d7abe76216311590f7764a65c19a946d` 재다운로드·402개 member 검증은 [receipt](sessions/20261113-e28-backup-verification.json), 이전 결과는 [E28 마감 기록](sessions/20261113-e28-close.ko.md)에 보존합니다. 과거 E27/928 same-arm 후보는 실제 E28의 출발점이 아닌 역사적 미실행 계획입니다.

새 환경의 CPU335개 검사, 실제 GPU smoke, 별도 wiring3/3전이 QC와 [62개 member 백업 검증](sessions/20261113-wiring-backup-verification.json)은 환경 연결 근거입니다. 착의 성공으로 합산하지 않습니다.
