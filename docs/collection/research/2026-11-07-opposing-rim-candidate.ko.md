# 반대 rim 제어 재파지 · M1 준비 이력과 E25 채택

**E24 종료 후 `coordinated-opposing-rim`을 채택하고 로컬 main `1e86599699ab8497c4227d8b43c30a7d1bcf7931`에 통합했다. E25는 E18/563·history510/542·30판단·max1400으로 계획했으며, 이 기록 시점에는 아직 실행하지 않았다.** 기존 양측 파지를 유지한 채 진입 방향만 바꾸는 실험과 구분해, 테이블 지지 아래 한쪽을 다른 rim 후보로 실제 옮기고 그 뒤 국소 천 동행·두 경계의 상대 변화를 검사한다. 실제 모델 행동·지지 개선·착의 성능은 미검증이다.

준비 당시에는 E23의 진전을 우선하며 미채택 후보로 분리했다. 작업 기준은 `357e5ebd7cd3c4608aab7857046c818c3033bd00`, 별도 worktree `../phyrc-opposing-rim-candidate`, branch `experiments/opposing-rim-candidate`였고 후보 commit은 `a3d10a5bed687469b2887cc28b7f4d01ed484548`다. 회귀 기준은 뒤이어 게시된 **공개 E23 소스 `952ec8da68cdc0ef635d0d45329712eee006fd1f`**로 고정했다. 이전 source에 task-progress 상수만 끼워 넣는 대조가 아니라 해당 공개 파일 전체를 독립 oracle로 사용한다. 이 별도 준비 단계에서는 main·활성 실행 파일이나 모델/GPU를 변경·호출하지 않았다.

그 뒤 E23의 새 팔–옷 관계를 이어 E24를 진행했고, E24가2026-11-07 **05:02:19 UTC** 종료한 것을 확인한 후 root가 후보를 통합했다. E24의 별도 종료 검수 결과는5점·착의0이며, 그 결과를 현재 파지 층이나 특정 실패 원인의 정답으로 사용하지 않는다. [E24 종료 검토](../reviews/20261107-astra-progress1179-named-001.ko.md)

## 무엇을 다시 시험하는가

[E17](../reviews/20261106-astra-layer352-001.ko.md)은 이미 다른 rim 후보로 한쪽 재파지를 시도했지만 반대층·새 양측 지지의 확인에 이르지 못했다. [E21](../reviews/20261107-astra-overhead470-named-001.ko.md)도 테이블 복귀 후 robot1을 다른 노출 경계로 옮겨 닫았으나, 새 지지의 lift/hold 검사 전에 예산이 끝났다. 따라서 **E17의 반대 경계 제어 가설을 더 나은 출발 상태와 확인 순서로 재시험하는 후보**이며 최초의 새 재파지 발명으로 세지 않는다.

준비 단계의 우선 출발 후보이자 E25에 선택한 출발점은 [E18/563](2026-11-07-support-startpoints-review.ko.md), 같은 재실행의 history510/542다. 해당 과거5점과 시각적 양측 지지 검토는 오프라인 선택 근거이며 actor 입력에 전달하지 않는다. 재생 후 현재 지지를 다시 관찰한다. E21의 마지막 미검증 새 파지를 검증된 양측 출발점으로 승격하지 않는다.

이번 비교가 실제 수행됐다고 기록하려면 release→다른 접근 가능한 경계에 배치→reclose가 있어야 한다. 이어서 바뀐 쪽 국소 천 동행, 기존 anchor 유지, 두 경계의 상대 운동/형상에 관한 공개 관측을 남긴다. 같은 corner를 다시 닫거나 기존 grip을 “반대 lip”이라고 이름만 바꾼 경우는 그 조작으로 분류하지 않는다. 선택한 경계가 실제 반대 lip였다는 결론은 별도 근거가 필요하다.

## 선택과 프롬프트

`--mode dressing --strategy coordinated-opposing-rim --plan-size 1`로 선택한다. 다른 mode 또는 plan-size 2/3은 출력 폴더·시뮬레이터 생성 전에 거부한다. [구현](../../../participant/collection/codex_client.py)은 신규 `OPPOSING_RIM_TASK`와 선택 분기만 추가한다.

```text
TASK + COORDINATED_TASK + OPPOSING_RIM_TASK + METHOD_SATURATION_TASK
```

기존 A/B·목 우선·상방·entry-probe·task-progress task를 덧붙이지 않는다. 기존 상수·기본 전략과 실행 함수는 그대로다.

1. **현재 지지를 보존하고 테이블 지지를 복구한다.** 초기 양쪽 open-align-close를 다시 수행하지 않는다. 현재 지정뷰·공개 상태로 몸판을 테이블에 지지하며 두 useful grip을 유지한다. 한쪽을 anchor로 남기고 다른 쪽만 바꾼다.
2. **보이는 다른 경계를 후보로 선택한다.** 연결·접힘·상대 운동을 근거로 anchor 쪽과 반대 경계를 제어할 수 있는 접근 가능한 rim을 고른다. 색·어두운 틈만으로 lip 정체를 확정하지 않고, 재파지 전에 이미 반대층임을 완전히 증명하도록 요구하지 않는다. 목선 재파지 후보가 아니다.
3. **한쪽 재파지1cycle, 짧은 배치 수정 최대2회다.** 몸판의 table support와 유용한 anchor를 release·placement·closing 동안 유지하고 양쪽을 동시에 열지 않는다. 두 번째 release/reclose는 배치 보정이 아니라 두 번째 cycle이므로 허용하지 않는다. 조건이나 접근 가능한 후보가 없으면 실제 재파지 시험을 수행하지 못했다고 기록한다.
4. **닫힘 뒤 검사 시간을 확보한다.** finger 실측·속도·목표와 영상을 함께 보며 잔류 닫힘이나 목표 추종을 고려한다. 필요하면 짧은 중립 관측을 사용한다. close intent·고정 wait·작은 fingertip-origin distance는 부착의 증거가 아니다.
5. **바뀐 쪽 국소 동행과 anchor를 확인한다.** 천을 테이블 가까이 두고 바뀐 그리퍼 중심의 작은 움직임을 수행한다. anchor는 grip/목표를 유지하되 실제 잔류 운동도 확인한다. 로봇 이동·해당 국소 천 동행·천을 통해 전달된 움직임을 구분한다. 새 국소 동행과 유지된 anchor는 잠정적인 양측 지지 판단의 근거가 될 수 있으며 완전한 독립 하중 증명이나 반복 lift-return 인증을 요구하지 않는다.
6. **두 경계의 상대 변화를 검사한다.** 작은 차등 형상 조정으로 후보 경계들이 다르게 움직이거나 분리·제어되는지 관찰한다. 입구 너머 뒤 몸판이 보일 수 있으므로 배경 빈틈을 필수조건으로 두지 않는다. 색이나 큰 주름만으로 새 배치의 정답을 확정하지 않는다.
7. **유용하면 운반·진입을 이어간다.** 현재 손을 향해 몸통 입구로 들어가 해당 소매로 나오는 방향을 유지하며, 그리퍼는 손의 passage 밖에 둔다. 새로운 지지/경계 관계가 계속 미확인이면 table support와 시야/자세를 회복하며 두 번째 재파지나 정보 없는 작은 보정을 반복하지 않는다.

**검사 시간을 확보하라는 지침은 prompt 수준이다.** 수집기가 남은 판단을 자동 예약하거나 close 뒤 지지 시험을 만들어 주지 않는다. 실제 후보를 선택할 때는 초기 재파지·닫힘 관찰·국소 동행·차등 경계 검사에 먼저 예산을 사용하고 긴 운반을 뒤에 배치해야 한다. close에서 예산이 끝나면 새 지지 검증은 미실행으로 기록한다. 같은 unresolved 상태를 오래 조사하는 것이 목표가 아니며 유용한 관계가 드러나면 실제 착의를 이어간다.

## 실행 경계와 미검증 범위

공식 float32(2,9)·[-1,1]·20Hz·최대20step schema, 물리·형상·관절 한계·검증·dispatch·종료·보존 경로를 바꾸지 않는다. Astra/ultra·CLI0.166.0·서비스 설정도 그대로다. named와 pixel-depth-query는 기존 기능이며 기본OFF다. 과거 평가·외부 영상·내부 상태·좌표 정답이나 학습 라벨을 actor에 추가하지 않는다. 같은 source_group의 재생 분기는 정확한 천 checkpoint나 독립 시연이 아니다.

동작 수와 의미 조건은 모델 지침이다. 실제 모델이 다른 경계를 선택하고 한 cycle 상한과 후속 검사 순서를 지키는지, 천 지지가 개선되거나 점수가 오르는지는 CPU 검사로 검증하지 않는다. 이번 준비를 학습 승인이나 실제 M1 성공으로 기록하지 않는다.

## CPU 검사

신규8개 검사는 첫 실행에서 **5.434초에 모두 통과**했다. 고정 공개 기준952ec8d의 **기존12전략×named ON/OFF×query ON/OFF=48조합** prompt/schema/이미지·호출·dispatch·수집 명령 동일성과 기존 상수·`main` 이외 함수 AST 불변을 대조한다. [전용 검사](../../../tests/test_opposing_rim_strategy.py)

별도 후보 준비 단계에서 관련 전략·named·query 회귀까지 합친 실행은 **71개 검사,20.792초,모두 통과**했다. 별도 읽기 검토에서도 재파지 상한·관측 가설·닫힘과 후속 지지 검사 분리·선택 분기의 중요한 미결을 발견하지 않았다. 읽기 검토자는 모델/GPU나 추가 검사를 실행하지 않았다.

**main 통합 뒤 전체 CPU 검사는310개,28.898초,exit0으로 모두 통과했다.** 실제 실행은2026-11-07 05:08:21–05:08:50 UTC이며 외부 subprocess 경과시간은29.179초다. 신규8개와 기존12전략×named/query48조합 비교도 이 전체 실행에서 통과했다.48조합은 한 검사의 내부 사례이며310개에 별도로 더하지 않는다. 실행 전후 client·전용 검사 파일 SHA가 같았다. [전체 검사 receipt](../../project/sessions/20261107-opposing-rim-validation.json)에 source commit·명령·실제 개수/시간·신규8개 결과·로컬 출력 파일 SHA를 기록했다. 전체 출력은 `output/verification/20261107-opposing-rim-full-suite.log`에 보존했다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
```

아래는 별도 작업 트리에서 수행한 기존71개 집중 검사 명령이며, 위 통합 전체 실행과 구분한다.

```bash
PYTHONPATH=.:tests:src/PhyRC_Sim \
  /home/shadeform/workspace/PhyRC_2027_phase1/.venv/bin/python -m unittest \
  test_opposing_rim_strategy test_task_progress_strategy test_entry_probe_strategy \
  test_overhead_strategy test_neckline_strategy test_regrasp_strategies \
  test_support_diagnostic_strategy test_named_actions test_depth_query -q
```

새 선택의 조합 분리·기본OFF·잘못된 mode/plan 사전 거부, trusted threshold10/50·parent/seed 격리를 확인한다. query 후속은 positional/named 모두 같은16이미지(현재 RGB5+과거 RGB10+현재depth1)·공개 clock·frozen ID를 유지하고 timeout180·질의0전이를 확인한다. 합성3재생+3움직임+6settle+예산 stop1은 총13전이다.

별도 fixture는 **gripper-only close8에는 자동 settle/지지 동작이 붙지 않으며**, 다음 모델 판단이 따로 요청한 local movement2 뒤에만 configured settle6이 붙는 것을 확인한다. 두 질의는 각자의 현재 관측에서 물리0이고 총전이는3재생+8닫기+2동작+6정착+1마감=20이다. 이는 실제 지지가 확인됐다는 검사가 아니라 닫힘 명령과 후속 검사 행동을 구분하는 기존 계약의 검증이다.

위 전략·프로토콜 검사는 fake actor/simulator를 사용하는 CPU 검사다. 실제 CLI 호출·GPU·물리·의복 행동·모델 지침 준수·점수 개선은 미검증이다. E24 종료 후 채택·main 통합과 E25 실행 계획이 정해졌으며, CPU 통과를 실제 시행이나 성공으로 표시하지 않는다.
