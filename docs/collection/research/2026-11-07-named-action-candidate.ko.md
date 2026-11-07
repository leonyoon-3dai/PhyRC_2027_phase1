# 명명된 행동 채널 출력 후보

**행동 표현의 신뢰성 후보이며 새로운 천 조작 전략이 아니다.** 별도 branch `experiments/named-action-candidate`에서 공개 기준 `5767a4829fc08d8a0ffdeb1a5037f300a0d2111d`에 추가했다. E18 종료 뒤 실제CLI 합성2턴과 모델 없는 실제GPU3기록 연결 검증을 완료했다. 실제 의복 조작의 채널 오류 감소와 착의 성능은 미검증이다. E18 실행 중에는 실행 파일을 수정하지 않았다.

## 관측된 문제와 제한된 목적

E18 `20261106-astra-guide470-depth-001`의 공개 최종 결정 D16은 함께 전진하고 지지를 유지한다고 설명했지만 robot1 실제 행에는 `wrist_roll=+1`이 포함됐다. D17에서 모델은 이전 회전이 코너를 비틀었다고 판단하고 `−0.5`로 복구했다. D21/D22에서도 같은 패턴을 확인했다. 출처는 해당 run의 `output/operator-traces/<run-id>/decisions.jsonl`에 기록된 최종 결정·명령이며 비공개 모델 추론이나 내부 천 상태가 아니다.

| 결정 | robot1의 실제 요청 행 | 전이 | 최종 운영 설명 |
|---|---|---:|---|
| D16 | `[.35,0,0,0,0,0,0,1,1]` | 8 | 함께 전진, 손과 입구 관계 관측 |
| D17 | `[0,0,0,0,0,0,0,−.5,1]` | 8 | 직전 추가 roll과 비틀림을 인정하고 부분 복구 |
| D21 | `[.3,0,0,0,0,0,0,1,1]` | 8 | 손을 향해 입구 전진, 관계 관측 |
| D22 | `[0,0,0,0,0,0,0,−.5,1]` | 8 | 직전 의도하지 않은 roll을 인정하고 복구 |

[E07 공개 최종 행동](../attempts/20261106-astra-coordinated-fresh-001/decisions.jsonl)의 D27에도 robot1 `wrist_roll=+1`이 포함됐다. 이 반복은 배열 칸과 의미의 결합을 명시하는 비교를 정당화하지만, 모델 오류 원인이 오직 인덱스 착오라고 입증하지 않는다. 명명된 출력에서도 모델이 잘못된 값을 선택할 수 있다.

## 선택과 변환

`--named-actions`는 기본 OFF이고 exec·`--plan-size 1`에서만 허용한다. cloth strategy와 독립된 옵션이므로 기존 B 또는 목 우선 전략을 유지하면서 출력 표현만 비교할 수 있다. Astra/ultra, CLI 경로, 공식 행동·물리·범위는 바꾸지 않는다.

ON이면 `action`은 `robot_0`, `robot_1` 객체이며 각 객체는 다음 이름을 정확히 한 번씩 포함한다.

```text
base_forward, base_left, base_CCW_yaw, lift, arm_extension,
wrist_yaw, wrist_pitch, wrist_roll, gripper
```

각 값은 기존과 같은 정규화 명령이다. 지정 순서로 값을 배열에 배치한 뒤 기존 `validate_decision`과 공식 `validate_action`을 거쳐 float32 `(2,9)`로 dispatch한다. 배율·부호·물리 제한을 바꾸거나 값을 잘라내지 않는다. 설명 문장으로 의도를 추측하지 않고 유효한 roll도 막지 않는다. 전진 `.35`와 닫기 `1`을 해당 이름에만 넣으면 robot1 행은 `[.35,0,0,0,0,0,0,0,1]`이다.

누락·추가·오탈자 이름, 배열 대신 이름 객체가 아닌 값, bool·비유한·범위 초과를 거부한다. 중복 JSON 키는 기존 exec actor parser에서 먼저 거부한다. stop/finish는 기존 18개 0값·steps=1 조건을 적용한다. 이름 순서는 변환 결과에 영향을 주지 않는다.

## 기록·질의·기본 OFF

최종 결정에는 canonical 배열과 별도로 `named_action.raw_action`, 고정 mapping schema 및 mapping SHA를 남긴다. attempt에는 로봇·채널 순서와 값 변환 없음, 공식 dtype을 기록한다. 공개 exporter는 원래 이름 값과 canonical 결정의 일치, 정확한 허용 필드를 확인한다. collection 모듈이므로 기존 source snapshot과 보존 허용 범위에 포함된다.

픽셀 질의와 함께 켜면 초기 응답과 후속 응답 모두 이름 객체만 사용한다. 질의 placeholder도 모두 0이어야 하며 실행하지 않는다. frozen observation ID·시각·16이미지와 질의 request/depth 의미는 바꾸지 않는다. 후속은 이름 기반 action-only schema이며 재질의를 거부한다. 잘못된 응답에서 모델의 act는 실행하지 않는다. 기존 중단 정리의 별도 neutral stop 1전이는 발생할 수 있으며 질의의 물리 진행과 구분한다.

OFF의 기존 9개 전략을 고정 공개 기준과 비교했다. 질의 ON/OFF 각각에서 actor prompt·schema·이미지·호출 순서·simulator 명령은 동일했다. 새 이름 기록 필드는 OFF에서 생성하지 않는다. 새 코드 파일이 source snapshot에 포함되는 사실은 코드 출처 차이이며 행동 프로토콜 변경이 아니다.

## CPU 검증과 다음 비교

다음 **71개 CPU 검사 통과**: 신규 12개와 기존 depth·actor·전략·snapshot·보존 검사 59개. 신규 검사에는 18개 단일 채널의 양 부호, 키 삽입 순서, 의도한 roll 유지, 이름/값 거부, 중복 JSON, stop/finish, 기본 OFF 동등성, 질의 16이미지 고정, 0이 아닌 placeholder·잘못된 후속·재질의 거부, 공개 provenance 불일치 거부가 포함된다. 초기 신규 검사의 한 오류는 테스트가 PNG bytes를 JSON으로 직렬화하려던 문제였으며 prompt 문자열만 검사하도록 고쳤다.

```bash
PYTHONPATH=.:tests:src/PhyRC_Sim \
  .venv/bin/python -m unittest \
  test_named_actions test_depth_query test_codex_actor test_neckline_strategy \
  test_regrasp_strategies test_support_diagnostic_strategy \
  test_wrist_depth test_preserve_collection -q
```

독립 읽기 전용 검토에서 기존 상수·공식 검증·관측 함수 불변과 변환·질의·공개 기록 경계에 중요 결함을 발견하지 못했다. 실제 오류 감소를 보장하는 검사는 아니다. 후속 비교는 원본 종료·전수 검증 뒤 유용한 접근 상태의 공개 행동 prefix를 새 실행하고, 같은 cloth strategy에 이름 출력만 더하는 방식이 적절하다. 예를 들어 B+query를 유지하고 명명 출력만 켜면 재파지/접근법 변경과 표현 변경을 섞지 않을 수 있다. 후속 실제 비교는 이미 승인된 실험 범위에서 새 run ID·소스·원본 출처를 기록하고 수행한다.

## 후속 실제 CLI 검증 · 합성 16이미지·2턴·물리 0

후보 통합 뒤 사용자 범위 내에서 **실제 `codex-cli 0.166.0` / Astra·ultra 2턴을 실행해 통과했다.** 위 CPU 후보 단계의 actor 미실행 상태와 구분한다. 의복 조작과 의미 있는 위치 선택을 검사한 것은 아니다.

[`probe_depth_query_protocol.py`](../../../scripts/probe_depth_query_protocol.py)에 선택적 `--named-actions`를 추가했다. 첫 응답은 이름 기반 18개 0값의 depth 질의이고, 동일 관측의 후속 응답은 이름 기반 action-only다. 후속에는 robot1 `base_forward=.35`, `gripper=1`만 지정하고 `wrist_roll`을 포함한 나머지 값을 0으로 요청했다. 반환값을 기존 검증기에 통과시켰으며 물리로 dispatch하지 않았다.

```bash
PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH" \
PYTHONPATH=. .venv/bin/python scripts/probe_depth_query_protocol.py \
  --output output/named-depth-query-probe-20261107-001 \
  --model-timeout 180 --named-actions
```

`--output`은 새 경로여야 하며 위 명령은 실제 모델을 최대 2회 호출한다. 기존 Actor의 인증 사본·격리 Docker·공개 요청 디렉터리와 도구 이벤트 거부를 그대로 사용했다. actor에 전달된 것은 합성 공개 관측과 과제별 fixture 지시뿐이며 소스·audit·평가를 전달하지 않았다.

| 검사 | 실제 결과 |
|---|---|
| 응답 | named zero `depth_query` → named `act`, 2전이 요청이지만 실행하지 않음 |
| canonical robot1 | `[0.3499999940395355,0,0,0,0,0,0,0,1]` float32. roll은 0 |
| 이미지·시계 | 양 호출 16장, actor staging PNG 16/16 바이트 동일, 같은 frozen ID·공개 시계 |
| 세션·조회 | 같은 세션 resume, 합성 픽셀 optical Z 0.75m·invalid null |
| 시간 | 호출 경로 9.458초 +7.554초, 준비·정리 포함 17.881초 |
| 토큰 | 호출 차분 합계 입력 40,627·출력 474. 내부 추론 시간은 제공되지 않음 |
| 실행·정리 | simulator 생성 없음, 물리 0전이·GPU 0회, Actor.close 성공 |

[선별 JSON 증거](../assets/20261107-named-action-candidate/synthetic-cli-probe.json)에 원래 명명된 최종 출력과 canonical 배열, mapping SHA, schema·prompt·소스·이미지 SHA, 숫자 사용량을 보존했다. 원시 CLI events·인증·세션 ID·추론 원문은 포함하지 않았다. 실행 summary SHA256은 `4929f43b97cad7d278ab43cc2faa8d94d24b8208d4917900f5b49d6508351682`다.

probe 수정 뒤 named/depth CPU 28개와 Python compile 검사를 통과했다. 모델이 지시된 합성 값을 올바른 이름으로 반환한 한 번의 연결 검사이며, 실제 장면에서 실수 감소·같은 접근의 개선·착의 점수 향상은 아직 검증하지 않았다.

## 실제 GPU 수집 연결·전체 검사

`20261107-named-depth-wiring-001`은 E18 종료 후 모델 없는 fixture로 실제 수집기를 실행했다. 질의1회(물리0)→이름 기반 lift/그리퍼 열기2기록→stop1→finish0, 총3기록이다. 원래 이름별 값과 canonical 결정, 실제 적용 action의 채널을 확인했고 **전수3/3검사 통과**했다. 실모델 호출0·fixture호출4이며 착의 시연이 아니다. [선별 보고서](../assets/20261107-named-action-candidate/model-free-gpu-wiring.json) · [고정 원본 재다운로드 검증](../../project/sessions/20261107-named-depth-wiring-backup-verification.json)

```bash
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python scripts/probe_depth_query_wiring.py \
  --run-id 20261107-named-depth-wiring-001 --named-actions \
  --report output/sessions/20261106-evening/named-depth-wiring-001.json
```

위 경로는 이미 존재하므로 재실행 때 새 이름을 사용한다. 연결 driver의 named 경우는 CPU fake-collector로 실제 dispatch 채널과 query0기록을 비교했다. probe들을 포함한 최신 전체 **270개 CPU검사를10.077초에 통과**했다. source snapshot은 실제 실행 당시의 커밋·수정 여부를 보존하며, wiring의 source_working_tree_modified=true를 깨끗한 소스 실행으로 바꾸어 쓰지 않는다.
