# 중앙 자유 구간 진입 전략: 사용자 제안의 다음 실행 반영

사용자가 [넓게 늘어진 중앙 구간으로 첫 손부터 입히는 제안](2026-11-13-user-central-span.ko.md)을 분석대로 반영하도록 요청했다. E31이 실행 중일 때 별도 worktree에서 후보를 준비하고, E31의 전체 원본 보존·고정 원격 복원 검증 뒤에만 main에 통합했다. 실행 중 actor 입력은 바꾸지 않았다. 아래 검증은 첫 실행 전의 CPU·통합 검토 범위다. 실제 시연 상태와 성과는 시작·마감 기록으로 따로 확인한다.

새 선택 경로는 `coordinated-central-span-entry`다. 기존 `TASK + COORDINATED_TASK + SIDE_HEM_WRISTS_TASK`에 `CENTRAL_SPAN_ENTRY_TASK`와 기존 saturation 규칙을 조합한다. 기존 task 상수·기본값·옛 경로는 유지한다. 새 경로는 dressing/exec/plan1을 요구한다. 공식 입력·float32(2,9) 행동·물리·평가·query schema는 바뀌지 않는다.

핵심은 **중앙 자유 밑단 구간의 폭·깊이·compliance를 조절하고 유지한 뒤, 같은 손을 잡힌 모서리/jaw 밖의 자유 구간에 정렬하여 관측이 지지하는 전완 진행으로 이어가는 것**이다. 상대 높이·손목 한 축·지지 간격 중 현재 근거가 있는 한 요소를 시험한다. 항상 좁히거나 벌리지 않으며 큰 장력·처짐 자체를 목표로 삼지 않는다. 관측상 팽팽한 자유 경계에는 지지가 허용할 때 넓게 휜/U형 구간을 만들 여유를 시험하되, U자 바깥 면을 열린 입구로 인증하지 않는다.

같은 손의 연결 전완을 추적하고 entry lift 전에 중앙 접근 관계를 비교한다. 아직 손이 구간 옆이면 정렬의 실제 효과를 먼저 관측한다. 진입 시도 뒤에도 현재/최근 관계가 같은 전완 방향 진행을 지지할 때 옷을 진행시키며 world-Z 상승을 목표로 삼지 않는다. 첫 팔의 유용한 관계를 보존해 반대쪽을 조절한다. anchor는 절대 위치 고정점이 아니며 유용한 형상을 유지하는 협동 이동이 가능하다.

완벽한 hole visibility·빈 배경·반대 lip 정체·정확한 midpoint를 선행 조건으로 두지 않는다. 가림은 성공도 자동 종료도 아니다. 기존 bounded regrasp/recovery와 실제 닫힘 후 동행 확인을 유지한다. 같은 효과의 작은 offset만 반복하지 않으며, 준비·운반의 유용한 중간 상태도 보존할 수 있다.20결정 안에 모든 착의 단계를 마친다고 약속하지 않는다. E31에서도 사용한 기존 camera XYZ query는 현재 표면 깊이 모호성을 줄이는 기능이며 새 camera→robot/world transform이 아니다.

## 검증 범위

- [격리 후보 검증](../../project/sessions/20261113-central-span-candidate-validation.json)은24개 focused CPU 검사(새7·diagonal4·side5·historical8), CLI help·diff, 독립 의미/계약·출처 검토를 기록한다. 준비 당시 main 미적용 상태를 기록한 역사적 receipt다.
- [main 통합 검증](../../project/sessions/20261113-central-span-integration-validation.json)은 동일3파일 해시와24개 재검사 통과를 기록한다. 최초 test helper 경로 누락으로 생긴 import 오류와 올바른 PYTHONPATH로 수행한 재검사를 구분한다.
- 기존38개 non-routing AST 항목(28상수/대입·10함수/클래스)은 동일하고, 기존23개 source snapshot 경로 안에서 변경 client를 보존한다. 신규 외부 의존성·모델·실시간 피드백 큐는 없다.
- client SHA256: `4797a5d010ffb8b0d8d6faf127aabdc57431b34be8ee78f4bcd59524dcae2899`. 실제 모델 순응·층 분리·착의 성공·새 전체 CPU suite의 결과로 확대하지 않는다.

다음 선택은 [E32 계획](../../project/sessions/20261113-e32-plan.ko.md): E28/380·새264/332 history·최대20결정/1400전이/review10이다. E31의 마지막830은 새 출발점으로 승격하지 않았다. 출발점과 방법이 함께 달라지므로 결과를 하나의 원인 효과로 주장하지 않는다. [E31 공개 검토](../reviews/20261113-astra-diagonal682-001.ko.md) / [결정·시간 비교](../reviews/20261113-decision-budget/E31/README.ko.md).

실행 후 연결: [E32 시작 기록](../../project/sessions/20261113-e32-start.ko.md)은2026-11-13 23:59:34 UTC의 실제 시작·clean source를 남긴다. 이 방법 문서의 준비 검증을 새 시연 성공으로 확대하지 않는다.

실행 후 결과: [E32 공개 리뷰](../reviews/20261113-astra-central380-001.ko.md)는 실제20개 act의 형상·운반·접촉 비교와 불완전 capture/QC 실패를 구분한다. [다음 E33 계획](../../project/sessions/20261114-e33-plan.ko.md)은 유효한 E28/632에서 같은 정적 전략을 유지하며 아직 실행 결과가 아니다.
