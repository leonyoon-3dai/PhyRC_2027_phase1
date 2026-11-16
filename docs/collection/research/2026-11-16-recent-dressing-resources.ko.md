# 2026-11-16 최신 착의 제어·진행 평가 자료 조사

**조사 완료·2026-11-16 후속 결정:** 이 문서는 조사 당시의 근거·적용 후보를 보존한다. 사용자는 조사를 마무리하고 [checkpoint 기반 사용자 피드백 시연](2026-11-16-user-guided-resume.ko.md)을 다음 방향으로 정했다. 현재 방향은 [COLLECTION_PLAN](../../COLLECTION_PLAN.md)이 정본이며, 아래의 HOLD·미실행 설명은 조사 당시 상태다. 이번 갱신도 문서 인계이고 새 시연·학습·추가 득점은 아직 없다.

[메인](../../../README.md) · [현재 계획](../../COLLECTION_PLAN.md) · [checkpoint·실행 효과 누적 분석](2026-11-16-checkpoint-effect-feedback.ko.md)

조사 기준일은 **2026-11-16**이다. 논문의 최초 공개일, 출판사의 온라인 출판일, 저장소 갱신일을 구분한다. 검색엔진 수집일을 연구 발표일로 쓰지 않았다. 아래의 **확인 사실**은 원문·공식 프로젝트·저장소에 근거하며, **PhyRC 적용 해석**은 우리 실험에 대한 제안이다.

## 1. 먼저 볼 자료

| 자료 | 확인한 날짜의 의미 | 공개 근거 수준 | 우선 참고할 문제 |
|---|---|---|---|
| Dressing in Motion | 2026-09-04 arXiv v1 | 논문 본문·실물 실험 보고, 프로젝트 링크 | 삽입과 진행률 분리, 연속 관측에 따른 경로 수정 |
| Geometry-Aware RL | 2026-10-23 arXiv v1 | 논문 본문·실물 마네킨 손 실험 보고 | 가까워 보임과 실제 통과 구분 |
| Wearing A Coat | 2026-07-13 arXiv v1 | 논문 본문·시뮬레이션 및 실물 실험 보고 | 이미 낀 부분의 접촉 제약, 단계별 제어 |
| Synchronous dressing support | 2026-06-05 온라인 출판 | 출판사 전체 본문·실물 실험 보고 | 작업 상태 예측 후 제어 갱신 |
| Force-Modulated Visual Policy | 2025-09-16 arXiv v1, CoRL 2025 | 논문·공식 프로젝트의 실물 데모 영상 | 힘에 따른 수정, 진행 평가와 중지 조건 |
| All Dressed Up | 2026-10-16 온라인 출판 | 논문·실제 FRET JSON 요구사항 | 제어권·감독·성능 감시 요구사항 |
| 공식 PhyRC 평가 문서·코드 | 2026-11-08 기준 공식 저장소 갱신 | 실행 코드·평가 명세 | 실제 득점 판정과 checkpoint 평가 경계 |
| REMORA / ReSTEP | 2026-10-29 arXiv v1 | 논문 본문, 비착의 작업 | 후퇴·복구를 허용하는 진행 추정의 보조 참고 |

공개 코드가 확인되지 않은 논문을 곧바로 실행 가능한 패키지로 소개하지 않는다. 논문 속 실물 실험 보고와 직접 열어 본 데모 영상도 구분한다.

## 2. Dressing in Motion: 삽입 여부와 팔을 덮은 비율을 별도로 평가

- 원문: [Dressing in Motion: A Human Motion-Aware Diffusion Policy for Robot-Assisted Dressing](https://arxiv.org/abs/2609.04759), [전체 본문](https://arxiv.org/html/2609.04759v1).
- 저자 프로젝트: [dressing-in-motion](https://anonymous.4open.science/w/dressing-in-motion/). 논문이 링크하지만 이번 조사에서는 프로젝트 내부의 실행 코드·영상 접근을 확인하지 못했다.

**확인 사실:** 부분 점군에서 학습한 diffusion policy에 팔 중심 표현과 연속 관측 간 움직임 추정을 결합한다. 정적 시연으로 학습한 경로를 사람의 팔 움직임에 맞춰 수정한다. 평가에서 소매 삽입 성공과 `덮인 팔 길이 / 전체 팔 길이`를 나눈다. 실물 실험은 부적절한 옷–몸 접촉 또는 5초 초과 정체 시 중단한다.

**PhyRC 적용 해석:** E36처럼 손 주변에 옷이 모인 장면에서 `접근 → 삽입 → 팔을 따라 전진`을 분리할 근거다. 로봇 이동량 외에 손–옷 경계 관계의 전후 변화를 남긴다. 가려진 통과는 unknown으로 유지한다. 논문의 5초 기준을 PhyRC에 그대로 이식하지 않는다.

**차이:** 움직이는 사람의 한쪽 팔 소매 착의와 PhyRC의 고정 마네킨·닫힌 티셔츠 전체 착의는 다르다. 연속 진행률은 진단 지표이며 공식 점수의 대체물이 아니다.

## 3. Geometry-Aware RL: 입구에 가까운 것과 실제 삽입은 다르다

- 원문: [Geometry-Aware Reinforcement Learning for Close-Fitting Wearable Insertion](https://arxiv.org/abs/2610.32143), [전체 본문](https://arxiv.org/html/2610.32143v1).
- 본문에서 실행 코드 저장소 링크는 확인하지 못했다.

**확인 사실:** 대상은 티셔츠가 아니라 강체·변형 가능한 **팔찌**다. 손–입구의 상대 기하, 정렬·삽입·최종 배치의 curriculum, 손가락별 삽입 gate를 사용한다. 성공은 다섯 손가락의 통과 조건과 손목–입구 거리 1cm 미만을 함께 요구한다. 실물 구성은 마커와 추가 카메라를 이용한다.

**PhyRC 적용 해석:** “손 가까이 왔다”와 “올바른 옷 구멍을 실제 통과했다”를 별도 판정하는 설계가 유용하다. 관측에서 확인 가능한 통과 증거와 아직 확인되지 않은 증거를 나눠, 정렬 수정·추가 관측·진행 중 하나를 선택하는 후보로 삼는다.

**차이:** 팔찌의 작은 입구·손가락 gate를 소매의 주름·큰 변형에 그대로 적용할 수 없다. 마커·추가 카메라·시뮬레이터 내부 기하를 현재 actor 입력에 추가하는 제안도 아니다.

## 4. Wearing A Coat: 이미 낀 부분의 제약을 고려하며 다음 부분을 입힌다

- 원문: [Wearing A Coat: Dual-Arm Robot-Assisted Dressing with Differentiable Clothing Simulation](https://arxiv.org/abs/2607.10999), [전체 본문](https://arxiv.org/html/2607.10999v1).
- 본문 제목은 “Dual-Arm Robot-Assisted Dressing with Differentiable Clothing Simulation”이다. 실행 코드·별도 공식 영상 링크는 확인하지 못했다.

**확인 사실:** 미분 가능한 옷 시뮬레이션으로 이미 착의한 소매의 접촉·운동 제약을 고려한다. 단계별 목표와 전역 경로를 두고, 국소 모델로 더 높은 빈도의 보정을 계산한다. 시뮬레이션 및 실물 양팔 착의 실험을 보고한다.

**PhyRC 적용 해석:** 한 손·한 소매에서 진전이 생긴 뒤 다음 동작이 그 진전을 훼손하는지 확인하는 데 유용하다. 큰 단계의 목표와 짧은 실행 후 국소 수정을 분리하고, 유지할 접촉·파지와 바꿀 방향을 기록하는 후보가 된다.

**차이:** 코트와 닫힌 티셔츠는 통과해야 할 구멍과 순서가 다르다. 논문의 내부 옷 모델을 바로 재현하거나 공식 물리를 변경하는 계획으로 해석하지 않는다.

## 5. Synchronous dressing support: 현재 작업 상태를 예측하고 제어를 갱신한다

- 출판사 원문: [Synchronous dressing support based on working-status prediction](https://link.springer.com/article/10.1186/s40648-026-00350-9).
- 공개 코드 저장소·독립 데모 링크는 확인한 논문 페이지에서 찾지 못했다.

**확인 사실:** 사람의 손·어깨 위치와 외력을 이용해 작업 상태를 예측하고 MPC 및 힘·위치 제어에 연결한다. 사람이 옷 한쪽을 잡고 로봇이 반대쪽을 보조하는 한쪽 팔 소매 착의다. RGB-D 관측과 손목 힘 센서를 사용하며, 관측되는 신체 위치를 완료 판정에도 활용한다.

**PhyRC 적용 해석:** 의미적 설명만 남기지 않고, 현재 상태·예상 변화·실제 변화·다음 행동을 연결하는 구조가 참고점이다. 우리 환경에서는 공개 RGB-D와 로봇 상태로 측정 가능한 항목부터 고른다.

**차이:** 사람의 능동적 협조와 힘 센서 입력은 현재 PhyRC actor 조건과 다르다. 논문의 제어 구조와 센서 구성을 따로 평가해야 한다.

## 6. Force-Modulated Visual Policy: 실제 영상으로 진행·걸림·중지를 비교하기 좋다

- [공식 프로젝트·실물 데모](https://dressing-motion.github.io/) · [논문](https://arxiv.org/abs/2509.12741).
- 2025년 자료지만 직접 착의 데모와 평가·종료 설계가 구체적이다. 프로젝트에서 실행 정책 코드 링크는 확인하지 못했다.

**확인 사실:** 시뮬레이션의 시각 정책을 실물 데이터와 힘 입력으로 보정한다. VLM 선호도와 시간 정보를 보상 학습에 사용하되, 실패·걸림에서 시간 순서가 진행 순서를 보장하지 않는 문제를 다룬다. 팔·상완 착의 비율을 평가한다. 중지에는 어깨 덮임, 80스텝 도달, 10스텝을 초과하는 연속 무진전, 사용자 중지, 힘 18N 초과가 포함된다.

**PhyRC 적용 해석:** 데모를 보며 실제 천의 전진과 로봇만 움직이는 구간을 비교할 수 있다. 종료 이유를 성공·정체·안전·예산으로 나눠 기록하고, 정체 판정 뒤 작은 복구를 시도할지 별도로 설계하는 근거다.

**차이:** 힘 기반 반응은 현재 입력 계약에 그대로 옮길 수 없다. VLM 선호도나 “더 늦은 프레임”을 통과 정답으로 쓰지 않는다. 위 수치도 PhyRC의 권장 임계값이 아니다.

## 7. All Dressed Up: 실행 정책보다 감독·전환 조건의 요구사항 자료

- [출판사 논문](https://link.springer.com/chapter/10.1007/978-3-032-40108-3_18) · [CRADLE RAD 저장소](https://github.com/cradlerobotics/RAD).
- 실제 파일: [TeamPerformanceMonitoring.json](https://github.com/cradlerobotics/RAD/blob/main/FRET_files/TeamPerformanceMonitoring.json), [ControlAndCoordination.json](https://github.com/cradlerobotics/RAD/blob/main/FRET_files/ControlAndCoordination.json).

**확인 사실:** 착의 로봇의 사람–로봇 팀워크 요구사항 145개를 정리하고 그중 일부를 FRET 형식으로 표현한다. 저장소에는 FRET JSON 6개가 실제 존재한다. README의 향후 공개 표현과 파일 현황을 구분했다. 실행 착의 정책·복구 controller가 공개된 것은 아니다.

**PhyRC 적용 해석:** 사람 개입, 제어권 전환, 진행 감시, 중지·재개 조건을 문장과 조건식으로 명확히 정리하는 참고다. “모델이 종료 요청”과 “과제 성공 확인”을 서로 다른 사건으로 기록하는 데 유용하다.

## 8. 공식 PhyRC: 논문 지표보다 실제 득점 정의를 먼저 고정한다

- [공식 과제](https://emprise.cs.cornell.edu/phyrc/challenge-2027/) · [평가 명세 고정 revision](https://github.com/rirolab/PhyRC_2027_Challenge/blob/48ffff25c9ff86cda3a2a21c7fc33d9022afa2fc/docs/competition/EVALUATION.md).
- 코드: [evaluation_geometry.py](https://github.com/rirolab/PhyRC_2027_Challenge/blob/48ffff25c9ff86cda3a2a21c7fc33d9022afa2fc/src/PhyRC_Sim/Policy/evaluation_geometry.py), [evaluation.py](https://github.com/rirolab/PhyRC_2027_Challenge/blob/48ffff25c9ff86cda3a2a21c7fc33d9022afa2fc/src/PhyRC_Sim/Policy/evaluation.py).

**확인 사실:** 점수는 화면 인상이 아닌 실제 장면 상태로 평가한다. 소매 통과는 손목과 손끝이 나온 증거를 요구한다. 상완 점수는 덮인 길이에 비례하지 않으며, 50점과 최종 성공은 별도다. save slot 복원은 현재 live attempt를 무효 종료하고 새 평가를 시작한다.

**PhyRC 적용 해석:** checkpoint 비교에서는 출발 상태의 복원 품질과 평가 재시작을 함께 기록해야 한다. 추가 득점은 공식 평가로 확인하고, 공개 영상 기반 진행 추정은 그 원인을 설명하는 진단으로 둔다. 시간을 늘렸다는 사실만으로 득점 가능성을 입증할 수 없다.

## 9. 보조 참고: REMORA는 착의 연구가 아닌 오류·복구 진행 평가 연구

- [Tracking Task Progress Through Errors and Recovery: A Benchmark and Recurrent Distributional Model](https://arxiv.org/abs/2610.39125), [전체 본문](https://arxiv.org/html/2610.39125v1).
- **확인 사실:** 소포 처리와 약병 스캔·수납 작업에서 오류·복구를 포함한 진행을 다룬다. 기억과 진행 분포를 사용해 후퇴 가능한 추정을 설계한다. 논문의 공개 선언과 별개로 이번 조사에서 실행 코드·데이터 다운로드 경로는 확인하지 못했다.
- **PhyRC 적용 해석:** “시간이 지났으니 진전” 대신 진행·정체·후퇴·복구·관측 불충분을 구분하는 보조 아이디어다. 착의 성능 근거로 인용하지 않는다.

## 10. 이번 조사로 구체화할 비교 질문 — 아직 미실행

| 질문 | 기록할 비교 | 판정 경계 |
|---|---|---|
| 실제 통과인가, 가까워진 것인가? | 같은 공개 관측의 손·입구 해석과 다음 행동 후 변화 | 보이지 않으면 unknown; 공식 통과 증거와 별도 |
| 요청 방향이 천의 진전으로 이어졌는가? | 명령, 실제 파지 pose, 정착 후 변화, 천–손 관계 | 로봇 변위와 천의 변위를 동일시하지 않음 |
| 정체 뒤 작은 교정이 효과가 있는가? | 같은 출발 후보에서 사람·모델의 짧은 수정과 결과 | checkpoint 복원 편차와 제어 효과를 분리 |
| 언제 종료·복구·관측을 선택할 것인가? | 성공, 예산, 오류, 정체 요청, 사용자 중지의 개별 사유 | 문헌의 임계값을 무검증 복사하지 않음 |

현재 우선순위는 큰 모델의 즉시 교체보다 **비교 가능한 출발 상태, 실행 효과 기록, 통과·진행·종료의 구분**을 구체화하는 것이다. 다른 방법은 후보로 유지한다. 지정 5 RGB-D와 공개 로봇 상태를 actor 입력으로 유지하며, 내부 기하·평가 정답·자유 viewport는 별도 진단 경계에 둔다. 실제 구현·비교·추가 착의점 검증은 분석 정리 후 클린 서버에서 별도로 수행한다.
