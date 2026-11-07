# 현재 상태와 다음 작업

**E26은5/50·착의0·success=false,1139/1139전이 검사 통과로 자율 종료했습니다.** 21act+finish1/25calls,3query22valid·물리0·마감0,1139=787replay+232model+120settle입니다. 최종 판단은 마지막22번째 슬롯의 모델finish이며 예산 강제중단이나 감독자 신호가 아닙니다. no_dressing_points/final_score0.0·host78009=0·shellPython0·sim0·capturecomplete/operator_finished입니다.

[최신 영상](../gallery/20261107-astra-hand-swap787-named-001.ko.md) · [분석](../collection/reviews/20261107-astra-hand-swap787-named-001.ko.md) · [학습 구간](../collection/reviews/20261107-astra-hand-swap787-named-001-learning-segments.json) · [백업 검증](sessions/20261107-e26-backup-verification.json)

E26은 상대 배치/접근을 바꿨고953에서 두 손 관계를 재노출했습니다. D13의 큰 자세 변화와 작은 gripper 기준점 변화, D17/D18의 보상 관측으로 손 후보를 드러낸 결과를 보존합니다. 초기E23와 목표 손이 달랐다는 근거를 전 이력 최초의 다른 손 접근이나 역할 교환 완료로 확대하지 않습니다. 공식 추가 득점은 없었습니다.

## E27 실행 중 · 2026-11-07T06:58:14Z

E27은 E25/698의 새 파지에서 기존 `coordinated-task-progress`로 운반·진입을 시험하도록 선택했습니다. history657/667·22판단/max1300/settle6·Astra/ultra를 유지하며, source`1ff16b29e28bc9d43faf6bb0f4518e9a65868cb9`·시작clean으로 실제 실행했습니다. D11 뒤968경계까지 공개 관측을 검토했습니다. 새270전이=198모델+72정착·12act/13calls·query1회6valid/물리0입니다. 운반 뒤 손 접근과928의 전완–노란 간격 겹침이 나타났으나950에서 일부 가림이 생겼고968에서는 다른 노출 손으로 접근 대상을 옮겼습니다. 첫 소매 통과·최종 점수는 미확인으로, `second_sleeve` 단계명을 성공으로 쓰지 않습니다. [진행 분석](../collection/reviews/20261107-astra-regrasp698-progress-named-001.ko.md). 새 파지의 국소 동행과 운반 하중 검증은 다르므로 현재 지지를 다시 확인합니다. 카메라 방향 보조 후보는 별도 worktree 전체 CPU335개 검사와 고정 백업을 마쳤으나 이번 설정에 적용하지 않습니다.

E25의 새 파지는 release→다른 경계 placement→보정1→reclose와 R1국소 동행까지 시험했고, 새 파지 뒤 운반/진입은 실행하지 않았습니다. 따라서 운반 효과가 실패한 것으로 단정하지 않습니다. support상태는uncertain이며 table기여·잔류운동·독립하중 미검증을 유지합니다. 직접부모E25/698·새과거관측657/667·같은E07source group,정확한천checkpoint아닙니다. loader는06:45:33UTC에float32(698,2,9)로 통과했고trusted seed등은 공개 출력하지 않았습니다.

현재 실행 코드는E26source53a58bb 이후 바뀌지 않았고 통합CPU317검사 결과가 적용됩니다. 새 카메라 방향 보조 후보는 별도worktree에서335CPU검사를 통과했고 실물리/실actor 성능은 미검증입니다. E27에 섞지 않습니다. 과거 점수나 검수자가 고른 좌표를actor에 전달하지 않습니다.

## E27 실제 시작 명령 · 2026-11-07T06:58:14Z

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-regrasp698-progress-named-001 --mode dressing \
  --strategy coordinated-task-progress --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261107-astra-opposing563-named-001 --replay-prefix-steps 698 \
  --parent-attempt 20261107-astra-opposing563-named-001 \
  --retry-reason transport_and_entry_with_e25_changed_grasp \
  --replay-observe-steps 657 667 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 22 --max-steps 1300 --model-timeout 180 \
  --profile-step-phases
```

E27 실행 로그는`output/sessions/20261106-evening/e27-regrasp698-progress-named-001.log`입니다. host exec session25974이며 Python 반환 후에만 별도 exit파일을 기록합니다. 현재 실행 결과와 종료값은 미확인입니다.

원본 백업은revision`41c78439105eb3a6e1f5fd9c0943cee6039d041b`,2,544,928,271bytes,SHA`82f7f3fb3b0b255c7549499078ef86e90352257f12cb728ccbd88221e5127d44`이며2026-11-07T06:49:13.774600+00:00에재다운로드·254member검증했습니다. 학습 승인은unreviewed입니다. 공식10점을 확인하면 보존 후 다음 득점으로 계속합니다.

<details>
<summary>E25 마감·E26 실행 당시 진행 이력</summary>

> 아래는 당시 기록이며 현재 상태는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**E25는5/50·픽업5·착의0·success=false,698/698전이 검사 통과로 종료했습니다.** 한쪽 재파지1cycle과새파지국소동행을확인했지만반대두입구경계의개방은미확인입니다. 운반/진입전에모델이자율종료했습니다. 최고5점·중간목표10점미달성입니다.

[최신 영상](../gallery/20261107-astra-opposing563-named-001.ko.md) · [분석](../collection/reviews/20261107-astra-opposing563-named-001.ko.md) · [학습 검토 구간](../collection/reviews/20261107-astra-opposing563-named-001-learning-segments.json) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E25 결과 |
|---|---|
| 실행 소스·부모 | `68658c9d9bb7e47591fb330f08f4f996ec4fcbfb`·시작clean·직접E18/563·history510/542 |
| 모델·전략 | Astra/ultra·coordinated-opposing-rim·named/query·13act+finish1/15calls·1query6유효점·질의물리0 |
| 실제 구간 | 563재실행+93모델+42정착=698·34.9sim초. 새135전이6.75sim초·마감물리0 |
| 실제 시간 | 05:18:00–05:38:26UTC·1225.593759초(20분26초) |
| 호출 경로 | 모델568.194194초·환경609.287344초. 순수 내부 추론시간은 미제공 |
| 공식 결과 | raw5·픽업5·착의전항목0·success=false·no_contact/final_scorenull |
| 마감·검사 | 모델finish·attempt completed/errornull·capture complete/operator_finished·QC698/698오류0·host76977=0·shell Python0·simulator0 |
| 보존·학습 | [고정 원본 백업·재다운로드 검증 완료](sessions/20261107-e25-backup-verification.json)·training unreviewed |

## 실제 파지 변경에서 확인한 범위

D2에서R1만열고D3초기배치·D5보정1후D7한번다시닫았습니다. R0쪽천을유지했고D9한쪽상승에서R1실제lift+26.62mm와국소천동행을확인했습니다. 추가닫힘도혼재하므로독립하중지지나반대free lip파지확정은아닙니다. D10수축/roll차등시험·D11자세복구·D12중립뒤에도큰파란면과한노란경계가주로보여두경계개방은미확인이었습니다. 30판단중14판단을사용했고16개를남긴자율finish입니다. 감독중단이나예산소진과구분합니다.

## E26에서 손·역할·접근면을 바꾸는 비교

**E18/787·history719/771·coordinated-leading-hand-swap·22판단/max1400**으로선택했습니다. 원래운반을마친출발점에서현재구별되는다른손을leading으로정하고guide/anchor역할과body-opening접근면을바꾸는비교입니다. 재파지0이며body opening으로들어가그손의대응sleeve로나오는방향을유지합니다. 과거손정체·좌표·평가정답을actor에주지않습니다.

현재/이전목표손이나역할을식별하지못하면교환미확인으로기록합니다. 그상태에서도유용한일반접근은가능하지만M2수행으로세지않습니다. E25새파지결과는보존하며,이번에는기존E18/787의다른접근비교를우선합니다. 기존E23/E24와도천접힘·예산차이가있으므로단일인과를확정하지않습니다. [방법·판정구분](../collection/research/2026-11-07-leading-hand-candidate.ko.md)

M2후보3d1bf2c를E25실제종료후통합했습니다. 전체CPU는[검증기록](sessions/20261107-leading-hand-validation.json)에남기며실제손교환·착의효과는아직미검증입니다. E25의추가중립에서위치추종수렴을봤지만이번E26은정착6을유지해새방법과관측시점변경을동시에섞지않습니다. 공식물리·20Hz·최대20step·모델·관측계약은그대로입니다. **E26는2026-11-07T05:51:36Z에source`53a58bb4e9fa4ff5366b66485c8690b0784ad71f`·시작clean으로 실제 시작했습니다.** 06:13 UTC 기준 새5act·총885=787replay+68model+30settle입니다. D0대각이동/R1추가신장→D1양pitch/R1신장→D2전진+pitch→D3후퇴+pitch복구→D4pitch유지전진을 실행했습니다. D2/D4에서 손 가림·틈 좁아짐, 중간 D3에서 실제 손 재노출·틈 복구를 확인했습니다. query1회6valid·물리0이며 후속 실행 중입니다. E23 초기 H_A와 이번 H_B 선택 차이는 [부분 비교](../collection/research/2026-11-07-e26-initial-hand-comparison.ko.md)에서 확인했지만, 전 이력 최초의 다른 손 접근·지속 leading·역할 교환 완료로 확대하지 않습니다. 최종 점수는 아직 확인하지 않았습니다.

### 공개 진행 갱신 · 2026-11-07 06:21 UTC

D8까지 새9act·953=787replay+112model+54settle이며 query1회6valid·물리0입니다. D5는 양base의 반대 전후 이동과 양wrist yaw로 상대 파지 배치를 바꿨고, D6은 새 방향에서 측면 접근했습니다. D7양lift하강 뒤 목표 손/전완이 경계 위로 재노출됐고 D8전진에서도 이 가시성을 유지하면서 다른 손도 다시 드러났습니다. 앞선 D2/D4전진에서의 가림과 구분되는 공개 관계 변화입니다. **953경계의 진전은 보존하되 손 통과·소매 통과·지속적 역할 교환·공식 추가 득점은 아직 확인하지 않았습니다.** 실행 중 점수 정보를 actor에 주지 않습니다.

### 공개 진행 갱신 · 2026-11-07 06:29 UTC

D13까지 새14act·1,027=787replay+156model+84settle·query2회14valid/물리0입니다. D9–11은 R0의 반대측 지지를 유지하며 R1의 실제 접근을 더했고, 953에서 보존된 두 손 관계는967/981까지 유지됐습니다. 이후995에서H_B가 더 가려졌고, D12의R0추가전진/상승+R1전진 뒤1009에서는H_A의아래손관계도소실됐습니다. D13은양pitch변경에lift/arm보상을더해잡힌경계위치를대략유지하려는방향시험을실행했습니다. obs13→14의공개grasp_base 기준점이동은R0약4.62mm/R1약3.10mm,실제pitch변화−.460/−.461rad·lift−131.6/−136.1mm였습니다. base도약.95/1.12mm움직였으므로완전정지나천재료점고정을뜻하지않습니다. root도이선별수치를재계산했습니다. R0head의가까운손/전완일부는재노출됐지만H_B연속추적·진입은미확인입니다. 최종 결과는 아직 미확인입니다.

[D5 실제 상대 배치 분석](../collection/reviews/20261107-astra-hand-swap787-named-001-orientation.ko.md)은903경계까지만다루며,두그리퍼공개기준점연결선15.223°변화를root도별도계산으로재확인했습니다. 이는옷입구평면·접촉·재료점회전을뜻하지않습니다.953의이전진전을이후가림때문에없었던것으로묶지않습니다.

### 공개 진행 갱신 · 2026-11-07 06:38 UTC

D18까지 새19act·1,107=787replay+212model+108settle입니다. D14의 모델 중립6은 추가 정착이고 자동 정착 설정을12로 바꾼 것이 아닙니다. D15전진/상승·D16옆이동/상승 뒤 R1head 화면 끝에 손 조각 후보가 나타났습니다. D17/D18은 base yaw·가로 이동·wrist counter-yaw를 결합한 보상 관측으로, D18 뒤 손과 짧은 손목이 화면 안에 더 분명히 보였습니다. 연결 전완·손 정체·소매 경계 통과는 미확인입니다.

D17의 R1 base yaw는 약8.19°, D18은 약20.46° 바뀌었습니다. D17의 world grasp 끝점 차이는 R0/R1 약6.27/6.22mm이며 수평 차이는 작아도 Z가 약6mm 변했습니다. D18의 차이는 R0약.70mm/R1약3.58mm입니다. root도 이 world 끝점 수치를 별도 계산으로 확인했습니다. 이는 유용한 관측 조작의 근거이며, 경로 중 최대 이탈·천 재료점 고정·손 통과를 인증하지 않습니다.

## E26 실제 시작 명령 · 2026-11-07T05:51:36Z

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-hand-swap787-named-001 --mode dressing \
  --strategy coordinated-leading-hand-swap --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-guide470-depth-001 --replay-prefix-steps 787 \
  --parent-attempt 20261106-astra-guide470-depth-001 \
  --retry-reason compare_leading_hand_roles_and_body_entry_approach \
  --replay-observe-steps 719 771 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 22 --max-steps 1400 --model-timeout 180 \
  --profile-step-phases
```

실제 source는`53a58bb4e9fa4ff5366b66485c8690b0784ad71f`,로그는output/sessions/20261106-evening/e26-hand-swap787-named-001.log입니다. 직접부모는E18이며같은E07 source group입니다. 재실행은정확한천checkpoint가아니고새현재지지를다시확인합니다. 공식10점을확인하면원본·성과를보존하고다음득점으로계속합니다.

<details>
<summary>E24 종료·E25 실행 중 당시 상태 이력</summary>

> 아래는 당시 기록입니다. 현재 상태는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**E24는5/50·픽업5·착의0·success=false,1,610/1,610전이 검사 통과로 종료했습니다.** 22회 실제 행동에서 손–경계 정렬과 진입 시도, 큰 면 가림과 마지막 부분 시야 복구를 확인했습니다. 공식 소매 통과는 없으며 최고5점·중간목표10점미달성입니다.

[최신 영상](../gallery/20261107-astra-progress1179-named-001.ko.md) · [분석](../collection/reviews/20261107-astra-progress1179-named-001.ko.md) · [학습 검토 구간](../collection/reviews/20261107-astra-progress1179-named-001-learning-segments.json) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E24 결과 |
|---|---|
| 실행 소스·부모 | `b0513d43a87c813397c57d8a4fa6ec4e6ff6ba03`·시작clean·직접E23/1179·history1077/1161 |
| 모델·전략 | Astra/ultra·coordinated-task-progress·named/query·22act/26calls·3query/16유효점·finish0 |
| 실제 구간 | 1179재실행+304모델+126정착+1감독 마감=1610·80.5sim초. 새431전이21.55sim초 |
| 실제 시간 | 04:11:53–05:02:19UTC·3025.995557초(50분26초) |
| 호출 경로 | 모델1443.976115초·환경1523.851616초. 순수 내부 추론시간은 미제공 |
| 공식 결과 | raw5·픽업5·착의전항목0·success=false·no_dressing_points/final_score0.0 |
| 마감·검사 | 감독SIGINT→attempt interrupted·capture complete/operator_finished·QC1610/1610오류0·host22076=130·shell Python130·simulator0 |
| 보존·학습 | [고정 원본 백업·재다운로드 검증 완료](sessions/20261107-e24-backup-verification.json)·training unreviewed |

05:01:38UTC에22행동을 마친1609경계에서 감독 종료를 요청했습니다. 세 번째 공개 깊이 질의는 실행됐지만 그 후 D22 행동 응답은 폐기됐고, 중립 마감1전이만 추가됐습니다. 모델 자율finish·30판단 예산 종료와 구분합니다. 원래 `human_intervention=false`는 수동 물리행동 주입이 없음을 뜻하며, 감독 종료 요청이 없었다는 뜻으로 읽지 않습니다.

## E25에서 파지 배치를 바꾸는 이유

E24 D15 높이 변경으로 손이 다시 보였고, D17 몸쪽 진입 뒤 큰 면이 손과 틈을 가렸습니다. D18의 base만 반전, D19 차등 높이, D20 자세 보정에서는 관계가 복구되지 않았습니다. D21 추가 후퇴·들기는 어두운 틈을 일부 다시 노출했습니다. **마지막까지 변화가 없었다거나 모든 진입 방향이 소진됐다는 결론은 아닙니다.** 유용한 부분 복구까지 보존하고, 동일 파지 조정22회 이후 실제 파지 변경을 비교하기로 했습니다.

E25는 **E18/563·history510/542·coordinated-opposing-rim·30판단/max1400**으로 선택했습니다. 새 재실행 관측에서 양측 지지와 테이블 지지를 확인하고, 한쪽 anchor를 남기며 다른 접근 가능한 경계를 한 번 다시 잡습니다. 닫힘 뒤 국소 천 동행·anchor 유지·차등 경계 반응을 확인한 다음 유용하면 운반과 착의를 이어갑니다. E17의 미확인 반대 경계 가설을 더 나은 출발점·검사 순서로 재시험하며 첫 발명으로 세지 않습니다. [방법·제약](../collection/research/2026-11-07-opposing-rim-candidate.ko.md)

후보a3d10a5를 E24 종료 후 main에 통합했습니다. source loader563개 float32(563,2,9) 검수를 완료했고, 전체 CPU 결과는 [검증 기록](sessions/20261107-opposing-rim-validation.json)에 남깁니다. 새 선택 지침 외 공식 물리·20Hz·최대20step·모델·관측 계약은 유지합니다. **E25는2026-11-07T05:18:00Z에source`68658c9d9bb7e47591fb330f08f4f996ec4fcbfb`·시작clean으로 실제 시작했습니다.** 563개 준비 행동 뒤D0/D1(각8act+6settle)로591경계까지 양측 하강했습니다. 현재 몸판이 테이블에 더 넓게 놓이고 jaw 부근 천은 남으나 잔류 하강이 있습니다. R0 anchor/R1 changed측 선택,release0·새파지0이며 최종점수미확인입니다. E18/563의 과거5점은 actor 입력이 아닙니다. E07/430·E15/367은 다른 자세·기존 파지·잔류 운동의 대안이어서 함께 바꾸지 않았습니다.

## E25 실제 시작 명령 · 2026-11-07T05:18:00Z

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-opposing563-named-001 --mode dressing \
  --strategy coordinated-opposing-rim --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-guide470-depth-001 --replay-prefix-steps 563 \
  --parent-attempt 20261106-astra-guide470-depth-001 \
  --retry-reason test_opposing_rim_grasp_after_current_grip_entry_comparisons \
  --replay-observe-steps 510 542 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 30 --max-steps 1400 --model-timeout 180 \
  --profile-step-phases
```

실제실행source는`68658c9d9bb7e47591fb330f08f4f996ec4fcbfb`,로그는output/sessions/20261106-evening/e25-opposing563-named-001.log입니다. 새 run ID·직접 부모E18·같은E07 source group을 보존합니다. 재실행은 정확한 천 checkpoint 복원이 아니며 새 지지를 다시 확인합니다. 공식10점 확인 뒤 보존·검증하고 다음 득점으로 계속합니다. [장기 구간 조합](../collection/research/2026-11-07-composable-scoring-data-plan.ko.md)은 현재 합성·학습 실행과 구분합니다.

<details>
<summary>E23 종료·E24 실행 중 당시 상태 이력</summary>

> 아래는 당시 기록입니다. 현재 상태는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**E23은5/50·픽업5·착의0·success=false,1,180/1,180전이 검사 통과로 종료했습니다.** 방향 반전·측면 접근·한쪽 경계 들기 뒤 손과 전완이 천 옆으로 드러났지만 공식 소매 통과·착의 득점은 없습니다. 머리 쪽 상승·하강·시점 복구 뒤18판단 예산을 소진했습니다. 최고5점·중간목표10점미달성입니다.

[최신 영상](../gallery/20261107-astra-progress787-named-001.ko.md) · [분석](../collection/reviews/20261107-astra-progress787-named-001.ko.md) · [학습 검토 구간](../collection/reviews/20261107-astra-progress787-named-001-learning-segments.json) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E23 결과 |
|---|---|
| 실행 소스·부모 | `952ec8da68cdc0ef635d0d45329712eee006fd1f`·시작clean·직접E18/787·history719/771 |
| 모델·전략 | 고정Astra/ultra·coordinated-task-progress·named/query·18판단18act/18calls·query0·finish0 |
| 실제 구간 | 787재실행+284모델+108정착+1예산 마감=1180·59sim초. 새393전이19.65sim초 |
| 실제 시간 | 03:30:54–04:02:40UTC·1906.180018초(31분46초) |
| 호출 경로 | 모델821.402335초·환경1031.865206초. 순수 내부 추론시간은 미제공 |
| 공식 결과 | raw5·픽업5·착의전항목0·success=false·no_dressing_points/final_score0.0 |
| 마감·검사 | decision_budget·capture complete/operator_finished·QC1180/1180오류0·host exec95905=0·shell 관측 Python0·simulator0 |
| 보존·학습 | [고정 원본 백업·재다운로드 검증 완료](sessions/20261107-e23-backup-verification.json)·training unreviewed |

## 같은 방법을 이어갈 근거

E22의 짧은 정보 탐색과 달리, E23에서는 실제 목표 방향 이동·천 변형·접근 방향 반전과 손/전완 재노출이 있었습니다. 마지막에도 팔 노출과 두 경계 부근 천 유지가 보입니다. 다만 공식 통과는 없고, 머리–입구 관계는 가려졌습니다. **새 관계를 보존해 미완료 목표를 확인하는 연속 분기**를 먼저 준비합니다. 실패 원인이 모두 해소됐거나 새 파지 방법이 검증됐다는 뜻은 아닙니다. 같은prefix라도 초기 천 접힘이 달라 E22/E23차이를 프롬프트 한 가지의 인과로 단정하지 않습니다.

**E24는2026-11-07 04:11:53UTC에 실제 시작했습니다.** source`b0513d43a87c813397c57d8a4fa6ec4e6ff6ba03`·working_tree_modified=false입니다. E23/1179·history1077/1161·30판단·max2000이며 1179개 준비 행동 뒤 하강·방향 변경을 수행했습니다. 한쪽 팔의 목표와 실제 움직임 차이를 확인해 목표·자세를 조정했고, 공개 깊이6점 조회 후 뒤·옆 방향으로 이동했습니다. D8까지(1361경계) 얼굴·몸통과 손–경계 관계가 더 드러났지만 입구 통과·최종 점수는 아직 미확인입니다. [공개 관절 수치 대조](../collection/reviews/20261107-astra-progress1179-named-001-motion.ko.md)1179는 마지막 모델행동과6정착 후, 추가 예산마감1전이 전입니다. 최종 공개5뷰·잔류 운동과 source loader1179개행동 검수를 완료했고, 실행소스22파일이 E23와 같음을 확인했습니다. 기존task-progress/모델/코드/공식20Hz·물리·최대20step은 유지하고, 재실행에서 현재 지지를 다시 판단합니다. 18판단에서30판단으로 늘리는 것은 모델 요청 예산이며 행동 한계 변경이 아닙니다. [다른 조작 후보](../collection/research/2026-11-07-post-overhead-method-options.ko.md)의 M1은 별도 준비 상태입니다.

[더 이른5점 후보](../collection/research/2026-11-07-earlier-support-startpoints.ko.md)의 E15/367은 원본 복원·loader 검증을 마쳤지만 아직 선택·실행하지 않았습니다. [의복 방향 가설](../collection/research/2026-11-07-garment-direction-hypotheses.ko.md)은 E23초기obs0–5만 검토한 시점별 기록이며 뒤의 팔 노출을 미리 주장하지 않습니다.

## E24 실제 시작 명령 · 2026-11-07 04:11:53 UTC

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-progress1179-named-001 --mode dressing \
  --strategy coordinated-task-progress --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261107-astra-progress787-named-001 --replay-prefix-steps 1179 \
  --parent-attempt 20261107-astra-progress787-named-001 \
  --retry-reason continue_new_arm_garment_relation_after_decision_budget \
  --replay-observe-steps 1077 1161 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 30 --max-steps 2000 --model-timeout 180 \
  --profile-step-phases
```

실제실행source는b0513d4 clean,로그는output/sessions/20261106-evening/e24-progress1179-named-001.log입니다. 재실행완료·새판단·결과는별도갱신합니다. 직접 부모는E23이며 같은E07 source group입니다. action replay는 정확한 천 checkpoint가 아닙니다. 공식10점 확인 뒤 보존·검증하고 다음 득점으로 계속합니다. [장기 구간 조합](../collection/research/2026-11-07-composable-scoring-data-plan.ko.md)은 현재 합성·학습 실행과 구분합니다.

<details>
<summary>E22 종료·E23 실행 중 당시 상태 이력</summary>

> 아래는 당시 기록입니다. 현재 상태는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**최신 E22는5/50·픽업5·착의0·success=false로 종료했고813/813전이 검사를 통과했습니다. 최고5점으로 중간 목표10점은 아직 미달성입니다.** 짧은 전진·시점 보정·잔류 대기 뒤 모델이 자율 종료했습니다. 실제 진입/안착 동작을 충분히 시험하지 못했고 공식 평가는no_contact/null입니다.

[최신 영상](../gallery/20261107-astra-probe787-named-001.ko.md) · [분석](../collection/reviews/20261107-astra-probe787-named-001.ko.md) · [출발점 화면 비교](../gallery/20261107-support-startpoints.ko.md) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E22 결과 |
|---|---|
| 소스·부모 | `11faab3797cacd0160a725578d4a9dc65c6b018f`·시작clean·E18직접부모/787·history719/771 |
| 전략·판단 | coordinated-entry-probe·18예산 중4판단=3act+finish·5호출·질의1회7유효점/물리0 |
| 실제 새 행동 | 양base전진4·양wrist pitch보정4·모델중립6. 재파지0회·마감물리0 |
| 기록 | **787재실행+14모델+12정착=813**,40.65sim초. 새26전이1.3sim초 |
| 실제 시간 | 2026-11-07 03:01:21–03:18:34 UTC,1032.883288초(17분12.883초) |
| 호출 경로 | 모델294.325561초·환경694.749380초. 내부 추론시간 미제공 |
| 평가 | raw5·착의0·success=false·no_contact/null |
| 마감·검사 | 모델finish·attempt completed·capture complete/operator_finished·simulator0·QC813/813오류0 |
| 별도 실행 도구 | exec session61989 반환143. 발신·원인 미확인, Python client 반환코드로 단정하지 않음. 직접 감독 중단 요청0 |
| 학습·보존 | unreviewed·원본 닫힘/QC확인·[고정 원본 백업 검증 완료](sessions/20261107-e22-backup-verification.json) |

## 다음 비교를 바꾸는 근거

첫4step전진 뒤, 시점 보정과 중립 대기에서도 새로운 손–경계 관계를 확인하지 못했습니다. 마지막 설명은 새 근거가 없고 재파지가 금지된 범위라서 같은 탐색을 반복하지 않겠다는 것이었습니다. 이는 **짧은 정보 탐색 이후 행동 선택이 진입 전에 종료된 결과**입니다. 입구의 물리적 진입 불가능성을 입증하지 않으며, 지침의 엄격한 정보 조건이 조기 종료에 기여했을 가능성을 다음 비교에서 다룹니다.

**E23은 2026-11-07 03:30:54 UTC에 시작했습니다.** source `952ec8da68cdc0ef635d0d45329712eee006fd1f`·working_tree_modified=false입니다. 787개 준비 행동을 마친 뒤 두 차례 전진과 손목 각도 조정까지 수행했습니다. 손과 경계의 투영 겹침은 새로 보이지만 통과·최종 점수는 아직 미확인입니다. 통합302CPU검사23.432초 통과 소스를 사용합니다. 같은 검수E18/787에서 `coordinated-task-progress`를 비교할 예정입니다. 현재 공개 관측에서 하나의 목표 관계를 고르고 공식 최대20control-step 범위에서 목적 있는 한 구간의 접근/하강을 수행합니다. 완전한 lip 식별·빈 배경·즉각적 시야 개선을 필수조건으로 추가하지 않으며, 가림·접촉·실패 가능성을 미리 성공이나 빈 공간으로 해석하지 않습니다. 한 행동 뒤 정착을 포함한 다음 관측에서 실제 옷의 목표 진전·지지를 평가하고, 효과 없는 가려진 동작을 연쇄 반복하지 않습니다. 기존 파지 유지·새 재파지0회,공식물리/관절/입력/행동변경없음입니다.

이번 변경은 불확실성 아래 행동 선택과 진전의 정의를 비교합니다. 실제로 새로운 안착 조작이 수행됐는지는 최종 동작 기록으로 따로 판정합니다. [다른 실제 조작 후보](../collection/research/2026-11-07-post-overhead-method-options.ko.md)에는 반대lip 재파지·다른손 leading 측면접근도 남겨뒀습니다. [국소depth 검토](../collection/reviews/20261107-astra-overhead470-named-001-local-depth.ko.md)는 손과 노란 띠의 유효한3D차이와 입구/접촉의 의미 판정을 분리합니다.

[후보 범위](../collection/research/2026-11-07-task-progress-candidate.ko.md) · [통합 검증 기록](sessions/20261107-task-progress-validation.json)

## E23 실제 시작 명령 · 2026-11-07 03:30:54 UTC

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-progress787-named-001 --mode dressing \
  --strategy coordinated-task-progress --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-guide470-depth-001 --replay-prefix-steps 787 \
  --parent-attempt 20261106-astra-guide470-depth-001 \
  --retry-reason task_progress_after_information_probe_stopped_before_entry \
  --replay-observe-steps 719 771 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 18 --max-steps 1300 --model-timeout 180 \
  --profile-step-phases
```

E22의 직접부모는E18이며E23도같은경계에서비교합니다. prefix는정확한천checkpoint가아니므로현재관측에서지지를다시확인합니다. E18고정백업44d01871f0099f8a537f1bdbfee06a404a95f38c 검증완료, [복원 안내](START_HERE.ko.md), [출발점/방법 DB](../collection/catalog/README.ko.md)를따릅니다. 공식10점확인후보존·검증하고다음득점항목으로계속합니다. [장기구간조합](../collection/research/2026-11-07-composable-scoring-data-plan.ko.md)은현재합성·학습실행과구분합니다.

<details>
<summary>E21 종료·E22 실행 중 당시 상태 이력</summary>

> 아래는 당시 기록이며 현재 지시는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**최신 종료 E21은5/50·픽업5·착의0·success=false,1111/1111전이 검사 통과입니다. 최고5점으로 중간 목표10점은 아직 미달성입니다.** 두 하강 접근·시야와 방향 보정에도 손 통과는 미확인입니다. 테이블 복귀 뒤 한쪽 새 위치 재파지를 실행했으나 지지 유지 검사는 하지 못하고40판단 예산으로 종료됐습니다.

[최신 영상](../gallery/20261107-astra-overhead470-named-001.ko.md) · [분석](../collection/reviews/20261107-astra-overhead470-named-001.ko.md) · [학습 검토 구간](../collection/reviews/20261107-astra-overhead470-named-001-learning-segments.json) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E21 결과 |
|---|---|
| 실행 소스 | `d383063670085afccabfb51e6af530607d2efd44`·시작clean |
| 직접 부모 | E18/470·history430/464·같은 E07 source group |
| 호출·행동 | 40act/44모델 호출·질의4회29유효점·질의 중 물리0 |
| 기록 | **470재실행+412모델+228정착+1예산 종료=1111**,55.55sim초. 새641전이32.05sim초 |
| 실제 시간 | 2026-11-07 01:56:25–02:48:54 UTC,3149.109434초(52분29초) |
| 호출 경로 | 모델2160.241971초·환경926.844498초. 내부 추론시간 미제공 |
| 평가·종료 | raw5·착의0·success=false·no_dressing_points/0.0. decision_budget·client0·complete·QC오류0 |
| 학습 승인 | unreviewed. 마지막 새 파지 지지·반대층 선택 미확인 |
| 원본 보존 | 고정HF revision `45e6adf8586f935b3ca9f6d19ed3ec97371be44f` 재다운로드 및416member 검증 완료 |

## 미세조정 뒤 다음 비교

E21은 기존 파지로 운반한 뒤 실제 하강·전후/측면 방향 보정을 수행했습니다. 두 시점 변경과 복구 뒤에도 손 가림·천 외면 관계를 해소하지 못해 테이블 복귀·파지 변경으로 전환했습니다. 모든 경로가 소진됐다는 뜻은 아닙니다. 마지막 닫힘 뒤 지지 검사 없는 상태를 검증된 시작점으로 승격하지 않습니다.

**E22는2026-11-07 03:01:21UTC에 시작했습니다.** source `11faab3797cacd0160a725578d4a9dc65c6b018f`·working_tree_modified=false, 현재 초기화·행동 재실행 중입니다. [검수 출발점](../collection/research/2026-11-07-support-startpoints-review.ko.md)의 **E18/787**에서 기존 양측 지지를 유지하고 부분 가림 아래 한 구간의 정보 획득용 진입 탐색을 비교합니다. [후보](../collection/research/2026-11-07-entry-probe-candidate.ko.md)는 같은 손–경계 관계·국소 천 동행·공개 실측이 뒷받침할 때2–4control-step probe 뒤 별도6정착을 포함한 다음 관측을 검사하게 합니다. 새 재파지는0회로 한정하고 유용한 관계 변화 없는 가려진 전진을 이어 붙이지 않습니다. 불확실성 아래 행동 선택 비교이며 새 파지 구조나 성공을 보장하지 않습니다.

후보5559af6을 E21 종료 뒤 통합했고 **전체295CPU검사18.451초 통과**했습니다. 기존10전략·공식입력/행동/물리/모델 경로는 유지합니다. E18 전체원본 hash·QC를 다시 확인하고787개의float32(2,9) 행동 prefix를 로드했습니다. 이번 새 환경에서의 물리·파지 상태는 별도로 다시 확인해야 합니다.

## E22 실제 시작 명령 · 2026-11-07 03:01:21 UTC

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-probe787-named-001 --mode dressing \
  --strategy coordinated-entry-probe --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-guide470-depth-001 --replay-prefix-steps 787 \
  --parent-attempt 20261106-astra-guide470-depth-001 \
  --retry-reason bounded_entry_probe_after_two_occluded_lowering_sequences \
  --replay-observe-steps 719 771 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 18 --max-steps 1300 --model-timeout 180 \
  --profile-step-phases
```

[출발점·방법 데이터베이스](../collection/catalog/README.ko.md)는30실행(현재E22포함)과조건부계획2건을분리합니다. E18/787은5점·선택 관측의 양측지지 근거가 있는 경계이며 실제 물리 checkpoint가 아닙니다. 직접출처의 고정HF revision은44d01871f0099f8a537f1bdbfee06a404a95f38c입니다. [E21 백업 receipt](sessions/20261107-e21-backup-verification.json) · [복원 안내](START_HERE.ko.md)

Astra/ultra를 유지하고 README를 갱신합니다. **공식10점 확인 후 보존·검증하고 다음 득점 항목으로 계속 진행합니다.** [0→5→10 구간 조합](../collection/research/2026-11-07-composable-scoring-data-plan.ko.md)은 장기 계획이며 현재 합성·학습을 실행하지 않습니다. [공식 영상](../collection/research/2026-11-07-official-demo-route-review.ko.md)·[BEHAVIOR 검토](../collection/research/2026-11-07-behavior-champion-visual-transfer.ko.md)는 후속 수집 참고이며 외부 영상·좌표·평가값은 actor에 전달하지 않습니다.

<details>
<summary>E20 종료·E21 실행 중 당시 상태 이력</summary>

> 아래는 당시 기록이며 현재 지시는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**최신 종료 E20는 0/50점·착의0·success=false이며 726/726전이 검사를 통과했습니다. 최고5점으로 목표10점은 아직 미달성입니다.** 목선 후보 두 곳을 새로 잡았지만 연속 입구를 확인하지 못해 운반 전에 테이블 지지 쪽으로 낮추고 모델이 자율 종료했습니다.

[최신 영상](../gallery/README.ko.md) · [공개 분석](../collection/reviews/20261107-astra-neckline470-named-001.ko.md) · [학습 구간](../collection/reviews/20261107-astra-neckline470-named-001-learning-segments.json) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E20 결과 |
|---|---|
| 실제 실행 소스 | `799fe804445c6e0fc401927f0ed82b4e5dd4f935`·시작clean |
| 직접 부모 | E18의470행동 재실행·이번 재실행 history430/464·같은 E07 source group |
| 실제 새 방법 | 기존 밑단 파지에서 목선 후보로 한쪽씩 두 차례 새 파지 사이클 |
| 준비 뒤 보정 | 짧은 들기·간격 변경·손목 시점 변경에도 연속 목 개구부 미확인 |
| 호출·행동 | 25호출/24판단=23act+finish1, 추가 depth 질의1회·물리진행0 |
| 기록 | **470재실행+154모델+102정착=726**,36.3sim초. 새256전이=12.8sim초 |
| 실제 시간 | 2026-11-07 01:18:21–01:48:05 UTC,1783.289405초(29분43초) |
| 호출 경로 | 모델1090.693713초·환경640.649879초. 모델 내부 추론시간 미제공 |
| 평가·종료 | raw0/50·전 항목0·success=false·no_contact/null. client0·complete·QC726/726오류0 |
| 학습 승인 | unreviewed. 실패 준비·부분 지지·질의·회복·종료를 구분해 원본 보존 |

## 미세조정과 새 방법 선택

E20의 두 재파지는 실제 파지 위치 변경이었습니다. 그 뒤 높이·간격·시점 보정에서도 목 입구는 파란 천으로 채워진 듯 보여 층 분리가 불명확했습니다. 따라서 이 결과를 머리 우선 착의 자체의 실패로 넓히지 않습니다. 이번 시도는 **입구 준비 단계에서 종료**됐습니다.

다음은 [공식 시연](../collection/research/2026-11-07-official-demo-route-review.ko.md)에 가까운 **몸통 입구를 머리·팔 위로 배치한 뒤 내려 안착시키는 경로**입니다. 목선 재파지나 첫 소매·목 통과를 선행조건으로 강제하지 않고, 현재 유용한 몸통 입구 지지에서 관측 가능한 경로를 검토합니다. 더 높이 드는 것만으로 새 방법을 수행했다고 세지 않습니다. [후보·검증 범위](../collection/research/2026-11-07-overhead-drape-candidate.ko.md)

사용자는 목선 파지가 어려워 보인다는 의견으로 앞선 선호를 수정했습니다. 현재 E20 근거도 목 우선 파지의 우선순위를 낮추는 판단을 지지합니다. 목선 조정은 부분 착의 뒤의 조건부 후보로 남기며, 이미 시작한 E21의 몸통 입구 상방·하강 비교는 그대로 진행합니다. [피드백 기록](../collection/feedback/2026-11-07.jsonl)

## 다음 분기 비교 · 검수된5점 출발점

사용자는 양측 가장자리 지지를 유지하는 자료를 모아 다음 시도부터5→10점 구간의 다양한 방법을 비교하도록 요청했습니다. [출발점·방법 조합 목록](../collection/catalog/README.ko.md)은 원본실행·출발경계·지지근거구간·점수·방법·실제/계획시도를 연결합니다. E18/563은 첫5점 발생543뒤의 완결된 판단 경계이고,510–563의 선택 관측에서 양측지지 유지 근거가 있어 우선 후보입니다.470은0점대조로구분합니다. 현재 E21 결과를 마감한 뒤 출발점과방법·짧은판단예산을정해다음분기를진행합니다.

Astra/ultra는 유지합니다. 사용자는README로모니터하며, **공식10점 확인뒤에도 다음득점항목으로계속**하도록 요청했습니다. [0→5→10등방법구간조합계획](../collection/research/2026-11-07-composable-scoring-data-plan.ko.md)은장기설계이며현재합성실행·학습은하지않습니다.

## E21 실행 중 · 2026-11-07 01:56:25 UTC 시작

E20 종료 후 후보 f148d6을 통합했고 전체 **277CPU검사를12.745초에 통과**했습니다. 기존 실행 계약·공식 물리·행동 한계는 유지합니다. 순서 지침만 바뀐 후보의 실제 착의 효과는 미검증입니다. 아래 명령으로 실제 시작했고 source snapshot은 `d383063670085afccabfb51e6af530607d2efd44`·working_tree_modified=false입니다. 470행동 재실행 뒤 기존양측지지로 운반하고,높은위치에서여러짧은하강을시험했습니다. 손끝가림뒤두시점변경과복구를수행했고,통과·안착·최종점수는아직미확인입니다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-overhead470-named-001 --mode dressing \
  --strategy coordinated-overhead-drape --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-guide470-depth-001 --replay-prefix-steps 470 \
  --parent-attempt 20261106-astra-guide470-depth-001 \
  --retry-reason overhead_lowering_after_neckline_preparation_unresolved \
  --replay-observe-steps 430 464 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 40 --max-steps 1400 --model-timeout 180 \
  --profile-step-phases
```

직접 출처는 E18/470이며 E20의 변경된 목선 파지를 그대로 재생하지 않습니다. 행동 재실행은 정확한 천 checkpoint가 아니므로 현재 지지를 새 관측에서 확인합니다. E18 원본은 고정HF revision44d01871f0099f8a537f1bdbfee06a404a95f38c에서 검증 완료했습니다. E20 비공개 원본은 고정HF revision `ad7b94f4dd65115082ad53527a48efbf99a5947d`에서 재다운로드 SHA검증을 완료했습니다. 1,721,601,271bytes·SHA256`b427dc7b27d14c933fa67f85df751379044163c05e849c84e7fb138f86b97096`,2026-11-07 01:53:01UTC 확인입니다. [검증 receipt](sessions/20261107-e20-backup-verification.json).

## 참고 연구와 수집 원칙

[공개 관측 절차·복구 카드 초안](../collection/research/2026-11-07-observable-procedure-cards.ko.md)은 E16–E20의 닫힌 증거에서 닫힘·잔류 운동·국소 지지·입구·통과를 분리합니다. 실제 선택기/제어기/훈련에는 연결하지 않았고, 입구 너머 천색만으로 폐쇄를 확정하지 않는 주의도 기록했습니다.

[BEHAVIOR 텍스트·공식 집계](../collection/research/2026-11-07-behavior-champion-text-review.ko.md), [그림·영상·후속 수집 후보](../collection/research/2026-11-07-behavior-champion-visual-transfer.ko.md)를 main에 기록했습니다. 관측으로 검증하는 절차·복구 조건은 후속 비교안이며 새 제어기·훈련에는 적용하지 않았습니다. 외부 영상·좌표·평가값은 actor 입력으로 넣지 않습니다.

[원본 복원](START_HERE.ko.md) · [E19 운동 수치](../collection/reviews/20261107-astra-entry801-named-001-motion.ko.md). 실패·미실행 제안·실행 행동·정착과 회복을 분리하며, 같은 출처 분기를 독립 시연·검증 표본으로 세지 않습니다.

<details>
<summary>E19 종료·E20 실행 중 당시 상태 이력</summary>

> 아래는 당시 기록이며 현재 지시는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**최신 종료 E19는 5/50점·착의 0·success=false이며 932/932기록 검사를 통과했습니다. 최고 5점으로 목표 10점은 아직 미달성입니다.** 명령 표현의 축 불일치는 재발하지 않았으나, 세 번의 접근과 시점 변경에도 손 통과를 확인하지 못해 모델이 후퇴 후 자율 종료했습니다.

[최신 영상](../gallery/README.ko.md) · [E19 분석](../collection/reviews/20261107-astra-entry801-named-001.ko.md) · [학습 검토 구간](../collection/reviews/20261107-astra-entry801-named-001-learning-segments.json) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E19 결과 |
|---|---|
| run ID·실행 소스 | `20261107-astra-entry801-named-001`, 공개 `9aad60138dc5cded2e0e5219fc12395d4c37ff0a`·시작 clean |
| 직접 부모·입력 | E18 행동801개 재실행, 이번 재실행771/787 과거 RGB. B+depth 유지·named-actions 추가 |
| 실제 행동 | 12개 행동, 새 release/regrasp 0회. 세 접근과 후퇴, 한쪽 낮춤, 의도적 roll, 상방·측면 관측 방향 변경 |
| 명령 검토 | 이름별 값·공식 배열·최종 설명의 축 일치. D6의 robot0 roll+0.25는 설명된 의도적 회전이며 E18 오류와 다름 |
| 호출·질의 | 14호출/13판단=행동12+종료1, 추가 depth 질의1회·물리 진행0 |
| 기록 | **801재실행+59모델+72제어기 정착=932**, 시뮬레이션46.6초 |
| 실제 시간 | 2026-11-07 00:45:20–01:11:37 UTC,1577.537494초(26분18초) |
| 호출 경로 | 모델736.917915초·환경793.905205초. 내부 추론시간 미제공 |
| 평가 | 픽업5·모든 착의 항목0·success=false·no_dressing_points/0.0points/s |
| 종료·검사 | 모델 자율 finish·client0·complete·932/932전이 검사 통과·오류0 |
| 학습 승인 | unreviewed. 접근·가림·회복·질의·자율 종료를 같은 출처 그룹으로 보존 |

## 미세조정을 마친 판단과 다음 방법

첫 접근의 가림 뒤 후퇴했고, 한쪽 높이를 바꾼 두 번째 접근도 같은 가림으로 돌아왔습니다. 이후 의도적 roll·상방/측면 시점 변경으로 새 관계를 관측한 뒤 세 번째 접근까지 수행했습니다. 그 결과에도 연속 손–rim crossing이나 소매 출현이 없었습니다. 현재 테이블 지지가 확보되지 않아 공중에서 새 파지를 강행하지 않고 종료했습니다.

이 결과는 이름 기반 표현만으로 입구 문제가 해결되지 않음을 보여줍니다. 현재 파지 배치에서 단순 전진·후퇴를 추가하기보다 **목선 제어와 첫 착의 순서를 바꾸는 목 우선 경로**를 실제 비교합니다. 모든 접근 방법이 실패했다거나 이름 기반 표현의 일반적 오류율이 입증됐다는 결론은 아닙니다. [공개 근거·분기 선택](../collection/research/2026-11-07-post-named-route-choice.ko.md)

## E20 목 우선 · 2026-11-07 01:18:21 UTC 시작

아래 명령으로 실제 시작했습니다. source snapshot은 `799fe804445c6e0fc401927f0ed82b4e5dd4f935`·working_tree_modified=false입니다. 470개 준비 행동의 재실행을 마친 뒤 양쪽 기존 밑단 파지를 순차적으로 목선 후보에 옮겨 닫았습니다. 국소 천 동행은 보였지만 연속 목 입구는 아직 불명확해 높이·간격·시점을 바꾸며 확인하고 있습니다. 이것은 실제 재파지라는 새 방법과 그 뒤 입구 확인 미세조정을 구분한 중간 관측이며, 최종 점수·머리 통과는 아직 미확인입니다.

E18의470경계는 테이블 위 몸판과 목선 후보를 다시 살펴볼 출발점입니다. 현재 지지·목선·머리/팔 여유를 새 관측에서 판단하고 필요하면 테이블 지지 아래 한쪽씩 파지를 바꿉니다. 머리가 몸통 입구로 들어가 목 입구로 나오고 가슴이 안착하는 경로를 먼저 다루며, 단순 목 접촉을 착의로 세지 않습니다. 정확한 천 checkpoint 복원이 아닙니다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-neckline470-named-001 --mode dressing \
  --strategy coordinated-neckline-first --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-guide470-depth-001 --replay-prefix-steps 470 \
  --parent-attempt 20261106-astra-guide470-depth-001 \
  --retry-reason neckline_first_after_three_occluded_entry_approaches \
  --replay-observe-steps 430 464 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 40 --max-steps 1400 --model-timeout 180 \
  --profile-step-phases
```

실행 소스의 전체270CPU검사·실CLI 합성2턴·모델 없는GPU3/3검증은 완료했습니다. E19 이후 실행 코드는 바꾸지 않았으며 목 우선 과제 효과는 아직 미검증입니다. [후보 범위](../collection/research/2026-11-06-neckline-first-candidate.ko.md)

## 원본 보존과 수집 시간

E19 종료 원본은 비공개 HF 고정 revision `a5f9136d1479933b6c026465a8af0321bad1504c`에서 재다운로드 SHA 검증을 완료했습니다. 2,130,731,675 bytes, SHA256 `b2fabcdba6d83418561925176a8fe48e02f9596a2e391d7132cf4f269ef03ab6`,01:16:34 UTC 확인입니다. [검증 receipt](sessions/20261107-e19-backup-verification.json). [복원 안내](START_HERE.ko.md). E18 원본은 고정 revision44d01871f0099f8a537f1bdbfee06a404a95f38c에서 검증 완료했고 E20의 직접 재실행 출처입니다.

[E18 수집 시간 재검토](../collection/research/2026-11-07-e18-capture-timing.ko.md)에서는 경계별 중복 관측·저장을 발견하지 못했습니다. 단순 wrapper 제거의 비현실적 상한도 전체 경과의0.051%여서 신규 최적화를 채택하지 않았습니다. 공식 물리·20Hz·렌더 정합성은 유지합니다.


## 공식 시연·BEHAVIOR 우승 자료 검토

사용자는 목 접근을 지지하며 공식 성공 시연과 비교하고 BEHAVIOR 우승 사이트의 텍스트·이미지를 이후 수집에 참고하도록 요청했습니다. [공식 영상 재검토](../collection/research/2026-11-07-official-demo-route-review.ko.md)에서는 넓은 가장자리 지지→머리·팔 위 이동→하강이 더 분명하며 목선 재파지·머리 우선 순서와 같다고 단정할 수 없었습니다. E20은 독립 가설로 유지하고 공식 영상에 가까운 별도 상방·하강 후보를 격리 작업 트리에서 준비했고49CPU검사를 통과했습니다. 후보 f148d6의 전체 저장소 검사·실제 모델/물리 효과는 아직 미검증이며 현재 실험에는 적용하지 않았습니다.

[BEHAVIOR 텍스트·공식 집계](../collection/research/2026-11-07-behavior-champion-text-review.ko.md)와 [그림·영상·적용 후보](../collection/research/2026-11-07-behavior-champion-visual-transfer.ko.md)를 기록했습니다. 직접 확인한 그림 수치·선택 영상 프레임, 설명/영상의 불일치, 현재 미공개인 방법 코드의 한계를 구분합니다. PhyRC의 공개 관측으로 검증하는 절차 카드·진행 조건·복구 후보는 향후 비교안이며 아직 제어·훈련에 도입하지 않았습니다.

[E19 수치 검토](../collection/reviews/20261107-astra-entry801-named-001-motion.ko.md)는 실제 arm 접근44/67/55mm를 확인했습니다. 동작이 없어서 가림이 반복됐다는 설명은 맞지 않으며, 정착 뒤 잔류 운동과 불완전한 위치 보상은 별도로 남았습니다.

<details>
<summary>E18 종료와 E19 시작 당시 상태 이력</summary>

> 아래는 당시 상태이며 현재 실행 지시는 위 내용을 따릅니다.

# 현재 상태와 다음 작업

**E18 마감: 픽업5/50·착의0·success=false,928/928기록 검사 통과. 최고5/50이며10점 미달성입니다.** 손 근처까지 운반·접근했지만 설명과 다른 robot1 손목 roll+1 명령이D16과D21에서 반복되어, 감독이 SIGINT 정상 종료 절차로 마감했습니다. 모델 자율 종료·사용자 작업 중지와 구분합니다.

[최신 영상](../gallery/README.ko.md) · [E18 분석](../collection/reviews/20261106-astra-guide470-depth-001.ko.md) · [오류·복구·학습 검토 구간](../collection/reviews/20261106-astra-guide470-depth-001-learning-segments.json) · [전체 일지](sessions/20261106-evening-resume.ko.md)

| 확인 항목 | E18 결과 |
|---|---|
| run ID·소스 | `20261106-astra-guide470-depth-001`, 공개499b3b8·시작 작업 트리 clean |
| 실제 수행 | 기존 양 hem 파지로 들기·운반·대형 회전·손 접근. **소매 쪽 가이드 재파지는 실제0회** |
| 실제 질의 | 현재 공개 depth 픽셀3회, 각 질의 물리 진행0. 운반 geometry1회·손/rim 거리2회 |
| 반복 오류 | D16,D21은 전진 설명과 달리 robot1 wrist_roll=+1 포함. 각각복구D17–19,D22–24 |
| 기록 | **470재실행 +313모델 +144제어기중립 +1감독종료 =928**, 시뮬레이션46.4초 |
| 호출·판단 |30모델호출시도,26실행행동. 질의추가3회와 응답반환후미실행호출1회를 포함하며30실행판단이아님 |
| 시간 |2026-11-06 23:58:53–2026-11-07 00:29:56 UTC,1862.366초(약31분2초) |
| 호출 경로 |모델1000.803초·환경806.244초, 내부 추론시간 미제공 |
| 종료 정합성 |SIGINT로client130·simulator0,finished/capture_complete=true,전수QC928/928통과 |
| 평가 |원점수5(픽업5·착의0),success=false,`no_dressing_points / 0.0 points/s` |
| 학습 승인 |`unreviewed`. 오류·복구 구간과 정상 진행을 구분해 보존하며 자동 학습 승인하지 않음 |

## 확인된 병목과 수정 범위

고정9채널 숫자 배열에서 gripper와 wrist_roll이 함께1로 나온 두 구간을 원본 그대로 보존했습니다. 이후 모델이 오류를 인지해 복구한 과정도 남겼습니다. 이것이 B 파지 방법 자체의 실패라는 결론은 내리지 않습니다. 실제 B 재파지는 실행되지 않았고 명령 오류가 접근 결과에 섞였습니다.

선택형 **`--named-actions`**는 각 로봇의9개 채널을 이름으로 지정한 뒤 값 변경 없이 기존 공식float32(2,9) 배열로 변환합니다. wrist_roll은 의도적으로 사용할 수 있으며 이유 문장을 추측해 행동을 고치지 않습니다. 원래 이름별 값·고정 매핑SHA·정규화 전 배열·실제 적용 배열을 보존합니다. 기본OFF이며 E18에는 사용하지 않았습니다.

- 최신 전체 **270개 CPU 검사(10.077초)**와 실제CLI 합성2턴 검사를 통과했습니다. 같은16이미지·같은관측 질의→이름기반행동→기존validator 변환을 확인했습니다.
- 모델 없는 실제GPU 연결도 query0→행동2→stop1→finish0으로 **3/3기록 검사 통과**, 실모델0회·fixture질의1회입니다.
- 실제 옷 조작에서 오류 감소·점수 향상은 아직 미검증입니다. [명명 행동 근거·검증](../collection/research/2026-11-07-named-action-candidate.ko.md)

## E19 실행 중 · 2026-11-07 00:45:20 UTC 시작

시작 소스는 공개 main `9aad60138dc5cded2e0e5219fc12395d4c37ff0a`이며 source snapshot의 작업 트리 수정 여부는 false입니다. 아래 명령으로 실제 시작했고 먼저801개 행동을 재실행합니다. 최종 점수·착의 효과는 아직 없습니다.

유용했던 손 접근을 유지해 **첫 roll 오류 직전801경계**에서 같은 B+depth 조건에 이름기반행동을 추가합니다. 옷을 다루는 전략은 유지하고 행동 표현을 비교합니다. 새 재실행 관측으로 현재 파지·손 위치를 다시 판단하며 정확한 천 checkpoint 복원을 주장하지 않습니다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261107-astra-entry801-named-001 --mode dressing \
  --strategy coordinated-support-guide --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-guide470-depth-001 --replay-prefix-steps 801 \
  --parent-attempt 20261106-astra-guide470-depth-001 \
  --retry-reason named_channels_before_repeated_roll_error \
  --replay-observe-steps 771 787 --wrist-depth-panel --pixel-depth-query --named-actions \
  --post-action-settle-steps 6 --decisions 40 --max-steps 1600 --model-timeout 180 \
  --profile-step-phases
```

목 우선 경로도 선택형 `coordinated-neckline-first`로 구현·CPU검증했지만 아직 실제미실행입니다. 현재는 E18의 유용한 접근을 이어 비교하고, 그 결과에 따라 목 우선 등 다른 순서를 선택합니다. [방법 전환 근거](../collection/research/2026-11-06-post-support-methods.ko.md) · [E19 이후 조건부 경로 선택](../collection/research/2026-11-07-post-named-route-choice.ko.md)

## 원본·기록

E18 비공개 원본은 고정HF revision `44d01871f0099f8a537f1bdbfee06a404a95f38c`에서 재다운로드 SHA검증을 완료했습니다. [E18 receipt](sessions/20261107-e18-backup-verification.json),2,167,209,525 bytes·00:36:13 UTC 확인. [named 연결시험 원본](sessions/20261107-named-depth-wiring-backup-verification.json)도 고정 revision 재다운로드검증을 완료했습니다. 실제실행 source_snapshot은499b3b8이며 이후 named코드가 들어가지 않습니다. 공개 원본의 점수·QC는 별도검수 결과로만 사용하고 actor에 넣지 않습니다.

[복원 안내](START_HERE.ko.md) · [E17 백업](sessions/20261106-e17-backup-verification.json) · [E16 백업](sessions/20261106-e16-backup-verification.json). 오류/복구/중단 구간은 동일 source group 안의 연속 기록이며 독립 성공·검증 표본으로 세지 않습니다. 원시 추론·CLI이벤트·인증·simulator로그는 공개/백업 묶음에 넣지 않습니다.

<details>
<summary>E17 마감과 E18 시작 당시 상태 이력</summary>

# 현재 상태와 다음 작업

**최신 종료 E17: 5/50(픽업5·첫 소매0), `success=false`.** 최고 기록은5/50이며 **10점은 아직 미달성**입니다. 다른 lower-rim 후보를 겨냥한 실제 재파지를 수행했지만, 반대 입구 층과 두 지지·연속 입구는 확인하지 못해 모델이 종료했습니다.

[최신 영상·피드백](../gallery/README.ko.md) · [E17 상세](../gallery/20261106-astra-layer352-001.ko.md) · [공개 관측 분석](../collection/reviews/20261106-astra-layer352-001.ko.md) · [실행 일지](sessions/20261106-evening-resume.ko.md) · [README](../../README.md)

## 실제 확인 결과

| 항목 | E17 확인값 |
|---|---|
| run ID | `20261106-astra-layer352-001` |
| 실제 방법 | A: 한쪽을 열고 다른 가시 경계에 두 번 배치 보정→닫기→짧은 동시 들기→지지 미확인으로 낮춤·종료 |
| 원점수 | **5/50 · 픽업5 · 착의 항목0 · `success=false`** |
| 점수율 | `no_contact / null`; 픽업5점만으로 양의 착의 순위 점수가 생기지 않음 |
| 기술 검사 | **452/452기록 통과**, complete·학습 승인 `unreviewed` |
| 기록·시간 | **352 재실행 +52 모델 행동 +48 제어기 중립 =452**, 시뮬레이션22.6초 |
| 모델 판단 | **12회**(행동11회+종료1회), Astra/ultra·고정 CLI0.166.0/exec |
| 실제 시간 | **23:37:50–23:51:35 UTC,824.158초**(약13분44초) |
| 경로 시간 | 모델 호출378.759초·환경 요청400.042초. 순수 내부 추론시간은 미제공 |
| 실행 소스 | 공개 main `98bb41ff6e83327a468abe5129517b4739ae33a1`, 시작 당시 작업 트리 수정 없음 |
| 직접 부모 | E16 `20261106-astra-support264-002`의352기록. source group은E07 계열 유지 |
| 입력 | 현재 RGB5장·공개 로봇 상태·depth 요약·손목 depth 패널. 첫 호출에 같은 새 replay의264·346경계 RGB10장 추가, 총16이미지 |
| 픽셀 질의 | **E16·E17에는 미사용** |
| 관찰 | Chrome·WebRTC OFF, 닫힌 기록의 GIF/MP4로 검토 |

기록1개(전이)는 관측→행동→다음 관측의0.05초이며, 실험/모델 판단 횟수가 아닙니다. 중립 명령 중에도 목표 추종 운동이 남을 수 있습니다. 기술 검사·착의 성공·학습 승인은 별도입니다. 이 점수는 로컬 공식 평가기 결과이며 Codabench 제출·공식 순위를 뜻하지 않습니다.

## 분석과 다음 비교

E16은 같은 오른쪽 가장자리 회복 뒤 국소 천 동행을 관측했지만0/50으로 종료했습니다. E17은 다른 아래 경계 후보를 겨냥해 접근 방향·위치를 바꾸는 재파지 사이클을 수행했습니다. 양측 동시 들기 후 robot0의 경계가 물러나는 듯한 관측이 있어 두 지지를 확인하지 못했습니다. **5점은 새 파지나 반대층 확보의 증명이 아닙니다.** 제한된 한 번의 시도로 A 전체가 소진됐다고 결론내리지 않습니다.

다음은 **B: 몸통 지지 + 소매 방향 가이드로 한쪽 실제 파지·역할 변경**입니다. E16의470경계에서 현재 지지를 다시 확인합니다. 보이는 표면의 거리 모호함에는 선택형 픽셀 depth 질의를 처음 과제에 제공하며, 가려진 층·입구·접촉을 알아내는 기능으로 취급하지 않습니다. 이 비교는 파지 전략과 입력 기능이 함께 달라져 단일 요인 비교가 아닙니다.

별도로 **목둘레부터 입히는 순서**를 선택형 전략 `coordinated-neckline-first`로 통합했습니다. 공개 평가 설명에는 첫 소매의 필수 선행 조건이 없습니다. 실제 머리 통과·몸통 내부 관계를 목표로 하며 목선 접촉이나 앞면 방향만으로 성공을 주장하지 않습니다. 아직 실행하지 않았습니다.

[방법 전환 기준](sessions/20261106-method-switch-matrix.ko.md) · [기존 들기와 새 역할/목 우선 후보 구분](../collection/research/2026-11-06-post-support-methods.ko.md) · [E16 대기 시간 분석](../collection/research/2026-11-06-e16-neutral-call-timing.ko.md)

## E18 B 실행 중 ·23:58:53 UTC 시작

아래 명령을 E17 갤러리·후보 통합 main `499b3b8cb29568e6d5530d7ce8bf039c73cd8f6a`의 깨끗한 작업 트리에서23:58:53 UTC에 시작했습니다. 종료 결과는 아직 없습니다. GPU 작업은 순차 실행합니다. 원본 재실행은 정확한 천 checkpoint 복원이 아니며 과거 사진은 현재 지지 증거를 대신하지 않습니다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261106-astra-guide470-depth-001 --mode dressing \
  --strategy coordinated-support-guide --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-support264-002 --replay-prefix-steps 470 \
  --parent-attempt 20261106-astra-support264-002 \
  --retry-reason support_and_sleeve_guide_with_public_pixel_depth \
  --replay-observe-steps 430 464 --wrist-depth-panel --pixel-depth-query \
  --post-action-settle-steps 6 --decisions 35 --max-steps 1400 --model-timeout 180 \
  --profile-step-phases
```

## 구현·검증·보존

- 기본 환경 복원·prepare·smoke·실제 Astra wiring을 완료했습니다. E09의 종료 응답 순서 오류는 이미 수정됐습니다.
- 최신 통합본 전체 CPU **257개 통과(7.529초)**. 목 우선 후보와 기존8전략 불변·depth OFF/ON 경로를 포함합니다. 이를 E16/E17 실행 당시 소스의 검사 수로 소급하지 않습니다.
- 픽셀 질의는 CPU·합성 실제 CLI2턴·모델 없는 실제 GPU3기록 전수검사까지 완료했습니다. fixture 질의1회·실모델 호출0·질의 물리 진행0이며 실제 착의 효과는 아직 미검증입니다. [검증 범위](../collection/research/2026-11-06-pixel-depth-query-candidate.ko.md)
- E16 원본은 고정 HF revision `1ad0f8ba3cc71ab80962907c713357fbd4005e3f`의 재다운로드 SHA 검증 완료입니다. [E16 receipt](sessions/20261106-e16-backup-verification.json)
- E17 원본은 고정 revision `d5ba6c645232c7674d3861fdf65da3a26e9e1ea9`에서 재다운로드 SHA 검증을 완료했습니다. [E17 receipt](sessions/20261106-e17-backup-verification.json),1,027,542,010 bytes,23:55:15 UTC 확인.
- 실제 모델 기본 wiring과 모델 없는 query wiring도 각각 [기본 receipt](sessions/20261106-evening-wiring-backup-verification.json), [query receipt](sessions/20261106-depth-query-wiring-backup-verification.json)로 원격 검증했습니다.

비공개 HF dataset은 `leonayoon/phyrc-2027-phase1-private-backup`입니다. audit·평가·배치 metadata는 검수 전용이며 actor 입력에 연결하지 않습니다. 공개 GitHub에는 코드·문서·선별 공개 관측만 게시하고 인증·원시 추론·CLI 이벤트·simulator 로그는 게시하지 않습니다.

[클린 서버 복원](START_HERE.ko.md) · [초기 자산·E07 복원 검증](sessions/20261106-evening-restore-validation.json) · [E16 분석](../collection/reviews/20261106-astra-support264-002.ko.md) · [E15 마감 이력](SESSION_WRAPUP_20261106.ko.md) · [전체 개발 이력](HISTORY.ko.md)

새 정책 학습·RL/VLA 성능 검증·학습 승인은 완료하지 않았습니다. 이전 문서의 일시 중지·미실행 문구는 당시 이력이며 현재 실행 상태는 이 문서와 최신 일지를 우선합니다.

</details>

</details>

</details>

</details>

</details>

</details>

</details>

</details>

</details>
