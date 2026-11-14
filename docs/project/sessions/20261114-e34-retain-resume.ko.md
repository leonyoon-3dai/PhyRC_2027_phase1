# E34: E33의 마지막 새 파지를 유지하며 후속 시험

사용자의 기존 방식 추가 수집 요청에 따른 두 번째 시도다. [E33 리뷰](../../collection/reviews/20261114-astra-middle-grip264-001.ko.md)와 [고정 백업](20261114-e33-backup-verification.json)을 확인했다. E33은0/50·20결정·471전이·QC통과였으며 마지막 robot1 닫기 뒤 들기 시험이 남았다.

- run: `20261114-astra-middle-grip470-retain-001`
- 직접 parent: E33 `20261114-astra-middle-grip264-001`; source group: E28 `20261113-astra-side-hem-fresh-001`
- prefix470 / 새 replay history434·454; 정확한 천 checkpoint가 아니다.
- `coordinated-middle-grip-drape-retain`, 새20결정/총1400/review10, Codex0.166.0/exec/gpt-6-astra/ultra, named·pixel query·wrist panel·plan1, motion-only settle6·timeout180·시간계측.
- 이전 파지 위치 변경 목표와 위에서 내려 걸치기를 유지하면서 추가 재파지0을 지시한다. 정적 프롬프트 제약이며 런타임 자동 차단·누적 상태기계 구현이 아니다. 공개 관측·스키마·물리·평가기는 유지한다.
- 정상 close·전수 QC·별도 평가·영상·고정 백업 후 추가 결정의 효용을 판단한다. 아직 시작·결과를 주장하지 않는다.

실행 조건 정본은 [COLLECTION_PLAN](../../COLLECTION_PLAN.md#다음-e34-실행-조건)이며 [CPU 분기 계획](../../collection/retry-plans/20261114-e34-e33-470-retain.json)을 보존한다.

변경 후 전체 CPU356개 검사가41.562초에 통과했다. 기존 전략의 동작 동등성, 새 선택지의 프롬프트/hash, exec/plan1 제한, 질의·정착 경로를 확인했다. 합성 open 응답이 기존 스키마를 통과하는 검사도 있어 이 제약이 hard gate가 아님을 명시적으로 유지한다. GPU 성과는 아직 미측정이다.
