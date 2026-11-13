# 미래 시연용 사람 피드백 큐 후보

**준비만 완료한 미적용 패치다.** 현재·과거 시연, main actor 코드, GPU 실행에 적용하지 않았다. 실제 사용자 피드백을 접수하거나 새 모델 호출을 하지 않았다. 향후 활성화 여부는 별도 결정이다.

- [패치](actor-feedback.patch): 기준 commit `9acf07631ca09480d620d849771022a73d490bbb`에 적용 검사를 통과했다.
- [검증 receipt](validation.json): 전체 CPU 353개, 신규 기능 18개 검사 및 독립 검토 통과. GPU·실제 actor 연결은 미검증이다.

새 수집에서 `--allow-human-feedback`를 명시해야 run 전용 큐를 만든다. helper는 사용자가 실제로 요청한 문장을 run ID·고유 message ID·목표 decision index에 묶어 접수한다. 기본 경로와 현재 실행에 자동으로 끼워 넣지 않는다.

새 결정 시작에서만 접수 순서대로 한 번 읽고 프롬프트를 고정한다. 진행 중 모델 호출·물리 요청·같은 frozen depth-query 후속 호출에는 새 문장을 전달하지 않는다. 접수·준비·전송·응답 확인을 구분하며, timeout은 전달 불명확으로 기록하고 재전송하지 않는다.

문장 원문과 시각·ID·hash는 비공개 ledger에 보존한다. 전달을 시도한 이후는 사람 보조 시연으로 표시하고, 부모의 assisted 행동을 재실행하는 자식·손자도 이력을 상속한다. 원문을 배우에게 상속하거나 큐를 자동 활성화하지 않는다. collector가 ledger를 먼저 닫고 최종 hash와 동일 provenance를 attempt·capture·HDF5 파일 및 episode에 남긴다.

자유 문장의 규칙 준수를 코드는 의미적으로 인증하지 않는다. 공개 RGB-D·로봇 상태에 근거한 사용자 지시만 허용하며, 점수·audit·내부 기하를 배우에게 전달하는 우회 경로로 사용하면 안 된다. 기존 도구 격리·행동 schema·물리·평가는 유지된다.

피드백이 actor 설명에 인용될 수 있으므로 assisted 공개 보고서는 별도 내용 검수와 정확한 파일 digest 지정 없이 생성하지 않는다. 원문 ledger는 공개 export에 포함하지 않는다. 검토가 끝난 patch와 이 문서는 실제 사용자 문장·인증 정보·실행 로그를 포함하지 않는다.

상세 미래 인터페이스와 보존 규칙은 패치 안의 `docs/collection/research/2026-11-13-human-feedback-prototype.ko.md`에 있다. 패치 보존은 구현 활성화나 실시간 조작 승인과 다르다.

`validation.json`은 준비 시점의 검사 기록이다. 이 디렉터리에 후보 자료를 게시하는 것과 main 실행 코드에 패치를 적용하는 것은 별개다.
