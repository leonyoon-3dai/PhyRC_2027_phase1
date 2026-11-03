# 다음 서버에서 기존 UI 테스트 재개

**최신: 2026-11-03 종료.** [오늘 종료·측정·내일 목표](END_20261103.ko.md)를 먼저 읽습니다. 텍스트 입력은 사용하지 않고 기존 UI로 0 → 50점 단계별 목표, 데이터 저장, 초기화·중간 상태 복원 가능 여부를 테스트합니다. 과거 데이터·정책 모델은 선행 조건이 아닙니다. 사용자의 다음 재개 요청 전 GPU 작업을 시작하지 않습니다.

## 1. 서버 선택과 최소 설치

이전 $1.06/h L40S와 오늘 $1.77/h L40S 중 선택은 사용자가 합니다. 오늘 라이브 누적은 약 10% 빠르지만 모든 60초 구간에서 +8%를 유지하지는 않았습니다. 높은 RAM 자체의 속도 효과는 확인되지 않았습니다.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git rev-parse HEAD
participant/ops/bootstrap.sh --check
# 결과와 docs/competition/SETUP.md 확인 후 필요할 때만:
participant/ops/bootstrap.sh --install
```

기존 checkout은 변경 사항을 확인하고 덮어쓰지 않습니다. build/prepare exit 0, smoke의 `PHYRC-SMOKE-PASS`를 확인합니다. 물리·형상·행동 한계를 변경하지 않습니다.

## 2. 새 접속 경로: 직접 IP 또는 Brev 중계

실제 맥북 IPv4, 서버 주소와 포트 매핑을 확인합니다. `curl`로 얻은 외부 송신 IP를 접속 가능한 서버 IP로 단정하지 않습니다. 오늘 서버는 Brev CLI 자동 등록으로 해결했습니다.

```bash
# 각 placeholder는 새 서버/클라이언트의 실제 값으로 교체합니다.
brev ports ls <instance> --json
# 로그아웃이면 사용자 브라우저 인증. 인증 정보를 문서/로그에 게시하지 않음.
brev login --skip-browser
brev ports open <instance> 8210-8211 --protocol tcp --allow <client-ip>/32 --json
brev ports open <instance> 49100 --protocol tcp --allow <client-ip>/32 --json
brev ports open <instance> 47998 --protocol udp --allow <client-ip>/32 --json
python3 participant/streaming/firewall.py --client-ip <client-ip>
python3 participant/streaming/firewall.py --client-ip <client-ip> --check
```

먼저 기존 등록을 확인해 중복 생성하지 않습니다. 중계는 외부 포트를 자동 배정합니다. 알려진 Brev gateway의 트래픽만 `wt0` 인터페이스에서 해당 streaming chain에 허용해야 할 수 있습니다. `netbird status -d`와 실제 패킷으로 peer를 확인하고, `sudo iptables -I PHYRC_STREAM 1 -i wt0 -s <verified-gateway-ip>/32 -j ACCEPT`를 적용합니다. 기존 세션의 gateway IP를 복사하지 않습니다. 외부 Brev 허용 출발지는 맥북 /32를 유지합니다. HTTPS HTTP 프록시만으로 WebRTC UDP가 해결됐다고 단정하지 않습니다.

```bash
python3 participant/streaming/prepare_viewer.py
python3 -m http.server 8210 --bind 0.0.0.0 --directory output/webrtc/viewer/dist
```

별도 터미널에서 외부 viewer origin과 공개 주소를 설정합니다. viewer 접속 형식은 `http://<relay-ip>:<viewer-public-port>/?keyboardPort=<keyboard-public-port>&signalPort=<signal-public-port>&mediaPort=<media-public-port>`입니다. public IP는 실제 해당 Brev endpoint에서 확인한 IPv4를 씁니다. `STRETCH4_VIEWER_ORIGIN`은 query 없는 정확한 viewer origin입니다.

## 3. 동일 연습 배치·기록·RAM guard로 실행

```bash
export STRETCH4_STREAM_HOST="<verified-public-ipv4>"
export STRETCH4_VIEWER_ORIGIN="http://<verified-public-ipv4>:<viewer-public-port>"
run_id="$(date -u +%Y%m%dT%H%M%SZ)-human-ui"
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

これは固定練習配置であり公式評価配置ではありません。Chromeで実際の映像と短い動作を確認します。既存のボタン・方向・キーボードを使い、テキスト入力は使用しません。`P`は初期化、`Esc`は終了・保存。deferred export時は complete原本とRGB-D変換待ちを区別します。RGB-D exporterと収集を同時実行しません。

## 4. 단계별 저장·재시작부터 검증

[종료 인계](END_20261103.ko.md)의 단계별 테스트 순서를 따릅니다. 데이터 구간 저장, 초기 상태 재시작, 중간 상태 checkpoint 복원은 각각 별도로 확인합니다. 브라우저에는 F1~F5 전달이 없으며, slot UI 연결과 복원 후 계속 조작은 내일의 구현·검증 대상입니다. smoke 통과를 정확한 중간 되감기 검증으로 확대 해석하지 않습니다.

실제 점수는 공식 평가 절차로 확인하고 임의의 단계별 숫자를 부여하지 않습니다. 처음에는 초기화·짧은 저장을 검증한 뒤 접근/파지/운반/착의 단계마다 기록합니다. 50점 달성은 목표이며 기존 결과가 아닙니다. 복원이 검증되지 않으면 초기 상태 재시작과 사람 재실행을 사용합니다.
