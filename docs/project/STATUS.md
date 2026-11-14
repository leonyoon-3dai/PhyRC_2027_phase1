# 현재 상태

**2026-11-14 09:29 UTC 최신 사용자 지시:** 정리된 E33/E34 결과와 재정비 계획을 먼저 GitHub에 게시한 뒤, 기존 수집 경로로 옷 아래를 넓게 펼쳐 같은 손목보다 약간 위에서 측면으로 넣는 시연을 **최대5회** 진행한다. 예상 작업 범위는3–4시간이며 매회 마감·QC·공개 검토·고정 백업 뒤 다음 출발점을 선택한다. 사용자의 중간 피드백·중지 지시를 우선한다. 종전 E34 이후 중지는 이 범위에서 해제됐으며 새 시스템 개편·학습은 수행하지 않는다. [이번 배치](sessions/20261114-wide-hem-five-attempt-batch.ko.md)

[메인](../../README.md) | [시연 목록](../EPISODES.md) | [마감·재정비 계획](../COLLECTION_PLAN.md) | [Astra 코드](../ASTRA.md) | [클린 서버](../OPERATIONS.md)

## 실행 중: E35 / 최대5회 중1회차

`20261114-astra-wide-hem723-001`은2026-11-14T09:52:22Z, 공개 source `9a09099f170a76469b99ee1f7a177e3429933302`의 clean 상태에서 시작했다. E34/723·새 history671/697을 재생한 뒤 기존 파지 유지·넓은 아래 자유구간·약간 위에서 같은 손목으로 측면 접근을 비교한다. 새20결정/총1400/review10이다. 아직 마감·QC·성과는 미확정이다. [실행 기록](sessions/20261114-e35-wide-hem.ko.md) / [배치](sessions/20261114-wide-hem-five-attempt-batch.ko.md).

## 정상 마감한 E34

| 구분 | 확인된 E34 상태 |
|---|---|
| 실행 / 소스 | `20261114-astra-middle-grip470-retain-001` / clean `0a5121cde33a32db5e4888255de150e846d52c15` |
| 직접 parent / source group | E33 `20261114-astra-middle-grip264-001` / E28 `20261113-astra-side-hem-fresh-001` |
| 출발·입력 | prefix470·새 history434/454; `coordinated-middle-grip-drape-retain` |
| 기록 |836=470 replay+245 model+120 settle+1 budget cleanup; 새366전이·18.3시뮬레이션초 |
| 판단·종료 |20개 모두 act·24모델 호출; decision budget 종료. client/simulator0, completed/closed/finished=true, capture complete |
| 전수 QC |836/836·오류0 |
| 별도 평가 | valid=true, raw5/50·pickup5·착의0·success=false. 픽업5는 replay 뒤 새 구간에서 발생 |
| 공개 검토 | 기존 파지의 들기·운반·같은 손 근처의 짧은 하강. 손목 걸침·소매 통과는 확인하지 못함 |
| 시간 | client 내부1959.323초(32.66분), actor1170.153초, 환경737.509초. 전체 경과에는470 replay 포함 |
| 고정 백업 | HF `ba71dd6a07e2b05202c3dcaa5b0c9a3c17997b1d`; archive1,910,237,869bytes·SHA,236개 manifest 파일·원본234파일 불변 검증 |
| 학습 승인 | `unreviewed` |

[E34 리뷰](../collection/reviews/20261114-astra-middle-grip470-retain-001.ko.md) / [전체836프레임 영상](../collection/attempts/20261114-astra-middle-grip470-retain-001/overview.mp4) / [공개 manifest](../collection/attempts/20261114-astra-middle-grip470-retain-001/manifest.json) / [마감 세션](sessions/20261114-e34-retain-resume.ko.md) / [고정 백업 receipt](sessions/20261114-e34-backup-verification.json).

추가 재파지0은 프롬프트 지시이며 런타임 차단·누적 상태 원장 구현이 아닙니다. E34에서 그리퍼 open 명령 위반은 없었지만 이것을 모든 실행에서의 보장으로 확대하지 않습니다. E33과 E34는 같은 E28 계보이며 파지 유지의 통제된 성능 비교가 아닙니다. E34 뒤 중지했던 이력은 보존하며, 최신09:29 UTC 요청에 따라 E35부터 최대5회 추가 수집을 준비합니다.

## 정상 마감한 E33

| 구분 | 확인된 E33 상태 |
|---|---|
| 실행 / 소스 | `20261114-astra-middle-grip264-001` / clean `464203860304631d00a8acd6747b86c23cfded61` |
| 직접 parent / source group | E28 `20261113-astra-side-hem-fresh-001` |
| 출발·입력 | prefix264·새 history242/254; `coordinated-middle-grip-drape` |
| 기록 |471=264 replay+128 model+78 settle+1 budget cleanup; 새207전이·10.35시뮬레이션초 |
| 판단·종료 |20개 모두 act·21호출(물리0 질의 후속1회); decision budget 종료 |
| 마감 / QC | client0·simulator0, completed/closed/finished=true, capture complete;471/471·오류0 |
| 별도 평가 | valid=true, raw0/50·pickup0·착의0·success=false, no_contact |
| 공개 검토 | 양측 각1회 순차 재파지와 국소 형상 변화. 유용한 세로 입구·손 접근·하강은 미확인/미실행. 마지막 R1 닫기 뒤 동행 검토가 E34의 질문 |
| 고정 백업 | HF `0a79834c426d1be7b325ff5010027752751d5cd5`; archive SHA·크기·236manifest entries·원본234파일 불변 검증 |
| 학습 승인 | `unreviewed`; QC·보존 검증과 학습 가치·착의 성공은 별도 |

[E33 리뷰](../collection/reviews/20261114-astra-middle-grip264-001.ko.md) / [전체 영상](../collection/attempts/20261114-astra-middle-grip264-001/overview.mp4) / [세션·환경 검사](sessions/20261114-e33-middle-grip-resume.ko.md) / [백업 receipt](sessions/20261114-e33-backup-verification.json).

## 불완전 원본과 과거 결과

E09·E32는 정상 replay·학습에서 계속 제외합니다. E32는758전이 내용 검사는 통과했으나 capture와 두 HDF5 root의 `complete=false` 세 오류로 전체 QC 실패입니다. 별도 평가5/50·착의0·success=false와 진단 archive 재다운로드 검증이 수집 완료를 대신하지 않습니다. host143 발신 원인은 미확정입니다. [E32 실패·보존 기록](sessions/20261114-e32-incomplete.ko.md) / [진단 백업 receipt](sessions/20261114-e32-backup-verification.json).

E31은 정상830/830 QC·5/50·새 득점0으로 마감한 이전 접근 비교이며 [리뷰](../collection/reviews/20261113-astra-diagonal682-001.ko.md)와 [마감 기록](sessions/20261113-e31-close.ko.md)을 보존합니다. 종전 E28/632 중앙 전략 후보는 [역사적 미실행 계획](sessions/20261114-e33-plan.ko.md)이며 실제 E33의 출발점은264였습니다.

[재정비 계획](../collection/research/2026-11-14-collection-system-redesign.ko.md)은 실행 상태·관측 가설·후속 검증 예산·구간 승인과 계보를 분리하는 방향입니다. 문서 검토와 후속 구현·GPU 실험은 별도 단계이며, 현재 기존 수집 방식의 최대5회 배치만 승인됐고 자동 재학습은 수행하지 않습니다. 실시간 피드백 큐도 계속 미적용입니다.

E28과 후속 분기는 같은 source group이며 독립 성공 표본이 아닙니다. 현재까지 정상 평가한 시연의 최고 로컬 원점수는5/50, 착의 득점0이며 완전 착의 성공은 확인하지 못했습니다. CPU 검사·실제 모델/시뮬레이션 실행·기술 QC·학습 승인·착의 성과를 구분합니다. 로컬 점수를 Codabench 제출 성과나 공식900초 평가 예산 준수로 설명하지 않습니다.
