# 구간 영상으로 착의 시연 수집하기

현재 기본 실험에서는 GPT‑6.2 Astra가 0전이부터 착의와 실패 복구를 진행한다. 사용자는 Brev의 비공개 갤러리 주소를 새 탭에서 열어 지난 구간과 최신 영상을 확인하고, 문제가 보일 때 개입한다. 갤러리 상단에는 이전 시연의 실패 분석과 공식 영상 비교가 있다. 모든 회차에서 +X 중앙 테이블(인덱스 2)과 마찰 0.35를 확인한다. [GPT 단독 실험의 관측 기준](autonomous.md)

## GPT 단독 수집

수집 서버 운영자는 검토 서버를 시작한 뒤 다음 명령으로 고유한 회차를 연다. 빈 공간과 운반 구간은 모델이 최대 20전이 동작을 선택할 수 있다. 공개 손목 깊이 영상으로 두 겹과 손끝을 비교하고, 필요한 정착 동작은 모델이 선택한다. 영상은 여러 행동을 묶어 게시한다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
phyrc_run_id="$(date -u +%Y%m%dT%H%M%SZ)-astra62-autonomous"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id "$phyrc_run_id" --mode dressing --gpt-only \
  --model gpt-6.2-astra --effort ultra --actor-backend exec --plan-size 1 \
  --seed 43 --named-actions --wrist-depth-panel --segment-review-dir output/segment-review \
  --segment-decisions 3 --segment-steps 60 --post-action-settle-steps 0 \
  --max-steps 18000 --model-timeout 180
```

## 사용자 피드백 모드와 로컬 검토 서버

저장소 루트에서 준비한 Python 환경과 고정 Codex CLI를 사용한다. GPU 환경 준비는 [서버 준비](start.md), 마찰과 공식 점수 기준은 [공식 변경점](upstream.md)에 있다. 브라우저는 클립과 사용자 의견을 전달하고, 서버의 수집기가 모델 호출과 시뮬레이터 제어를 담당한다.

지금 화면 구성을 확인하려면 [검토 화면 HTML](../../tools/segment_review.html)을 다운로드해 로컬에서 연다. 서버 연결 전에는 수집 대기 상태를 표시한다.

실제 수집 때는 서버의 첫 터미널에서 실행한다.

```bash
python tools/segment_review.py --root output/segment-review serve --port 8765
```

사용자 PC에서 SSH 포트를 연결한다. `SSH_HOST`는 새 서버의 실제 SSH 별칭 또는 접속 주소로 바꾼다.

```bash
ssh -N -L 8765:127.0.0.1:8765 SSH_HOST
```

브라우저에서 [구간 검토 화면](http://127.0.0.1:8765/)을 연다. 실행 전에는 대기 화면이며 첫 관측의 분석이 도착하면 자동으로 갱신된다. [수집 계획](experiment.md)의 단계를 옆에 놓고 판단할 수 있다.

서버의 두 번째 터미널에서 수집기를 시작한다. 아래의 구간 예산과 정착 길이는 첫 회차의 운영값이다. 호출 시간이 걸리는 동안 시뮬레이션은 멈춘다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
phyrc_run_id="$(date -u +%Y%m%dT%H%M%SZ)-astra62-dressing"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id "$phyrc_run_id" --mode dressing --user-guided \
  --model gpt-6.2-astra --effort ultra --actor-backend exec --plan-size 1 \
  --seed 43 --named-actions --segment-review-dir output/segment-review \
  --segment-decisions 3 --segment-steps 60 --post-action-settle-steps 2 \
  --max-steps 2400 --model-timeout 180
```

## 첫 화면과 다음 조작

1. 첫 화면은 0전이의 관측 한 장이다. 상단 overview, 왼쪽 robot_1, 오른쪽 robot_0이고 양쪽 모두 head가 위, wrist가 아래다. 배치와 옷의 위치를 확인한다. 마찰은 서버 시작 로그의 shirt/manikin 0.35, gripper/cloth 0.5, table/cloth 0.5와 대조한다. `unverified`는 해당 계수를 로그에서 확인하지 못했다는 뜻이다.
2. 이후에는 실제 20 Hz 경계마다 지정 5뷰를 저장한다. 웹은 **구간 시작·끝을 포함한 모든 경계**를 5 fps(4배 느리게)로 재생한다. 모델은 같은 JPEG들 가운데 조작·정착 끝점을 우선한 최대 8장의 시간순 표본으로 분석한다. 모델에 들어간 정확한 전이 번호는 `review_frame_steps`에 남는다.
3. 직전 지시, 영상에서 확인한 변화와 실패 원인, 다음 제안을 함께 본다. 모델은 현재 구간의 지시, 기록된 실제 행동과 두 그리퍼의 공개 실측 변위로 영상 속 변화를 해석한다. 가림으로 판정할 수 없으면 `uncertain`을 쓴다. 공식 항목별 점수와 `success`는 감독자가 같은 물리 경계의 평가 샘플에서 합친다.
4. 다음 동작을 수락하거나 공개 카메라에서 관찰한 근거로 지시를 교정한다. 수락하면 **표시된 다음 프롬프트**, 수정하면 **입력한 새 지시**가 다음 행동 호출에 들어간다. 관측 근거와 최근 실측 움직임이 함께 전달된다. HOLD는 정지 상태를 유지하고, 종료는 전이를 추가하지 않고 기록을 닫는다. 마감 예산에서는 HOLD 또는 종료를 선택한다.
5. 새 점수·성공이 나타난 조작의 ACK, 모델이 다음 단계로 전환하는 제안, 시야상 정체, 종료 제안, 구간 예산이 검토 경계다. 단계 전환 제안은 승인 후 같은 상태에서 다시 판단한다. 클립 분석이 실패하면 화면에서 직접 교정하거나 종료할 수 있다. 기존 HOLD의 응답은 새 구간에 적용되지 않는다.

홀드마다 읽는 파일은 현재 구간의 프레임과 새로 기록된 점수 샘플이다. 중간 단계에서 전체 HDF5를 복제하거나 GitHub에 게시할 필요가 없다. 사용자 대기시간, 모델 연산과 클립 처리시간은 실제 작업시간에 포함되며 시뮬레이션 진행시간과 구분한다.

## 마감과 데이터 확인

실행 중 Codex가 읽을 상태는 아래 한 줄이면 충분하다. 돌아가는 수집기가 웹 응답을 직접 수신하므로 별도 터미널에서는 `latest`로 조회한다.

```bash
python tools/segment_review.py --root output/segment-review latest --run "$phyrc_run_id"
```

사용자가 정상 종료한 후, 닫힌 HDF5의 전이를 검사하고 이번 run의 데이터셋을 내보낸다. 출력 ZIP에는 영상, 프롬프트·피드백이 연결된 `segments.jsonl`, 평가 마감 상태가 들어간다. 파일명은 새 경로를 사용한다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.validate_capture \
  "output/collections/$phyrc_run_id" --output "output/collections/$phyrc_run_id/validation.json"
mkdir -p output/review-exports
python tools/segment_review.py --root output/segment-review bundle \
  --run "$phyrc_run_id" --collection "output/collections/$phyrc_run_id" \
  --out "output/review-exports/$phyrc_run_id.zip"
```

| 확인 목적 | 근거 |
|---|---|
| 정확한 원본 관측과 행동 | `output/collections/RUN/policy.hdf5`의 `data/demo_0/actions[start_step:end_step]`. 0전이 정지 화면은 행동 표본 수에 포함하지 않는다. |
| 목표·실제 효과·계보 | JSONL의 `stage`, `outcome`, `labels`, `parent`, `source_group`, 이전 지시와 다음 제안, 피드백 ID. 동일 run을 여러 독립 시연으로 세지 않는다. |
| 실제 조작과 정착 | `output/operator-traces/RUN/segment-evidence/hold-NNNN/actions.json`에 명령별 결정 번호, 2×9 동작, 실제 범위, 각 로봇의 세계좌표 그리퍼 변위(mm)가 있다. `model`과 `controller_settle`을 구분한다. 영상에서 확인한 천의 움직임은 별도다. |
| 점수·학습 검수 | `score_breakdown_before/after`, `evaluator_success_before/after`, 최종 평가의 유효성, capture QC를 대조한다. 값이 `null`이면 해당 경계에서 판정 근거가 없었다. 검토·학습 승인 전에는 영상을 자동 성공 예제로 채택하지 않는다. |

닫힌 데이터를 비공개로 보관할 때는 아래 명령으로 HDF5, 최종 평가와 구간별 실제 명령·변위 기록을 함께 묶고, 검토 ZIP을 같은 run ID로 연결한다.

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python scripts/preserve_collection.py \
  --run-id "$phyrc_run_id" --bundle-id "$phyrc_run_id-raw" --pack
```

서버 종료 전 ZIP을 별도로 보존한다. 비교 분석에서는 `source_group`과 회차를 기준으로 분리한다.

[수집기](../../participant/collection/codex_client.py) · [HOLD와 재개](../../participant/collection/user_review.py) · [영상 분석·제안·피드백 연결](../../participant/collection/segment_bridge.py) · [구간 저널·서버](../../tools/segment_review.py)
