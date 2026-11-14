# 현재 상태

**[이번 세션 영상·실패 분석 모음](../collection/reviews/20261114-session-review.ko.md)**에서 E28–E32 영상과 시도별 판단을 바로 검토할 수 있습니다.

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [다음 수집](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

**사용자 요청으로 시연·분석 자동 반복을 일시 중지했습니다. E33은 시작하지 않습니다.** 현재 실행 중인 simulator는 없으며, E32 실패 자료 보존·검증·저장소 정리만 마칩니다. 이후 클린 서버에서 사용자가 명시적으로 재개한 뒤 다음 실행을 검토합니다. [클린 서버 인계](sessions/20261114-paused-clean-server-handoff.ko.md)

**E32는 수집 불완전으로 종료했고 전체 QC를 통과하지 못했습니다.** 20개 행동과 정착은756까지 기록됐지만 정상 마감 요청 없이 입력이 닫혔습니다. 종료 정리2전이를 포함한758전이를 전수 검사했고, capture와 두 HDF5 파일의 `complete=false` 때문에 실패했습니다. 원본 표식을 고치거나 E32 경계를 정상 replay 출처로 승격하지 않습니다. [불완전 수집 기록](sessions/20261114-e32-incomplete.ko.md) / [공개 리뷰](../collection/reviews/20261113-astra-central380-001.ko.md)

**다음 E33은 아직 시작하지 않은 계획입니다.** 2026-11-14 사용자 제안인 **더 가운데 파지·노란 경계의 위아래 늘어짐과 여유 공간·손 위에서 살짝 내려 걸치기**를 [다음 시연 메모](../COLLECTION_PLAN.md#2026-11-14-다음-시연-메모)에 문서로만 기록했습니다. 코드·actor 프롬프트에는 적용하지 않았습니다. 종전 E28/632·history588/614·같은 `coordinated-central-span-entry`·최대20새 결정/총1400전이/review10 후보는 파지 변경에 맞춰 재검토합니다. 다음 클린 서버에서 명시적으로 재개한 뒤 환경·clean source·유효 출처와 시연 방법을 다시 확인합니다. [종전 E33 후보](sessions/20261114-e33-plan.ko.md) / [현재 실행 조건](../COLLECTION_PLAN.md)

| 구분 | 확인된 E32 상태 |
|---|---|
| 실행 | `20261113-astra-central380-001` |
| source / 계보 | clean `0421f8b3c45fd0291455fb278144ce279682dd98`; 직접 parent/source group E28 `20261113-astra-side-hem-fresh-001` |
| 실제 시작 | 2026-11-13 23:59:34 UTC. 자정 뒤 진행 시각을 시작 시각으로 바꾸지 않음 |
| 재실행·입력 | prefix380 완료, 새 replay history264·332; 정확한 천 checkpoint 복원 아님 |
| 기록 |758=380 replay+256 model+120 settle+1 collector stop+1 EOF cleanup. accepted trace는756까지 |
| 결정·종료 |20개 모두 act·21호출(질의 후속1회), finish_episode 없음. host143; 입력 종료 원인의 발신자는 미확정 |
| 원본 상태 | attempt는 collecting/controller_settle·finished=false·756에 남음; capture758/complete=false/input_closed, 두 HDF5 root complete=false |
| QC |758/758 검사. episode 검사는 통과했지만 capture와 두 파일의 incomplete 오류3개로 전체 quality_passed=false |
| 별도 평가 | 기록된 evaluation_valid=true, raw5/50·pickup5·착의0·success=false, 새 득점0. 전체 QC·replay·학습 승인 아님 |
| 다음 출처 |E32 전체와 중간 경계는 진단 전용. 종전 후보는 검증된 E28/632이며 최신 파지 변경 제안에 따라 재검토 |
| 보존 |고정 private HF91f91b06 강제 재다운로드·234members·원본233파일 불변 검증. [진단 백업 receipt](sessions/20261114-e32-backup-verification.json); 정상 replay 불가 |

E32에서 넓어진 형상과 운반 유지, 같은 손 근처의 접촉·좁아짐·일부 복구를 관측했습니다. 공개 마지막 actor 관측은744이며,756/758은 정지 후 파일의 지정 공개 RGB로 검토했습니다. 손 통과나 연결 전완 진행은 확인하지 못했습니다. 최신 경계를 더 좋은 시작점으로 취급하지 않습니다. [E28/632 비교 근거](../collection/research/2026-11-14-e33-central632-direction.ko.md)

[결정·시간 분석](../collection/reviews/20261113-decision-budget/E32/README.ko.md): actor1220.871초, 환경646.737초(replay324.026+새322.711). 최종 client 전체 경과는 미기록이며 collector wall을 대신 쓰지 않습니다.

마지막 **정상 마감·전체 QC 통과** 시연은 E31입니다.830/830·오류0, 로컬5/50·새 득점0·착의0·success=false이며 고정 비공개 백업209members 검증을 마쳤습니다. [E31 마감](sessions/20261113-e31-close.ko.md) / [리뷰](../collection/reviews/20261113-astra-diagonal682-001.ko.md) / [영상](../gallery/20261113-e31-diagonal-682-830/event.mp4) / [백업 receipt](sessions/20261113-e31-backup-verification.json).50점 목표는 아직 달성하지 못했습니다.

이전 단일 시연→검사·보존→분석 자동 반복 승인은 이번 중지 요청으로 일시 중단됐습니다. 문서·백업 완료나 새 서버 준비를 재개 승인으로 해석하지 않습니다. 불완전 시도는 실패 자료로 따로 보존하고 유효한 출처에서만 재실행합니다. 기본 새 결정20개를 유지하며 중지·방향 변경 지시를 우선합니다. 실시간 피드백 큐는 계속 미적용입니다.

E28과 후속 분기는 같은 source group이며 독립 성공 표본이 아닙니다. CPU 검사·실제 모델/시뮬레이션 실행·기술 QC·학습 승인·착의 성과를 구분합니다. 로컬5/50을 Codabench 제출 성과나 공식900초 평가 예산 준수로 설명하지 않습니다.
