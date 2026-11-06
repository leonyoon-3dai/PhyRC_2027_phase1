# WebRTC 관찰 기능의 수집 비용 비교 계획

[수집 과정](../README.ko.md) · [방법 비교](2026-11-06-method-comparison.ko.md)

**이 문서는 GPU 실행 전 계획을 보존합니다. 이후 네 과정의 실행·260전이 검수를 완료했으며 [실측 결과](2026-11-06-streaming-benchmark-result.ko.md)에 따로 기록했습니다.** 모델을 호출하지 않고 같은 공식 환경·중립 행동·공개 RGB-D 20 Hz 기록을 사용합니다. 현재 과제 수집과 동시에 GPU에서 실행하지 않습니다. 기존 포트·방화벽·접속 설정은 변경하지 않습니다.

## 무엇을 비교하는가

현재 [`--webrtc`](../../../scripts/collect_operator.py)는 송출 SDK를 켜는 것 외에도 아래 경로를 바꿉니다.

| 경로 | OFF | ON |
|---|---|---|
| 공식 RGB-D 관측 | 공개 카메라 5개·256×256, 매 정책 step 저장 | 동일 |
| 센서 렌더링 | `world.render()`와 Replicator `step(rt_subframes=4, delta_time=0)` | 동일 호출 경로에 송출 확장 이벤트가 추가됨 |
| 앱 기본 크기 | 설치된 SimulationApp 기본값 1280×720 | 1280×720 명시 |
| 앱 UI | `hide_ui=None`: headless 기본 숨김 | `hide_ui=False`: 표시 |
| 요청 대기 | 0.1초 queue polling, idle render 없음 | 0.05초 queue polling 뒤 요청이 없으면 `world.render()` |
| 송출 확장·관찰 endpoint | 없음 | `omni.kit.livestream.app`, 관찰 전용 endpoint |
| 대기 중 물리 시계 | 진행하지 않음 | render 전후 시계 불변 검사 |

설치된 Isaac Sim 6.0.1의 `simulation_app.py` 기본값을 GPU 없이 파일로 확인했습니다. 따라서 기본 해상도가 이미 같은데 해상도 차이로 오버헤드를 설명하지 않습니다. SDK는 앱 framebuffer를 복사하고 렌더링 이벤트와 동기화하므로, 프레임 렌더링 뒤의 작업도 영향을 줄 수 있습니다. [공식 livestream app 설명](https://docs.omniverse.nvidia.com/kit/docs/omni.kit.livestream.app/latest/Overview.html)

1차 조건은 **실제 운영 flag 전체 비용**입니다. `--viewport native`를 사용하며 결과에는 `comparison=operational_flag`, `sdk_only_isolated=false`를 기록합니다. 선택형 `--viewport matched`는 [별도 진입점](../../../scripts/collect_benchmark_viewport.py)으로 양쪽 앱을 1280×720·`hide_ui=False`로 맞추며 `operational_flag_matched_viewport`로 구분합니다. 이 경우에도 대기 중 렌더링 차이가 남으므로 SDK만의 비용이 아닙니다. 동일 idle render를 유지하고 SDK만 바꾸는 실험은 이번 스크립트의 구현 범위 밖입니다.

## 최소 실행 순서

[`benchmark_streaming.py`](../../../scripts/benchmark_streaming.py)는 OFF → ON → ON → OFF 순서로 독립 프로세스 4개를 차례로 실행합니다. 각 조건이 두 번이므로 순서 편향을 일부 점검할 수 있지만 충분한 통계적 반복이라고 주장하지 않습니다. 기존 환경은 프로세스당 하나의 Isaac application을 소유하고 collector는 episode 종료 후 닫히므로, 이 비교는 네 번의 초기화를 그대로 기록합니다.

각 과정은 `--no-randomization`으로 고정된 초기 배치를 사용하고 공식 평가·HDF5 기록을 양쪽 모두 켭니다. 이는 성능 측정용 `source=integration_test`이며 과제 시연 성공 자료가 아닙니다. 평가 점수는 행동이나 조건 선택에 사용하지 않습니다.

1. 공개 ready까지 초기화 시간을 측정합니다.
2. 같은 중립 행동으로 5 step을 실행해 warmup으로 따로 기록합니다.
3. 요청 없이 10 wall초 기다린 뒤 공개 simulation 시계가 그대로인지 확인합니다. OFF는 렌더 없이 대기하고 ON은 현재 운영 코드대로 idle render를 수행합니다.
4. 같은 중립 행동을 20 step씩 3회 실행합니다. 측정 전이는 60개·3 simulation초이며 warmup을 포함한 저장 전이는 총 65개입니다.
5. 정상 finish 후 writer·프로세스 종료를 기다리고, 저장 cadence·전이 수·파일 해시와 시간 자료를 확인합니다. 전수 capture QC는 별도 실행해야 합니다.

기본 실행은 계획 출력만 하며 Docker·GPU·모델을 시작하지 않습니다.

```bash
.venv/bin/python scripts/benchmark_streaming.py \
  --run-id <새-비교-ID>
```

과제 수집 종료 후 GPU 실행을 조율하고, 이미 사용 중인 비공개 `STRETCH4_STREAM_HOST` 환경을 전달한 상태에서 실행합니다. 접속 주소를 공개 명령에 넣지 않습니다.

```bash
.venv/bin/python scripts/benchmark_streaming.py \
  --run-id <새-비교-ID> --execute
```

출력은 `output/stream-benchmarks/<ID>/`와 각 과정의 `output/collections/<ID>-NN-on|off/`에 보존합니다. 기존 ID는 덮어쓰지 않으며, 한 조건이 실패하거나 정상 종료되지 않으면 다음 GPU 과정을 시작하지 않습니다. 중단 시 진행 중 과정의 기록을 닫고 실패·중단 상태를 남깁니다. 기존 수집기의 종료 대기는 시간 제한 뒤 오류로 기록하며 강제 삭제하지 않습니다.

## 시간의 측정 범위

| 지표 | 포함 범위·주의점 |
|---|---|
| startup to public ready | Docker 실행·Kit 초기화·scene·reset·최초 공개 관측 전송/해석. reset은 이 값의 부분집합 |
| measured dispatch | 호스트 요청부터 공개 응답 해석까지. 환경·sensor·평가·writer·JSON 전송을 포함 |
| environment step | 기존 `RecordedEnvironment`의 실제 `env.step` 구간. 순수 물리 시간으로 부르지 않음 |
| dataset write | 기존 `RecordedWriter`의 저장 구간. dispatch의 부분집합 |
| explicit idle window | 요청하지 않은 실제 wall시간, 이후 observe 왕복 시간, 물리 시계 불변 여부 |
| idle render total | collector의 모든 요청 대기 구간에서 실행한 render 호출 수·누적 시간. 정확히 10초 창의 비용과 같다고 해석하지 않음 |
| shutdown / whole process | 최종 JSON 응답 후 종료 대기 / 최초 시작부터 종료까지. 별도로 보고 |

각 과정의 raw 측정값과 반복 구간별 분포를 먼저 보고합니다. OFF와 ON의 평균 dispatch 차이를 백분율로 표시한다면 `100 × (ON / OFF − 1)`이라는 계산과 사용 표본을 함께 적습니다. 초기화와 warmup을 섞은 값으로 정상 수집 구간의 속도를 설명하지 않습니다. 이 중립 장면의 차이를 복잡한 천 접촉 장면이나 모델 전체 loop 속도로 그대로 확대하지 않습니다.

CPU·GPU·NVENC encoder 사용률·장치 전력은 추가 관측에 도움이 되지만 시스템 전체 지표입니다. 모델/GPU 작업이 함께 있으면 혼입되며, encoder 사용만으로 원격 브라우저가 영상을 정상 수신한다고 단정할 수 없습니다. 첫 비교는 추가 profiler 없이 같은 경로를 유지합니다.

## 실제 viewer 연결의 확인 범위

현재 스크립트는 기본적으로 `viewer_connection_status=unverified`를 기록합니다. 브라우저를 자동으로 추가 연결하지 않습니다. 공식 Isaac 문서는 한 instance에 한 client만 연결하도록 설명하며, 기존 Mac Chrome 연결을 다른 측정 client로 대체하지 않습니다. [공식 Isaac Sim livestream client 문서](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/manual_livestream_clients.html)

실제 수신 확인에는 SDK의 `onStart` 성공 상태뿐 아니라 같은 시간창의 영상 frame count 증가가 필요합니다. 현재 설치된 Web SDK 5.17.0의 callback 계약과 viewer 코드를 확인했습니다. 후속 UI telemetry에는 다음 최소 필드만 제안합니다.

- 서버 수신 UTC와 run label, SDK 연결 bool
- `videoWidth`, `videoHeight`, `getVideoPlaybackQuality().totalVideoFrames`
- 페이지 표시 여부와 시간창 내 frame count 변화

포트 listen, signaling TCP 연결, keyboard heartbeat는 영상 수신의 충분한 증거가 아닙니다. SDP·ICE·실제 IP·peer/session 식별자는 이 측정에 필요하지 않습니다. telemetry가 추가되면 원본 성능 기록은 유지한 채 같은 run·시간창의 별도 관측 근거로 연결합니다. 연결 미확인 상태의 ON 결과를 실제 원격 시청 중 비용이라고 표시하지 않습니다.

기존 viewer는 1920×1080·60 fps를 요청하고 서버 app 설정은 1280×720입니다. 요청값만으로 실제 수신 해상도·fps를 결정하지 않으며 video 속성과 frame 증가를 확인해야 합니다. 비교 중 창 크기·자유 카메라·UI 설정을 바꾸면 해당 구간을 별도 조건으로 기록합니다.

## 준비 시점의 검증

CPU 검사 5개로 기본 dry-run이 프로세스를 실행하지 않는지, 잘못된 시간·step·경로 거부, idle 시계 변화 감지, warmup 제외와 저장 cadence 검사, viewport 보정에서 나머지 renderer 설정 보존을 확인했습니다. Python 구문 검사도 통과했습니다. 실제 Kit·송출 ON/OFF·원격 영상 수신·성능 차이는 아직 미측정입니다.
