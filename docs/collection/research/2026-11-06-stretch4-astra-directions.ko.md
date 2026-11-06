# Stretch 4·Georgia Tech Astra 연구에서 가져올 다음 비교

**2026-11-06 조사. E13은 손목 depth 패널을 실제 사용했지만 원점수 5/50·첫 소매 0·착의 `success=false`로 종료됐습니다.** 810/810전이 기술 검사를 통과했으며 10점은 미달성입니다. 아래 외부 연구는 다음 실험의 근거이고 이미 적용한 성능 개선이 아닙니다. 공식 웹·논문과 GitHub connector로 문서·관련 소스만 읽었으며 설치·가중치 다운로드·모델·GPU 실행은 하지 않았습니다. [E13 실제 결과](../../gallery/20261106-astra-hem-depth-001.ko.md) · [최종 manifest](../attempts/20261106-astra-hem-depth-001/manifest.json)

## 1. 찾은 연구: 같은 Astra, 다른 제어 인터페이스

사용자가 언급한 연구는 Georgia Tech RAIL Lab의 **Astra Beyond Tabletop: Into the Home**과 일치합니다. 공식 연구실은 2026년 10월 글로 소개하며, 본문은 `gpt-6-astra`를 Codex CLI로 사용했다고 명시합니다. Google Project Astra와 구분합니다. [공식 연구실](https://www.gt-rail.com/) · [연구 본문·부록](https://www.gt-rail.com/blog/astra-beyond-tabletop/)

| 연구에서 확인한 것 | 적용할 때 구분할 것 |
|---|---|
| 실제 단일 Stretch 4, 가정 작업 24종 | 두 로봇·티셔츠 착의 벤치마크가 아님 |
| 상대 위치·각도 명령과 `completed`, `stopped_short`, `timeout`, `rejected` 결과 | 우리는 정규화 속도와 제한된 전이 수를 명령함 |
| 명령 종료 뒤 모든 카메라의 새 프레임 수신 | 우리의 전이 종료가 관절 목표 도달을 뜻하지는 않음 |
| RGB 픽셀을 지정해 wrist depth 조회 | API는 Euclidean range·cm; 우리 입력은 optical Z·m |
| 정밀 접촉·시야 가림·이전 파지를 재검토하지 못하는 실패 | 국소 접근 반복뿐 아니라 초기 파지의 후속 실행 가능성도 비교할 근거 |

오븐 작업의 depth 비교는 **조건당 5회**입니다. API/이미지/무깊이 성공은 각각 **3/5·1/5·2/5**, 평균 호출은 **49.6·63.8·66.6회**였습니다. 연구진은 이미지 조건의 RGB 정렬 문제를 원인 후보로 제시했습니다. 우리 고정 범위 패널의 실패를 입증하지 않으며 표본도 작습니다. `high`보다 `ultra`가 낫다는 체계적 이점도 보고하지 않았지만, 이 결과만으로 우리 설정을 바꾸지 않습니다. 공개 자료는 연구 블로그이며 확인한 본문에는 연구 코드 GitHub 링크가 없고 프롬프트·schema·API·실험 표가 있습니다. [방법·한계·ablation·부록](https://www.gt-rail.com/blog/astra-beyond-tabletop/)

## 2. 공식 Hello Robot 저장소: 그대로 설치할 묶음이 아닌 설계 참고

| 공식 저장소 | 확인한 기능 | 우리 과제와의 차이 |
|---|---|---|
| [stretch4_grasping_demo](https://github.com/hello-robot/stretch4_grasping_demo/blob/main/README.md) | Molmo 2의 대상 픽셀 → SAM 2 추적·분할 → wrist depth·손끝 좌표계 기반 FSM 시각 제어 | 물체 집기 데모. 장애물 회피가 없으며 옷 구멍·손 통과 판단은 제공하지 않음 |
| [stretch4_kinematics](https://github.com/hello-robot/stretch4_kinematics/blob/main/README.md) | Pinocchio FK/IK, 가중 Jacobian, task-space 위치 추종과 관절 속도 출력 | 개발 중·제한된 시험이라고 명시. 우리 공식 행동·축·한계와 연결하는 검증이 필요 |
| [stretch4_flying_gripper](https://github.com/hello-robot/stretch4_flying_gripper/blob/main/README.md) | 그리퍼 좌표계 이동과 base 평면 투영 이동, 가중 감쇠 의사역행렬·관절 한계 근처의 base 협조 | 카메라에서 보이는 방향과 관절 축을 연결하는 참고. 실제 기체의 가중치·한계를 그대로 복사하지 않음 |
| [stretch4_urdf](https://github.com/hello-robot/stretch4_urdf/blob/main/README.md) | Stretch 4 로봇·도구 설명, frame 변환, calibration·광학 좌표계 문서 | 로봇의 정적 좌표계 참고용. 경기 로봇 자산을 교체하거나 옷·사람 내부 기하를 얻는 수단이 아님 |
| [stretch_ai](https://github.com/hello-robot/stretch_ai/blob/main/README.md) | LLM agent·집기·이동 등의 기존 통합 코드 | README의 개발·시험 중심은 **Stretch 3**. Stretch 4 전용 제어기로 간주하지 않음 |

Grasping demo의 `--move_to_front`는 옆으로 이동하며 대상의 보이는 폭이 작아지는 방향을 찾는 선택 기능입니다. 옷에서는 폭 감소가 유용한 정면 정렬 대신 접힘·입구 축소일 수 있습니다. **이 탐색 규칙을 소매나 밑단에 그대로 적용하지 않습니다.** [README](https://github.com/hello-robot/stretch4_grasping_demo/blob/main/README.md) · [FSM 단계와 정착 조건](https://github.com/hello-robot/stretch4_grasping_demo/blob/main/visual_servo_fsm_params.py)

## 3. 구현에서 특히 구분할 네 가지

**명령 종료와 물리 정착.** E13의 6전이 중립 명령도 기존 리프트 목표를 향한 움직임을 이어갔습니다. `controller_target`과 실제 위치·속도를 함께 보아야 합니다. 실제 로봇의 `stopped_short`를 우리 관절 잔차만으로 만들어 접촉 라벨로 쓰지 않습니다. 추가 중립 시간은 정착을 보장하지 않으며 천도 움직일 수 있습니다. [E13 완료 행동](../attempts/20261106-astra-hem-depth-001/decisions.jsonl)

**광학축 Z와 카메라까지의 거리.** E13 패널은 0.03–1.20m의 Z를 고정 밝기로 표시합니다. 픽셀의 카메라 XYZ를 계산할 때도 intrinsics와 축을 사용해야 합니다. 예를 들어 optical frame에서 `X=(u−cx)Z/fx`, `Y=(v−cy)Z/fy`이며 Euclidean range는 `sqrt(X²+Y²+Z²)`입니다. GT의 cm 수치·손끝 거리 안내를 우리 Z·기하에 그대로 대입하지 않습니다. 무효 depth는 `null`로 유지하고, RGB·depth의 시각·픽셀 대응을 먼저 확인합니다. [우리 depth 의미·변환 검토](2026-11-06-wrist-depth-input.ko.md) · [공개 인터페이스](../../../config/policy_interface.json)

**화면 중앙과 손끝 기준 오차.** Hello Robot의 기존 [issue #18](https://github.com/hello-robot/stretch_ai/issues/18)은 화면 중앙 맞추기와 고정 카메라 거리 접근의 문제를 지적합니다. 손가락이 닫히면 손끝 위치·깊이도 달라집니다. 최신 demo는 높이 정렬 등에서 대상과 손끝 중심의 3D 차이를 사용하지만 일부 시야 정렬에는 화면 중앙도 사용합니다. 모든 단계가 손끝 기준이라고 확대해석하지 않습니다. [실제 FSM](https://github.com/hello-robot/stretch4_grasping_demo/blob/main/visual_servo_fsm.py)

**물체 마스크와 옷의 입구.** 전체 티셔츠 중심이나 노란 영역의 중심은 밑단·소매 입구의 중심이 아닙니다. 우리 후보 제어기는 같은 손, 가까운/먼 테두리, 잡은 모서리를 구분하고 가려지면 판단을 보류해야 합니다. 공개 RGB-D의 3D 점도 가시 표면점이지 숨은 구멍·접촉 정답이 아닙니다. 옷 입히기 전 펼침 상태를 별도 단계로 다룬 [IROS 2025 pre-dressing 연구](https://sites.google.com/view/pre-dressing/)는 참고가 되지만 의료 가운·UR5e·학습한 동작을 사용하므로 우리의 티셔츠 위상 인식을 검증하지 않습니다.

## 4. 권장 비교 순서 — 아직 적용하지 않은 가설

| 순서 | 구체적인 비교 | 먼저 확인할 것 |
|---|---|---|
| 1 | **E14 후보: controller가 고정 6전이 중립을 덧붙임.** 같은 hem-route·과거 RGB·depth·모델과 `plan_size=1`을 유지하고, 첫 8개 움직임 열 중 비영 명령이 있는 모델 `act` 뒤 모든 행동 열이 0인 중립 구간을 자동 적용 | 남은 전이 예산까지만 적용하고 앞뒤에서 점수 gate 확인. `controller_settle`을 모델 결정·호출과 별도 기록. 기본값 0은 기존 동작 유지; 구현·CPU195개 검사 통과, 실제 성능 효과 미검증 |
| 2 | **RGB에서 고른 픽셀의 수치 depth 조회.** 손·테두리·손끝 후보에 현재 Z와 유효 여부를 반환 | 종료된 E12·E13 관측으로 시각·픽셀·단위 검사부터 수행. 가림·경계 혼합·범위 밖을 별도 표시하고 숨은 점을 채우지 않음 |
| 3 | **더 이른 264경계에서 펼침·재파지.** 700경계의 국소 조정과 초기 파지 설계 변경을 별도 분기로 비교 | 초기 파지가 손·테두리 시야와 입구 모양을 계속 제한하는지 확인. 밑단 파지 자체를 실패로 단정하지 않음 |
| 4 | **VLM 단계 판단＋작은 시각 피드백 제어기.** 모델은 대상·입구 후보·단계를 지정하고 제어기는 공개 관측의 상대 오차를 제한된 공식 속도 명령으로 변환 | 손끝·손·테두리의 추적과 depth 유효성부터 검증. 양쪽 옷 지지, 가림, 관절 한계에서 중단·재관측하는 조건 필요 |

선택한 E14 후보는 모델에게 두 구간을 미리 만들게 하는 방식이 아닙니다. controller가 모델 이동 뒤 정해진 6전이(0.30초)를 덧붙이며, 모델 결정 수를 늘리지 않고 추가 물리 진행을 별도 집계합니다. 중립 전에 gate가 충족되면 적용하지 않고 적용 뒤에도 다시 확인합니다. 남은 전이 예산이 6보다 작으면 그 범위로 제한합니다. 중립 구간의 관측·행동·출처를 보존하되 다음 모델 호출은 정착 뒤 상태를 받습니다. 기존 기본값 0과 `plan_size=1` 제약을 검사하며, 중립은 실제 관절·천의 정지나 가림 해소를 보장하지 않습니다. 두 번 무진전 보정 제한도 유지합니다. 이전의 모델 계획 2구간(이동 ≤8＋중립 ≤12)은 별도 대안으로 남기며 이번 선택과 섞지 않습니다. [수집 controller](../../../participant/collection/codex_client.py)

4번의 구조적 참고는 [ReKep](https://rekep-robot.github.io/)의 RGB-D 특징점 관계·최적화와 [VoxPoser](https://voxposer.github.io/)의 재사용 가능한 모델 출력·시각 피드백 재계획입니다. 옷 접기는 착의 통과와 다른 과제이며 이 구조가 현재 실패를 해결한다고 보장하지 않습니다. [FCVP](https://arxiv.org/abs/2311.04390)의 착의 제어는 실제 힘 데이터로 배운 모델도 사용하므로 현재 공개 입력만으로 힘 제약 효과를 가져올 수 없습니다.

## 5. 적용 상태와 측정 기준

**적용됨:** E13의 현재 손목 depth 패널, 기존 공개 상태·16×16 depth 수치, 첫 호출의 같은 에피소드 과거 RGB. **구현·CPU 검사를 마치고11:33:49 UTC에 시작한 E14 비교(새 결과 미측정):** controller의 고정 6전이 정착 추가. **추가 연구 제안:** 픽셀 조회 API, 초기 파지 변경, VLM과 시각 제어기의 분리. E13의 입력 성공과 과제 성능 향상을 구분합니다. [실제 첫 16이미지·순서·SHA](../attempts/20261106-astra-hem-depth-001/first-call-images.json)

우선 측정할 것은 같은 손·테두리의 추적 연속성, 목표 대비 실제 관절 잔차, 가림 때문에 판단을 보류한 경우, 새 호출·전이·실제 시간입니다. 입구 통과는 여러 지정 시점의 연속 관측으로 검토하고, 공식 첫 소매 점수는 별도 평가로 확인합니다. 평가·숨은 기하·배치 정보는 정책 입력으로 전달하지 않습니다. 공식 행동·물리·평가를 유지하며 한 번에 한 가지 가설을 비교합니다.
