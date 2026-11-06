# 공개 픽셀 depth 질의 · 통합·실제 CLI·모델 없는 GPU 연결 검증

**후보는 `8f9f30b`로 작업 브랜치에 통합됐고, 통합 CPU251개·합성 입력 실제 CLI2턴·모델 없는 실제 GPU wiring3/3전이 검사를 통과했다.** 종료된 E16에는 픽셀 질의를 사용하지 않았다. 실제 착의 모델의 픽셀 선택·질의 사용·득점 향상은 아직 미검증이다. GPU wiring은 **질의1회·질의 물리0전이·실모델 호출0**이며, 물리0을 질의 호출0으로 혼동하지 않는다.

## 출처와 변경

- 후보 브랜치: `experiments/depth-query-candidate`, 기준 `05152fa4bf250257481cae988b6f8f26c817084a`. 이후 `8f9f30b555e5ac0d89275023994ac069d1d20af0`으로 `experiments/20261106-evening-resume`에 통합했다. E16 실행 소스와 이후 통합 소스를 구분한다.
- 원본 후보: 비공개 연구 인계의 `.runtime/depth-query-integration-candidate/`, HF 고정 revision `3349b6a73bf266cfba015654613e58ae490290b5`. 복원한 prototype/integration 관련 20개 파일의 크기·SHA256을 `scope.json`과 대조했다.
- 기존 client 전체를 교체하지 않고 기능 단위 patch를 적용했다. 이번 독립 지지·밑단 재파지·지지/가이드 전략과 기존 전략을 보존했다.
- `participant/collection/depth_query.py`: 고정된 현재 공개 depth/mask와 정적 K만 사용하는 순수 조회. 지정 카메라 하나·정수 1–8점·한 관측당 1질의. 정확한 optical Z 또는 null, 선택적 camera XYZ/range. 보간·주변값 대체·world 변환·숨은 표면 추정 없음.
- `codex_client.py`: 기본 OFF의 `--pixel-depth-query`, exec/plan-size1만 허용. 최초 응답 JSON을 분기하고 질의 placeholder는 실행하지 않는다. 같은 관측·이미지의 후속 1호출은 원래 행동 schema만 허용한다. 호출별 사용량·입력 SHA·질의 결과와 실제 전이를 분리한다.
- `export_report.py`: 모델 호출·조회·실패의 공개 허용 필드만 기록한다. session ID·원시 CLI 이벤트·추론 원문을 공개하지 않는다.
- `source_snapshot`은 조회 모듈과 재사용한 역투영 모듈도 보존한다. `--model-timeout`은 180초 이하를 명시해야 하며 collector idle timeout은 `2*model_timeout+120`이다.

## CPU 검증

후보 단계에서 **238개 검사 통과**, 이 중 신규 질의 검사는16개였다. 모델 없는 wiring driver의 CPU4개와 보존 검사를 함께 포함한 **통합본 전체251개 검사도7.369초에 통과**했다. `output/sessions/20261106-evening/cpu-integrated.log`의 SHA256은 `a95a924e316f58adf44b93c4358d878cac4e7926ebb2e77de250ab11897551bd`다.

```bash
PYTHONPATH=.:tests:src/PhyRC_Sim .venv/bin/python \
  -m unittest discover -s tests -p 'test_*.py' -q
```

- 고정 기준 소스와 flag OFF의 schema·prompt·image bytes·명령·호출 수 동등성. 이번 3개 전략과 16이미지 구성을 포함한다.
- query→action의 두 호출 사이 simulator dispatch 0회. 실제 replay history 10장+현재 RGB 5장+현재 depth 1장의 16장 순서·SHA 유지.
- stale/과다/bool/혼합/비영 placeholder·반복 질의·잘못된 후속 행동 거부, 두 호출의 timeout·중단, 이미지 변경 감지.
- 누계 input100→160의 차분100+60, 후속 실패 시 첫 사용량 보존·미확정 호출 구분.
- 정확한 Z, invalid/null, 영상 경계, 표시범위 밖 값 비절단, Z와 ray range 구분. 공개 export의 가짜 비공개 필드 제외.

첫 전체 실행은 `PYTHONPATH`에 `src/PhyRC_Sim`이 빠져 import가 실패했고, 확장된 source snapshot의 연구 모듈을 기존 시험 fixture에 추가해야 했다. 경로와 fixture를 수정한 뒤 위 전체 검사가 통과했다. GPU·모델을 사용하는 CPU 검사로 설명하지 않는다.

## 실제 CLI 2턴 · 물리 0

[`scripts/probe_depth_query_protocol.py`](../../../scripts/probe_depth_query_protocol.py)는 합성 공개 관측만 생성한다. simulator를 만들지 않으며 source/audit/점수 파일을 actor에 전달하지 않는다. 기존 Actor의 Docker 내부망·제한된 송신·전용 인증 사본·공개 요청 디렉터리·도구 이벤트 거부를 사용했다.

```bash
PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH" \
PYTHONPATH=. .venv/bin/python \
  scripts/probe_depth_query_protocol.py \
  --output output/depth-query-probe-20261106-001 --model-timeout 180
```

`--output`은 존재하지 않는 새 경로여야 한다. 이 명령은 실제 모델을 최대 두 번 호출하므로 CPU 검사 명령과 구분한다.

| 측정 | 결과 |
|---|---|
| 모델·CLI | `gpt-6-astra` / `ultra`, `codex-cli 0.166.0` |
| 응답 | 확장 schema의 `depth_query` → 원래 schema의 `finish_episode` |
| 세션 | 동일 세션 resume 확인. 원시 ID는 공개하지 않음 |
| 이미지 | 16장 → 동일 16장. actor에 staging된 PNG 16/16의 바이트 일치 추가 확인 |
| 수치 | 지정 합성 픽셀의 optical Z `0.75m`, invalid 픽셀 `null` |
| 호출 시간 | 7.756초 + 5.999초. 준비·정리 포함 전체14.477초 |
| 입력/출력 토큰 | 실제 호출 차분 합계39,761 /311. 내부 추론 시간은 제공되지 않음 |
| 물리·GPU | simulator 생성 없음, 물리0전이, GPU0회 |
| 정리 | Actor.close 성공 |

[선별한 구조화 증거·소스 SHA](../assets/20261106-pixel-depth-query-candidate/synthetic-cli-probe.json). 합성 fixture가 요청할 좌표를 명시했으므로 모델이 실제 손·입구를 찾았다는 결과가 아니다. 관측은 정확한 lookup과 schema/session/image 전송을 검사하기 위한 합성 자료이며 시연 데이터가 아니다.

## 통합 검토와 남은 적용 한계

독립 검토에서 보존 도구와의 허용목록 불일치를 발견했다. 현재 보존 도구는 `participant/research/depth_backprojection.py`만 정확한 source snapshot 경로로 선택 허용한다. 기존 snapshot에 이 파일을 필수화하지 않으며 임의 research 파일은 거부한다. 보존9개 CPU 검사와 통합본251개 검사로 회귀를 확인했다. 입력격리·질의 중 dispatch·호출별 사용량·중단 경로에서는 추가 중요 결함을 찾지 못했다.

실제 collector의 모델 없는 GPU wiring도 아래와 같이 완료했다. 이 결과와 합성 입력의 실제 CLI 검사는 서로 다른 범위다. **실제 모델이 실제 의복 장면의 표면을 선택해 질의하고 그 결과로 행동하는 전체 과제 경로는 아직 검증하지 않았다.**

1. 실제 공개 RGB에서 모델이 의미 있는 가시 표면을 선택하는지 검토해야 한다. 가려진 점에 억지 좌표를 채우지 않고 invalid를 빈 공간으로 해석하지 않는다.
2. 지지와 입구가 보이는데 가시 점 사이 깊이 관계만 모호할 때 제한적으로 비교한다. 입구 위상 불명·그리퍼 가림·미확인 파지는 재파지·펼침·접근면 변경으로 먼저 구분한다.
3. 같은 시각·같은 카메라의 점만 비교한다. 서로 다른 시각의 같은 카메라 이름도 동일 좌표계를 보장하지 않는다. 선택 표면 사이 거리가 통과 여유·접촉·소매 통과를 뜻하지 않는다.
4. 질의는 모델 왕복을 추가한다. 합성 연결 검사 시간으로 실제 수집 지연·호출 절감·득점 개선을 주장하지 않는다.

E16은 픽셀 질의 없이0/50·516/516전이 검사 통과로 마감했다. E16 원본과 당시 소스는 보존했으며 후보 통합을 과거 실행에 소급하지 않는다. 다음 E17 A 경로도 현재 계획에서는 질의를 끈다. [E16 결과·후속 계획](../../project/sessions/20261106-evening-resume.ko.md)

## 모델 없는 실제 collector wiring · 실제 실행·3/3전이 검사 완료

[`probe_depth_query_wiring.py`](../../../scripts/probe_depth_query_wiring.py)를 **`20261106-depth-query-wiring-001`로 실제 GPU에서 실행했다.** 기존 수집기의 Actor만 결정론적 fixture로 교체하며 simulator/기록/조회/행동 validator는 정상 경로를 사용했다. fixture는 공급된 공개 prompt·query result만 읽고 환경 객체·숨은 상태·평가·파일을 조회하지 않는다. 실제 Actor 생성·인증 접근·모델 호출은 없다.

실제 확인한 순서는 **질의1회(물리0전이)** → 양쪽 lift `+0.03`, gripper `-1`의 작은 움직임2전이 → stop1전이 → finish0전이, 합계 **3전이**다. 명시적인 finish가 실행될 여유를 남기기 위해 episode 상한은4전이로 둔다. 잘못된 placeholder 실행이나 짧은 actual action으로 기록 전이가 달라지면 driver가 실패한다. query와 follow-up의 공개 시계·관측 ID도 같아야 한다.

- `source=integration_test`, source group은 `integration-depth-query-wiring-<run-id>`.
- `model_id=synthetic-depth-query-wiring-fixture`, effort=`none`, CLI=`not_invoked`. 실제 Astra 설정 변경이나 호출이 아니다.
- client의 `actor_calls_attempted=4`는 fixture 함수 호출4회를 뜻한다. 별도 probe report에 `real_model_calls=0`과 `client_actor_invocations=4`를 함께 기록한다.
- query1회→action-only 후속1회, timeout상한180초, 단일 행동 계획. 최종 기록·ACK·요청 기대치3전이가 모두 맞아야 통과한다.
- CPU fake-collector4검사는 정상3전이, 부족한 실제 전이의 거부, 질의 중 시계변화 거부, 기존 report 보호를 확인했다. 그 뒤 별도 실제 GPU 실행과 전수검사를 완료했다.

아래는 E16 종료 뒤 순차 실행한 실제 명령이다. 같은 run ID와 보고서는 이미 존재하므로 재검사 시 새 이름을 사용해야 한다.

```bash
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python scripts/probe_depth_query_wiring.py \
  --run-id 20261106-depth-query-wiring-001 \
  --report output/sessions/20261106-evening/depth-query-wiring-001.json
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.validate_capture \
  output/collections/20261106-depth-query-wiring-001 \
  --output output/collections/20261106-depth-query-wiring-001/validation.json
```

첫 명령은 실제 simulator/GPU를 사용하고 모델은 호출하지 않았다. 두 번째는 마감한 capture의 모든 전이를 검사했다. **driver `passed=true`와 전수검사 `quality_passed=true`,3/3전이를 모두 확인**했다.

| 측정 | 실제 결과 |
|---|---|
| run ID·출처 | `20261106-depth-query-wiring-001` · `integration_test` |
| 실모델 호출 | **0회** |
| fixture 응답·질의 | **4회 응답 중 질의1회**. 이후 act·stop·finish 각각1회 |
| 물리 진행 | **질의0전이**, 실제 행동·정지 합계3전이 |
| 관측 일치 | 질의와 후속 행동의 공개 시계·관측 ID 동일, 매 호출 현재 RGB5장 |
| 전수검사 | **3/3전이 통과**, complete·정상 마감 |
| 경과 | driver 전체42.069초. 모델 추론시간이 아님 |
| 공식 평가·승인 | 0/50·success=false·`no_contact / null`, 학습 승인 `unreviewed`. 과제 시연이 아님 |

로컬 원본 보고서 `output/sessions/20261106-evening/depth-query-wiring-001.json`의 SHA256은 `d63546030c3952ae0f6aba1cd2121301adf9e4430eb0fd4cc65c3f818570a565`, 전수검사 `output/collections/20261106-depth-query-wiring-001/validation.json`의 SHA256은 `089e4c5009a0c6c9d080ec2dc75839e5841464a3f2fcb9ea79e0d651e8f15b85`다. 이 wiring은 실제 모델의 의복 표면 선택이나 득점 개선을 검증하지 않는다.
