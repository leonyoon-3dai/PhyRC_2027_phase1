# 테이블 peel 후보 · 중단 당시 미완성 작업 보존

**NOT APPLIED / NOT APPROVED — main에 적용하지 않았고 실행하지 않은 미완성 후보다.** 사용자의 2026-11-14 중지 요청 즉시 개발을 멈췄다. 이후 요청에 따라 기존 작업을 그대로 저장했으며 오류 수정·추가 테스트·시연은 하지 않았다. 이 자료는 새 서버 인계를 위한 보존물이며 자동 적용·수집 재개 지시가 아니다.

원본 작업트리는 `/home/shadeform/workspace/phyrc-table-peel-candidate`, branch는 `codex/table-peel-candidate`, base는 **`7fbe477584822b1a1a500bf97b7ffe1b2ea3e6da`**다. 원본 작업도 미커밋 상태로 남겨 두었다. 공개 Python 사본은 자동 테스트 탐색·import를 막기 위해 `.py.txt`로 저장했으며 바이트는 원본과 같다. 보존 manifest는 `original_source_path`와 `saved_copy`를 구분한다. 패치와 원본 작업트리의 이름·내용은 바꾸지 않았다. [4개 파일 패치](table-peel-incomplete.patch)와 [그대로 복사한 파일](files/), [base·파일·패치 SHA-256](preservation.json)을 함께 보존한다. 패치 SHA-256은 `63bc8385e935cf9a213ff98fa91b6f1da199a8e7688f0fdc85fd49eddb9d40c8`이다.

| 파일 | 중단 당시 변경 |
|---|---|
| `participant/collection/codex_client.py` | 별도 opt-in `coordinated-table-peel-entry` 지시문·CLI 선택·dressing/exec/plan1 제한·조합 경로 |
| `tests/test_table_peel_strategy.py` | 새 경로의 공개 입력·행동 연결, 기본 경로 불변성, 닫기와 물리 dwell 분리 검사 후보 |
| `tests/test_central_span_strategy.py` | 새 상수만 허용하도록 기존 불변성 검사의 상수 목록 갱신 |
| `tests/test_single_arm_progress_strategy.py` | 같은 상수 목록 갱신 |

조건부 조작 가설은 **guide를 열린 채 두고 anchor로 접근 가능한 자유 경계를 먼저 드러낸 뒤 guide를 배치·닫는 순서**다. 양쪽이 처음부터 열린 경우에는 먼저 한쪽 anchor를 실제 물리 대기·국소 천 동행으로 확인한다. 이후 별도 dwell·guide 국소 동행·차등 형상 검사를 남기고, 유용한 중앙 자유 구간을 운반해 같은 첫 손/전완을 진행시킨 다음 반대 손을 다룬다. 준비 중 재파지 1회·배치 보정 최대 2회, 숨은 층으로의 blind scoop 금지, 빈 배경이나 완전한 입술 인증을 필수 조건으로 두지 않는 지침을 포함했다. [선행 가설](../../2026-11-13-hem-peel-grasp-dwell.ko.md)

이 문구는 그 순서를 실제 로봇에서 검증했다는 뜻이 아니다. 기존 파지가 실패했다거나 E33 결과가 나왔다는 전제도 없다. E33은 시작하지 않았으며 현재 수집은 중지 상태다.

## 마지막 검사 상태

중지 직전에 실행된 CPU 검사 한 번은 **총 30개 중 29개 통과·1개 ERROR**였다. 새 테스트 `test_close_and_explicit_dwell_remain_separate_physical_actions`의 line 155에서 두 번째 `model_call` 항목을 참조하다 `IndexError: list index out of range`가 발생했다. 검사 fixture/이벤트 가정을 포함한 원인 수정과 재검사는 하지 않았다. 테스트 명령·기준 파일 해시·8.619초의 실행 기록은 [보존 manifest](preservation.json)에 남겼다.

따라서 전체 검사 통과·독립 전략 승인·실제 모델 호출·GPU 검증·성능 향상을 주장하지 않는다. 복원 시 먼저 보존 해시와 base를 확인하고 후보로만 검토한다. 사용자가 명시적으로 재개하기 전에는 패치를 main이나 actor 입력에 적용하거나 실험을 실행하지 않는다.
