# 이어가기 시작 실패와 설정 수정 후 중단 기록

**E08은 WebRTC 필수 환경 변수 누락으로 환경 초기화 전에 실패했습니다.** 기존 E07의 700전이를 재실행하려던 시도였지만 물리 전이·모델 호출·평가는 시작하지 않았습니다. 원본 실패를 보존하고 새 ID의 E09로 설정을 수정해 시작했으며, 이후 사용자의 휴식 요청에 따라 E09도 중단·보존했습니다. [선별 기록·근거 해시](../assets/20261106-continuation-startup/record.json)

| 구분 | 확인한 상태 |
|---|---|
| 부모 E07 | `20261106-astra-coordinated-fresh-001`, 정상 종료·1,067전이 전수 QC 통과. [종료 검토](../reviews/20261106-astra-coordinated-fresh-001.ko.md) |
| E08 | `20261106-astra-coordinated-branch700-001`, 06:09:21 UTC launch, controller wall 0.466초·simulator exit 1 |
| E08에서 실행한 것 | 재실행 0전이·신규 행동 0전이·모델 호출 0회, capture 디렉터리 생성 전 실패 |
| E08 점수 | **평가 미실행·점수 없음**. 유효한 0점 평가나 착의 실패 판정으로 세지 않음 |
| E09 | `20261106-astra-coordinated-branch700-002`, 06:15:34 UTC 새 launch. 같은 부모의 700전이를 요청한 새 시도 |
| E09 초기 진행 | 06:17:48 UTC에 초기화 통과·60/700전이 재실행·새 결정 0개·error=null 확인 |
| E09 중단 스냅샷 | 06:19:01 UTC, 사용자 SIGTERM·simulator exit 0. controller는 failed/closed, 기록 141전이·replay ACK 120·새 결정 0개, capture complete=false |

## E08 원인과 최소 수정

비공개 simulator 로그의 예외는 다음 호출 경로에 있습니다. 공개 기록에는 환경 변수 **이름만** 남기며 접속 값은 넣지 않습니다.

1. [`collect_operator.py:187`](../../../scripts/collect_operator.py#L187)에서 WebRTC용 `CollectorStream.from_environment()` 호출.
2. [`collector_stream.py:78`](../../../participant/streaming/collector_stream.py#L78)의 필수 `STRETCH4_STREAM_HOST` 조회에서 `KeyError` 발생.
3. 수집기가 `collector_error`를 반환해 [`codex_client.py:548`](../../../participant/collection/codex_client.py#L548)의 ready 수신이 실패.

이 호출은 `DressingEnv` 초기화와 `DatasetWriter` 생성보다 앞이며, 모델 Actor 생성도 ready 이후입니다. 따라서 0전이·capture 없음·모델 호출 0회와 부합합니다. 700전이의 행동 재실행이나 seed 복원 로직이 실행된 뒤 발생한 오류는 아닙니다.

E09 launch 환경에 기존 비공개 `STRETCH4_STREAM_HOST`와 `STRETCH4_VIEWER_ORIGIN`을 명시했습니다. client가 이를 상속하고 [`run.sh`](../../../run.sh#L124)가 export된 `STRETCH4_*` 이름을 컨테이너에 전달하는 기존 경로를 유지했습니다. 물리·평가·행동 정의나 runtime 코드를 고치지 않은 설정 수정입니다. launch에서 설정을 확인한 것과 수집기에 자동 사전 검사를 구현한 것은 다릅니다. runtime의 존재·IPv4·origin 형식 자동 검사는 후속 예방 후보입니다.

## 사용자 중단과 재개 경계

E09에서 확인한 60전이는 **06:17:48의 진행 스냅샷**입니다. 700전이 전체 재실행이나 정확한 물리 상태 복원을 확인한 결과가 아닙니다. 이후 사용자 요청으로 중단했으므로 E08의 초기 설정 오류와 종료 원인을 구분합니다.

06:19:01 기준 E09의 `simulation_steps=141`, `replay_steps_completed=120`, `capture.json.complete=false`를 그대로 보존했습니다. 이 초기 진단에서는 활성 HDF5나 E09 점수를 읽지 않았고 적용·응답 경계와 종료 정리 전이를 후속 검수 대상으로 남겼습니다.

이후 [닫힌 E09의 전수 검토](../reviews/20261106-astra-coordinated-branch700-002.ko.md)에서 **앞 140전이는 부모 E07의 실제 행동과 일치하고 마지막 1전이는 중립 정리**임을 확인했습니다. 차이 21을 신규 모델 시연으로 세지 않습니다. 전체 검사는 manifest·policy 파일·audit 파일의 incomplete 오류 3개로 실패했으며, 원본의 완료 표시를 고치지 않았습니다. 부분 실행의 평가 결과와 종료 응답 정합성 오류는 연결한 검토에 별도로 기록했습니다.

계보는 **닫힌 E07 → E08 시작 실패 → E09 설정 수정 후 사용자 중단**입니다. 두 후속 시도의 원래 프롬프트·실패·시간·상태는 덮어쓰지 않으며, 휴식 뒤 복원과 소매 단계의 다음 시도는 별도 새 실행으로 관리합니다.
