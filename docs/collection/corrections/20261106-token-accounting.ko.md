# 2026-11-06 토큰 사용량 해석 정정

[수집 기록](../README.ko.md) · [연결 시험 r5](../attempts/20261106-codex-robot-wiring-r5/README.ko.md) · [착의 시도 001](../attempts/20261106-astra-dressing-001/README.ko.md)

**기존 시도·공개 패키지의 `actor_usage` 합산값은 총 사용량으로 사용하면 안 됩니다.** 원본은 그대로 보존하고, 이 페이지와 시도별 정정 JSON을 분석 기준으로 사용합니다. 수집 코드·모델·추론 설정·입력·호출 구조는 변경하지 않았습니다.

CLI 0.166.0의 `turn.completed.usage`는 재개한 thread의 누적 스냅샷입니다. 기존 수집기는 이 값을 매 호출 더해 앞선 사용량을 중복 집계했습니다. 공식 버전 고정 소스에서 `usage_from_last_total()`이 `ThreadTokenUsage.total`을 복사하는 것을 확인했고, 각 시도의 비공개 세션 `total_token_usage`와 대조했습니다. [Codex CLI 0.166.0 공식 소스](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/exec/src/event_processor_with_jsonl_output.rs)

| 시도 | 범위 | 입력 | 캐시 입력 | 출력 | 추론 출력 |
|---|---|---:|---:|---:|---:|
| wiring-r5 | 잘못된 원본 누계 합산 | 133,146 | 58,240 | 719 | 159 |
| wiring-r5 | 완료한 3회 호출의 정정 누계 | **74,558** | **41,472** | **330** | **53** |
| dressing-001 | 잘못된 원본 누계 합산 | 6,756,621 | 5,609,856 | 121,915 | 108,063 |
| dressing-001 | 완료한 15회 호출의 정정 누계 | **1,146,514** | **1,008,896** | **13,825** | **12,100** |

캐시 입력은 입력 토큰의 부분집합이며 추론 출력은 출력 토큰의 부분집합입니다. 각 열을 모두 더해 총 토큰으로 계산하지 않습니다. 이 기록은 화폐 비용이나 청구서를 산출하지 않습니다.

dressing-001의 16번째 호출은 SIGTERM으로 중단되어 최종 usage가 없습니다. 따라서 위 값은 **완료한 15회 호출에서 확인한 사용량**이며, 시도 전체 사용량이 완전히 확정된 것은 아닙니다. 중단된 호출의 추가 사용량을 0으로 채우지 않습니다.

- [wiring-r5 정정 JSON](20261106-codex-robot-wiring-r5.json): 완료한 3회 호출의 누적값과 차분, 원본 SHA-256.
- [dressing-001 정정 JSON](20261106-astra-dressing-001.json): 완료한 15회 호출의 누적값과 차분, 미확정 호출, 원본 SHA-256.

공개 `decisions.jsonl`의 결정별 `usage`도 턴별 사용량이 아니라 원본 CLI의 누적 스냅샷입니다. 턴별 비교에는 정정 JSON의 `per_completed_turn[].incremental_usage`를 사용합니다. 정정 자료에는 인증정보·세션 식별자·내부 추론 내용·원본의 절대 경로를 포함하지 않았습니다.
