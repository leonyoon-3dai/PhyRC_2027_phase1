> **보관 기록** · 11월 16일 M1과 B 분기를 마감했을 때의 상태·검증 기록입니다. 현재 서버 작업은 새 계획과 수집 절차에서 시작합니다. [현재 메인](../../README.md) · [새 실험 계획](../active/experiment.md) · [새 서버 수집 절차](../active/collection.md) · [보관 목차](../ARCHIVE.md)

# 현재 상태

**이번 세션은 종료됐다.** 마지막 `20261116-astra-right-hand-hold10-001`은135전이에서 사용자 `finish`로 정상 마감했고 추가 물리 전이는0이다. `completed/closed/finished=true`, `capture_complete=true`, simulator 종료코드0을 확인했다. **전수 QC135/135·오류0**이며 비공개 HF 고정 revision의 강제 재다운로드·전체 파일 SHA 검증도 완료했다. 현재 live HOLD는 없다.

다음 방향은 **마지막 R0 단독 접근 전110전이 상태에서 두 로봇을 마네킹 왼손 쪽으로 함께 이동한 뒤, 옷을 양손에 모두 걸치기**다. 사용자 제안으로 기록했으며 실행하지 않았다. [각 움직임의 지시·명령·실제 효과·GIF](../collection/reviews/20261116-user-guided-movement-ledger.ko.md) · [다음 계획](../COLLECTION_PLAN.md)

## 이번 실행과 검증 경계

| 항목 | 확인한 상태 |
|---|---|
| 마지막 시연 | `20261116-astra-right-hand-hold10-001`,135전이=110 replay+25 new. 새9 act·10호출, 마지막 tick1620/8.258334s. 사용자 종료·추가 전이0·QC135/135 |
| 직전 M1 시연 | `20261116-astra-m1-checkpoint-001`,38 act·48호출·120전이. 정상 마감·QC120/120·고정HF 백업 재다운로드 검증 완료 |
| 마지막 실제 이동 | R0만 평면 접근을 명령했으나 파지점 XY 순변위 R0 41.57mm/R1 12.66mm. R1 모든9채널0과 실제 고정은 다르다. [분석](../collection/reviews/20261116-right-hand-hold10-branch.ko.md) |
| 해석의 한계 | 오른팔 두 줄무늬 간격 도달·실제 충돌·소매 통과 미확인. 사용자 왼손 충돌 우려는 다음 전략을 바꾼 근거이며 접촉 검증 결과는 아님 |
| 이번 두 시연 평가 | raw0/50·first_sleeve0·success=false. checkpoint reset의 새 평가로 과거 pickup5를 이월하지 않음 |
| 다음 출발 후보 | 새 분기 hold-0001·110전이에서 저장한slot, SHA `c26cc58c…`. 저장·해시 확인 완료, **복원 미검증**. [저장 receipt](../gallery/20261116-right-hand-hold10/start-checkpoint-verification.json) |
| 기능 검증 | checkpoint/HOLD/게시·재개 CPU394개 및 GPU HOLD8개 검사 통과. 이후slot+prefix 계보 검증 확장 CPU399개 통과, 실제110전이 replay와 시작checkpoint 저장 확인 |
| 모델·HF | 격리 Codex CLI0.166.0 / exec / gpt-6-astra / ultra; HF CLI2.4.0·leonayoon 로그인 확인. L40S GPU |
| 현재 성능·학습 | 정상 평가 최고 raw5/50, 착의0·완전 착의 성공 미확인. 두 최신 시연 학습 승인 `unreviewed`; 기술QC와 별개 |

[마지막 실행 마감 기록](../collection/attempts/20261116-astra-right-hand-hold10-001/README.ko.md) · [이전 M1 마감 기록](../collection/attempts/20261116-astra-m1-checkpoint-001/README.ko.md) · [기전](../MECHANISMS.ko.md) · [과거 요약](../HISTORY_SUMMARY.ko.md) · [복원 인계서](../collection/research/2026-11-16-user-guided-resume.ko.md)

마감 뒤 `supervisor_state.json`의 held/active 표시는 마지막 스냅샷으로 남을 수 있다. 최종 attempt·capture 마감과 프로세스 종료를 기준으로 판정하며 이를 살아 있는 HOLD로 표시하지 않는다. 클라우드 서버 전원 종료는 수행하지 않았다.

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

준비934전이·복원1전이는 전수 QC와 비공개 HF 고정 revision `eb05c6f98f59cce84084ab9a10e153687292ee53`의 재다운로드 SHA 검증까지 완료했다. [91개 파일·2.11GB 백업 receipt](../collection/reviews/20261116-checkpoint-backup-verification.json). 이번 두 과제 시연은 이 준비 원본과 별도 실행으로 마감했다.

M1 120전이는 HF 고정 revision `91384b01de9d566ec6d1d221ff332a6d4fddd289`에서486개 원본/488개 manifest 파일의 SHA·크기·정확한 구성까지 재검증했다. [M1 백업 receipt](../collection/reviews/20261116-m1-checkpoint-backup-verification.json).

마지막 R0 분기135전이와110전이 출발slot은 HF 고정 revision `7b432df530a4b7001f3aaa63dea67b9bd6c44ef7`에 보존했다. 304,192,227bytes archive의 재다운로드 SHA와144개 manifest 파일의 크기·SHA·정확한 목록을 검증했고 원본142개 파일도 불변이었다. [R0 분기 백업 receipt](../collection/reviews/20261116-right-hand-hold10-backup-verification.json). 저장slot 자체를 다시 복원해 품질을 검증한 것은 아니다.
