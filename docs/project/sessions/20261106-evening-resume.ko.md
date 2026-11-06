# 2026-11-06 저녁 · 클린 L40S 복원과 10점 목표 재개

사용자 요청으로 E15 마감의 일시 중지를 해제했다. 라이브 화면 없이 다양한 접근을 실행하고 공식 원점수10점 이상을 목표로 한다. 달성 전에는 미달성으로 기록한다. **E16은0/50·첫 소매0·success=false로 종료했고516/516전이 검사를 통과했다. 최고 기록5/50과10점 미달성 상태는 그대로다.** [최신 영상·피드백](../../gallery/README.ko.md) · [E16 원인 검토](../../collection/reviews/20261106-astra-support264-002.ko.md)

- 시작 소스: `06980e2` (전체 해시는 git 이력 참조).
- 호스트: NVIDIA L40S 46068MiB, 드라이버580.126.09, Docker29.1.5, Python3.12.16.
- HF CLI2.4.0 설치 완료. 사용자 별도 터미널 로그인 확인. 고정 초기백업 SHA256·11,779,782,360 bytes 검증 및 전체 복원 완료.
- 로컬 Codex CLI0.166.0 설치 완료. 전역0.167.0과 분리.
- 고정 Isaac Sim6.0.1 Docker 이미지 build 완료 (로컬 이미지 `sha256:e16e818c13383e014314411c575fed273e24f0531cd0e8ac80cfbb37f16a9ed8`). 이후 아래 smoke와 실제 수집 연결 검사를 통과했다.
- 기준 소스 CPU unittest **208개 통과** (6.730초). 로그 `output/sessions/20261106-evening/cpu-baseline.log`.

## 초기 비교 설계 · E16 실행 전 계획

1. 초기264경계 분기에서 닫힘 상태의 안정과 각 그리퍼의 독립 지지를 순서대로 확인한다. 양쪽 동시 들기와 구분하고 정지측 실제 변위·천 움직임을 함께 검토한다.
2. 지지가 확인된 경우 입구와 그리퍼를 분리해 보이는 경계를 유지하며 손에 접근한다. 지속 가림 시 같은 전진을 반복하지 않는다.
3. 독립 지지가 불명확하면 더 이른258경계 또는 새로운 초기 상태에서 테이블 지지·재파지 전략을 비교한다.

공식 점수·success는 actor 입력 밖에서 확인한다. 재실행 prefix와 새 모델 행동·제어기 중립을 분리하며 같은 E07 출처의 분기를 독립 성공률 표본으로 세지 않는다. 새로운 실행의 `--review-points 10`을 명시하여 기존 기본5점에서 조기 종료하지 않도록 한다.

## 추가 사용자 지시와 방법 전환 기준

사용자는 충분한 미세조정 뒤 새로운 방법이 필요한지를 계속 분석하도록 요청했다. 각 실험에서 (a) 바꾼 변수, (b) 실제 공개 관측 변화, (c) 같은 실패의 반복 여부, (d) 다음 선택을 기록한다.

- 짧은 보정 뒤 가시적 림·손·천의 상대관계가 개선되는 동안만 해당 접근을 유지한다.
- 연속 보정에도 가림이 그대로이거나, 같은 접힘/외부 패널 접촉으로 돌아오거나, 실제 관절이 목표에 이르지 못한 채 명령만 누적되면 해당 미세조정의 근거가 약해진 것으로 분류한다.
- 이후 새 시도에서는 재파지의 위치/층, 중력에 의한 펼침, 두 로봇의 지지·가이드 역할, 접근 방향 또는 공개 관측 도구 중 하나를 구조적으로 바꾼다. 모델 프롬프트 문구만 달라진 것을 새로운 조작 방법으로 세지 않는다.
- 점수 개선이 없어도 독립 지지·입구 가시성·손 통과 여부 중 어떤 불확실성을 줄였는지 따로 기록한다. 새 방법의 필요성은 분석 결론이며 성공을 보장하지 않는다.

새 `coordinated-support-diagnostic` 전략과 실행 제약을 추가했다. 전략 추가 당시 전체 CPU 검사212개를 통과했다(6.454초). 이후 E16에 적용했다. E13·E15에서 비대칭 lift·tilt가 이미 사용됐으므로 그 자체는 새 방법으로 세지 않는다.

## 복원 검증

초기 고정 백업 `e1d32f9f9ea82438f90bc379452abf83a150999b`를 새 staging에 내려받아 archive SHA 및 manifest 전수 검증 후 충돌 거부 병합했다. 잠긴 자산8개 모두 일치. E07 **1,067/1,067전이**, `quality_passed=true`, 오류0. prepare는 종료0·7.262초. smoke는 종료0·`PHYRC-SMOKE-PASS`,266.557초로 마쳤다. [복원 검증 기록](20261106-evening-restore-validation.json)

[방법 전환 비교표](20261106-method-switch-matrix.ko.md)에 기존 시도의 공개 관측·최종 행동 근거, A/B/C 후보와 미세조정 포화 기준을 연결했다. 공개 관측만 분석하는 `scripts/analyze_support_diagnostic.py`는6개 CPU 검사를 통과했고 복원된 E07에서도80개 구간 중79개 측정, 마지막 후속 관측 누락1개를 구분했다. 이 분석은 천 지지·착의 성공을 자동 판정하지 않는다.

개발 작업은 `experiments/20261106-evening-resume`에서 진행했다. 픽셀 질의 후보는 `8f9f30b555e5ac0d89275023994ac069d1d20af0`으로 이 작업 브랜치에 통합했다. E16 실행 소스05152fa와 이후 통합 소스를 구분한다. main 게시와 현재 작업 상태는 [STATUS](../STATUS.md)를 따른다. 인증값은 코드·문서에 보존하지 않는다.

## 전략 구현과 적용 상태

- `coordinated-support-diagnostic`: 각 그리퍼 순차 지지 확인. E16 실제 적용 완료.
- `coordinated-regrasp-hem`: 좁은 입구가 포화되면 다른 가시적 경계·층으로 한쪽 재파지. E17 A 경로로 준비 중이며 아직 과제 실행 전.
- `coordinated-support-guide`: 한쪽 몸통 지지·다른 쪽 소매 방향 가이드로 배치 변경. 구현·CPU 검증 단계이며 과제 미실행.

세 전략은 단일 행동 뒤 관측을 요구한다. 기존 파지/입구가 유용할 때 재파지를 강제하지 않으며, 실제 행동이 바뀌었는지는 기록을 보고 판단한다. 기존6전략 프롬프트는 보존했다. 세 전략 구현 당시 전체 CPU 검사 **222개 통과**(6.489초). 이후 질의·보존 기능 통합본은 **251개 통과**(7.369초). 코드 존재/CPU 검사와 과제 성능 검증을 구분한다.

## 실제 실행

- smoke: 종료0·`PHYRC-SMOKE-PASS`,266.557초. 초기 shader 준비 포함, 착의 성능 시험 아님.
- wiring `20261106-evening-wiring-001`: Astra/ultra·CLI0.166.0/exec,3호출·3판단·3전이, 정상 종료 및 전수검사 통과. 점수0/50·성공 시연 아님.
- **E16 첫 요청·시작 전 실패** `20261106-astra-support264-001`: 실행 소스 `05152fa4bf250257481cae988b6f8f26c817084a`, E07 prefix264, parent E15, `coordinated-support-diagnostic`, plan1,40판단/최대1600전이, 중립6·손목depth·단계계측, review10. 부모 표시를 E15로 주었지만 실제 재실행 원본 E07과 일치해야 하므로 인자 검사에서 차단됨. 모델·GPU 호출0, capture 없음. 실패 로그 `output/sessions/20261106-evening/e16.log` 보존.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261106-astra-support264-002 --mode dressing \
  --strategy coordinated-support-diagnostic --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-coordinated-fresh-001 --replay-prefix-steps 264 \
  --parent-attempt 20261106-astra-coordinated-fresh-001 --retry-reason sequential_support_diagnostic_parent_corrected \
  --decisions 40 --max-steps 1600 --model-timeout 600 --wrist-depth-panel \
  --post-action-settle-steps 6 --profile-step-phases
```

**E16 재시작·종료** `20261106-astra-support264-002`: 위 명령처럼 부모를 E07로 수정했고 나머지 전략/예산은 동일했다. **22:46:26–23:19:06 UTC에 실행 후 모델 자율 종료했다.** E15는 비교 대상이지 직접 재실행 부모가 아니다. 실행 시작 시 문서 갱신만 미커밋 상태였으며 조작 코드는05152fa와 동일했다.


## E16 최종 결과·분석·보존

| 항목 | 확인값 |
|---|---|
| 로컬 공식 평가 | **0/50·첫 소매0·success=false**, 점수율 상태 `no_contact / null` |
| 종료·행동 | 운반 없이 모델 자율 종료. **34호출·34판단 = act33회 + finish_episode1회** |
| 전이 | **516 = E07 재실행264 + 새 모델156 + 제어기 중립96** |
| 기술 검사·승인 | complete·**516/516전이 통과**·학습 승인 `unreviewed` |
| 시간 | 실제 **1,959.82056초**. 모델 호출 경로1,451.035초, 환경456.8095초. 순수 모델 추론시간은 미제공 |
| 입력 | 현재 RGB5장·공개 로봇 상태·16×16 depth 요약·손목 depth 패널. **픽셀 질의 미사용** |
| 실행 소스 | `05152fa4bf250257481cae988b6f8f26c817084a` |

양측을 따로 시험했고 로봇0의 같은 오른쪽 가장자리 재파지와 재시험을 실제 실행했다. 후반 국소 천 동행의 시각적 근거를 얻었지만, 두 지지점 사이에 통과 가능한 연속 입구는 확인하지 못했다. **0점만으로 파지 실패를 단정하지 않는다.** 같은 가장자리의 회복과 다른 경계·층으로의 조작 방법 변경도 구분한다. [경계별 관측·한계](../../collection/reviews/20261106-astra-support264-002.ko.md)

[세 구간 갤러리](../../gallery/20261106-astra-support264-002.ko.md)에 지지 진단264–352, 재파지352–440, 지지 재확인·입구 시도440–516을 보존했다. 카메라·선택 경계·원본 SHA·재생 조건을 각 provenance에 남겼다. README 상단에서 최신 큰 GIF·MP4·분석·피드백 작성 링크로 연결한다. 실제 피드백 issue나 메시지는 자동 발송하지 않았다.

E16 원본은 비공개 HF `leonayoon/phyrc-2027-phase1-private-backup`의 **revision `1ad0f8ba3cc71ab80962907c713357fbd4005e3f`**에 보존했다. archive **1,181,871,453 bytes**, SHA256 `88926022d38c8e98c5e82f457c307205a357f5ab70be3f618854b51a16a39333`이며 **23:24:18 UTC에 고정 revision 재다운로드 SHA 일치를 확인**했다. [검증 receipt](20261106-e16-backup-verification.json)

허용된 collection·평가/audit·최종 행동·프롬프트·source snapshot·공개 관측만 보존한다. 평가/audit는 비공개 검수 자료이며 actor 입력이 아니다. simulator 로그·인증·actor runtime·원시 CLI 이벤트·추론 원문은 묶음에서 제외했다. [앞선 wiring 원격 검증](20261106-evening-wiring-backup-verification.json)

## 픽셀 depth 질의 통합·연결 검증

후보 코드를 `8f9f30b`로 통합한 뒤 전체 CPU **251개 검사를7.369초에 통과**했다. 로그 `output/sessions/20261106-evening/cpu-integrated.log`, SHA256 `a95a924e316f58adf44b93c4358d878cac4e7926ebb2e77de250ab11897551bd`다. 이 검사 수를 E16 실행 당시 결과로 소급하지 않는다.

| 검사 | 실제 수행 | 확인한 범위 |
|---|---|---|
| 합성 관측·실제 CLI | Astra/ultra·고정 CLI0.166.0으로2턴, 같은 세션·16이미지 재사용, 물리0·GPU0 | schema·세션·이미지·정확한 depth lookup 연결 |
| 실제 GPU·모델 없는 wiring | `20261106-depth-query-wiring-001`, 결정론적 fixture4호출, **질의1회·질의 물리0전이·실모델 호출0** | 정상 수집기에서 질의 placeholder 미실행과 후속 실제 행동 |
| wiring 전수 검사 | **3/3전이 통과**, query0 → 작은 움직임2 → stop1 → finish0의 물리 전이 | 전체 capture·HDF5·ACK·정상 마감 |
| 실제 착의 적용 | E16 미사용, 실제 과제 모델의 픽셀 선택·질의 사용 없음 | 의미 있는 표면 선택·득점 향상은 미검증 |

여기서 **질의0은 물리 전이 수이며 질의 호출 수가 아니다.** wiring fixture가 공개 관측에 대한 질의를1회 실행했고 실제 모델은 호출하지 않았다. 연결 시험의0/50·success=false는 착의 성능 결과로 비교하지 않는다.

원본 보고서는 `output/sessions/20261106-evening/depth-query-wiring-001.json`(SHA256 `d63546030c3952ae0f6aba1cd2121301adf9e4430eb0fd4cc65c3f818570a565`), 전수검사는 `output/collections/20261106-depth-query-wiring-001/validation.json`(SHA256 `089e4c5009a0c6c9d080ec2dc75839e5841464a3f2fcb9ea79e0d651e8f15b85`)이다. [기능·각 검증 범위·재현 명령](../../collection/research/2026-11-06-pixel-depth-query-candidate.ko.md)

## 다음 E17 A 경로 · 계획이며 아직 실행하지 않음

다른 가시 입구 경계·층에서 실제 한쪽 재파지를 비교한다. E16의 같은 오른쪽 가장자리 회복과 구분한다. E16 prefix352를 새 환경에서 재실행하고264·346경계의 관측도 새로 얻는다. 현재 지지는 다시 판단하며 과거의 국소 지지를 그대로 보장하지 않는다. 픽셀 질의는 끈다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261106-astra-layer352-001 --mode dressing \
  --strategy coordinated-regrasp-hem --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-support264-002 --replay-prefix-steps 352 \
  --parent-attempt 20261106-astra-support264-002 \
  --retry-reason different_visible_rim_layer_after_support_diagnostic \
  --replay-observe-steps 264 346 --wrist-depth-panel \
  --post-action-settle-steps 6 --decisions 50 --max-steps 1800 --model-timeout 600
```

main 게시 확인 후 새 run ID로 진행할 계획이며, 현재 이 명령의 실행 결과는 없다. 지지·입구·손 통과·평가 점수·학습 승인은 계속 분리해 기록한다.
