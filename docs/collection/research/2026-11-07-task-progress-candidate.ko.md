# 부분 관측에서 과제 진전을 우선하는 후보

**`coordinated-task-progress`는 불확실성 아래의 행동 선택과 진전 정의를 비교하는 미실행 후보다.** 실제로 새 drape 조작을 수행했는지, 통과나 득점이 개선되는지는 이후 실행 결과로 판단한다. 승인된 문구를 공개 기준 `a68182eb8a8a5b3165b26bb1b56d461e11d2f2df`의 별도 worktree `../phyrc-task-progress-candidate`, branch `experiments/task-progress-candidate`에 구현했다. main이나 이미 종료한 E22의 실행 파일·원본을 변경하지 않았다.

## E22에서 확인한 한계

[E22 공개 검토](../reviews/20261107-astra-probe787-named-001.ko.md)는 E18/787을 재생한 뒤4step 전진,4step pitch,6step 중립 관측, 자율 finish를 기록한다. 새 손-rim 관계가 생기지 않았다는 판단과 재파지 금지 범위가 종료 설명에 등장했다. **실제 가려진 경계 통과를 충분히 시도했는데 실패했다는 증거로 확대할 수 없다.** 5점·`no_contact`는 별도 마감 기록이며 정책에 주는 원인 판정이나 다음 행동 근거가 아니다.

전체 실제 시간은 **1032.883초(17분12.883초)**였고 기록813전이 중787이 재생이었다. 공개 `replayed_segment`79행의 `environment_dispatch_wall_s`를 합하면 **671.212초(약11분11초)**다. 전체 환경 왕복694.749초 및 모델 호출 경로294.326초와 범위를 구분한다. 재생은 허용된 행동을 새 환경에서 다시 실행하는 것이어서 필요한 물리 기록을 생략하는 속도 최적화로 해결하지 않는다. 이번 비교는 비싼 재생 뒤 아주 작은 새 행동만 수행하고 끝나는 정책 지침의 한계를 다룬다.

새 후보는 완전한 입구 식별이나 즉시 더 명료한 그림을 얻는 것을 모든 진전의 선행조건으로 두지 않는다. 현재 공개 관계에서 하나의 의미 있는 과제 목표를 고르고, 유한한 이동 뒤 관측한 실제 목표 진전을 평가한다. 접촉·실패가 가능한 시험을 허용하되 불확실한 공간을 비어 있다고 하거나 손이 이미 안쪽에 들어갔다고 가정하지 않는다.

## 선택과 프롬프트 구성

선택은 `--mode dressing --strategy coordinated-task-progress --plan-size 1`이다. 다른 mode 또는 plan-size 2/3은 출력 폴더와 시뮬레이터를 만들기 전에 거부한다. [구현](../../../participant/collection/codex_client.py)은 `TASK_PROGRESS_TASK`와 선택 분기만 추가한다.

```text
TASK + COORDINATED_TASK + TASK_PROGRESS_TASK + METHOD_SATURATION_TASK
```

`ENTRY_PROBE_TASK`, `HEM_ROUTE_TASK`, `SLEEVE_TASK`, 상방·목 우선·A/B task를 덧붙이지 않는다. 기존 모든 task 상수는 그대로다. 새 task의 핵심은 다음과 같다.

- 현재 유용한 양측 지지와 같은 grasp set을 유지한다. **새 재파지 상한은0회**지만 지지 유지 위치 조정·입구 방향 변경·접근·하강·복구는 가능하다.
- 현재 옷·손·전완·몸통 관계에서 **하나의 과제 목표**를 고른다. 몸통 입구를 같은 손 쪽으로 접근시키거나, 팔 방향을 따라 몸통 쪽으로 옷을 이동시키며 내리는 등의 목표이며 두 경로를 동시에 강제하지 않는다. 손은 몸통 입구로 들어가 해당 소매로 나오는 방향을 유지한다.
- 공개 관절 실측·목표·남은 이동·행동 척도·최근 실제 반응으로 방향·속도·길이를 정한다. 적절하면 **한 act에서 기존 최대20step**을 사용할 수 있고 모든 작업 이동을2–4step 정보 probe로 줄이지 않는다. 10cm 같은 고정 거리를 주거나 모든 act를20step으로 강제하지 않는다. 잔류 목표 추종과 포화를 고려한다.
- 완전한 lip 정체·배경이 보이는 틈·즉시 새 구분 정보는 이 유한한 이동의 필수조건이 아니다. 현재/최근 관측에서 정한 가설 아래 한 구간의 부분 가림을 통과하는 시험을 허용한다. 같은 공식 물리·행동 한계 안의 접촉이나 실패도 가능한 결과다. 과거만으로 현재 상태를 승인하지 않으며 free-space·inside·성공을 거짓 확정하지 않는다.
- 다음 관측에서 configured settle을 포함한 실제 로봇 이동·잔류, 천 동행, 과제 목표 진전을 분리한다. 간격 감소·rim-팔 관계 변화·전완을 따르는 옷 이동은 입구 정체가 아직 불확실해도 검토할 진전이다. 로봇이 움직였다는 사실만으로 천 이동·진입을 확정하지 않는다.
- 의미 있는 진전과 유용한 지지가 유지되면 다음 현재 목표로 전체 착의를 이어간다. 첫 유한한 움직임이 모든 모호함을 없애지 못했거나 재파지가 금지라는 이유만으로 종료하지 않는다. 한 번의 가려진 시험을 근거로 계속 같은 숨은 방향을 연쇄 실행하지 않고 매번 목표와 남은 움직임을 다시 평가한다.
- 지지 상실·변형 악화·실측 포화·반복적인 과제 관계 불변이면 지지된 자세/시야 복구나 접근·입구 방향 변경을 검토한다. 공통 SATURATION은 **효과 없는 보정의 반복**에 적용하며, 생산적인 위치 이동마다 새 입구 식별이나 즉시 통과 증거를 요구하는 뜻이 아님을 새 task에 명시한다.

이것은 프롬프트 지침이다. 새 성공 판정기·관측 의미 분류기·행동 clipping이나 강제 거리 제어를 추가하지 않는다. 단순히 기존보다 큰 명령을 출력했다는 이유로 새 M3 조작이나 착의 성과를 수행했다고 기록하지 않는다. 실제 시작 관계·방향·변위·천/손 변화와 결과가 분류 근거다.

## 변경하지 않는 실행 경계

공식 float32(2,9)·범위[-1,1]·20Hz·최대20step schema, 물리·관절 제한, 기존 검증·dispatch·정착·종료 경로는 같다. Astra/ultra·CLI0.166.0·서비스 설정을 변경하지 않았다. named와 pixel-depth-query는 기존 선택 기능이며 기본 OFF다. 예정 입력의16이미지는 현재 RGB5개+같은 재실행의 과거 RGB2×5개+현재depth panel1개다. query는 이 이미지들과 현재 frozen 시계, 기존 camera XYZ/range, action-only 후속을 그대로 사용하며 추가 도구는 없다.

평가·과거 성공·외부 영상·내부 기하·정답 좌표를 actor 입력에 추가하지 않는다. 점수는 기존 trusted 검토 종료와 오프라인 출발점 선택에만 남는다. 같은 source_group의 새 분기는 독립 시연이나 정확한 천 checkpoint가 아니다.

후속 E23의 예정 조건은 **E18/787·history719/771·18판단/max1300/timeout180/settle6/review10·named+query·Astra/ultra**다. root의 전체 CPU 검증과 E22 보존·게시 후 실제 시작을 결정한다. 이 문서나 후보 커밋은 E23 시작·성공 기록이 아니다. 10점은 중간 검토 목표이며 달성 뒤 다음 득점 진행은 실제 원본 마감과 검토에 이어서 수행한다.

## CPU 검사 범위

신규7개 검사는 첫 실행에서 **4.463초에 모두 통과**했다. 기존56개 전략·named·depth 회귀를 더한 첫 **63개 집중 검사도14.626초에 모두 통과**했다. 독립 읽기 검토에서 중대한 의미 충돌은 없었으며, 신규 문구의 `20 control steps`는 내부 제어 주기와 혼동하지 않도록 `20 steps (0.05 simulation seconds each)`로 정밀화했다. 동작·공식 한계 변경은 없다. 집중 명령은 다음과 같다.

```bash
PYTHONPATH=.:tests:src/PhyRC_Sim \
  /home/shadeform/workspace/PhyRC_2027_phase1/.venv/bin/python -m unittest \
  test_task_progress_strategy test_entry_probe_strategy test_overhead_strategy \
  test_neckline_strategy test_regrasp_strategies test_support_diagnostic_strategy \
  test_named_actions test_depth_query -q
```

[전용 검사](../../../tests/test_task_progress_strategy.py)는 고정 기준a68182e의 **기존11전략×named ON/OFF×query ON/OFF=44조합**에서 준비된 prompt/schema/이미지·호출·dispatch·수집 명령이 동일함을 확인한다. 기존 상수·`main` 이외 함수 AST 불변, 새 선택의 task 분리, 공식schema/default OFF, 비착의·다중 plan의 사전 거부도 검사한다.

새 전략의 합성 query→행동은 positional/named 모두 **같은16이미지·공개 시계·frozen ID**, timeout180을 유지한다. 기존 validator를 통과한20step act 뒤 별도6step neutral settle과 예산 종료 stop1이 수행된다. fixture의 총30전이는3재생+20행동+6정착+1마감이며 질의 전이는0이다. trusted 검토 임계값10/50이나 부모·seed 정보가 actor 프롬프트에 영향을 주지 않는지도 대조한다.

모든 검사는 fake actor/simulator를 사용한다. 실제 CLI·GPU·물리·모델의 지침 준수·착의·점수 향상은 이번 CPU 검사 범위 밖이다. 실제 모델/GPU 호출과 main 변경은 수행하지 않았다.

위 시간 표현을 정밀화한 **최종 문구에서도63개 집중 검사가14.805초에 모두 통과**했다. 실패한 검사나 이를 맞추기 위한 실행 코드 변경은 없다. 독립 읽기 검토와 root의 직접 source/test 검토를 마쳤다. 전체 저장소 CPU 검사는 root 통합 단계에서 별도로 수행하며, 이63개 결과를 실제 모델 행동이나 과제 성능 검증으로 표시하지 않는다.
