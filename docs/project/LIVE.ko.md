# 맥북 크롬으로 연습·수집하기

[첫 화면](../../README.md) · [시연 결과](RESULTS.ko.md) · [오늘 상태](sessions/20261026-live.md)

## 오늘 실행 순서

1. 서버에서 공식 환경 build → prepare → smoke를 한 번 수행합니다. 통과 표시는 `PHYRC-SMOKE-PASS`입니다.
2. 맥북의 현재 공인 IPv4로 `participant/streaming/firewall.py --client-ip <맥북_IP>`를 실행합니다. 접속 주소·IP는 공개 저장소에 기록하지 않습니다.
3. `python3 participant/streaming/prepare_viewer.py`로 뷰어를 준비하고 아래처럼 실행합니다.

```bash
python3 -m http.server 8210 --bind 0.0.0.0 --directory output/webrtc/viewer/dist
# 별도 터미널: 서버 공인 IPv4를 실제 값으로 설정
export STRETCH4_STREAM_HOST=<서버_공인_IPv4>
participant/streaming/start.sh
```

크롬에서 전달받은 접속 주소를 열고 화면을 클릭합니다. 영문 입력 상태에서 아래 키를 짧게 눌렀다 떼며 연습합니다. 숫자는 맥북 상단 숫자열을 사용합니다. 화면 오른쪽 아래에도 접을 수 있는 키 안내와 서버 수신 상태가 나옵니다.

| 동작 | 로봇 0 | 로봇 1 |
|---|---|---|
| 전진 / 후진 | I / K | ↑ / ↓ |
| 옆 이동 | L / J | → / ← |
| 베이스 회전 | U / O | [ / ] |
| 리프트 올림 / 내림 | W / S | 8 / 2 |
| 팔 늘림 / 줄임 | D / A | 6 / 4 |
| 손목 좌우 | E / Q | 9 / 7 |
| 손목 위아래 | V / R | = / - |
| 손목 비틀기 | C / Z | 3 / 1 |
| 그리퍼 열기·닫기 | Space | 0 또는 Enter |

**P는 초기화, ESC는 종료·저장**입니다. 첫 연습에서는 두 로봇 이동·그리퍼·키를 뗐을 때 정지를 확인합니다. 창을 벗어났을 때도 키 해제가 되는지 확인합니다. 서버 수신 표시는 로봇 동작 완료를 뜻하지 않으므로 영상도 확인합니다.

## 짧게 저장부터 확인

첫 시도는 짧게 끝내 데이터 저장 경로부터 확인합니다. ESC 뒤 원본 저장과 별도 RGB-D export가 이어집니다. `[Dataset export] READY`, `capture.json`의 `status=ready`, `complete=true`, `policy.hdf5`를 확인하기 전에는 완성 데이터로 세지 않습니다. export 중에는 같은 checkout에서 다음 simulator를 동시에 실행하지 않습니다.

이후 접근 → 집기 → 들기 → 옷 입히기를 연습합니다. 잘된 시도와 실패·중단을 구분해 남깁니다. 긴 연습은 export도 오래 걸릴 수 있으므로 첫 정상 저장을 확인한 뒤 길이를 늘립니다. 원본·데이터 검수·영상 근거가 확보된 결과만 [시연 결과](RESULTS.ko.md)와 첫 화면에 반영합니다.

## 새 서버 복제

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
participant/ops/bootstrap.sh --check
participant/ops/bootstrap.sh --install
```

GPU 작업은 하나씩 실행합니다. 오늘 사람 수집에는 과거 정책 모델이나 학습 상태를 먼저 복원할 필요가 없습니다. 과거 실험 재현이 필요할 때만 [복원 안내](RECOVERY.ko.md)를 따릅니다.

## 연속 연습 후 변환을 모아서 실행

`STRETCH4_DEFER_EXPORT=1 participant/streaming/start.sh`는 ESC 뒤 complete 원본과 export request를 저장하고 RGB-D 변환을 뒤로 미룹니다. 첫 기본값은 기존처럼 자동 변환입니다. `complete` 원본과 `READY` 학습 파일은 다릅니다. 다음 simulator와 exporter는 동시에 실행하지 않습니다.

2026-10-26 정상 보존한 727전이 원본의 실제 대기 명령:

```bash
./run.sh python /scripts/export_policy_dataset.py \
  --request /output/training_export_requests/20261026T060306Z-stream-28357.json
```

이 명령은 수집이 끝난 뒤 실행합니다. 이전 부분 HDF5가 있으면 덮어쓰지 않고 새 `--output` 경로를 사용합니다.

## 사용자 요청의 옷 옆 연습 배치

`STRETCH4_PRACTICE_LAYOUT=garment_side`와 `STRETCH4_RANDOMIZE=0`을 함께 지정하면 두 로봇을 원래 파란 옷 테이블 양옆에서 시작시킵니다. 네 테이블·옷·사람·물리·지정 카메라는 유지하며 초기 로봇 배치와 사람/옷 무작위 초기화만 연습용으로 고정합니다. 기본값에는 적용되지 않고 공식 평가에도 사용하지 않습니다. `STRETCH4_PRACTICE_LAYOUT_LOG`에 배치 JSON을 남깁니다. 데이터 출처·분할에서도 이 연습 배치를 구분합니다.

## 방향 화살표·화면 버튼·정밀 모드

로봇 주변의 전진/후진/좌우 화살표는 실제 로봇 방향과 현재 카메라로 투영됩니다. 로봇이 돌아가면 화살표도 바뀝니다. 화살표를 누르고 있거나 해당 키를 사용합니다. 왼쪽 패널에서 로봇 0/1을 선택하고 회전·리프트·팔·그리퍼 버튼을 누를 수도 있습니다. 두 로봇 동시 조작은 기존 키보드를 사용합니다.

- 초록: 지금 누른 키. `✓`: 서버 수신. `●`: simulator keyboard callback에 입력 반영. 실제 이동·파지는 영상에서 확인합니다.
- 정밀 모드: 한 번 누를 때마다 짧은 입력만 보냅니다. 미세 접근에 사용합니다.
- 연속 모드: 누르는 동안 이동하고 떼면 해제합니다. 아주 짧은 탭은 최소 한 행동 경계를 지나도록 보정합니다.
- 포커스 이탈·연결 watchdog은 보정 대기보다 우선해 즉시 키를 해제합니다.
- 안내가 가리면 왼쪽 패널/오른쪽 키 표를 접거나 화살표를 숨길 수 있습니다.

화살표는 사람용 브라우저 오버레이입니다. 3D 장면 형상과 학습 카메라에 화살표를 넣지 않습니다. 자유 viewport 투영 정보는 정책/자동 수집 모델의 입력으로 제공하지 않습니다.
