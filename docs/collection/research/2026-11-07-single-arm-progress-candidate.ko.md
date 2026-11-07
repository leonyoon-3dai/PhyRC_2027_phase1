# 같은 팔의 진행을 유지하는 목표 순서 · 격리 후보

**조건부·미채택·main 미통합 후보**다. E27 실행 중 공개 기준 `18f307dcadd7a323debb7fd26e99f6da6d4cc045`에서 별도 `experiments/single-arm-progress-candidate` 브랜치로 준비했다. 현재 실행·손목 방향 보조 후보를 바꾸지 않았고 GPU·실제 actor 호출·득점 검증은 하지 않았다. 새 grasp나 새 관측 도구가 아니라 **같은 팔을 향한 목표 순서의 비교**다.

## 근거와 비교 범위

고정 기준에 실린 [E27 공개 검토](../reviews/20261107-astra-regrasp698-progress-named-001.ko.md)는 D9 뒤928경계에서 줄무늬 전완이 큰 노란 경계의 간격을 가로질러 보이는 새 관계, D10 뒤950에서 그 접근 지속과 몸판 가림 증가, D11 뒤968에서 다른 노출 손으로의 목표 전환을 기록한다. `second_sleeve`라는 단계는 실제 첫 소매 exit 확인이 아니다. 첫 팔의 연속성·입구 정체·소매 통과는 이 시점에 미확인이다. **목표 전환이 실패의 원인이라는 인과 결론도 내리지 않는다.**

이 문서의 고정 공개 근거 cutoff는 D11/968이다. 준비 요청자가 전달한 이후 행동·실행 결과를 actor 문구나 확인된 성공/실패 근거로 추가하지 않는다. E27이 계속 새 관계를 만들면 그 진행을 우선한다. 종료 뒤928 근처의 연속 분기가 논의될 수 있지만, 정확한 source boundary·history·예산은 아직 선택하지 않았다. 행동 재실행은 같은 천 checkpoint가 아니며 새 실행의 현재 관측에서 팔·지지를 다시 판단한다.

기존 `TASK_PROGRESS_TASK`는 부분 관측 아래 유한한 목적 동작을 허용하지만, 매 판단에 선택한 목표가 같은 팔을 이어가도록 명시하지 않는다. 이번 후보는 현재 가장 유용한 팔–몸통 입구–전완 관계를 actor가 직접 고르고, 그 팔의 진입과 해당 소매/어깨 방향 진행을 유지하게 한다. 검수자가 고른 손 identity·픽셀·좌표·과거 성공 라벨을 전달하지 않는다.

## 새 선택지의 의미

`--strategy coordinated-single-arm-progress`는 dressing·plan-size1에만 허용한다. [실제 문구와 선택 분기](../../../participant/collection/codex_client.py)는 다음을 한 번씩 조합한다.

```text
TASK + COORDINATED_TASK + TASK_PROGRESS_TASK
     + SINGLE_ARM_PROGRESS_TASK + METHOD_SATURATION_TASK
```

기존 task-progress 원문을 그대로 재사용한다. 다른 `HEM_ROUTE_TASK`·`SUPPORT_GUIDE_TASK`·목 우선·overhead·leading-hand-swap·opposing-rim task는 붙이지 않는다.

- actor가 현재 공개 다중뷰와 같은 episode의 과거 관측을 이용해 연결된 손/전완을 추적한다. 카메라 소유 로봇이나 지정된 해부학적 좌우로 손 identity를 대신하지 않는다.
- 같은 손의 **body-opening 진입 → 같은 전완 → 해당 sleeve/shoulder 방향**을 이어간다. 외부 cuff에서 역방향으로 밀어 넣기를 같은 작업으로 세지 않는다. 진입 전에 cuff가 반드시 보여야 하는 것은 아니다.
- 손 재노출·피부색·겹침·단계 문자열만으로 첫 팔 완료를 선언하거나 다른 팔/머리로 전환하지 않는다. 같은 손/손목의 경계 연결과 상대 운동을 비교하되 전체 경로를 한 장에 동시에 볼 것을 요구하지 않는다.
- 부분 가림에서도 기존 task-progress의 한 구간 유한 동작과 다음 관측을 허용한다. 완전한 lip 식별·빈 배경·즉각적인 시야 개선·고정 두 번 보정 뒤 중단을 새 gate로 추가하지 않는다.
- 다른 팔은 여유·시점·몸판 지지를 판단하는 데 사용할 수 있고 로봇 guide/support 역할도 바뀔 수 있다. 이를 목표 팔 교환 완료로 자동 집계하지 않는다.
- 현재 공개 근거가 의도한 sleeve-exit 관계를 지지하거나, 유용한 복구 뒤 현재 팔 목표가 비생산적/부적합해지면 이유를 남기고 다른 목표로 바꿀 수 있다. 불확실성은 미확인으로 남긴다. **첫 팔의 완료가 불확실하다는 이유로 영구 고착하거나 자동 finish하는 정책이 아니다.**

그립 변경은 기존 task-progress와 같은0회 범위다. 기존 short `reason`에 현재 팔 관계·목적·불확실성을 적도록 할 뿐 출력 schema·stage enum·상태기계·행동 validator를 추가하지 않는다. 따라서 `second_sleeve`나 `neck` 단계 문자열을 runtime에서 차단하거나 시각 정답으로 해석하지 않는다. 실제 순서 변화와 관련 관계 진전은 추후 공개 행동·관측으로 검토해야 한다.

## 불변 범위와 CPU 검사

변경 파일은 client의 새 문자열·선택 분기, [전용 검사](../../../tests/test_single_arm_progress_strategy.py), 이 문서의3개다. 기존 상수·실행 함수·관측/질의/보존 의존성은 바꾸지 않는다. 고정 Astra/ultra·CLI0.166.0·공식 float32(2,9)·[-1,1]·20Hz·최대20steps·관절/물리·configured settle·named/query 기본값은 유지한다. wrist 방향 보조는 이 브랜치에 통합하지 않았다.

전용 CPU 검사는 선택 task의 정확한 조합·경쟁 task 배제, 공개 기준 대비 기존 상수/비선택 함수 AST 불변, 기존14전략×named/query ON/OFF의56조합 prompt/schema/이미지/호출/dispatch 동등성, 새 전략의 불확실 reason·단계 문자열이 runtime gate가 되지 않는 점, 동일16 frozen 이미지/clock·named 정규화·질의 물리0·20step act와 별도 settle6, malformed/재질의/중단의 act 미실행, trusted 점수·계보 격리, 잘못된 mode/plan의 실행 전 거부를 포함한다. 56조합은 하위 검사이며 unittest 개수에 별도로 더하지 않는다.

전용8개는5.911초에 통과했다. 이어2026-11-07T07:33:26–07:33:45UTC에 아래 집중 묶음 **64개·19.041초 PASS**(외부 wall19.281초)를 확인했다. 새8개와 기존 task-progress/leading-hand/query/named/client 회귀를 포함한다. 기존14전략의56설정은 새8개 중 한 unittest 안의 하위 조합이다.

```bash
PYTHONPATH=.:src/PhyRC_Sim:tests /home/shadeform/workspace/PhyRC_2027_phase1/.venv/bin/python -m unittest test_single_arm_progress_strategy test_task_progress_strategy test_leading_hand_strategy test_depth_query test_named_actions test_codex_client -v
```

격리 작업 트리의 로그 `output/verification/20261107-single-arm-focused.log`는11,884bytes, SHA256 `7bd11354af673854f8990534d82b5035e39a0e9382c196f60e9f2315fde0a538`다. 같은 디렉터리의 `20261107-single-arm-focused.json`에 명령·실제 시각·전후 소스 hash 불변을 기록했다. client SHA는 `24e8be926e326b5c67465c2af82e00c5207dbd875709d752c0e994517e20d4cd`, 전용 test SHA는 `ff560282ba02225405c94735e4e916c234330573923e501bdc5cbaa07fda186f`다.

추가로2026-11-07T07:35:13–07:35:52UTC, 같은 격리 코드에서 아래 **전체325개·38.190초 PASS**(외부 wall38.534초)를 확인했다. 전용8개가 포함된 실제 unittest 총수다. 모든325개 결과를 확인했고 실패·skip은 없었다. Git 추적 Python 및 config JSON166파일의 전후 bytes/SHA가 같았고 작업 트리는 깨끗했다.

```bash
PYTHONPATH=.:src/PhyRC_Sim /home/shadeform/workspace/PhyRC_2027_phase1/.venv/bin/python -m unittest discover -s tests -v
```

전체 로그 `output/verification/20261107-single-arm-full-suite.log`는57,430bytes, SHA256 `2c4b4ed657905dcdaa00c8c9bd9586181920a2ead2d3267e18697d121d214481`다. 같은 이름의 JSON receipt에 전체 명령·시각·검사 시점 commit/tree·166파일 전후 fingerprint를 보존했다. 전체 검사는 준비 commit `3869acadc449458b2d8043e590ec560a3c47059d`에서 실행했으며, 이후 최종 후보를 만들 때 이 문서에 결과만 보충했다. 위 client/test SHA와 실행 코드는 그대로다. 향후 통합 검토에서는 실행 파일 hash를 대조해 이 검사와의 동일성을 확인할 수 있다.

이는 **격리 후보의 전체 검사이며 root 통합 검사는 아니다.** 실제 CLI/model·GPU/physics 시험은 수행하지 않았다. CPU 통과는 실제 actor의 목표 유지·팔 추적·소매 통과·득점 향상을 검증하지 않는다. 선택·통합·실제 비교는 E27 종료 뒤 별도 결정한다.
