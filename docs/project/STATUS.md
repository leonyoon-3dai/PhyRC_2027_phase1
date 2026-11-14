# 현재 상태

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [다음 수집](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

**E32 `20261113-astra-central380-001`이 2026-11-13 23:59:34 UTC에 시작했습니다.** clean source `0421f8b3c45fd0291455fb278144ce279682dd98`, 직접 parent/source group E28, prefix380·새 history264/332, `coordinated-central-span-entry`, 최대20개 새 결정·총1400전이·review10입니다. 실제 attempt의 시작과 prefix replay 진입을 확인했으며 replay 완료·새 행동·최종 득점·QC는 아직 확인하지 않았습니다. 자정 뒤의 진행 시각을 시작 시각으로 바꾸지 않습니다. [E32 시작 기록](sessions/20261113-e32-start.ko.md) / [현재 실행 조건](../COLLECTION_PLAN.md)

**아래 표는 마지막 마감 E31의 결과입니다.** 로컬5/50·픽업5·착의0·success=false, 새 구간 득점0이며50점 목표는 달성하지 못했습니다.

| 구분 | 확인된 E31 상태 |
|---|---|
| 마지막 마감 시연 | `20261113-astra-diagonal682-001` |
| source / 계보 | clean `000d4fcc1a44bcc602a6275b2f79f9dc6456c641`; 직접 parent/source group 모두 E28 `20261113-astra-side-hem-fresh-001` |
| 시작–종료 | 2026-11-13 23:17:37–23:46:18 UTC |
| 재실행·입력 | prefix682 완료, 새 history632·668; 정확한 천 checkpoint 복원 아님 |
| 수집 | 830전이=682 replay+58 model+90 settle; 새148전이·7.4시뮬레이션초, 종료 중립0 |
| 결정·호출 | 최대20개 중17결정=16 act+1 finish_episode,19호출=depth 질의 후속2회 포함. 질의 중 물리0 |
| 종료 | D16 actor finish; 결정/전이 예산 소진·review10·timeout 종료 아님. 국소 판단이며 불가능성 증명 아님 |
| QC·평가 | completed/closed/finished, capture complete,830/830 전수 QC·오류0; evaluation_valid=true, raw5/50, success=false |
| 득점 구간 | pickup5 at371(`replayed_parent`), 새 구간 득점0·착의0 |
| 시간 | 전체1,721.580초(28.69분), actor971.602초, 환경699.982초= replay577.617 +새122.366초 |
| 반환값 | host session143, simulator0. 서로 다른 종료 상태로 기록 |
| 원본 백업 | 고정 HF9254bf1e1fbdae8f4aebeb7d4f4c9858a88235fb 강제 재다운로드·archive SHA/크기·209members 검증 |
| 학습 | unreviewed; 기록 완료·QC·단계명은 학습 승인이나 착의 성공이 아님 |

[실행 manifest](../collection/attempts/20261113-astra-diagonal682-001/manifest.json) / [공개 리뷰](../collection/reviews/20261113-astra-diagonal682-001.ko.md) / [추가 구간 MP4](../gallery/20261113-e31-diagonal-682-830/event.mp4) / [전체 영상](../collection/attempts/20261113-astra-diagonal682-001/overview.mp4) / [백업 receipt](sessions/20261113-e31-backup-verification.json) / [마감 기록](sessions/20261113-e31-close.ko.md) / [결정·시간 분석](../collection/reviews/20261113-decision-budget/E31/README.ko.md)

수평 접근과 자세 복구는 관측했지만 첫 손의 중앙 진입·전완 진행은 확인하지 못했습니다. E31의 마지막830을 더 좋은 출발점으로 승격하지 않습니다. E32는 출발점과 방법을 함께 바꾸므로 단일 원인의 효과로 해석하지 않습니다. 기존 camera XYZ 질의를 새 기능으로 세지 않으며, 입구의 폭·깊이와 손–자유 구간의 실제 상대 변화를 검토합니다.

사용자 승인에 따라 단일 시연→마감·전수 QC·고정 백업→공개 관측 및 별도 점수/시간 분석→다음 시연을 자동 반복합니다. 기본 새 결정20개를 유지하며 남은 예산을 다음 run에 합산하지 않습니다. 중지·방향 변경 지시는 우선합니다. 실시간 피드백 큐 후보는 계속 미적용입니다.

E28·E29·E30·E31은 같은 source group이며 독립 성공 표본이 아닙니다. [E28](sessions/20261113-e28-close.ko.md), [E29](sessions/20261113-e29-close.ko.md), [E30](sessions/20261113-e30-close.ko.md)의 원본·검증·성과는 각각 보존합니다. 각 방법의 CPU 검사와 실제 모델/시뮬레이션 성과를 구분하며 로컬5/50을 Codabench 제출 성과나 공식900초 평가 예산 준수로 설명하지 않습니다.
