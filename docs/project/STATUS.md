# 현재 상태

**현재 M1은 충분한 추가 후퇴 뒤 hold-0003에서 live HOLD다.** `20261116-astra-m1-checkpoint-001`에서 새5 act·23전이(1.15초), 누적12호출·12결정·10 act·39전이를 기록했다. 파지점은 world Y 방향으로 약12.0/11.4cm 더 이동했고 높이 변화는 약1.9/2.6mm였다. head 화면의 손·연결 손목 노출과 옷의 처짐이 개선됐다. 여유가 충분한지와 다음 높이·방향은 [구간별 GIF](../gallery/20261116-m1-guided-segments/README.ko.md)와 [현재5카메라](../collection/user-reviews/20261116-astra-m1-checkpoint-001/hold-0003/README.ko.md)로 사용자 판단을 기다린다. [실제 효과 분석](../collection/reviews/20261116-m1-right-hand-clearance.ko.md). 추가 하강·재접근은 실행하지 않았다.

개발 대화의 `gpt-6-astra` 전환, HF CLI2.4.0과 `leonayoon` 로그인, L40S GPU, 초기 자산·E36 복원/QC933/933, 격리 CLI0.166.0/Astra/ultra 연결, CPU394개 검사와 GPU smoke/HOLD·checkpoint 비교를 확인했다. 사용자가 정착 차이를 검토하고 현재 복원 상태를 채택했다. [출발 비교](../collection/reviews/20261116-checkpoint-validation.ko.md)

[현재 실행 계획](../COLLECTION_PLAN.md) · [기전·판단 기준](../MECHANISMS.ko.md) · [과거 결과 요약](../HISTORY_SUMMARY.ko.md) · [실행 인계서](../collection/research/2026-11-16-user-guided-resume.ko.md) · [환경 복원](../OPERATIONS.md)

## 현재 실행과 검증 경계

| 항목 | 확인한 상태 |
|---|---|
| 현재 열린 과제 시연 | `20261116-astra-m1-checkpoint-001`, hold-0003·39전이·물리0 대기. 마감·QC·백업 전 |
| 현재 분기 평가 | raw0/50·first_sleeve0·success=false. checkpoint reset의 새 평가로 과거 pickup5를 이월하지 않음 |
| 최신 정상 과제 시연 | E36 `20261114-astra-wrist-body835-001`, 정상 마감 |
| 새 시연 출발 후보 | E36의933전이 경계. 재생·slot 저장/복원 확인. 정착 차이를 게시한 뒤 사용자가 현재 복원 상태를 채택하고 구체적 방향을 교정 |
| 새 기능 | `e9cca07`에 checkpoint·물리0 HOLD·5카메라 export·텍스트 재개 구현. CPU394개 통과; GPU HOLD8개 검사 통과·slot 비교 완료. 원래934전이/복원1전이 전수 QC 통과 |
| 첫 방법 / 목표 | M1 현재 파지 유지·국소 교정 / trusted evaluator의 `first_sleeve` 새0→5 |
| 사용자 판단 | 자동 종료 제안·구간 예산·득점·출발 부적합에서 물리0 HOLD 후 README 상단에 같은 관측의5장 게시 |
| 현재 성능 | 정상 평가 최고 로컬 raw5/50, 착의0, 완전 착의 성공 미확인 |
| 학습 | 최신 시연 `unreviewed`; 새 VLA/RL 학습은 현재 범위에 없음 |

사용자의 답변 전에는 동작·정착·자동 재개를 하지 않는다. 살아 있는 HOLD와 실제 환경 종료·프로세스 장애를 구분한다. 실행 상태의 최신 화면은 [README 검토 패널](../../README.md)에서 확인한다.

## 출발 근거: E36

| 항목 | 확인된 결과 |
|---|---|
| 직접 parent / source group | E34/835 / E28 `20261113-astra-side-hem-fresh-001` |
| 수집 | 933전이 =835 replay+50 model+48 settle. 새98전이·4.90시뮬레이션초 |
| 종료 | 10 act+모델 `finish_episode`, 총11결정·12호출. 예산·review10·timeout 종료가 아님 |
| 기술 QC | 전수933/933·오류0, capture complete, client/simulator0 |
| 별도 평가 | valid=true, raw5/50·pickup5·착의0·success=false. 새 구간 득점0 |
| 공개 관측 | 같은 전완이 새로 보였으나 손은 파지 모서리/housing 곁에 남음. 자유 경계 통과·유지된 손목 걸침·소매 출구 미확인 |
| 미시험 조건 | 새10개 act의 base yaw는 모두0. 베이스 방향 변경의 효과는 충분히 시험하지 않음 |
| 고정 백업 | HF `dcf059881e4e6c103dc8206438a70eb1b8ccb26f`, SHA·크기·155 manifest 파일·원본153파일 불변 검증 |

[E36 리뷰](../collection/reviews/20261114-astra-wrist-body835-001.ko.md) · [GIF](../gallery/20261114-e36-overview/README.ko.md) · [전체 영상](../collection/attempts/20261114-astra-wrist-body835-001/overview.mp4) · [manifest](../collection/attempts/20261114-astra-wrist-body835-001/manifest.json) · [실행 상세](sessions/20261114-e36-wrist-body.ko.md) · [백업 receipt](sessions/20261114-e36-backup-verification.json)

## 결과 해석과 보존

- E36은 E35 말단의 후속이 아니라 E34/835에서 행동을 재생한 분기다. E28과 후속 분기·공통 prefix는 독립 성공 표본이 아니다.
- E09·E32는 불완전 원본으로 정상 replay·학습에서 제외한다. E32의758전이 내용 검사와 진단 백업 검증은 전체 QC 통과를 뜻하지 않는다. [E32 기록](sessions/20261114-e32-incomplete.ko.md)
- 기술 QC, 공식 로컬 평가, 시각 검토, 학습 승인은 별도다. 로컬 점수를 Codabench 제출 성과나 공식900초 예산 준수로 설명하지 않는다.
- 과거 최대5회 배치는 E35·E36에서 종료됐다. 당시 E37–E39는 미실행이며 남은 횟수·예산은 현재 계획에 이월하지 않는다.

상세 시행착오는 [과거 결과 요약](../HISTORY_SUMMARY.ko.md)에서 필요한 근거로 연결한다. 원본 세션·실패·백업은 [보관함](../ARCHIVE.md), 영상과 계보는 [시연 목록](../EPISODES.md)에 보존한다. [E00–E36 통합 PDF](../reports/20261114-e36-integrated-review/phyrc-e36-integrated-review.ko.pdf)와 [출처·검증](../reports/20261114-e36-integrated-review/README.ko.md)은 기존 분석 자료다.

## 현재 검증 원본 백업

준비934전이·복원1전이는 전수 QC와 비공개 HF 고정 revision `eb05c6f98f59cce84084ab9a10e153687292ee53`의 재다운로드 SHA 검증까지 완료했다. [91개 파일·2.11GB 백업 receipt](../collection/reviews/20261116-checkpoint-backup-verification.json). 현재 M1을 수행하는 열린 run은 별도다.
