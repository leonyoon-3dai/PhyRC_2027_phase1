# PhyRC 시연·개발 기록 보관함

[현재 실험 계획](../README.md) · [날짜별 실험](#chronology) · [시연·데이터](#data) · [코드·운영](#code) · [연구·이전 계획](#research) · [고정 백업](#고정-백업)

11월 22–23일의 세 회차는 [사용자 피드백·한 팔 먼저·양팔 먼저 비교](active/20261123-demonstrations.ko.md)에 있습니다. 아래는 2026년 11월 19일까지의 수집 기록입니다. **어떤 행동이 효과가 있었는지**는 [과거 결과 요약](HISTORY_SUMMARY.ko.md), **그 장면이 어느 영상에 있는지**는 [에피소드 색인](EPISODES.md), **직전 메인 화면에 무엇이 있었는지**는 [11월 19일 README](archive/README-2026-11-19.ko.md)에서 확인할 수 있습니다. 문서에 남은 ‘현재’, ‘다음’, HOLD, 재개 명령은 각 기록의 작성 시점을 가리킵니다.

M1의 실행 지시와 실제 변위는 [P10 구간 원본과 움직임 장부](gallery/20261116-m1-guided-segments/README.ko.md#p10)에서 확인할 수 있습니다.

<a id="chronology"></a>

## 날짜별 실험

| 시기 | 당시 질문과 확인된 결과 | 먼저 열 자료 |
|---|---|---|
| 10월 22일–11월 3일 | 초기 설치, 사람 키보드 조작, 티셔츠 픽업·운반의 부분 시연, 서버 이전 | [사람 조작 영상과 설명](gallery/20261026-human-pickup-transport.ko.md) · [세션 일지](project/sessions/) |
| 11월 6–7일 · E00–E27 | 연결 시험과 Astra의 공동 픽업·운반, 재파지, 손·접근면 변경. E07에서 갈라진 분기는 같은 원본 행동을 일부 공유합니다. E09는 불완전 원본입니다. | [영상과 부모 관계](EPISODES.md) · [E07 공동 운반](gallery/20261106-astra-coordinated-fresh-001.ko.md) · [E27까지의 마감](project/SESSION_WRAPUP_20261107.ko.md) |
| 11월 13–14일 · E28–E36 | 새 reset에서 측면 파지, 밑단 펼치기, 손목 접근을 시험했습니다. E36의 5/50은 재생 구간의 픽업이고 새 착의 득점은 0입니다. E32는 불완전 원본입니다. | [E28 이후 영상·실패](collection/reviews/20261114-session-review.ko.md) · [E34](gallery/20261114-e34-overview/README.ko.md) · [E35](gallery/20261114-e35-overview/README.ko.md) · [E36 분석 PDF·근거](reports/20261114-e36-integrated-review/README.ko.md) |
| 11월 16일 · 사용자 교정 M/B | M1은 120전이, B는 앞 110전이를 다시 실행한 뒤 25전이를 추가했습니다. 두 실행의 새 조작 47개는 145전이입니다. | [사용자 지시·실제 운동·GIF](collection/reviews/20261116-user-guided-movement-ledger.ko.md) · [M1 구간](gallery/20261116-m1-guided-segments/README.ko.md) · [B 구간](gallery/20261116-right-hand-hold10/README.ko.md) |
| 11월 16–19일 · 재개 후보와 선행연구 | B/HOLD1 저장 슬롯, 공식 데모 전체, 손목 진입·걸침 조건을 검토했습니다. 이 기간 기록에서 해당 슬롯의 재복원과 새 소매 득점은 미검증입니다. | [저장·복원 비교 실험](collection/reviews/20261116-checkpoint-validation.ko.md) · [공식 영상 분석](collection/research/2026-11-19-official-demo-full-review.ko.md) · [당시 계획](COLLECTION_PLAN.md) |

<a id="data"></a>

## 시연과 데이터 찾기

| 찾는 항목 | 열어볼 위치 |
|---|---|
| 특정 E번호의 run ID, 영상, 원본 출처, 직접 부모 | [E00–E36 전체 자료](EPISODES.md#e00e36-전체-자료) · [각 시도 요약·manifest](collection/attempts/) |
| 같은 상태에서 갈라진 분기와 재사용한 전이 | [출발점·방법 색인](collection/catalog/README.ko.md) · [기계 판독용 catalog](collection/catalog/catalog.v1.json) · [조회 명령](collection/catalog/TOOL_GUIDE.ko.md) |
| 당시 프레임과 파지·깊이·관측 해석 | [성공·실패 검수 일지](collection/reviews/) · [중간 시점 증거](collection/milestones/) · [선별 영상](gallery/) · [표시 기준](gallery/ROBOT_LAYOUT.ko.md) |
| 사람이 무엇을 보고 어떤 피드백을 줬는지 | [HOLD별 공개 카메라와 관측 ID](collection/user-reviews/) · [사용자 피드백 원본](collection/feedback/) · [47개 조작의 명령과 실측 JSON](collection/reviews/20261116-user-guided-movement-ledger.json) |
| 당시 HDF5·비공개 자산과 검증 결과 | [정상 마감·QC·원본 백업 상태](project/STATUS.md) · [고정 백업 영수증](#고정-백업) · [재생·복원 절차](OPERATIONS.md) |
| 운영 중 취소·실패한 시도, 자원·시간·호출 비용 | [날짜별 세션](project/sessions/) · [수집 일지](collection/sessions/) · [수정·정정](collection/corrections/) · [성능 측정](project/performance/) |

이 시기 카탈로그에는 실행 47건, 출발점 22개, 방법 29종, 시도 49건(계획 포함)이 있습니다. prefix 재생, 새 행동, 정착, 종료 전이는 각각 출처가 다릅니다. 카탈로그에서 source group과 직접 부모를 먼저 확인하면 같은 행동을 중복 집계하는 일을 피할 수 있습니다. 정상 QC, 공식 평가 득점, 시각 검수, 학습 승인도 각각의 기록에서 확인합니다.

<a id="code"></a>

## 코드와 운영 자료

| 필요할 때 | 코드 · 당시 사용 설명 |
|---|---|
| 격리 actor에 실제로 어떤 관측과 행동이 오갔는지 추적 | [수집기 진입점](../scripts/collect_operator.py) · [actor·계획·경계·기록 검사](../participant/collection/) · [Astra 수집 코드 지도](ASTRA.md) · [공개 관측·행동 규격](../config/policy_interface.json) |
| 참가자 정책·공식 환경의 경계 확인 | [참가 정책](../participant/policy.py) · [환경·공식 정책](../src/PhyRC_Sim/) · [최소 정책 예제](../examples/zero_policy.py) · [평가·제출 문서](competition/) |
| 과거 브라우저 라이브 뷰·README 게시·직접 조작을 재현 | [뷰어·키보드·스트리밍](../participant/streaming/) · [guided 수집 계약](collection/GUIDED_RUNTIME.ko.md) · [시연 구간 내보내기](../scripts/export_held_segments.py) |
| 어떤 도구가 수집 중 실행됐는지, 사후 진단인지 확인 | [수집·검사·변환 스크립트](../scripts/) · [실험 원장](../experiments/index.csv) · [깊이·색상 분석 도구](../participant/research/) · [오프라인 실험 기록](collection/experiments/) · [검증 코드](../tests/) |
| 기존 자산·실행 의존성·컨테이너 재현 | [자산 잠금](../config/assets.lock.json) · [로컬 자산](../assets/) · [참가자 런타임](../participant/runtime/) · [준비·백업 도구](../participant/ops/) · [Dockerfile](../Dockerfile) · [환경 진입점](../entrypoint.sh) · [실행 스크립트](../run.sh) · [Python 초기화](../sitecustomize/) |
| 기존 학습 경로와 후속 연구 범위 확인 | [π0.5 전처리·학습 코드](../participant/pi05/) · [VLA·지각 연구 이력](project/research/) · [데이터 규격](competition/DATA.md) |
| 인용·재배포·공식 배포판 근거 확인 | [주최 측 README](../README.upstream.md) · [LICENSE](../LICENSE) · [NOTICE](../NOTICE) · [THIRD_PARTY](../THIRD_PARTY.md) |

<a id="research"></a>

## 연구와 이전 계획

| 연구 질문 | 보존 자료 |
|---|---|
| 손목 위에서 내릴 때 무엇을 확인했나? | [기전·실측 그래프](MECHANISMS.ko.md) · [공식 35.8초 영상 타임라인](collection/research/2026-11-19-official-demo-full-review.ko.md) · [DexGarmentLab](collection/research/2026-11-18-dexgarmentlab-phyrc.ko.md) |
| 직전 명령의 실제 효과, 복원 오차, 정체를 어떻게 판단했나? | [실행 효과 비교](collection/research/2026-11-16-checkpoint-effect-feedback.ko.md) · [사용자 교정 인계](collection/research/2026-11-16-user-guided-resume.ko.md) · [에이전트 로보틱스 워크숍](collection/research/2026-11-14-agentic-robotics-workshop.ko.md) |
| 어떤 아이디어를 조사하거나 보류했나? | [연구 전체](collection/research/) · [후보 패치](collection/research/candidates/) · [재시도 계획](collection/retry-plans/) · [이전 프로젝트 문서·세션·발표](project/) |
| 예전 첫 화면·점수 그림·공식 데모·보고서가 필요한가? | [직전 README 전체](archive/README-2026-11-19.ko.md) · [11월 19일 Codex 지침 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/777e5fab3cd038c181000dd2eb106e58945fc554/AGENTS.md) · [50점 개념도](project/assets/score-roadmap-20261104/score-roadmap.ko.svg) · [주최 측 데모](https://emprise.cs.cornell.edu/phyrc/assets/c27/media/teleop-overhead.mp4) · [보고서 모음](reports/) · [이전 저장소 가이드 PDF](guide/PhyRC_2027_Repository_Guide_KR.pdf) |

## 고정 백업

다운로드·SHA·누락 파일 병합 명령은 [OPERATIONS](OPERATIONS.md)에 있습니다. 각 receipt는 해당 묶음의 고정 revision과 archive hash를 지정합니다. 한 archive를 전체 데이터 백업으로 해석하지 않습니다.

| 복원 대상 | 검증 receipt |
|---|---|
| `20261116` R0 분기135전이·출발slot | [JSON](collection/reviews/20261116-right-hand-hold10-backup-verification.json) |
| `20261116` 사용자 교정 M1 120전이 | [JSON](collection/reviews/20261116-m1-checkpoint-backup-verification.json) |
| `20261116` 출발 준비934전이·복원1전이 | [JSON](collection/reviews/20261116-checkpoint-backup-verification.json) |
| `20261114-e36` | [JSON](project/sessions/20261114-e36-backup-verification.json) |
| `20261114-e35` | [JSON](project/sessions/20261114-e35-backup-verification.json) |
| `20261114-e34` | [JSON](project/sessions/20261114-e34-backup-verification.json) |
| `20261114-e33` | [JSON](project/sessions/20261114-e33-backup-verification.json) |
| `20261114-e32` (진단 전용·불완전 원본) | [JSON](project/sessions/20261114-e32-backup-verification.json) |
| `20261113-e31` | [JSON](project/sessions/20261113-e31-backup-verification.json) |
| `20261113-e30` | [JSON](project/sessions/20261113-e30-backup-verification.json) |
| `20261113-e29` | [JSON](project/sessions/20261113-e29-backup-verification.json) |
| `20261113-e28` | [JSON](project/sessions/20261113-e28-backup-verification.json) |
| `20261106-depth-query-wiring-backup-verification` | [JSON](project/sessions/20261106-depth-query-wiring-backup-verification.json) |
| `20261106-e10-backup-verification` | [JSON](project/sessions/20261106-e10-backup-verification.json) |
| `20261106-e11-backup-verification` | [JSON](project/sessions/20261106-e11-backup-verification.json) |
| `20261106-e12-backup-verification` | [JSON](project/sessions/20261106-e12-backup-verification.json) |
| `20261106-e13-backup-verification` | [JSON](project/sessions/20261106-e13-backup-verification.json) |
| `20261106-e14-backup-verification` | [JSON](project/sessions/20261106-e14-backup-verification.json) |
| `20261106-e15-backup-verification` | [JSON](project/sessions/20261106-e15-backup-verification.json) |
| `20261106-e16-backup-verification` | [JSON](project/sessions/20261106-e16-backup-verification.json) |
| `20261106-e17-backup-verification` | [JSON](project/sessions/20261106-e17-backup-verification.json) |
| `20261106-evening-wiring-backup-verification` | [JSON](project/sessions/20261106-evening-wiring-backup-verification.json) |
| `20261106-private-research-backup-verification` | [JSON](project/sessions/20261106-private-research-backup-verification.json) |
| `20261106-remote-backup-verification` | [JSON](project/sessions/20261106-remote-backup-verification.json) |
| `20261107-champion-reference-backup-verification` | [JSON](project/sessions/20261107-champion-reference-backup-verification.json) |
| `20261107-e18-backup-verification` | [JSON](project/sessions/20261107-e18-backup-verification.json) |
| `20261107-e19-backup-verification` | [JSON](project/sessions/20261107-e19-backup-verification.json) |
| `20261107-e20-backup-verification` | [JSON](project/sessions/20261107-e20-backup-verification.json) |
| `20261107-e21-backup-verification` | [JSON](project/sessions/20261107-e21-backup-verification.json) |
| `20261107-e22-backup-verification` | [JSON](project/sessions/20261107-e22-backup-verification.json) |
| `20261107-e23-backup-verification` | [JSON](project/sessions/20261107-e23-backup-verification.json) |
| `20261107-e24-backup-verification` | [JSON](project/sessions/20261107-e24-backup-verification.json) |
| `20261107-e25-backup-verification` | [JSON](project/sessions/20261107-e25-backup-verification.json) |
| `20261107-e26-backup-verification` | [JSON](project/sessions/20261107-e26-backup-verification.json) |
| `20261107-e27-backup-verification` | [JSON](project/sessions/20261107-e27-backup-verification.json) |
| `20261107-m2-candidate-backup-verification` | [JSON](project/sessions/20261107-m2-candidate-backup-verification.json) |
| `20261107-named-depth-wiring-backup-verification` | [JSON](project/sessions/20261107-named-depth-wiring-backup-verification.json) |
| `20261107-single-arm-offline-backup-verification` | [JSON](project/sessions/20261107-single-arm-offline-backup-verification.json) |
| `20261107-wrist-translation-candidate-backup-verification` | [JSON](project/sessions/20261107-wrist-translation-candidate-backup-verification.json) |

## 공식 자료와 보존 연구

[주최 측 README](../README.upstream.md) / [공식 문서](competition/) / [챌린지·점수 설명](project/CHALLENGE_GUIDE.ko.md) / [초기 계획](project/PLAN.ko.md) / [연구 검토](collection/research/)

## 통합 전 설명

아래는 개편 직전 commit에 고정한 원문입니다. Git 이력에서 그대로 보존하며 현재 checkout에 같은 설명을 중복 관리하지 않습니다. 실행 원본·영상·manifest·provenance는 기존 경로를 유지합니다.

| 이전 문서 | 원문 |
|---|---|
| `README.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.md) |
| `AGENTS.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/AGENTS.md) |
| `docs/project/STATUS.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/STATUS.md) |
| `README.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.ko.md) |
| `README.before-reorganization-20261106.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.before-reorganization-20261106.ko.md) |
| `README.history.en.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.history.en.md) |
| `README.history.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/README.history.ko.md) |
| `docs/gallery/README.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/gallery/README.ko.md) |
| `docs/collection/README.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/collection/README.ko.md) |
| `docs/collection/guides/astra-end-to-end.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/collection/guides/astra-end-to-end.ko.md) |
| `docs/project/START_HERE.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/START_HERE.ko.md) |
| `docs/project/CODE_MAP.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/CODE_MAP.ko.md) |
| `docs/project/CODEX_CONTEXT.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/CODEX_CONTEXT.ko.md) |
| `docs/project/PRESENTATION.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/PRESENTATION.ko.md) |
| `docs/project/RESEARCH_ROADMAP.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/RESEARCH_ROADMAP.ko.md) |
| `docs/project/TODO.ko.md` | [고정 원문](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/f17f5495259468ce2c9fc625b4eff145a28d27cf/docs/project/TODO.ko.md) |

## 현재 전략 중심 정리 이전 본문

2026-11-16의 상세 E33–E36 표와 이전 실행 지시를 확인하려면 아래 고정 원문을 사용합니다. 현재 checkout은 중복을 줄였으며 세션·영상·manifest·백업 receipt 경로는 보존했습니다.

| 문서 | 정리 전 고정 원문 |
|---|---|
| STATUS | [1bd3f597의 상세 상태](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/1bd3f597ac5da6ee037f0f491b5b078ba57b7b32/docs/project/STATUS.md) |
| AGENTS | [1bd3f597의 인계 지침](https://github.com/leonyoon-3dai/PhyRC_2027_phase1/blob/1bd3f597ac5da6ee037f0f491b5b078ba57b7b32/AGENTS.md) |

## 사용자 피드백 checkpoint 검증

[E36 저장·복원 비교](collection/reviews/20261116-checkpoint-validation.ko.md) · [고정 백업 receipt](collection/reviews/20261116-checkpoint-backup-verification.json). 준비934전이·복원1전이 정상 마감 및 전수 QC, HF revision `eb05c6f98f59cce84084ab9a10e153687292ee53`,91개 manifest 파일·archive 재다운로드 SHA 검증. M1 착의 성과나 현재 열린 HOLD의 마감으로 세지 않는다.
