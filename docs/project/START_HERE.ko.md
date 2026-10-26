# 다음 클린 서버에서 시연 다시 시작하기

**2026-10-26 종료 인계.** 오늘 시연·viewer를 종료했고 GPU 0MiB를 확인했습니다. 사용자는 UI가 조금 나아졌으나 개선할 점이 많다고 평가했고, 다음 클린 서버에서 다시 직접 시연한 뒤 피드백하기로 했습니다. [종료 요약](END_20261026.ko.md) · [실제 시연 영상](DEMO_20261026.ko.md) · [현재 상태](STATUS.md)

다음 목표는 **최소 준비 → 같은 UI로 짧은 시연 → 사용자 피드백**입니다. 이전 날짜 계획을 따라 새 학습·긴 정책 평가·자동 조작을 먼저 시작하지 않습니다. 공식 물리·행동 한계를 바꾸지 않습니다.

## 1. 코드와 환경

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git rev-parse HEAD
participant/ops/bootstrap.sh --check
participant/ops/bootstrap.sh --install
```

기존 checkout이면 먼저 변경 내용을 확인하고 덮어쓰지 않습니다. bootstrap은 Docker/NVIDIA/uv 등 host prerequisite를 전제로 공식 build/prepare/smoke를 실행합니다. `PHYRC-SMOKE-PASS`와 exit 0을 확인합니다. 다음 시연에는 과거 정책 모델을 먼저 복원할 필요가 없습니다.

## 2. 접속 준비

새 서버의 공인 IPv4와 사용자의 현재 맥북 공인 IPv4를 확인합니다. 이전 세션 주소를 재사용하거나 추측하지 않습니다. 접속 정보·토큰은 공개 문서에 쓰지 않습니다.

```bash
# 아래 값을 실제 새 주소로 바꿔 설정합니다.
export PHYRC_CLIENT_IP="<맥북 공인 IPv4>"
export STRETCH4_STREAM_HOST="<서버 공인 IPv4>"
python3 participant/streaming/firewall.py --client-ip "$PHYRC_CLIENT_IP"
python3 participant/streaming/firewall.py --client-ip "$PHYRC_CLIENT_IP" --check
python3 participant/streaming/prepare_viewer.py
python3 -m http.server 8210 --bind 0.0.0.0 --directory output/webrtc/viewer/dist
```

마지막 HTTP server는 별도 터미널에서 유지합니다. Node/npm이 필요합니다. 제한 포트는 viewer 8210/TCP, keyboard 8211/TCP, signaling 49100/TCP, media 47998/UDP입니다.

## 3. 같은 연습 배치·RAM 감시로 시작

다른 터미널에서도 새 `STRETCH4_STREAM_HOST`를 설정합니다. 로봇은 파란 옷 테이블 양옆, 사람은 무작위 회전 없는 고정 연습 배치입니다. 공식 평가 기본 배치와 다릅니다.

```bash
run_id="$(date -u +%Y%m%dT%H%M%SZ)-human-feedback"
mkdir -p "output/sessions/$run_id"
chmod g+rwx "output/sessions/$run_id"
export STRETCH4_CAMERA_EYE="1.0,-5.0,3.3"
export STRETCH4_CAMERA_TARGET="0.9,-0.6,0.85"
export STRETCH4_PRACTICE_LAYOUT=garment_side STRETCH4_RANDOMIZE=0
export STRETCH4_PRACTICE_LAYOUT_LOG="/output/sessions/$run_id/practice-layout.json"
export STRETCH4_PERF_LOG="/output/sessions/$run_id/performance.jsonl"
export STRETCH4_MAX_RSS_GIB=40 STRETCH4_DEFER_EXPORT=1
.venv/bin/python participant/ops/run.py --id "$run_id" -- participant/streaming/start.sh
```

run wrapper는 로그를 `output/runs/$run_id/command.log`에 남깁니다. WebRTC/keyboard ready와 초기 장면을 확인한 뒤 실제 주소를 사용자에게 전달합니다. IPv4/방화벽·단일 client 연결을 확인합니다. 처음에는 짧게 움직이고 ESC로 원본 정상 저장을 확인합니다. 수집과 exporter/GPU 진단을 동시에 실행하지 않습니다.

## 4. 사용자 피드백으로 확인할 것

- 카메라 시점과 로봇 주변 화살표가 실제 방향을 이해하는 데 도움이 되는가.
- 키보드·화살표 클릭·큰 버튼 중 무엇이 편하고, 무엇이 혼란스러운가.
- 정밀 모드의 이동량, 길게 누르기와 놓았을 때 정지가 적절한가.
- 팔·손목·그리퍼 피드백과 UI 가림을 어떻게 개선할 것인가.

이는 다음 확인 목록이며 오늘 모두 해결됐다는 뜻이 아닙니다. `✓`는 서버 수신, `●`는 키 callback 반영이고 실제 로봇 동작 완료 표시는 아닙니다. [전체 키·저장 안내](LIVE.ko.md)

## 5. 오늘 자료가 필요할 때

[오늘 종료/복원 정보](END_20261026.ko.md)의 고정 HF revision으로 내려받고 SHA256을 확인합니다. 정상 원본과 OOM 원본·profiling fixture를 구분합니다. RGB-D 학습 export와 적합성 검수는 아직입니다. **새 시연을 시작하기 위해 과거 전체 export를 먼저 실행할 필요는 없습니다.**

[과거 10월 23일 시작 안내 보존본](START_HERE.20261023.ko.md)은 당시 인계이며 오늘의 우선순위를 대체하지 않습니다.

## 다음 Codex에게 전달할 요청

```text
2026-10-26 종료 인계를 이어갑니다. AGENTS.md, README, STATUS,
END_20261026.ko.md, START_HERE.ko.md를 먼저 읽으세요.
사용자는 다음 클린 서버에서 시연을 다시 해보고 UI 피드백을 주려 합니다.
최소 환경 점검 후 기존 방향 화살표/버튼/정밀 UI로 먼저 연결하세요.
새 학습·긴 평가·과거 전체 RGB-D export를 먼저 시작하지 마세요.
새 서버/맥북 IP를 확인하고 RAM guard·성능 로그·deferred export를 유지하세요.
고정 연습 배치와 공식 평가 기본 배치를 구분하세요.
오늘 원본과 33초 편집 영상, HF 고정 revision/checksum을 보존하세요.
초기 OOM 원인은 미확정이며 UI 사용성도 추가 개선이 필요합니다.
사용자 피드백과 실제 프로파일을 보고 다음 변경을 정하세요.
```
