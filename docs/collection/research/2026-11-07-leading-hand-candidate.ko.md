# M2: leading hand·guide/anchor 교환과 다른 body-entry 접근 후보

2026-11-07 준비 기록. 아래 설계·집중 검사는 **당시 미채택·실제 모델/물리 실행 전 후보**의 이력이다. 준비 중에는 E25의 opposing-rim 실험과 진전을 우선하며 활성 main·actor·시뮬레이터에 적용하지 않았다. 고정 공개 기준은 `68658c9d9bb7e47591fb330f08f4f996ec4fcbfb`, 격리 브랜치는 `experiments/leading-hand-candidate`다. **E25 종료 뒤의 main 통합·E26 채택 기록은 맨 아래에 별도로 구분한다.**

## 기존 방법과 구별할 실제 변화

[M2 원래 검토](2026-11-07-post-overhead-method-options.ko.md#m2-목표손역할식별의-추가검토)에서 E19의 한쪽 높이·roll·시점 조정과 E21의 비대칭 보정은 이미 수행됐다고 구분했다. 따라서 한 로봇만 움직이거나 두 로봇의 행동 크기가 다르다는 이유로 새 M2 수행으로 세지 않는다. 일반 task-progress는 현재 유용한 목표를 계속 선택하지만, 이 후보는 **구별되는 다른 손·역할 교환·상대 접근면 변경을 함께 시험하는 방향**을 명시한다. 프롬프트 선택만으로 그 조작이 실제 수행됐다고 보장하지 않는다.

| 비교축 | 현재 공개 관측에서 필요한 근거 | 불충분한 근거 |
|---|---|---|
| Leading hand | 연결된 팔과 상대 위치로 현재 접근하던 손과 다른 손을 구별하고, 선택한 손을 후속 접근에서도 추적 | 다른 카메라에 보임, 해부학적 좌우 추측, 손 이름만 교체 |
| Guide/anchor | 관측 가능한 기존 역할에서 실제 역할을 바꾸고, 해당 경계를 움직이며 partner 지지를 유지 | 역할 이름 변경, zero 명령을 정지로 간주 |
| Body-entry 접근 | mouth–손의 상대 배치/방향을 바꾼 뒤 해당 손을 향한 실제 접근 | 카메라만 이동, 같은 외면 가림을 작은 lift/roll로 반복 |

이 세 축은 별도로 검토한다. 현재/최근 관측에서 이전 목표를 구별할 수 없으면 기존 짧은 `reason`에 `hand swap unestablished`를 기록한다. 유용한 목표 접근은 계속할 수 있지만, 그런 **일반 task-progress로의 진행을 M2 완료나 실제 손 교환으로 세지 않는다.** 역할의 이전 상태·교환이 미확인이면 그것도 별도 한계로 남긴다. 새 schema·성공 라벨·자동 M2 판정기를 추가하지 않는다.

## 후보 지침과 과도한 gate 방지

새 선택지는 `coordinated-leading-hand-swap`이다. `TASK + COORDINATED_TASK + LEADING_HAND_SWAP_TASK + METHOD_SATURATION_TASK`만 조합하고 dressing·plan-size1로 제한한다. 기존 grasp를 유지하고 **새 재파지0회**이므로 M1의 반대 rim 재파지나 목선 재파지와 섞지 않는다. 현재 유용한 지지가 있으면 최초 양손 open/close 절차를 반복하지 않는다.

현재 구별되는 손과 그립 배치를 보고 guide/anchor를 정한다. 과거 E19의 특정 robot 역할·손 정체·좌표·이미지를 actor에 주입하지 않으며, 로봇을 교차시키거나 특정 robot을 guide로 고정하지 않는다. 손은 **body opening으로 들어가 같은 손의 대응 sleeve로 나오는 방향**을 유지한다. cuff 밖에서 거꾸로 넣는 방법은 해당하지 않는다.

손 둘이 한 화면에 보이거나 입구 전체·배경 빈틈이 확인돼야만 움직일 수 있다는 gate는 두지 않는다. 현재 공개 관계에서 방향과 유용한 지지가 뒷받침되면, 실제 관절/목표·남은 이동·최근 실측에 맞춘 한 구간의 유한한 배치 또는 진입 행동을 선택한다. 기존 최대20step·각0.05초 안에서 관측에 맞춰 짧게 정하며 고정 거리나 정답 방향은 없다. 부분 가림 구간을 한 가설 아래 시험할 수 있지만 여유/inside/통과를 사실로 승격하지 않는다.

다음 관측에서 로봇 실측·잔류·천 동행·손–경계 상대 변화·과제 진전을 분리한다. 시각 선명도 증가만을 진전으로 요구하지 않으며, 가림 구간을 무제한 연쇄 허용하지도 않는다. 같은 관계에서 무효 보정이 반복되거나 지지 약화·변형 악화·실측 포화가 있으면 파지를 열지 않고 지지된 자세/시야/접근을 복구한다. 새 지지 파지가 필요하면 이번 후보 범위의 한계로 남긴다.

이는 불확실성 아래 역할·목표·접근 선택을 유도하는 프롬프트 비교다. 실제 손 교환·다른 접근면 수행, 착의 성과, 지침 준수 여부는 후속 공개 실행 자료에서 검토해야 한다. [의복 방향 가설](2026-11-07-garment-direction-hypotheses.ko.md)처럼 관측된 경계를 hem/neck/cuff로 확정하거나 world 상하를 재료 방향으로 대체하지 않는다.

## 변경·검증 범위

소스 변경은 [client](../../../participant/collection/codex_client.py)의 새 문자열 상수와 선택 분기뿐이다. [전용 CPU 검사](../../../tests/test_leading_hand_strategy.py)는 고정 공개 기준의 전체 client를 로드한다. 기존13전략 × named ON/OFF × query ON/OFF **52조합**에서 actor prompt·schema·이미지/요청·호출 순서·실행 명령을 비교하고, 기존 모든 상수와 `main` 외 함수/클래스의 AST 불변을 확인한다. 52조합은 한 검사 안의 하위 경우이며 별도52개 테스트로 세지 않는다.

새 선택지에서는 경쟁 task 혼입 없음, 기존 schema와 최대20step, query 동안 물리0·같은16이미지/관측시각·후속 action-only 응답, named 정규화, 실제 act/별도 settle/cleanup 경계를 검사한다. `hand swap unestablished`라는 이유를 가진 합법적인 fake act도 그대로 실행되어 새 의미 판정 gate나 암묵적 역할/재파지 명령이 없음을 확인한다. trusted 점수 임계·parent/seed가 actor prompt에 들어가지 않는 경계와, 잘못된 mode/plan을 simulator 생성 전에 거부하는 경계도 포함한다.

공식 float32(2,9)·[-1,1]·20Hz·물리·actuation·dispatch·settle·관측 도구·모델/service/CLI 설정은 변경하지 않았다. Astra/ultra 고정 설정을 유지한다. 모델/GPU 호출은0회이며 CPU 통과는 실제 손 식별·역할 교환·성과 검증이 아니다.

고정 oracle client의 SHA256은 `c567927658dfe3b713b10b04b5bc4ee82722fb98171cbd853d78c2237b12f943`이다. 2026-11-07T05:25:07–05:25:25UTC에 아래 집중 회귀를 실행해 **77개·18.052초 PASS**(프로세스 외부 wall18.298초)를 확인했다. 신규 전용 검사는7개이며 기존 opposing-rim/task-progress·depth query·named action·client·continuation 회귀를 함께 실행했다. 저장소 전체 검사를 다시 실행한 결과로 표현하지 않는다.

```bash
PYTHONPATH=.:src/PhyRC_Sim:tests /home/shadeform/workspace/PhyRC_2027_phase1/.venv/bin/python -m unittest test_leading_hand_strategy test_opposing_rim_strategy test_task_progress_strategy test_depth_query test_named_actions test_codex_client test_collection_continuation -v
```

격리 worktree 로컬 로그는 `output/verification/20261107-leading-hand-focused.log`(13,989bytes, SHA256 `2e137ce70835e940f4509d9647dc49ea90177713f08a22096a7ca86590e0e4be`)다. 테스트는 fake actor/simulator만 사용하며 실제 모델/GPU·착의 평가를 실행하지 않았다.

## 준비 당시 조건부 실제 비교안

E18/787·history719/771, 22decisions·max1400은 준비 당시 root가 후속 결과를 보고 선택할 수 있는 예비 조건이었다. 출발 원본·현재 지지·잔류를 재검토하며, 같은 E07 계보의 반복 분기이지 독립 시연이나 정확한 천 checkpoint가 아니다. 당시 E25 진전을 우선해 후보의 병합·실행을 선택하지 않았다. 점수는 trusted 오프라인 선택에만 사용하며 actor 입력에 추가하지 않는다. 새 원본 수집·학습·자동 조합은 이번 변경에 포함하지 않는다.

## E25 종료 뒤 채택·통합 · E26 아직 미실행

root가 E25의05:38:26UTC 종료를 확인한 뒤 후보 `3d1bf2c4e1d13a342f73869be3348ac441f4903c`를 main `bd92e931b338fdc636f26a6633e9c37a461c1ac0`에 통합했다. 다음 E26은 **E18/787·history719/771·coordinated-leading-hand-swap·22decisions/max1400·settle6**로 선택했다. 이 기록 시점에는 실제 M2 실행·손 교환·착의 성능을 검증하지 않았다.

[E25 중립 구간 분석](../reviews/20261107-astra-opposing563-named-001-settle.ko.md)의 자동 정착12는 유용한 비교 후보로 남긴다. 이번에는 기존 정착6을 유지하여 새로운 방법과 관측 시점/물리 시간을 동시에 바꾸지 않는다. task-progress로 유용한 이동이 있었더라도 hand/role/approach 세 축의 실제 변화가 확인되지 않으면 M2 수행 완료로 기록하지 않는다.

통합 뒤 전체 CPU 검사를 실행해 **317개·31.785초 PASS**(프로세스 외부 wall32.091초)를 확인했다. 신규7개와 기존13전략×named/query52조합 검사도 이 전체 실행에 포함됐다. 실제 개수·시간·원본 로그 SHA·검사 당시 source는 [검증 receipt](../../project/sessions/20261107-leading-hand-validation.json)에 기록한다. 이는 준비 당시77개 집중 검사와 구분하며, 실제 모델/GPU·착의 성능 검증을 대체하지 않는다.

격리준비당시3파일은[고정비공개연구백업](../../project/sessions/20261107-m2-candidate-backup-verification.json)에별도로보존했다. 당시미통합상태의receipt는이후E26채택/통합이력과구분한다.
