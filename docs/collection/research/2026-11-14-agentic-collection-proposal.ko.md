# 에이전틱 데이터 수집: 추가 연구와 적용 제안

[현재 수집 계획](../../COLLECTION_PLAN.md) · [Astra 경로](../../ASTRA.md) · [선행 워크숍 조사](2026-11-14-agentic-robotics-workshop.ko.md) · [현재 상태](../../project/STATUS.md)

조사 기준일: **2026-11-14**. 최초 코드 검토 기준: `112cc5145dda4203ddce478473ddd70e7f17b3bb`. 최초 요청은 최신 파지·하강 시연1회와 새로운 연구의 수집 시스템 적용 분석이었다. 이후 추가 수집 요청으로 우선3회를 검토했으나, 최신 사용자 지시는 **E34까지만 마감하고 수집 중지·E35 취소**다. 전체 경험을 통합한 최신 제안은 [수집 시스템 재정비 계획](2026-11-14-collection-system-redesign.ko.md)이다. 아래 E33 마감 분석과 당시 E34 준비 근거는 이력으로 보존한다. **이 문서는 연구 제안이며 아래 연구 기능을 구현하거나 효과를 검증한 기록이 아니다.** 실제 실행 결과는 [수집 계획](../../COLLECTION_PLAN.md), 세션 기록, STATUS가 정본이다.

**우선 제안은 실패를 구간별로 검토하는 수집 인덱스와 검증된 실패 기억이다.** 현재는 착의 성공 데이터를 대량 생산하기보다 “어떤 파지에서 어떤 접근 공간이 생겼고, 어느 동작이 그 관계를 깨뜨렸는가”를 구분하는 편이 먼저다. 단일 actor와 기존 공개 관측 계약을 유지하면서도 마감 이후 분석을 상당 부분 자동화할 수 있다. 새로운 VLA·world model·다중 제어원 도입은 이번 기존 방식의 수집 배치에 통합하지 않는다.

검토 시작 시 마지막 정상 시연 E31은 로컬 공식 평가기 **5/50, 착의 0, success=false**였다. E32는 capture incomplete이며 정상 replay·학습 출처로 쓸 수 없다. 같은 E28 계보의 분기를 독립 성공 표본으로 세지 않는다. 위 사실은 새 시연 결과가 아니라 기존 [STATUS](../../project/STATUS.md)와 원본 기록의 요약이다.

## E33 마감에서 추가된 근거와 우선순위

E33은 **로컬0/50·pickup0·착의0·success=false**, capture complete=true, **QC471/471 통과**로 마감했다.20개 새 행동 결정·21모델 호출, 총1,351.411초(약22.52분)를 사용했다. 기록471전이는264 replay +128 model +78 settle +1 budget cleanup이다. 파지 위치 변경과 준비 형상은 시험했지만 운반·마네킹 손 위 정렬·짧은 하강에는 도달하지 않았다. 따라서 하강 제안의 효과나 실패를 평가한 결과가 아니다. 기술 QC와 학습 승인도 별개이며 승인은 `unreviewed`다. [E33 리뷰](../reviews/20261114-astra-middle-grip264-001.ko.md), [원본 근거를 연결한 공개 manifest](../attempts/20261114-astra-middle-grip264-001/manifest.json)

마지막 D19는 robot_1 닫기로 끝났고 그 뒤의 짧은 들어 보기·천 동행 시험이 남았다. 이에 후속 E34를 E33/470에서 현재 파지를 유지하며 이 미완료 시험부터 관측하는 방향으로 준비했다. `coordinated-middle-grip-drape-retain`은 재파지를 허용하지 않는 **actor 프롬프트 조건**이며, 자동 행동 차단기나 누적 재파지 상태기계를 구현한 것은 아니다. E34 결과는 [최신 재정비 계획](2026-11-14-collection-system-redesign.ko.md)과 별도 리뷰에 반영하고 E35는 실행하지 않는다. [E33 후속 검토](../reviews/20261114-astra-middle-grip264-001.ko.md#추가20결정에-대한-의견과-e34-후보), [E34 원본 검증 계획](../retry-plans/20261114-e34-e33-470-retain.json)

**새로운 구체적 병목은 run 사이에 누적 준비 횟수가 이어지지 않는 점이다.** E33의 공개 행동 기록에서는 robot_0과 robot_1이 각각 초기 재파지 사이클을 한 번 사용했다. 그런데 action-prefix replay 뒤에는 fresh actor가 시작하고, 두 장의 새 replay history는 과거의 누적 open→배치→close 횟수를 기계적으로 보존하지 않는다. 새 run 이름이 기존 재파지 예산을 다시 부여하는 근거가 되어서는 안 된다. 이는 E34에서 이미 반복 위반이 관측됐다는 주장이 아니라, E33 리뷰와 현재 continuation 경로에서 확인한 **다음 실행의 상태 전달 한계**다. [`continuation.py`](../../../participant/collection/continuation.py), [`codex_client.py`](../../../participant/collection/codex_client.py)

이에 따라 향후 P0 후보에 **공개 행동 이력에서 검증한 제한 상태와 실행 전 검사**를 추가한다. 단순히 지난 리뷰를 actor에게 붙이는 방식은 제안하지 않는다.

- 출처는 정상 마감·해시 검증된 parent의 공개 관측과 실제 적용 행동으로 한정한다. `source_group`, 직접 parent, prefix 경계, 원본·공개 trace hash, 로봇별 사이클 경계, 사용/잔여 횟수, 미확인 여부를 별도 파생 manifest에 기록한다. audit·점수·숨은 접촉 정답·원시 reasoning은 이 입력에 넣지 않는다.
- 중첩 replay prefix를 새 시도로 중복 계산하지 않으며 run 이름 변경으로 누적 횟수를 초기화하지 않는다. 최초 획득과 재파지, 같은 close 명령 반복과 새로운 사이클을 구분하는 정의가 필요하다. 숫자 action만으로 천 부착이나 과제 단계가 증명되지는 않으므로, 분류 근거가 부족하면 `unknown`으로 남기고 잔여 횟수를 임의로0회 사용 상태로 만들지 않는다.
- 미래 actor에는 허용된 행동 이력으로부터 만든 최소 상태만 새 계약으로 전달하고, 현재 지지·공간은 새 replay 관측에서 재확인하게 한다. 별도 실행 전 검사는 예산을 넘는 release 요청을 실행하기 전에 거부하고 기록하도록 설계한다. 정책의 모호한 단계 이름만으로 예산을 다시 허용하지 않는다. “재파지0회” 조건은 그리퍼 open 요청의 기계적 제한부터 검토할 수 있지만, 천이 실제로 잡혔는지 판정하는 센서 기능과는 다르다.
- 채택 전에는 같은 정상 prefix에서 **프롬프트만 / 검증된 제한 상태 / 상태+실행 전 검사**를 비교한다. 사이클 재개 오류, 허용된 행동의 잘못된 차단, 상태 출처·hash 오류, 새로운 진척과 호출 비용을 측정한다. 이 연구 기능은 이번 수집 배치에 아직 통합하지 않았고 효능도 검증하지 않았다.

## 기존 워크숍 조사에서 추가되는 내용

선행 문서는 초기 파지, 관측 근거, 복구, 검증된 기억의 필요성을 설명했다. 이번에는 그 원칙을 **구간 선별·수집 대상 선택·데이터 혼합·기억 갱신·교정 쌍**의 구체적인 설계로 옮긴다. 아래 6편은 별도의 arXiv 원문 또는 학회·저자 공식 자료에서 확인했다. 워크숍 39편을 다시 전수 조사한 결과는 아니다.

| 우선순위 | 새로 검토할 변화 | 지금 적용 가능한 범위 | 이후 조건 |
|---|---|---|---|
| P0 | HELP식 구간 인덱스 | 정상 마감 시연을 공개 관측으로 progress/idle/failure/recovery/unknown 분류하는 별도 리뷰 | 검수자 일치도 확인 뒤 학습 sampler 연결 |
| P0 | ACE식 실패 기억 | 근거 프레임·적용 조건·반례를 가진 개발자용 기록을 증분 갱신 | 재실행으로 확인된 항목만 다음 전략 개정의 근거로 사용 |
| P0 | MAST식 완료 검증 | 종료 명령, 마감 응답, 파일 complete, 전수 QC를 서로 다른 사건으로 기록 | 기존 중단/EOF 경로의 독립적인 검증 |
| P1 | RECALL식 선택 수집 | 다음 시연의 병목 상태를 고르는 검토 우선순위 | 공개 관측 기반 위험 신호의 보정, 다양한 정상 데이터와 혼합 |
| P1 | RoboClaw식 복구 정책 구조 | 재시도/준비 복구/종료 사유를 명시하는 리뷰 | 실제 재현 가능한 복구 행동과 전제조건 확보 |
| P2 | PHIL식 선제 교정 쌍 | 향후 필요한 데이터 필드 설계 | 관측을 고정한 승인·교정 절차, 단일 제어권 이전, 학습 목적 구현 |

## 1. HELP: 성공 여부만으로 데이터 전체를 고르지 않기

**확인한 연구:** HELP는 2026-07-08 최초 공개, 07-15 v2다. 두 역할의 운영자가 12대 로봇을 감독하고, VLAC-CUT이 rollout을 progress-making, idle, failure-inducing, recovery 구간으로 나눈다. 유용한 구간과 인간 교정을 다음 학습에 섞는다. 연구의 네 실물 조작 과제에서 성공률 80–95%, 기반 모델 대비 처리량 1.7–4.2배를 보고한다. **PhyRC 예상 개선치가 아니다.** [논문·실험](https://arxiv.org/abs/2607.09776v2)

**적용 제안:** E28–E31에서 이미 저장한 `applied_segment`, `controller_settle`, 공개 RGB-D를 연결해 별도 `segment-review`를 만든다. 우선 사람 검수로 기준 자료를 만들고, 자동 리뷰어의 판정은 제안으로만 취급한다. `unknown`은 본 제안에서 추가한 범주다. 손과 천이 가려지거나 여러 원인이 섞이면 억지로 progress/failure를 정하지 않는다.

**학습 연결 시 중요한 제한:** HELP도 flow-matching에서 실패 유발 행동을 직접 negative loss로 쓰는 신뢰할 만한 방법을 확보하지 못했다고 설명한다. 따라서 현재 π0.5에 실패 행동까지 일괄 behavior cloning하는 방식을 피한다. 실패 기록은 보존하고, 검수된 progress/recovery 구간만 향후 positive 학습 후보로 삼는다. [방법 §3.3](https://arxiv.org/html/2607.09776v2)

**코드 대응:** [`codex_client.py`](../../../participant/collection/codex_client.py)의 `applied_segment`가 시작/끝 전이, 실제 행동, actor의 의도와 공개 판단을 이미 기록한다. [`export_report.py`](../../../participant/collection/export_report.py)의 `public_events()`를 입력으로 별도 리뷰 파일을 만들 수 있다. 현재 actor의 `stage`/`visual_assessment`는 검수 라벨이 아니다. [`pi05/data.py`](../../../participant/pi05/data.py)의 `Episodes`는 현재 episode 전체의 행을 표본화하고 `approved_pipeline_test`를 요구하므로, 의미 구간 sampler가 이미 있다는 설명은 틀리다.

미래 sampler는 action horizon이 제외 구간·다른 episode·reset을 가로지르지 않도록 해야 한다. 구간 끝에서 다음 실패 행동을 붙이거나 마지막 행동을 임의 반복하면 새로운 학습 의미가 생긴다. 기본적으로 horizon 전체가 승인 구간에 있는 창만 사용하고, 짧은 구간은 별도 mask 학습을 구현하기 전 제외하는 안을 권한다.

## 2. RECALL: 실패 뒤 처음부터 다시 수집하는 비용 줄이기

**확인한 연구:** 2026-06-22 공개된 RECALL은 불확실성이 높은 중간 상태에서 recovery demonstration을 수집하는 active continual learning을 연구한다. 능동 수집의 이점과 함께 새 recovery 데이터만 학습하면 기존 행동이 망각되는 문제를 보고하고, 넓은 replay 범위의 중요성을 확인한다. 실험은 **LIBERO-10의 autoregressive VLA**이며 실제 변형체 착의나 π0.5 LoRA 결과가 아니다. [논문](https://arxiv.org/abs/2606.23617v1)

**적용 제안:** 파지 유지·공간 붕괴·손 오식별·접촉 후 정체를 분리하고, 다음 시행의 시작점을 “가장 최근 경계” 대신 “현재 가설을 시험할 여유가 있는 검증 경계”로 고른다. 더 가운데 파지가 목적이면 이미 파지가 끝난 E28/632를 자동 선택하지 않는다. 기존 [`retry_plan.build_plan()`](../../../participant/collection/retry_plan.py)의 정상 원본 검증을 유지하고 선택 근거를 새 리뷰에 남긴다.

**제한:** 논문의 INSIGHT는 action-token 확률 특징을 쓴다. 현재 Astra의 `visual_assessment=uncertain`는 보정된 실패 확률이 아니며 π0.5 flow head에 token entropy를 바로 옮길 수도 없다. 우선 공개 시계열의 진척 정체·지지 상실 등 관측 신호와 사람 라벨을 비교하고 false positive/negative를 측정한다. 새 recovery 데이터만 학습하는 안보다 기존 검수 데이터와의 혼합을 대조해야 한다. 단, 현재의 파이프라인 시험 데이터만으로 폭넓은 replay 기반이 확보됐다고 보지 않는다. [방법·한계 §3, §11](https://arxiv.org/html/2606.23617v1)

PhyRC의 prefix replay는 새 물리 실행이다. RECALL의 중간 simulator reset과 같은 정확한 상태 복원이 아니므로, 다른 분기에서 만든 행동 둘을 “동일 상태 교정 쌍”이라고 부르지 않는다.

## 3. ACE: 실패를 요약문으로 계속 덮어쓰지 않기

**확인한 연구:** ACE는 2025-10-06 최초 공개, 2026-03-29 v3이며 ICLR 2026 논문이다. generator/reflector/curator를 나누고 실행 경험을 구조화한 playbook에 증분 반영한다. 텍스트를 반복해서 전면 재작성하며 정보가 사라지는 문제를 다룬다. agent·도메인 추론 벤치마크 연구이며 로봇 성공률 증거가 아니다. [논문](https://arxiv.org/abs/2510.04618v3)

**적용 제안:** 개발자용 기억 항목을 `관측 사실 → 원인 후보 → 변경 → 관측 결과 → 적용 조건/반례`로 저장한다. 예를 들어 “손 진입이 안 됨”을 “E31의 특정 프레임에서 같은 손과 중앙 자유 구간의 관계가 확인되지 않음; 파지를 바꾼 경우에는 아직 미검증”처럼 범위를 좁힌다. 같은 파지를 유지한 미세 접근 실패를 새 파지 제안의 반례로 잘못 합치지 않는다.

새 항목은 `proposed`에서 시작하고 재실행과 시각 검수 근거가 쌓이면 `supported`로 옮긴다. 잘못된 항목은 삭제 대신 `superseded`와 반례를 연결해 추적한다. 모든 상태명·필드는 **새 설계 제안**이다. 기억 항목에는 run/source group/코드·프롬프트 hash/관측 프레임/적용 조건이 필요하다.

**경계:** reflector가 잘못된 설명을 뽑으면 기억이 해로워질 수 있다는 원논문의 한계가 있다. 검수되지 않은 추론·평가 점수·숨은 기하를 actor 기억으로 주입하지 않는다. 우선 저장소의 리뷰 자료로 운용하며, 다음 고정 전략을 개정할 때 공개 관측으로 설명 가능한 일반 절차만 별도 검토한다. 기존 미적용 피드백 큐 활성화와는 별개다. [방법·한계](https://arxiv.org/html/2510.04618v3)

## 4. RoboClaw: 복구의 종류와 전제조건을 기록하기

**확인한 연구:** RoboClaw는 2026-03-12 최초 공개, 04-01 v3다. VLM 감독자가 수집·학습·실행을 연결하고, forward/inverse action pair로 재설정 가능한 수집 순환을 만든다. 실행 상태가 유지되는 실패와 상태를 악화시킨 실패를 구분해 retry와 recovery를 달리한다. 클라우드 지연과 실제로 가능한 inverse reset 가정이 한계다. [논문](https://arxiv.org/abs/2603.11558v3), [방법·한계](https://arxiv.org/html/2603.11558v3)

**적용 제안:** 이번 파지 변경에서는 실패 후 선택을 세 가지로 나누어 리뷰한다. (1) 지지·형상이 유지되면 작은 정렬 수정, (2) 천의 형상이 접히거나 지지가 바뀌면 준비 조건 복구, (3) 복구할 근거가 없으면 정상 마감 후 다음 출발점 선택이다. 같은 접촉 시도를 계속하는 비율과 준비 조건을 회복한 비율을 따로 측정한다.

**즉시 가져오지 않을 부분:** 천의 접힘·마찰·접촉은 단순 역행동으로 원상복구되지 않는다. inverse skill을 기존 속도 명령의 부호 반전으로 구현하거나, 공식 상태를 직접 조작하는 reset 도구를 actor에 주면 안 된다. 기존 한 제어원·20결정·짧은 행동 한도를 유지하고, 새 복구 skill은 실제 공개 관측과 재현 결과를 얻은 뒤 검토한다.

## 5. PHIL: 실행 전 예측과 실제 교정을 같은 상태에 연결하기

**확인한 연구:** 2026-11-03 공개된 PHIL은 XR로 미래 end-effector 경로를 보여 주고 사람이 선제 교정한다. 같은 query state·같은 horizon의 거절된 정책 예측과 실제 교정 action chunk를 선호쌍으로 남긴다. 조건당 교정 5개 episode에서 HG-DAgger 대비 평균 성공률이 Diffusion Policy 44.0→70.3%, X-VLA 57.8→76.9%로 보고됐다. DP는 4과제, X-VLA는 3과제이며 각자 시연 예산을 평균한 값이다. **π0.5·PhyRC 결과나 교정 5번만으로 같은 개선을 보장하는 근거가 아니다.** [논문](https://arxiv.org/abs/2611.05667v1), [저자 공식 실험 설명](https://intuitive-robots.github.io/PHIL-page/)

**적용 제안:** 향후 단일 제어권 아래 실행 전 검토를 만들 때 `observation_id`, RGB-D hash, public time, proposed action/steps, actual corrected action chunk, intervention reason, controller source를 남긴다. 교정 전에 물리가 진행했거나 action horizon이 다르면 선호쌍으로 승격하지 않는다. 거절한 행동을 실제 executed action으로 HDF5에 기록하지 않는다.

**현재는 P2:** 사람–Astra 실시간 handoff, 3D 경로 preview, paired preference trainer가 없다. 현재 named `(2,9)` 속도 명령만으로 PHIL의 XR 미래 궤적이 구현되지 않는다. `freeze_public_frame()`의 관측 식별·hash 패턴은 참고할 수 있지만 pixel query는 교정 기능이 아니다. 첫 단계는 명세이며, 이번 시연에 동시 human/AI 제어원을 붙이지 않는다.

선제 수집만으로 BC 성능이 항상 좋아진 것은 아니라는 저자 결과도 중요하다. preference 학습을 붙인 효과와 새로운 수집 방식의 효과를 별도 실험해야 한다. 현재 [`pi05/train.py`](../../../participant/pi05/train.py)는 이 목적을 구현하지 않는다.

## 6. MAST: 에이전트 수보다 인계·검증 계약 먼저

**확인한 연구:** *Why Do Multi-Agent LLM Systems Fail?*은 2025-03-17 최초 공개, 10-26 v3, NeurIPS 2025 Datasets and Benchmarks 논문이다. 7개 프레임워크에서 1,600개 이상의 trace를 수집하고 system design/inter-agent alignment/task verification 범주의 14개 실패 유형을 제시한다. 로봇 벤치마크는 아니다. [논문](https://arxiv.org/abs/2503.13657v3), [학회 출판본](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html)

**적용 제안:** 수집 actor, 공개 관측 reviewer, 원본/QC verifier, 다음 실험 planner의 역할을 분리하되 환경을 움직이는 주체는 하나로 둔다. 나머지는 마감된 결과를 비동기로 읽는다. 리뷰어가 “끝났다”고 쓰는 일, client가 종료된 일, HDF5가 정상 마감된 일, 학습 승인된 일은 별도 상태다.

E32와 같은 기록 실패는 로봇 정책 실패와 별도 분류한다. `finish_episode` 요청 → simulator 응답 → writer 종료 → manifest/hash 생성 → `validate_capture` 통과를 각각 확인한다. EOF/timeout을 성공으로 바꾸거나 기존 incomplete 파일의 표식을 고치지 않는다. 이 검증 단계는 논문을 그대로 구현한 것이 아니라 MAST의 검증 실패 문제를 현재 수집기의 사건 계약에 맞춘 설계다.

## 권장 구조와 코드 경계

```text
고정 전략 + 현재 공개 RGB-D/로봇 상태
                 ↓
       격리된 Astra actor 한 개
                 ↓
      기존 action 검증 → simulator
                 ↓
       원본 capture 정상 마감
                 ↓
         전수 QC + 비공개 보존
                 ↓
 공개 관측 구간 리뷰 ── 별도 점수/시간 분석
                 ↓
 개발자용 실패 기억 + 다음 수집 후보
                 ↓
   검토된 새 전략/출발점으로 다음 run
```

구간 리뷰가 `unknown`이면 품질이나 성과를 임의로 올리지 않는다. evaluator·audit은 별도 분석에만 사용하고 actor·critic·world model·증류 교사의 입력으로 연결하지 않는다. single L40S에서는 수집/렌더/학습을 순차 운영하고, 처음부터 다수 VLM을 동시에 올릴 이유가 없다.

| 현재 접점 | 현재 확보된 기능 | 제안하는 추가 작업 |
|---|---|---|
| [`codex_client.py`](../../../participant/collection/codex_client.py) | 결정, 실제 적용 구간, 입력 hash, 호출 비용, 정착 기록 | 원본을 바꾸지 않는 구간 리뷰용 연결 인덱스 |
| [`export_report.py`](../../../participant/collection/export_report.py) | 공개 허용 목록에 따른 이벤트·영상 내보내기 | 새 리뷰를 별도 산출물로 작성; 자유 텍스트·비공개 필드 검증 유지 |
| [`validate_capture.py`](../../../participant/collection/validate_capture.py), [`training_dataset.py`](../../../src/PhyRC_Sim/Policy/training_dataset.py) | incomplete 거부, 해시·전이·관측 검사, `training_approval=unreviewed` | 마감 상태의 독립 검증·실패 분류. QC gate 완화 금지 |
| [`retry_plan.py`](../../../participant/collection/retry_plan.py) | 정상 source 검증, 명시적 prefix와 계보 | 수집 후보마다 가설·관측 근거·필요한 준비 여유 기록 |
| [`pi05/data.py`](../../../participant/pi05/data.py) | source-group split, 해시, 명시적 review, episode 내 action 창 | 검수된 구간만 표본화하고 horizon 경계를 지키는 sampler |
| [`pi05/train.py`](../../../participant/pi05/train.py) | upstream openpi LoRA 훈련 연결 | 혼합 비율·데이터 버전·학습 seed를 고정한 후속 ablation. 선호 loss는 별도 구현 |

구간 리뷰의 최소 필드는 `run_id`, `source_group`, `source_commit`, `policy_sha256`, `start_step`, `end_step_exclusive`, `action_source`, `camera/frame references`, `observed_facts`, `hypothesis`, `segment_label`, `reviewer`, `confidence`, `review_status`다. 평가 점수는 별도 결과 테이블로 연결한다. `confidence`는 리뷰어의 주관값이며 보정된 실패 확률로 사용하지 않는다. 새 파일은 `output/reviews/` 또는 `docs/collection/reviews/`에 두고 collection 원본에 추가하지 않는다.

## 현재 수집 배치와 연구 기능 비교를 분리하기

최초 E33은 최신 제안의 **더 가운데 파지 → 공간 형상 → 같은 손 위 정렬 → 짧은 하강 → 걸침 관계 재확인**을 시험하려 했으나 준비 단계에서 마감했다. 후속 E34도 기존 수집 경로와 제한을 유지했다. 최신 지시에 따라 E34의 마감·QC·보존·분석 뒤 수집을 중지한다. 현재 파지를 유지하는 프롬프트 조건과 새 상태기계·학습 기능 도입은 구분한다. E32는 계속 정상 출처에서 제외한다.

각 마감 리뷰에서는 결정별로 기대한 변화, 실제 공개 관측 변화, 반복 여부, 다음 선택의 근거를 남긴다. 득점이 없어도 파지와 공간 형상 변화의 관측 근거는 자료가 되지만 “성공 시연”으로 올리지 않는다. 정상 마감·QC·백업 이후 남아 있는 구별 가능한 시험과 현재 지지 근거를 보고 후속 경계의 활용을 판단한다. E33/470 후속은 착의 성과 향상 때문이 아니라 마지막 닫기의 동행 시험이 남았다는 근거로 검토한다.

후속 연구는 다음 대조군으로 나눈다. 아래는 **미실행 실험안**이며 성능 목표를 달성했다는 기록이 아니다.

| 비교 | 고정할 조건 | 주 지표 | 채택 판단 |
|---|---|---|---|
| 기존 기록 vs 구간 리뷰+실패 카드 | 동일한 완료 시연·공개 입력 | 사람 검수 시간, 구간 label 일치도, false-progress/false-success 비율 | 근거 없는 성공 판정을 늘리지 않으면서 검토 비용을 줄이는가 |
| 고정 출발점 vs 병목 기반 출발점 선택 | 모델/입력/action 계약/새 결정20개 | 새로운 관측 관계의 진척, 착의 새 득점, 반복 결정 비율 | 재실행 편차를 보고한 뒤 수집 가치가 높아지는가 |
| 기억 없음 vs 근거 있는 기억으로 개정한 전략 | 같은 연구 가설·예산·독립 초기 조건 묶음 | 반복 실패율, 잘못된 복구 선택, 착의 성과, 호출/token/wall time | 비용을 포함해 개선하며 미확인 기억의 악영향이 없는가 |
| 검수된 전체 정상 자료 vs progress/recovery 구간 자료 | 초기 checkpoint/학습 steps/seed/원본 group split | held-out 성공률, 회복 행동 남용, 기존 픽업·운반 능력 보존 | 처리량·성공·망각을 함께 개선하는가 |
| 새 recovery만 vs 기존+recovery 혼합 | 총 학습 step과 신규 데이터 예산 | 신규 상황 적응과 기존 상황 성능의 차이 | 수집 효율 개선이 망각으로 상쇄되지 않는가 |
| 나중의 reactive BC vs proactive BC vs proactive preference | 동일 교정 예산·관측·초기 정책 | 교정 시간, 불필요 복구, full-task success | 수집 방식과 loss 변화의 효과를 분리할 수 있는가 |

단일 시연에서는 통계적 우월성을 주장하지 않는다. 후속 평가 단위는 프레임이 아니라 **독립 episode/source group**이다. 성공률에는 시도 수와 구간 추정치를 함께 보고하고, 같은 E28 분기끼리만 비교한 결과는 해당 계보 안의 사례 연구로 한정한다. 점수·시각적 진척·QC·학습 승인·전체 성공은 별도 열로 유지한다. 새 득점이 0인 경우 득점당 효율을 임의로 계산하지 않는다.

## 검증 범위

6편의 arXiv 초록·본문 또는 학회/저자 공식 자료와 수집/학습 코드의 접점을 확인했다. 연구 기능의 모델 실행·논문 재현·GPU 훈련·PhyRC 성능 비교는 수행하지 않았다. 이후 기존 방식으로 실행한 E33의 공개 리뷰·manifest와 누적 상태 전달 한계를 추가 확인했으며, 이를 연구 기능의 효능 검증으로 세지 않는다. Hugging Face 논문 검색 connector는 호출 시 `Tool paper_search not found`를 반환하여 1차 원문 웹 열람을 사용했다. 기존 워크숍 문서의 본문 미확인 논문을 제목만으로 보완하거나 이번 검토의 근거로 사용하지 않았다.
