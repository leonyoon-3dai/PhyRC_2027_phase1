# Agentic Robotics 워크숍: PhyRC 시연 수집 참고

[메인](../../../README.md) · [현재 수집 계획](../../COLLECTION_PLAN.md) · [Astra 코드](../../ASTRA.md) · [클린 서버](../../OPERATIONS.md)

**조사일: 2026-11-14. 개발용 Codex CLI가 저장소만 읽어도 조사 결과와 적용 한계를 이해하도록 남긴 연구 기록이다.** 워크숍의 연구 결과와 이 저장소에 대한 적용 제안을 구분한다. 이번 변경은 문서뿐이며, 새 전략·프롬프트·메모리·도구를 구현하거나 시연을 실행한 기록이 아니다.

현재 실행 상태는 [STATUS](../../project/STATUS.md), 실행 조건과 최신 사용자 제안은 [COLLECTION_PLAN](../../COLLECTION_PLAN.md)이 정본이다. 조사 당시 수집은 중지 상태이고 E33은 미실행이다. 마지막 정상 마감 E31은 로컬 공식 평가기 **5/50, 착의 0, success=false**이며, E32는 **complete=false·전체 QC 실패**로 진단 전용이다. 이 문서를 새 실행 승인으로 해석하지 않는다.

## 먼저 읽을 결론

가장 직접적인 출처는 **실제 Stretch 4를 Codex CLI의 Astra로 제어한 Georgia Tech의 수상 데모**다. 특히 잘못된 초기 파지가 이후 조작을 막는데도 접근 동작만 반복하는 현상은, 다음 시연에서 파지 위치 자체를 바꾸려는 사용자 제안과 연결된다. 다만 이 연결은 PhyRC 적용 가설이며 착의 성공을 입증한 결과가 아니다.

| 우선순위 | 가져올 생각 | PhyRC에서 검토할 일 |
|---|---|---|
| 1 | 초기 파지와 후속 동작의 의존성 | 더 가운데 파지한 뒤 공간이 실제로 열리는지 먼저 확인. 손 접근만 계속 바꾸지 않기 |
| 1 | 짧은 행동과 관측에 의한 검증 | 같은 마네킹 손 위에서 조금 낮춘 뒤 천·손·지지점 관계 재확인 |
| 1 | 관측 근거가 붙은 실패 기록 | 파지·빈 공간·손 접근·접촉 전후를 같은 시점의 다중 카메라로 묶고 미확인을 남기기 |
| 2 | 검증된 경험만 기억으로 승격 | 결과가 다른 시행을 구분하고, 실패 원인과 재시도 조건을 개발자 리뷰에 기록 |
| 2 | 비용과 진척을 함께 비교 | 추가 결정·모델 호출·token·wall time·sim time과 실제 진행을 나란히 기록 |
| 3 | 검증된 해법에서 데이터 확장 | 첫 손목 관계부터 재현 가능한 근거를 확보한 뒤 VLA/증류·변형 시연 검토 |

이 순위는 현재 프로젝트의 병목에 대한 판단이다. 논문 전체의 성능 순위가 아니다. 새 월드모델이나 플랫폼 교체를 다음 시연의 선행 조건으로 삼지 않는다.

**읽기 순서:** [직접 관련 데모](#direct-demo) → [연구에서 가져올 방법](#methods) → [다음 시연 적용안](#next-trial) → [코드 대응](#code-map) → [39편 조사 목록](#paper-inventory) → [클린 서버 인계](#codex-handoff).

## 1. 조사 범위와 근거 수준

- 출발점: [워크숍 공식 사이트](https://agentic-robotics-workshop.github.io/), [채택 논문 목록](https://agentic-robotics-workshop.github.io/papers), [데모 플랫폼 상세](https://agentic-robotics-workshop.github.io/demo?from=demo-track).
- CoRL 2026 연계 행사이며 사이트에 행사일 **2026-11-12, Austin**으로 기재돼 있다. 채택 논문은 **39편**이고 별도 채택 데모는 그 수에 포함하지 않는다.
- 39편 모두 제목·원문 연결을 조사하고, 접근 가능한 저자 프로젝트·arXiv·공식 저장소로 방법과 조건을 확인했다. 아래 목록은 **프로젝트/초록 확인, PDF 확인, 관련 버전, 목록만 확인**을 구분한다. 모든 논문 PDF와 동영상을 완독·시청했다는 뜻이 아니다.
- 공식 사이트의 두 Best Paper는 **Agentic World Action Models**, **EmbodiedSWE**이고 두 Best Demo는 **Astra Beyond Tabletop**, **ATLAS**다. 수상 여부와 PhyRC 적합성은 별개다.
- [행사 녹화](https://www.youtube.com/watch?v=SuZwqlS-weA)는 링크를 확인했지만 접근 제한으로 내용·자막을 검증하지 못했다. 따라서 특정 연사가 어떤 주장을 했는지나 현장 시연의 실제 성공을 이 문서에서 단정하지 않는다.

사이트의 문제 제기는 agent–policy 역할 분담, 실제 환경에서의 개선, 적절한 수준의 피드백, 시뮬레이션 데이터 확장, 기술 조합, 복구까지 포함한 평가에 걸쳐 있다. PhyRC에서는 이를 **행동 생성과 검수의 분리, 관측 가능한 단계 조건, 실패 후 다른 출발점 선택, 검증된 시연만 학습 후보로 사용**하는 문제로 읽는다. 이는 본 문서의 해석이다.

메인 일정은 `Tentative`로 표시되어 있으며 Ran Zhang, Guanya Shi, Ken Goldberg, Philipp Wu, Wentao Yuan, Jonathan Tremblay, Tianyu Li 등의 발표 순서가 올라 있다. 일정·소개만으로 발표 내용을 재구성하지 않았다. 데모 물류에 관해서도 메인과 상세 페이지의 일부 설명이 달라, 현장 compute 제공·시뮬레이션 참여 조건을 현재 확정 안내로 옮기지 않는다. 원문 링크를 기준으로 재확인한다.

<a id="direct-demo"></a>
## 2. 가장 직접적인 사례: Astra Beyond Tabletop

출처: [Georgia Tech RAIL 공식 글·방법·실험·부록](https://www.gt-rail.com/blog/astra-beyond-tabletop/).

실제 **Stretch 4 한 대**, **Codex CLI의 gpt-6-astra**로 가정 내 조작을 평가한다. 관측, 명령 생성, 실행, 새 관측의 반복과 선택적인 손목 픽셀 깊이 조회를 사용한다. 접촉점이 가려지는 정밀 조작과 이전 단계의 부적절한 파지가 뒤의 동작을 막는 사례를 보고한다. **명령 실행 상태와 과제 완료는 별도**로 다룬다.

| 비교 | RAIL 사례 | 현재 PhyRC |
|---|---|---|
| 로봇·환경 | 실물 Stretch 4 한 대, 가정 조작 | Stretch 4 두 대, 공식 착의 시뮬레이터 |
| 행동 의미 | cm·degree 등의 상대 위치 명령 | `(2,9)` 정규화 속도 비율과 그리퍼 의도 |
| 깊이 | 픽셀에 대한 카메라 기준 거리 조회 | 현재 한 카메라 최대 8점·관측당 1회. 기본값은 광축 Z(m), 선택적 카메라 XYZ/range |
| 실행 결과 | 목표 도달·조기 정지·시간 초과·거절 구분 | 공개 관절/목표/직전 행동 비교 가능. 동일한 결과 분류가 구현된 것으로 가정하지 않음 |
| reasoning | 기본 high와 별도 ablation | 고정 ultra 유지. 외부 결과만으로 설정 변경하지 않음 |

**적용 가설:** 파지 변경이 만든 천의 형상과 관측 가능성을 먼저 평가한다. 접근 실패가 반복되면 같은 손 근처에서 이동량만 바꾸기 전에 “이 파지로 필요한 공간을 만들 수 있는가”를 다시 검토한다. 이는 [최신 사용자 메모](../../COLLECTION_PLAN.md#2026-11-14-다음-시연-메모)의 의도를 구체화한 것으로, 논문이 해당 파지나 착의를 검증했다는 뜻은 아니다.

깊이·reasoning 비교는 특정 가정 과제의 소규모 실험이다. 이를 PhyRC의 성공률 예측이나 입력 제거의 근거로 일반화하지 않는다. 원문 부록의 프롬프트·수치 명령을 현재 actor에 복사하지 않는다. 특히 **색 depth와 정확한 픽셀 질의는 다른 입력**이고, 깊이값도 숨은 통로나 소매 통과를 증명하지 않는다.

<a id="methods"></a>
## 3. 연구에서 가져올 방법

### 3.1 시연을 관측 근거가 있는 전략 자료로 만들기

[ENCORE](https://github.com/YIFANK/encore/blob/main/README.md)는 소수 시연의 다중 시점 프레임, 그리퍼 이벤트와 시간적 맥락을 에이전트가 읽을 수 있는 형태로 묶고, 개발 뒤 고정한 전략을 평가한다. **PhyRC 제안:** 기존 정상 마감 시연에서 파지 직전/직후, 벌림, 손 접근, 접촉 전후를 동일 전이 번호로 묶는다. 각 묶음에 “보인 사실 / 의도 / 결과 / 미확인”을 적는다. 리뷰 자료는 개발자용이며 격리 actor에 통째로 전달하지 않는다.

[2AM](https://agent-mem-action-model.github.io/)은 agent의 기억을 언어와 2D 힌트로 action model에 연결한다. 진행률과 정확한 종료는 별도이며, 모든 성공 지표가 개선된 결과는 아니다. **PhyRC 제안:** “가운데”·“위”를 현재 이미지의 어떤 대상과 관계인지 기록하되, 픽셀은 `observation_id`, 카메라, 시점에 귀속시킨다. 고정 3D 좌표나 새 장면의 정답 파지로 재사용하지 않는다. 2AM의 학습된 VLA 인터페이스는 현재 Astra 속도 행동과 다르다.

### 3.2 접촉 관계가 달라졌다면 이전 동작을 계속하지 않기

[Topology-Informed Visual Prompting](https://arxiv.org/pdf/2609.23944)은 겉보기 거리만으로 구분하기 어려운 통과·감김 관계를 다룬다. 정상 시연에 관계 복구와 복구 이후 진행 데이터를 더하고, 배포 시 영상 기반 안내를 사용한다. PhyRC에서도 노란 경계와 손이 겹쳐 보이는 것, 실제로 손목에 천이 걸린 것, 소매가 통과한 것을 분리해야 한다. 논문의 기하 기반 데이터 생성 절차를 actor의 내부 상태 조회로 바꾸지 않는다. 천의 위상 지표를 현재 계산·검증했다는 뜻은 아니다.

**개발자 리뷰용 단계 카드 제안:** 각 단계에 시작 조건, 짧은 행동의 목적, 다음 관측에서 확인할 변화, 실패하면 되돌아갈 준비 단계를 적는다. “파지 유지”, “공간 확보”, “같은 손 정렬”, “소량 하강”, “관계 유지”는 검토할 의미 단위이며 현재 호출 가능한 skill/API 이름이 아니다. 아래 4절에 다음 시연용 항목을 구체화했다.

[RAPID](https://yuyaoliu.me/projects/rapid/)는 시연에서 작업 정의와 관계 중심의 조작 프로그램을 얻는 방법을 다룬다. **PhyRC 제안:** 공식 영상은 지지·접근·접촉·단계 전환을 이해하는 자료로 쓰고, 관절값이나 시간을 복사한 정답 trajectory로 취급하지 않는다. RAPID의 주 실험은 강체 비파지 접촉 조작이므로 옷의 변형과 두 Stretch의 착의로 그대로 일반화할 수 없다.

### 3.3 실패를 기억하되 검증되지 않은 요령을 성공 기술로 저장하지 않기

[ASPIRE](https://research.nvidia.com/labs/gear/aspire/)는 실행 trace에서 실패를 좁혀 프로그램을 수정하고, 재실행으로 검증한 교정을 재사용 경험으로 축적한다. **PhyRC에서는 우선 별도 리뷰 문서에** 실패한 관측 관계, 시도한 수정, 결과, 같은 수정을 다시 시도할 조건을 남긴다. 모델의 자신감이나 단계 이름만으로 skill 성공을 등록하지 않는다.

[ARCHITECT](https://robo-architect.github.io/)는 사람의 언어 교정을 실행 trace와 연결해 프로그램과 지속적인 skill memory에 반영하며 천 접기도 다룬다. **PhyRC 제안:** 사용자의 “가운데 파지·위에서 내려 걸치기”를 적용 단계, 변경 이유, 확인할 관측, 미실행 상태와 함께 보존한다. 풍부한 perception/planning/guarded-motion 도구를 전제로 한 연구이므로 현재 속도 action이나 미적용 피드백 큐와 동일한 구현으로 설명하지 않는다.

[Robo-COP](https://xilunzhangrobo.github.io/robo-cop/)은 정책 변경과 orchestrator의 경험을 함께 관리하고 검증 뒤 채택하는 구조를 연구한다. **PhyRC 제안:** 기억에는 source group, 코드·프롬프트 버전, 관측 근거와 적용 범위를 붙인다. 새 정책에 이전 요령을 무조건 적용하지 않는다. 실시간 피드백 큐는 현재 미적용이므로, 이번 문서가 실행 중 외부 피드백 주입을 활성화하지 않는다.

### 3.4 관측을 줄이는 것과 필요한 피드백을 보존하는 것

[PyRUA-Lean](https://dagroup-pku.github.io/PyRUA-Lean/)은 로컬 코드와 primitives를 이용해 상호작용 비용을 줄이고, [Guava](https://guava-harness.github.io/)는 observation/tool/feedback 설계와 짧은 피드백 반복을 평가한다. 서로 다른 인터페이스에서 나온 결과다. 어느 쪽도 현재 PhyRC의 긴 무관측 접촉 동작을 정당화하지 않는다.

**비교 가설:** 자유 이동의 중복 설명과 접촉 구간의 필요한 관측을 구분한다. 파지 변경·천 접힘·손 접촉 직전/직후는 짧게 실행하고 다시 본다. 비용 감소는 추가 득점·실제 진행·실패 증가와 함께 판단한다. 공개된 token 절감률을 PhyRC 예상 절감률로 옮기지 않는다. 우선 현재 `plan-size=1`과 행동 상한을 유지한 상태에서 기록을 분석한다.

### 3.5 해법을 먼저 검증한 뒤 데이터를 늘리기

[EmbodiedSWE](https://embodiedswe.github.io/)는 검증된 해법에서 여러 변형의 시연을 생성하는 방향을 제시한다. 그러나 agent의 full simulation access와 IK 같은 도구, 별도 task 생성은 이 저장소의 공개 관측 actor 조건과 다르다. **이식할 것은 검증 순서**다. 현재 E31의 QC 통과는 착의 성공 seed 확보가 아니다. E32 불완전 기록도 정상 학습·replay 자료로 승격하지 않는다.

[Agentic World Action Models](https://agentic-wam.github.io/)는 code, 미래 영상, 행동을 함께 다루고 시연에 프로그램 단위를 붙이는 연구다. **단기적으로는** 기존 시연의 의미 구간과 실제 행동·관측을 연결해 기록하는 방식을 참고한다. **중장기적으로는** 충분한 검증 데이터와 별도 실험이 있어야 모델 학습·실행을 검토할 수 있다. 미래 영상의 그럴듯함은 천의 실제 접촉 성공이나 공식 점수의 증거가 아니다. 현재 PhyRC WAM이 구현됐다는 뜻도 아니다.

### 3.6 완료 판정과 수정 가설을 따로 검증하기

[SimEX](https://arxiv.org/pdf/2609.38982)는 실패에서 여러 수정 후보를 만들고 시뮬레이션으로 비교한다. **PhyRC 제안:** 파지 위치·보이는 공간·접근 방향을 개별 가설로 적고, 어느 변화가 진척을 만들었는지 비교한다. 논문에서 simulator를 개선하는 단계는 공식 PhyRC physics·자산·평가기를 변경하는 근거가 아니다.

[Astra on RoboMME](https://arxiv.org/pdf/2611.06184)는 계획기, VLA, 작은 완료 모니터를 나누고 목표 발행과 완료 확인을 구분한다. 모니터 오판은 후속 기억도 오염시킬 수 있다. **PhyRC 제안:** 의도한 걸침, 관측된 관계, 미확인을 분리한다. 현재 검증된 착의 VLA나 학습 모니터가 있다는 뜻은 아니며, 해당 논문은 항상 재계획하는 대조군·실제 금전비용 등을 충분히 측정한 비교로 해석하면 안 된다.

[RPG](https://arxiv.org/pdf/2610.02204)는 별도 실패 진단에서 코드·프롬프트 수정안을 만들고 개별·병합 수정의 효과를 확인한다. **PhyRC 제안:** 개선이 다른 준비 단계의 파지 유지나 관측 경계를 깨뜨리지 않는지 함께 검토한다. 특권 진단 정보는 별도 검수 영역에 두며 actor로 전달하지 않는다.

<a id="next-trial"></a>
## 4. 다음 사용자 제안을 검토하는 방법

정본은 [2026-11-14 다음 시연 메모](../../COLLECTION_PLAN.md#2026-11-14-다음-시연-메모)다. 아래는 연구를 참고해 관측 항목을 구체화한 **미실행 검토안**이다. “더 가운데 파지 → 노란 경계가 위아래로 늘어지고 공간이 보임 → 같은 마네킹 손 위에서 조금 내려 걸침 → 첫 손목 관계 유지”의 흐름을 따른다.

| 단계 | 공개 관측에서 확인할 것 | 불확실하거나 실패했을 때의 검토 |
|---|---|---|
| 출발점 선택 | 파지를 바꿀 여유와 양쪽 지지가 있는가 | 종전 E28/632에 고정하지 않고 더 이른 유효 경계·새 reset 비교. E32는 제외 |
| 더 가운데 파지 | 실제 파지 위치가 바뀌고 천이 함께 움직이는가 | 그리퍼 닫힘만으로 파지 성공 선언 금지. 지지 상실/미파지/가림을 분리 |
| 공간 만들기 | 같은 경계의 연속성, 보이는 간격, 손이 접근할 방향 | 노란색·U자 모양을 입구 증거로 삼지 않기. 접힘인지 통로인지 미확인 표시 |
| 손 위 정렬 | 같은 마네킹 손과 연결 전완, 천의 상대 위치 | 화면 위아래를 world-Z 명령으로 직결하지 않기. 필요한 현재 픽셀만 depth 조회 |
| 소량 하강 | 짧은 행동 전후 손·천·두 지지점 관계 | 빈 공간 붕괴·손 가림·과도한 당김이 보이면 같은 하강 반복 전 원인 재검토 |
| 걸침 확인 | 여러 공개 시점과 후속 관측에서 관계가 유지되는가 | 단순 겹침·가림과 구분. 시각적 걸침, 공식 득점, 전체 success를 별도 기록 |
| 다음 손으로 진행 | 첫 손목 관계를 보존하며 반대쪽 작업이 가능한가 | 첫 관계가 미확인인데 다음 단계로 넘어간 것을 성공 진행으로 세지 않기 |

### 비교 실험을 준비한다면

실제 재개 후 **한 번에 바꿀 요소를 제한**한다. 파지 위치, 접근 방향, 행동 길이, 관측 표현을 한꺼번에 바꾸면 효과의 원인을 구분하기 어렵다. 아래 순서는 후보이며 새 run·예산·전략명을 확정하지 않는다.

| 비교 | 유지할 조건 | 알아보려는 것 |
|---|---|---|
| 파지 위치 후보 | 가능한 같은 초기 조건·행동 계약·관측·예산 | 파지 자체가 접근 공간을 지속적으로 만들 수 있는가 |
| 같은 준비 형상에서 위쪽 접근·짧은 하강 | 대상 손·파지·기록 조건 | 손 위에서 내려 걸치는 제안에 실제 진행 근거가 생기는가 |
| 기존 관측 대 구조화한 단계 기록 | 동일 모델·입력 허용 범위·action 예산 | 반복 실패를 더 일찍 구분할 수 있는가 |
| 나중의 관측 빈도/길이 비교 | 위 준비·접촉 방법이 어느 정도 검증된 뒤 | 비용을 줄이면서 접촉 실패를 늘리지 않는가 |

행동 prefix 재실행은 정확한 천 checkpoint 복원이 아니다. 시작 관측이 달라지면 **같은 초기 상태의 엄밀한 대조 실험이라고 쓰지 않는다.** 실제 차이를 보고하고 source group을 유지한다. 같은 E28 계열 분기를 독립된 성공 표본으로 합산하지 않는다.

### 새 리뷰에 남길 필드

아래는 **추가 리뷰 문서의 제안 형식**이다. 현재 capture/actor 스키마에 추가된 필드가 아니며 원본 HDF5를 수정하지 않는다.

| 범주 | 기록할 내용 |
|---|---|
| 출처 | run, source commit, 직접 parent/source group, replay 경계, 새 행동 범위 |
| 관측 근거 | 카메라·전이 번호·시각, 파지점/목표 손의 식별, 필요한 경우 현재 pixel/depth 근거 |
| 의도와 결과 | 바꾸려던 관계, 실제 관측 변화, 미확인 사항, 실패 원인 후보 |
| 실패 구분 | 파지 미확인, 공간 접힘, 손 오식별, 가림, 접근 불일치, 지지 상실, 실행/기록 오류 |
| 다음 선택 | 현재 단계에서 수정 / 준비·파지로 돌아가기 / 정상 마감. 이유와 기대 관측 |
| 성과 | raw score, 착의 score, success, 시각 검토, capture complete, QC, 학습 승인 각각 |
| 비용 | 새 결정 수, depth 후속 포함 모델 호출 수, token, wall time, sim time, 실제 행동/정착 전이 |

실패 원인 분류는 관측 기반 가설이며 자동 접촉 판정기가 아니다. “조금 더 움직이면 될 것”이라는 설명 대신 **어떤 관측이 달라져야 하는지**를 적는다. 종료 상태·추가 결정 효과를 분석하고 정체 시 준비나 방법을 다시 선택한다는 기존 예산 지침을 유지한다.

<a id="code-map"></a>
## 5. 현재 코드와 연결할 위치

확인 기준: `main`의 조사 시작 commit **8a1730d1ef8d3312574d2d1cb1e2f1ec0790d63a**. 함수 이름은 이 소스에서 확인했다. 이후 Codex는 현재 HEAD의 정의를 다시 찾는다. 외부 논문의 기능이 아래 코드에 이미 있다는 뜻은 아니다.

| 목적 | 현재 파일·심볼 | 연구를 읽을 때의 경계 |
|---|---|---|
| 공개 입력과 최신 관측 | [`codex_client.py`](../../../participant/collection/codex_client.py): `prepare_observation`, `replay_image_context` | 리뷰·점수·내부 기하를 actor 입력으로 합치지 않음 |
| 격리 모델 호출 | [`codex_actor.py`](../../../participant/collection/codex_actor.py): `Actor._provision`, `Actor.invoke`, `_read_result` | 개발자 Codex와 로봇 actor는 다른 역할. 코드 실행 자유도를 외부 benchmark처럼 확대하지 않음 |
| 현재 픽셀 깊이 | [`depth_query.py`](../../../participant/collection/depth_query.py): `freeze_public_frame`, `lookup` | 한 카메라·현재 관측·최대 8점·1회. invalid≠빈 공간 |
| 응답·실행 길이 | [`codex_client.py`](../../../participant/collection/codex_client.py): `validate_decision`; [`boundary.py`](../../../participant/collection/boundary.py): `validate_action`, `Operator.act` | 유한 길이·속도 계약 유지. 코드/skill 제안과 실행 가능한 API를 구분 |
| 이름 기반 행동 | [`named_actions.py`](../../../participant/collection/named_actions.py): `pack` | `(2,9)` 값 재배열. IK·cm 이동·각도 위치 명령으로 해석하지 않음 |
| 분기 출처 | [`continuation.py`](../../../participant/collection/continuation.py): `load_replay_prefix`; [`retry_plan.py`](../../../participant/collection/retry_plan.py): `build_plan` | 완료·QC·해시 검증한 원본만. 새 physics에서 prefix 재실행 |
| 정상 마감과 QC | [`validate_capture.py`](../../../participant/collection/validate_capture.py): `validate_capture`, `complete_flag` | 파일 완결성·정렬과 착의 성공 분리. E32 표식 수정 금지 |
| 별도 성과 기록 | [`evaluation.py`](../../../participant/collection/evaluation.py): `ScoreEvents`, `CollectionEvaluation`; [`milestones.py`](../../../participant/collection/milestones.py): `build_index` | 검수/허용 보상과 actor 입력의 경계 유지. 모델 stage를 공식 milestone으로 대체하지 않음 |
| 보존 | [`preserve_collection.py`](../../../scripts/preserve_collection.py), [클린 서버 인계](../../project/sessions/20261114-paused-clean-server-handoff.ko.md) | 원본 불변·고정 revision·SHA. 연구 리뷰는 별도 파일 |

현재 액션은 `float32 (2,9)`, `[-1,1]`이며 행 0=robot_0, 행 1=robot_1이다. 앞 8채널은 속도 비율, gripper 0은 기존 의도 유지다. 기록 20 Hz·제어 60 Hz·물리 240 Hz와 모델 응답 주기를 혼동하지 않는다. 중립 명령 중에도 목표 추종 운동이 남을 수 있다. 로봇별 비교 화면은 **왼쪽 robot_1 / 오른쪽 robot_0**으로 표시하며 action 행 순서는 바꾸지 않는다.

연구가 권하는 메모리·확인 도구를 새로 만들더라도 [공식 규칙](../../competition/RULES.md), [입력 계약](../../../config/policy_interface.json), [AGENTS](../../../AGENTS.md)가 우선이다. simulator 물체 좌표·천 mesh·접촉 정답·평가 JSON을 actor/critic/world model/증류 teacher 입력으로 전달하지 않는다. 공식 장면·physics·평가기를 점수 개선 목적으로 바꾸지 않는다.

## 6. 공식 데모 플랫폼과 ATLAS에서 참고할 운영 구조

### NERO: 명령 수락·실행 완료·과제 성공을 분리

[공식 플랫폼 상세](https://agentic-robotics-workshop.github.io/demo?from=demo-track)의 NERO는 양팔 7-DoF와 거치형 RGB-D 카메라를 사용하는 Python/MCP 플랫폼이다. place/select/sort 시뮬레이터와 IK/FK·joint/TCP 명령을 제공하고 정책에 simulator 물체 좌표·점수를 노출하지 않는다. Unitree G1도 별도 플랫폼으로 소개되지만 PhyRC 착의의 직접 대체재는 아니다.

| 확인한 원문 | 가져올 운영 원칙 | 현재 PhyRC에 적용할 때 |
|---|---|---|
| [참가자 가이드](https://github.com/ZiWang1105/agile-x-deploy/blob/main/docs/WORKSHOP.md) | 단일 제어 소유자, 요청 중복 방지, 최종 cleanup 뒤 관측, 성공 주장의 독립 검증 | 요청 수락·action 실행·기록 완료·착의 성공을 분리하고 종료 정리 전이를 별도 기록 |
| [RobotClient / Operation](https://github.com/ZiWang1105/agile-x-deploy/blob/main/src/agilex_deploy/workshop_client.py) | 관측 frame ID와 depth 결합, operation 상태 조회·명시적 취소 | timeout이 자동 취소나 정상 마감을 뜻한다고 가정하지 않기. request/ack/저장 action 대응 검토 |
| [MCP adapter](https://github.com/ZiWang1105/agile-x-deploy/blob/main/src/agilex_deploy/workshop_mcp.py) | 관측 조회와 실행·취소 API 분리, 그리퍼 닫힘과 파지 증거 분리 | 현재 depth query의 물리 진행 0 원칙 유지. 외부 MCP를 붙이는 것만으로 파지 기능이 생긴다고 설명하지 않기 |

조사 시 원문 blob SHA: 가이드 `46f58d75db0ffc3ccc55b07e3fa81be875cd31de`, client `933a5cadd3b14d04feb161b2f0ac356ae155e866`, MCP `3be62306aa5944ffc7befa8917aab2bfeaef00e8`. 이 파일들은 읽기 참고자료이며 PhyRC에 설치하지 않았다. NERO의 위치/IK/TCP·gripper 계약을 PhyRC 속도 행동으로 직접 복사하지 않는다.

### ATLAS: 뒤의 관측이 앞의 성공 판단을 반박할 수 있음

[ATLAS 프로젝트](https://atlas-humanoid.github.io/)와 [기술 글](https://atlas-humanoid.github.io/blog/)은 사람 영상에서 작업 정의를 얻고 frozen whole-body tracker와 실행 보정을 연결한다. 저장 관측과 시도에 대해 판단 수정안을 비교하고, 후속 프레임이 이전의 성공 판단을 뒤집을 수 있다는 점을 다룬다.

**PhyRC 제안:** 손목에 걸렸다는 판단은 한 장의 겹침보다 후속 공개 프레임에서 관계가 유지되는지 확인한다. 향후 별도 시각 검수기를 만든다면 기존 시연에서 false success가 늘지 않는지 먼저 비교한다. **공식 evaluator를 수정하는 제안은 아니다.** ATLAS는 휴머노이드 tracker·retargeting 등 다른 전제가 있고 지속 접촉은 후속 연구 범위다. 실제 착의나 변형체 양팔 제어가 검증됐다고 해석하지 않는다.

<a id="paper-inventory"></a>
## 7. 채택 논문 39편 조사 목록

번호는 [공식 목록](https://agentic-robotics-workshop.github.io/papers)의 순서다. 짧은 이름을 눌러 각 OpenReview 항목으로 갈 수 있다. **적용 제안은 본 저장소에 대한 해석**이다. 목록만 확인된 항목은 방법·실험 결과를 추정하지 않았다. 관련성이 낮은 scene 재구성·휴머노이드·항공 제어도 누락 없이 표시한다.

**확인 범위:** 30편은 원논문·저자 자료 내용을 확인했고, 1편(#34)은 같은 저자의 관련 연구로 구분했다. 8편(#2·5·25·26·29·31·33·36)은 방법·결과 미확인이다. OpenReview 직접 본문이 검증 화면으로 막힌 경우 저자 프로젝트·arXiv를 대체 출처로 썼으며, 워크숍 제출판과 문장·버전이 완전히 같다고 보장하지 않는다.

### 1–13

| 번호·자료·근거 | 확인한 핵심 | PhyRC 연결과 한계 |
|---|---|---|
| 1. [ENCORE](https://openreview.net/forum?id=9CSIakHmiD)<br>[자료1](https://arxiv.org/abs/2609.37359) · [자료2](https://github.com/YIFANK/encore/blob/main/README.md)<br>arXiv 초록 + 공식 GitHub README 직접 확인; OpenReview 본문 접근 제한 | 소수 시연을 바로 학습시키기보다 다중 시점 핵심 프레임·그리퍼 이벤트·연속 장면·전체 궤적으로 묶어 코딩 에이전트가 전략을 읽게 한다. 개발 시행 뒤 프로그램을 동결하고 별도 평가한다. | E28 계열/E31의 파지·벌림·손 접근 전후를 증거 묶음으로 정리하고 다음 시연 가설과 연결한다. 초기 파지 변경이 필요하면 더 이른 유효 prefix 또는 새 reset을 검토한다. **한계:** PhyRC 변형체 착의 성능 근거가 아니다. 현재 actor에게 저장소 리뷰/평가를 넘길 수 없으므로 개발자 분석용 묶음부터 적용한다. |
| 2. [Recovery Credit](https://openreview.net/forum?id=UPAuYhlq0Y)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |
| 3. [2AM](https://openreview.net/forum?id=y0qBMe2qH3)<br>[자료1](https://agent-mem-action-model.github.io/) · [자료2](https://arxiv.org/abs/2609.11308)<br>공식 프로젝트 방법·결과 + arXiv 초록 확인 | Agent에 기억을 두고 단일 RGB action model에 언어와 선택적 2D grasp/place/move 힌트를 전달한다. LIBERO-Mem에서 진행률 개선과 정확한 종료의 어려움을 별도 보고한다. | 어느 손, 어느 파지점, 어느 빈 공간, 다음 짧은 이동을 observation_id·camera·pixel과 함께 기록하는 표식 설계에 참고한다. 이동 목표와 종료 판단을 분리한다. **한계:** 힌트를 따르도록 학습한 VLA가 전제이다. 현재 속도 제어 Astra에 즉시 연결되는 기능이 아니다. strict success는 aligned π0 대비 개선되지 않았으며 다른 벤치마크 확장은 예정 상태이다. |
| 4. [World Action Planner](https://openreview.net/forum?id=rNHO9vQF9h)<br>[자료1](https://worldactionplanner.github.io/)<br>공식 프로젝트 초록·알고리즘 설명·평가 범위 확인 | action-conditioned world model의 상상 rollout으로 전체 계획을 고치고 인접 행동 후보를 비교하는 coarse-to-fine 탐색을 제안한다. | 파지 위치·위쪽 진입·하강량을 한 번에 바꾸지 않고 후보별 기대 결과와 실제 관측을 비교하는 실험 설계에 참고한다. **한계:** 현재 PhyRC용 cloth world model은 없다. 상상 영상으로 접촉 성공을 확정하거나 실제 evaluator를 대체하지 않는다. |
| 5. [Uncertainty Is the Wrong Trigger](https://openreview.net/forum?id=cPUMmLHDG6)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |
| 6. [EmbodiedSWE](https://openreview.net/forum?id=3c1CfvfHa7)<br>[자료1](https://embodiedswe.github.io/) · [자료2](https://arxiv.org/abs/2609.27308)<br>공식 프로젝트 benchmark·API 원칙 + arXiv 초록 확인 | 접촉·변형체·장기 과제에서 코딩 에이전트의 해법을 검증한 뒤 변형하여 VLA 학습 궤적을 늘린다. 과제별 특화와 반복 탐색 비용도 보고한다. | 먼저 검증된 첫 손목 걸침 해법 하나를 확보한 뒤 파지·초기 상태 변형을 수집하고, 완전한 기록과 과제 성과를 따로 검사한다. **한계:** 해당 benchmark는 agent에 full simulation access와 IK 등 도구를 제공한다. PhyRC 공개 관측 경계로 그대로 이식할 수 없다. 현재 E31은 완전 기록이지만 착의 성공 시연이 아니므로 성공 seed로 부르지 않는다. |
| 7. [Agentic Real2Sim](https://openreview.net/forum?id=G9RmahESMC)<br>[자료1](https://agentic-real2sim.github.io/) · [자료2](https://arxiv.org/abs/2607.19190) · [자료3](https://github.com/agentic-real2sim/agentic_real2sim/blob/main/README.md)<br>공식 프로젝트 초록·deformable adapter 설명 + arXiv 초록 확인 | 로봇-물체 상호작용 영상을 geometry·state·물리 파라미터가 있는 실행 가능한 episode twin으로 변환한다. 강체·변형체·휴머노이드 영역을 다룬다. | 천 변형을 평가할 때 단일 RGB 모양뿐 아니라 시간에 따른 변형과 접촉 결과가 맞는지 보는 관점을 참고한다. **한계:** 이미 공식 시뮬레이터가 있는 PhyRC 수집의 선행 조건이 아니다. 챌린지 physics/assets를 목표 점수에 맞춰 변경하는 근거로 쓰지 않는다. |
| 8. [Adversarial Self-Play](https://openreview.net/forum?id=LkW6BOlHMY)<br>[자료1](https://arxiv.org/abs/2610.36143)<br>1차 arXiv 초록 확인 | 코딩 에이전트가 상대 프로그램과 수행 피드백을 바탕으로 공격/방어 코드를 수정하는 self-play를 연구한다. 두 사례의 국소 복구는 장기 강건성 입증과 구분된다. | 입력 검증·실패 재현·수정 전후 artifact 보존을 참고하는 수준이다. **한계:** 착의 시연 수집 방법이나 데이터 증강의 직접 근거는 아니다. adversarial 실행을 현재 시스템에 추가할 필요가 없다. |
| 9. [SceneRig](https://openreview.net/forum?id=C3sG9bZPbs)<br>[자료1](https://arxiv.org/abs/2610.28585)<br>1차 arXiv 초록 확인; 비공식 미러는 근거에서 제외 | 단일 영상에서 editable simulation scene을 만들며 geometry·vision·physics 도구와 수정/검증 반복으로 물리적 안정성을 확보한다. | 보기 좋은 장면과 재현 가능한 물리 상태가 다름을 설명할 때 참고한다. action-prefix replay의 결과는 매번 관측으로 확인한다. **한계:** PhyRC용 재구성 시스템을 도입하거나 제공 환경을 수정할 이유는 아니다. cloth checkpoint 재현을 보장하지 않는다. |
| 10. [Robo-COP](https://openreview.net/forum?id=UJHkYOreYB)<br>[자료1](https://xilunzhangrobo.github.io/robo-cop/) · [자료2](https://arxiv.org/abs/2610.09228)<br>공식 프로젝트 method·held-out 평가·채택 기록 + arXiv 초록 확인 | Robo-COP은 수행 이력에서 기술 구간을 선별하고 필요한 경우 policy를 학습시킨다. 새 policy 검증 뒤 채택/복귀하며 그 동작에 맞춰 orchestrator memory도 갱신한다. | 완전한 episode 내 유효한 벌림·접근·걸침 구간을 검토 후보로 분리하고, policy/prompt 버전과 기억이 어느 모델에 해당하는지 함께 기록한다. **한계:** E32 incomplete 기록을 자동 학습 편입할 근거가 아니다. 고정 주기 fine-tuning보다 검증이 핵심이며 현재 정책 개선은 미검증이다. 공식 코드 공개는 coming soon. |
| 11. [PyRUA-Lean](https://openreview.net/forum?id=wKgMn9vqUi)<br>[자료1](https://dagroup-pku.github.io/PyRUA-Lean/) · [자료2](https://arxiv.org/abs/2610.01939)<br>공식 프로젝트 abstract·수치 조건·예제 cell 확인 | PyRUA-Lean은 짧은 Python cell에서 robot primitives를 합성하고 로컬 검사/재시도하며 필요한 관측만 반환한다. 동일 planner·primitive 비교에서 호출과 입력 token 비용을 줄인다. | 빈 공간 운반 구간의 불필요한 재설명을 줄이는 개선 후보이다. 접촉 직전/직후에는 짧은 action과 새 관측을 유지해 Guava식 빈번한 feedback과 구간별 비교한다. **한계:** 논문 primitive와 현재 normalized velocity action은 다르다. 장기 open-loop action 확장의 근거가 아니다. 65% token 절감은 양쪽 모두 성공한 instance 집합 기준; PhyRC 절감 예상치가 아니다. |
| 12. [Skill2Real](https://openreview.net/forum?id=52exBmCzDf)<br>[자료1](https://arxiv.org/abs/2610.02788)<br>1차 arXiv 초록 확인 | 공통 API 위에서 local skill과 task composition을 분리 학습한다. proposer/verifier/governor가 시뮬레이션 진단과 skill 갱신을 검증하며 배포 skill은 공개 관측에 의존한다. | 수집 actor와 분석 reviewer 역할을 명시하고, 변경 후보가 실제로 개선됐는지 검증 후 다음 계획에 채택하는 구조를 참고한다. **한계:** privileged 평가 신호를 actor/critic 입력으로 전달하면 안 된다. API와 embodiment가 달라 해당 skill을 가져와 바로 실행할 수 없다. |
| 13. [Guava](https://openreview.net/forum?id=02FSMHg6ii)<br>[자료1](https://guava-harness.github.io/) · [자료2](https://arxiv.org/abs/2606.18363)<br>공식 프로젝트 harness ablation·data generation·latency 조건 확인 | 동일한 observation/tool/feedback 인터페이스로 teacher 상호작용을 모아 compact agent를 학습한다. semantic tools, 반복 관측, 수치 상태·도구 응답을 함께 제공하는 설계를 비교한다. | 실패 뒤 복구 시연을 따로 보존하고 기록 무결성·영상 검토 후 채택한다. 먼저 현재 도구 의미/피드백을 안정화한 후 소형 agent 증류를 고려한다. **한계:** Robo 도구 grasp/align은 현재 속도 action과 다르다. 논문 state branching은 PhyRC action-prefix replay와 동일하지 않다. model-call latency는 simulator 포함 전체 소요시간이 아니다. |


### 14–26

| 번호·자료·근거 | 확인한 핵심 | PhyRC 연결과 한계 |
|---|---|---|
| 14. [Topology-Informed Prompting](https://openreview.net/forum?id=RkzWx9Sfcz)<br>[자료1](https://arxiv.org/pdf/2609.23944) · [자료2](https://arxiv.org/abs/2609.23944)<br>원문 PDF 8쪽 확인. arXiv 제목은 “Topology-Informed Visual Prompting For Vision Language Action Policies”로 다르며 동일 저자 및 저자 홈페이지 연결을 확인. | 국소적으로 비슷한 영상에도 서로 다른 통과·감김 관계가 필요할 수 있음을 다룬다. 시뮬레이션에서 위상 서명을 교정하는 궤적과 이후 진행 궤적을 추가하고, 영상에서 추정한 서명·waypoint를 VLA 시각 프롬프트로 전달한다. | 손 근처까지 이동한 것과 손이 옷의 적절한 틈을 통과한 것을 구분하는 관찰 기록. 정상 진행뿐 아니라 관계 복구와 복구 후 진행 구간을 별도 수집. **한계:** Gauss linking 기반 계산을 PhyRC 옷에 바로 적용했다는 근거 없음. 논문은 데이터 생성 때 특권 geometry를 사용하므로 현재 actor 입력 경계와 그대로 호환되지 않음. 현재 프롬프트나 학습에 미적용. |
| 15. [PhysCaP](https://openreview.net/forum?id=JprkI7JQDW)<br>[자료1](https://physcap.github.io/)<br>저자 프로젝트의 abstract/method/limits 확인 | Planner가 필요한 물리 정보를 정하고 Prioritizer가 탐색 대상을 줄인다. 로봇 고유감각으로 물체 질량·강성을 추정해 belief를 갱신한 뒤 작업한다. | 짧은 조작 전 '무엇을 확인하려는가'를 기록하고 충분한 증거를 얻으면 탐색을 끝내는 절차를 참고. **한계:** 질량·강성 API는 토크·힘·jaw displacement 등을 전제한다. PhyRC 공개 관측에 해당 센서가 있는지 확인 없이 도입하거나 simulator 내부 물성으로 대체하지 않음. |
| 16. [ARCHITECT](https://openreview.net/forum?id=cRzAMT2Jll)<br>[자료1](https://robo-architect.github.io/) · [자료2](https://arxiv.org/abs/2607.23784)<br>저자 프로젝트 abstract/method/tool suite/results 확인 | ARCHITECT는 사람의 자연어 교정을 실행 trace에 연결해 모듈식 프로그램을 수정하고 지속적인 skill memory에 남긴다. Franka 실험에 천 접기 과제가 포함된다. | '가운데쪽으로 다시 잡기·손 위에서 조금 내려 걸치기'를 적용 대상 단계, 관찰 근거, 변경점, 확인 기준과 함께 보존. **한계:** cuRobo/guarded motion 등 풍부한 제어 도구와 사람 개입을 전제한다. 현재 PhyRC의 finite normalized velocity API나 아직 활성화되지 않은 feedback queue와 동일한 기능이 아님. |
| 17. [FEIJOA](https://openreview.net/forum?id=Eq3xq6KZDC)<br>[자료1](https://arxiv.org/abs/2611.04080)<br>arXiv 초록 확인 | 작업에 맞춰 RGB-D grounding 질의를 갱신하고, 로봇별 실행 전제와 접근 가능성을 확인하며 전후 관찰로 skill 효과를 검증한다. | 같은 마네킨 손인지, 지지 파지가 유지되는지, 다음 움직임 공간이 보이는지 등 전제 확인 후 조작하고 실제 결과를 다시 확인. **한계:** Spot 기반 모바일 조작 결과이며 cloth dressing 성능은 검증되지 않음. 논문의 grounding/skill 기능을 현재 저장소에 구현된 것처럼 쓰지 않음. |
| 18. [ASPIRE](https://openreview.net/forum?id=LDd7VM2doA)<br>[자료1](https://research.nvidia.com/labs/gear/aspire/) · [자료2](https://github.com/NVlabs/ASPIRE)<br>공식 NVIDIA 프로젝트 method/benchmarks/limitations 확인 | 조작별 멀티모달 trace로 실패를 좁혀 프로그램을 고치고, 재실행으로 검증된 수정을 재사용 가능한 skill library로 축적한다. 프로그램 탐색과 별도의 held-out 평가를 둔다. | E28–E31의 어떤 구간에서 의도와 결과가 달라졌는지 기록하고, 한 번의 가설 변경을 비교한 후 확인된 교정만 승격. **한계:** 미검증 메모를 성공 skill로 만들지 않음. 원문도 자동 reset·성공 판정·calibration·memory 노후화·추론 비용을 한계로 적는다. 병렬 탐색 제안이 PhyRC 단일 제어자 실행 규칙을 바꾸지 않음. |
| 19. [Geometric Abstraction](https://openreview.net/forum?id=CQFstcjx1Z)<br>[자료1](https://arxiv.org/abs/2611.05058)<br>arXiv 검색 결과에 노출된 전체 초록 확인; 본문 미확인 | 보정된 RGB-D에서 근거가 있는 부위 참조를 만들고 조작 뒤 갱신한 기하 관계를 텍스트로 전달하여 반복적인 영상 해석을 줄인다. 필요할 때 직접 영상을 다시 본다. | 관측 번호·카메라·pixel/depth·확신도를 붙인 간결한 상태 메모 설계를 참고. **한계:** 옷은 계속 변형되므로 오래된 텍스트 기하를 현재 진실로 취급하지 않음. 정해진 공개 관측에서 계산한 정보만 허용하며 무조건 영상 빈도를 줄이는 근거로 쓰지 않음. |
| 20. [SPROUT](https://openreview.net/forum?id=sU18hA2zbD)<br>[자료1](https://sprout-project-d81650.pages.dev/) · [자료2](https://benzandonati.co.uk/)<br>저자 홈페이지 연결 확인, SPROUT 프로젝트 abstract/method/evaluation/limits 확인 | SPROUT은 목표·skill 순서·제약·구체 궤적을 섞어 요청받고, 빠진 기하·동작 선택을 샘플링과 최적화로 채우는 generalized planning interface이다. | 교정이 목표 오류인지 접근방향 오류인지 미세 이동 오류인지 구분해 필요한 수준의 설명을 기록. **한계:** 실험은 24개 시뮬레이션 task-scene instance이며 FR3 기반. 현재 PhyRC named action adapter는 planner/IK가 아니므로 이 API가 있는 것처럼 호출할 수 없음. |
| 21. [STeP](https://openreview.net/forum?id=ys5jtBPagk)<br>[자료1](https://arxiv.org/abs/2607.18580)<br>arXiv 검색 결과의 전체 초록 확인; 본문 미확인 | 언어 목표를 STL 공간·시간·논리 조건으로 바꾸고, MPC 제약 또는 learned policy 실행 감시로 사용하여 계획 검증과 재계획을 연결한다. | 진행 순서와 유지 조건을 분리: 파지 유지 중 공간 확보, 첫 손목 관계 확인 뒤 두 번째 손목 진행. **한계:** 정확한 predicate와 센서 근거가 선행되어야 한다. 시각적 추정을 공식 성공 판정으로 바꾸거나 현재 코드에 STL 감시기가 구현됐다고 주장하지 않음. |
| 22. [RAPID](https://openreview.net/forum?id=xQRzEp0Zhj)<br>[자료1](https://yuyaoliu.me/projects/rapid/) · [자료2](https://arxiv.org/abs/2609.30249)<br>저자 프로젝트 abstract/method/results 확인 | 한 시각 시연에서 검증 가능한 작업 정의·조작 primitive·검증 환경을 구성한다. 물체 사이 관계로 전략을 나타내고 장면별 기하를 실행 시 다시 결정해 프로그램을 재사용한다. | 공식 영상의 관절값을 복제하려 하지 말고 지지점·통과 관계·접근방향·단계 전환 증거를 사람이 검토한 전략으로 기록. **한계:** 주요 실험은 강체의 비파지 접촉 조작과 Franka이다. PhyRC cloth dynamics·두 Stretch에 대한 성능 보장이 없고 공식 시뮬레이터 재구성/변경을 요구하지 않음. |
| 23. [Agentic WAM / AW-0](https://openreview.net/forum?id=RgpYrdqaFM)<br>[자료1](https://agentic-wam.github.io/) · [자료2](https://arxiv.org/abs/2610.30136)<br>공식 프로젝트 abstract/annotation/skill library/hybrid/limits 확인 | AW-0은 코드·미래 영상·행동을 공동 생성하며, 시연 구간을 프로그램에 맞춰 주석화하고 반복 패턴을 재사용 skill로 정리한다. | 원본 action과 분리하여 시연 구간의 단계·의도·파지 역할·관찰된 결과를 주석화하고, 재사용 표현과 실제 실행 근거를 연결. **한계:** 생성 코드가 기본 모드에서 항상 실행되는 것이 아님. syntax가 맞아도 대상 grounding은 틀릴 수 있고 온라인 자기학습은 미완성. 현재 소규모 PhyRC 데이터로 같은 성능을 기대하지 않음. |
| 24. [Harness VLA](https://openreview.net/forum?id=vTOrVYhBnp)<br>[자료1](https://arxiv.org/abs/2607.08448) · [자료2](https://rpent.readthedocs.io/en/latest/rst_source/resources/harnessvla.html)<br>arXiv 초록 및 연구팀 RPent 문서 확인 | 동결 VLA를 재시도 가능한 국소 접촉 primitive로 쓰고 grounding·운반·배치 준비·복구를 planner와 분석적 primitive가 담당한다. 작업별 기억과 공통 실패 기억을 둔다. | 추후 검증된 착의 local policy가 생기면 위쪽 배치와 접촉 구간의 책임을 분리하는 설계 후보. **한계:** 현재 정상 착의 baseline가 검증됐다는 뜻이 아니며 π0.5의 플랫폼·행동 공간 적합성부터 확인해야 한다. 다른 benchmark 수치를 PhyRC 성공률로 전용하지 않음. |
| 25. [ComDex](https://openreview.net/forum?id=l0BBYNeW4A)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |
| 26. [Impossible Twins](https://openreview.net/forum?id=uMkXmX3mAy)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |


### 27–39

| 번호·자료·근거 | 확인한 핵심 | PhyRC 연결과 한계 |
|---|---|---|
| 27. [RLE-Bench](https://openreview.net/forum?id=YxvA7kHDbK)<br>[자료1](https://arxiv.org/abs/2609.34210) · [자료2](https://github.com/RLE-Bench/RLE-Bench/blob/master/README.md)<br>원논문 초록 + 공식 저장소 README 확인; 워크숍 판본 직접 열람 불가 | 코딩 에이전트가 제어뿐 아니라 정책 학습·인지·기구 설계 문제를 자원 예산 안에서 해결하는지 평가한다. 결과물과 실행 행동을 과제별 지표로 검증한다. | 실행 성공, 캡처 QC, 재시작 가능성, 예산 준수를 별도 지표로 기록하는 운영 관점에 유용. **한계:** PhyRC 착의 성공이나 옷 파지 전략을 검증한 자료가 아니다. |
| 28. [SimEX](https://openreview.net/forum?id=Hpk5GERa1W)<br>[자료1](https://arxiv.org/pdf/2609.38982) · [자료2](https://robo-simex.github.io/)<br>arXiv PDF 본문·실험·부록 확인; 프로젝트 페이지 도구 접근 불가 | 시뮬레이션에서 코드와 사용 지식을 담은 로봇 도구 모음을 개선하고, 실제 실패 한 건으로 여러 수리 후보를 시뮬레이션에서 비교한다. 수건 접기도 다룬다. | 같은 유효 시작점에서 중앙 파지·공간 확보·위에서 하강의 가설을 나누어 비교하고, 실패마다 후보와 관찰 근거를 남기는 방법에 참고. **한계:** 논문의 simulator 수정 단계는 PhyRC 공식 물리·평가기를 변경하는 허가가 아니다. 수건 접기 결과는 착의 성능의 증거가 아니다. |
| 29. [Embodied XAI](https://openreview.net/forum?id=9HKnVoy6O0)<br>[자료1](https://ieeevis.org/year/2026/program/content/8dcf2282-8729-4918-bffd-126bb6130cfb/) · [자료2](https://isahalim.github.io/Embodied-XAI-Is-All-You-Need/)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |
| 30. [Aerial Cinematography](https://openreview.net/forum?id=AVqVpgtKYF)<br>[자료1](https://arxiv.org/abs/2509.16176) · [자료2](https://acdc-drone.github.io/) · [자료3](https://georgexue.com/)<br>동일 제목/저자 arXiv 초록·프로젝트 방법 및 저자 설명 확인 | 언어 요청에서 장면 내 촬영 지점을 검색하고, 선호도 최적화로 시점을 다듬은 뒤 드론 궤적을 계획한다. | 시연 설명용 관측 시점 선정이라는 간접 아이디어에 한정. **한계:** 정적 복원 장면의 항공 촬영이며, PhyRC 관측 카메라나 행동 권한을 늘리는 근거가 아니다. |
| 31. [Contact Code](https://openreview.net/forum?id=78L8T5nsLM)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |
| 32. [Astra on RoboMME](https://openreview.net/forum?id=F1qPCjfU0x)<br>[자료1](https://arxiv.org/pdf/2611.06184) · [자료2](https://bingaochen.github.io/Astra-on-RoboMME/)<br>arXiv PDF 본문·모니터 학습·한계·프롬프트 부록 확인; 프로젝트 URL은 PDF에 명시 | Astra가 이력으로 하위 목표를 정하고 π0.5가 실행하며 학습된 작은 시각 모니터가 각 chunk 뒤 완료를 확인한다. 완료나 특정 사건 때 계획기를 다시 호출한다. | 명령 발행과 관측상 완료를 구분해 기록하고, 핵심 접촉 사건을 재관측·재계획 기준으로 삼는 구조에 참고. **한계:** RoboMME용 정책·모니터 데이터가 필요하다. 항상 재계획 대조실험, 실제 금전비용, 모니터 오류율은 미측정이며 시뮬레이터는 계획 중 정지한다. |
| 33. [SUTO](https://openreview.net/forum?id=BCdDYO0jo9)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |
| 34. [Physical Agency / Pigey](https://openreview.net/forum?id=SlmaqmaqW0)<br>[자료1](https://arxiv.org/abs/2607.21725) · [자료2](https://lianegalanti.github.io/Pigey/) · [자료3](https://github.com/lianegalanti/Pigey)<br>**관련 연구만 확인** Pigey는 제목이 달라 동일 워크숍 판본으로 단정하지 않음. | 관련 연구 Pigey는 동결된 정책과 매개변수화된 기술 위에서 목표 분해·관측·도구 선택·결과 확인·복구를 반복하는 상위 조정기를 둔다. | Astra에게 남은 목표와 관측 사실을 간결히 제공하고, 진행 확인 실패 시 짧은 복구 분기로 바꾸는 실행 인터페이스 설계에 참고. **한계:** 이미 유용한 저수준 기술이 있다는 전제다. FR3/TAMP/π0.5 스택을 Stretch의 속도 명령으로 바로 치환할 수 없다. |
| 35. [RL²-VLA](https://openreview.net/forum?id=DdoqCu21kt)<br>[자료1](https://rl2-vla.github.io/)<br>공식 프로젝트 방법·한계 확인 | VLA 잠재표현으로 작은 RL 조정 모델을 학습하고, 실패가 예상될 때 행동 생성 흐름을 조합해 후보 다양성을 늘린다. | 정체 구간에만 후보 행동 비교 예산을 집중한다는 원칙은 참고 가능. **한계:** 사용 가능한 VLA·실패 예측기·신뢰할 검증기가 선행 조건이다. 현재 Astra 시연 수집기에 바로 설치할 기능이 아니다. |
| 36. [Memory Benchmarks](https://openreview.net/forum?id=z5FsJD37Dj)<br>**본문 미확인** | 제목·원문 연결 확인. 방법·실험 결과는 확보하지 못함. | 후속 열람 후보로만 보존. 현재 적용 근거와 성과 주장에 사용하지 않음. |
| 37. [KPI](https://openreview.net/forum?id=F7Dp4022mM)<br>[자료1](https://arxiv.org/abs/2609.36151) · [자료2](https://kpi-robot.github.io/)<br>arXiv 초록·공식 프로젝트 방법 확인 | 참조 궤적과 접촉 계약을 함께 보내고, 추정 wrench와 추종 오차로 강성·감쇠·피드포워드를 접촉 주기에 조절한다. | 목표 위치뿐 아니라 원하는 접촉 관계를 명시한다는 관점만 참고. **한계:** PhyRC 공개 행동은 정규화 속도 명령이며 해당 토크·강성·wrench 인터페이스가 없다. 제어기 직접 이식 제안 제외. |
| 38. [RPG](https://openreview.net/forum?id=RxO0XrZm0h)<br>[자료1](https://arxiv.org/pdf/2610.02204) · [자료2](https://rpg-robot.github.io/)<br>arXiv PDF 방법·실험·한계 및 공식 프로젝트 확인 | 오프라인 데이터로 연습 과제를 만들고, 실행·영상·특권 시뮬레이터 정보로 실패를 진단해 기술 코드와 프롬프트를 수정한다. 개별 및 병합 수정안을 교차 과제로 검증한다. | 완료된 시연과 실패 리뷰에서 재사용할 관측·조작 요령을 추출하고, 새 전략이 기존 파지 유지 등을 깨지 않는지 검증하는 방식에 참고. **한계:** 특권 정보는 별도 오프라인 검토에만 두고 actor 입력으로 옮기지 않는다. 공식 평가기·물리 설정 변경은 적용 대상이 아니다. |
| 39. [MemBodied](https://openreview.net/forum?id=ttNVX8zEcB)<br>[자료1](https://arxiv.org/abs/2609.28256) · [자료2](https://declare-lab.github.io/projects/membodied/)<br>arXiv 서지 및 연구실 공식 방법·수치·한계 확인 | 초기 장면을 별도 보존하고, 행동 후 관측된 결과를 고정 크기의 재귀 연상 기억에 기록하는 VLA 메모리 구조. | 의도한 동작이 아니라 실제 다음 관측까지 연결해 시연을 저장해야 한다는 데이터 구성 관점에 참고. **한계:** 모델 학습 변경이 필요하며 기억은 학습된 정보만 유지한다. 실물 세 과제 60회 중16회 성공으로 보편적 해결을 입증하지 않는다. |


<a id="codex-handoff"></a>
## 8. 클린 서버 Codex CLI 인계

이 Markdown 본문과 상대 링크는 clone 후 읽을 수 있다. 논문 원본·동영상·큰 시연 원본은 별도 외부 자료이며 이 파일에 복제하지 않았다. 외부 링크가 나중에 바뀌어도 위 요약, 미확인 표시, 코드 대응과 적용안을 먼저 사용할 수 있다.

아래는 **개발용 Codex에 주는 검토 프롬프트**다. 로봇 행동 생성 actor에게 넣는 프롬프트가 아니다.

```text
AGENTS.md, docs/project/STATUS.md, docs/OPERATIONS.md,
docs/COLLECTION_PLAN.md, docs/ASTRA.md,
docs/collection/research/2026-11-14-agentic-robotics-workshop.ko.md를 읽어라.

최신 사용자 지시와 현재 HEAD를 먼저 확인하라.
연구 결과, 이 저장소의 실제 구현, 미실행 적용 제안을 구분하라.
다음 시연 메모의 파지 위치 변경·보이는 공간·같은 마네킹 손 위에서
짧게 내려 걸치기를 기준으로, 출발점과 관측 확인 항목을 검토하라.
종전 E28/632를 자동 선택하지 말고 E32 불완전 원본은 replay/학습에서 제외하라.
현재 action 의미와 공개 관측 경계를 유지하고 repo 리뷰를 actor에 전달하지 마라.
필요한 코드 변경과 검증 계획은 별도로 제시하라.
현재 중지 상태를 이 연구 문서만으로 해제하지 마라.
이번 요청이 문서 확인이면 GPU/모델/시연을 시작하지 마라.
사용자가 나중에 재개를 지시하면 그 최신 범위와 정본 계획에 따라 진행하라.
```

이 파일의 조사일은 고정돼 있다. 재개 때는 링크된 코드·논문·공식 규칙의 변경 여부를 확인한다. 구현을 바꾸면 별도 commit·검증 근거를 남기고, 실험을 하면 원본 보존과 QC·성과 검토를 마친 뒤 정본 계획을 갱신한다. **문서 게시, CPU 검사, 모델 연결, 실제 착의 성과를 서로 대체하지 않는다.**
