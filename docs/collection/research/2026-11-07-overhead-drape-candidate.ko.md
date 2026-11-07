# 몸통 입구 상방 배치·하강 후보

**E20 종료 후 main에 통합하고 전체277CPU검사를 통과했다. 실제 모델 행동·GPU·착의 효과는 아직 검증하지 않았다.** 아래 후보 개발 당시에는 활성 E20와 분리한 worktree `../phyrc-overhead-candidate`, branch `experiments/official-overhead-candidate`에서 공개 기준 `f9271fb3b7b968cb12a8391a2d30e4f67241a4ee`를 바탕으로 준비했다. 당시 E20 실행 소스·입력이나 공식 물리·형상·행동 한계는 변경하지 않았다. E20 종료 뒤 통합 검증은 문서 마지막에 기록했고 실제 시작 상태는 STATUS를 우선한다.

## 참고와 비교할 실제 행동

[공식 과제 페이지](https://emprise.cs.cornell.edu/phyrc/challenge-2027/#task-details)의 [overhead teleoperation 영상](https://emprise.cs.cornell.edu/phyrc/assets/c27/media/teleop-overhead.mp4)은 두 가장자리 지지·몸 앞 운반·머리/팔 부근 상방 배치·몸판 하강을 보여 준다. 2026-11-07 재다운로드 SHA256은 기존 보존본과 같은 `96ed735d0bca97eac758c534175133b1ea8dd01e11f59c376611c8a672b93c09`다. 후반에 두 손이 외부에 보이는 동안 얼굴은 가려지지만, 그 사실만으로 실제 소매·목 통과의 선후관계를 확정할 수 없다. **후보도 어느 통과를 반드시 먼저 완료하도록 요구하지 않는다.**

기존 [E07·E15의 공동 lift](2026-11-06-post-support-methods.ko.md)와 [E18의 큰 lift·운반](../reviews/20261106-astra-guide470-depth-001.ko.md)은 이미 수행했다. 이번 비교점은 단순한 상승량 증가가 아니라 **몸통 입구와 머리·든 팔의 상하 관계를 실제로 바꾼 뒤, 관측을 따라 몸판을 내려 가슴에 안착시키는 구간**이다. 그 단계에 이르지 못하면 준비 실패로 기록하며 새 착의 방법을 수행했다고 부풀리지 않는다.

[목 우선 후보](2026-11-06-neckline-first-candidate.ko.md)는 유용한 목선 파지를 보존할 수 있으므로 무조건 재파지를 강제하지 않는다. 다만 목 입구 제어와 머리 우선 순서를 명시한다. 이번 후보는 현재 유용한 몸통 입구 지지를 유지할 수 있고, 목선으로 파지를 옮기거나 첫 소매를 먼저 완료하는 것을 전제로 두지 않는 별도 목표다.

## 선택과 최종 프롬프트 구성

선택지는 `--mode dressing --strategy coordinated-overhead-drape --plan-size 1`이다. 다른 mode와 plan-size 2/3은 출력 폴더·시뮬레이터 생성 전에 거부한다. [구현](../../../participant/collection/codex_client.py)의 신규 상수는 `OVERHEAD_BASE_TASK`, `OVERHEAD_TASK` 두 개다.

`OVERHEAD_BASE_TASK`는 공통 `TASK`의 목표 순서와 소매 협업 문장 두 곳만 이번 선택지용으로 바꾼다. 기존 행동 계약 문단은 그대로 사용한다. 최종 조합은 **OVERHEAD_BASE + COORDINATED + OVERHEAD + METHOD_SATURATION**이다. `NECKLINE_TASK`, `SLEEVE_TASK`, 첫 소매를 우선하는 `HEM_ROUTE_TASK`, 기존 A/B task를 덧붙이지 않는다.

- 현재 파지가 몸통 입구의 유용한 지지라면 유지하고 불필요한 처음부터 열기·정렬·닫기를 반복하지 않는다. 각 그리퍼의 실제 이동과 국소 천 동행을 구분하며 양측 지지를 확인한다.
- 불분명한 경계는 작은 지지 유지 형태·시야 변경으로 확인할 수 있다. 새 파지가 필요하면 몸판을 테이블에 지지한 채 한쪽 변경 1회, 짧은 배치 보정 최대 2회로 제한한다. 파트너가 불확실해도 테이블 지지는 계속 유지하며 양쪽 동시 해제는 금지한다. 운반 전 두 지지·몸통 입구를 다시 확인한다.
- 현재 지정 영상의 머리·든 팔·천·그리퍼 관계와 공개 관절 실측·목표·최근 이동을 사용해 가능한 상방 배치와 여유를 판단한다. 목표나 실측 이동이 포화됐을 때 같은 방향 lift/arm 명령을 누적하지 않는다. 높은 목표값을 머리 위 여유로 해석하거나 고정 세계 높이를 공급하지 않는다.
- 경계와 진행 공간이 보일 때 한 구간씩 관계를 바꾸고 하강·안착을 관측한다. 관측 가능한 하강에 앞서 목이나 소매 통과 완료를 요구하지 않는다. 한 카메라의 가림은 통과 증거도 자동 종료 이유도 아니다. 다른 CURRENT 지정뷰와 최근 공개 관측·실측 운동으로 같은 경계와 경로를 재확인하고, 현재 관계·여유·방향이 추적될 때만 짧은 지지된 상승·하강을 허용한다. 과거만으로 현재 여유를 승인하지 않는다. 지정뷰 전체에서도 경로가 모호하거나 몸통 입구 진입과 외부 패널 누름을 구별하지 못하면 밀기를 멈추고 지지된 시야·접근을 회복한다.
- 실제 관계가 개선되면 양 소매·목·어깨·상완·앞면까지 전체 착의를 이어간다. 실행·관측 2–3회에도 같은 가림·접힘만 남으면 작은 속도·기간 변경만 반복하지 않는 공통 포화 원칙을 유지한다.

이는 프롬프트 지침이며 새로운 강제 제어기나 성공 판정기가 아니다. 모델이 실제로 유용한 개구를 식별하고 제한을 준수할지는 후속 실행에서 확인해야 한다. 관측 도구·기록 경로·응답 schema·검증·dispatch를 바꾸지 않았고 Astra/ultra 기본값과 CLI 실행 경로도 그대로다. named 및 pixel-depth-query는 기존 선택 기능과 호환하며 기본 OFF다. 질의는 같은 현재 공개 depth의 보이는 표면만 읽으며 가림·의복 위상·통과 판정을 제공하지 않는다.

## CPU 검사

다음 명령으로 **49개 검사 통과**했다. 신규 7개와 기존 목 우선·A/B·지지 진단·named·depth 42개다. 가상환경은 루트에서 제공했지만 실행 디렉터리와 변경 파일은 후보 worktree에 한정했다. 최초 정상 검사 뒤 검토에서 단일 카메라 가림과 전체 경로 불명확을 구분하도록 후보 문구를 좁혔고, 최종 문구에서도 같은 검사를 다시 수행했다.

```bash
PYTHONPATH=.:tests:src/PhyRC_Sim \
  /home/shadeform/workspace/PhyRC_2027_phase1/.venv/bin/python -m unittest \
  test_overhead_strategy test_neckline_strategy test_regrasp_strategies \
  test_support_diagnostic_strategy test_named_actions test_depth_query -q
```

[신규 검사](../../../tests/test_overhead_strategy.py)는 다음 경계를 확인한다.

1. 새 선택지의 task 분리, 순서 충돌 제거, 기존 행동 계약과 prompt hash 기록.
2. 고정 기준 `f9271fb`의 기존 상수·클래스·`main` 이외 함수 AST 불변. 기존 9전략 × named ON/OFF × depth query ON/OFF의 36설정에서 실제 준비된 prompt/schema/16이미지/호출·dispatch 순서/시뮬레이터 명령을 고정 기준과 비교해 동일함.
3. 새 전략의 기능 기본 OFF, 기존 행동 schema, 비착의/다중 행동의 사전 거부, 평가 임계값·재실행 seed·계보가 actor prompt에 들어가지 않음.
4. 새 전략의 query→행동 후속에서 positional/named 모두 같은 16이미지·공개 시계·frozen ID 유지, timeout180, 질의 중 dispatch0, 후속을 기존 float32 배열로 검증한 뒤 실행. 합성 3재실행+2행동+기존 예산 종료 중립1을 구분함.

첫 검사 실행의 실패 2개는 마지막 항목의 **예산 종료 중립1전이를 기대값에서 누락한 테스트 오류**였다. 기존 수집기는 마지막 `act` 뒤 판단 예산이 끝나면 `stop` 후 `finish_episode`로 마감한다. 실행 코드를 바꾸지 않고 기대 순서와 총전이를 보정해 통과했다. 실제 질의·물리 실패나 모델 행동 결과가 아니다. 전체 저장소 검사·실제 모델 프로토콜·GPU wiring·과제 성능 검증을 이번 49개 CPU 검사로 대체하지 않는다.

외부 자유 시점 영상·프레임·좌표·궤적·평가값은 actor나 학습 입력에 추가하지 않았다. 영상은 개발 단계의 일반적인 경로 설계 참고로만 사용하며 현재 표적·여유·행동은 지정 RGB-D와 공개 로봇 상태에서 판단한다. 최종 프롬프트 검토와 E20 종료 후 선택이 남아 있다. [공식 정보 경계](https://github.com/rirolab/PhyRC_2027_Challenge/blob/main/docs/competition/RULES.md)

## E20 종료 뒤 통합 검증

E20은 목선 후보 두 곳의 재파지·입구 확인 뒤 운반 전에 종료했다. 이 결과를 확인한 후 f148d6 후보를 루트 main에 병합했고 전체277CPU검사를12.745초에 통과했다. 로그 SHA256은`ae4af21a8deafc14b4f69ffc0b17703e143761b799b155f57ebb59c79a36153f`다. 위49검사는 후보 당시 범위이며 이277검사와 구분한다. 독립 읽기 검토에서도 선행 순서·현재 관측·기존 실행 계약의 중대한 충돌은 발견하지 못했다. 실제 모델/GPU 과제는 아직 미실행이며 E21 시작 여부는 [현재 상태](../../project/STATUS.md)를 우선한다.

E21 실제 과제는2026-11-07 01:56:25UTC에 공개main d383063·시작clean에서 시작했다. E18/470·hist430464·named+query를 사용하며 현재 결과는 미확정이다. 위 후보/CPU 단계 설명은 해당 시점의 이력이고 실제 시행은 STATUS·세션일지를 우선한다.
