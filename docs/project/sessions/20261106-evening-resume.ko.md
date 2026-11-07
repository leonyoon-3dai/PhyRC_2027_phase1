# 2026-11-06 저녁 · 클린 L40S 복원과 10점 목표 재개

사용자 요청으로 E15 마감의 일시 중지를 해제했다. 라이브 화면 없이 다양한 접근을 실행하고 공식 원점수10점 이상을 목표로 한다. **최신 종료 E19는5/50·932/932기록 검사 통과다. E20 목 우선 경로를 실행 중이며 최고5점으로10점은 아직 미달성이다.** 아래는 E16부터 시간순으로 보존한 실행 일지이며 각 절의 계획·검사 수는 당시 상태다. [최신 상태](../STATUS.md) · [최신 영상·피드백](../../gallery/README.ko.md)

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
- `coordinated-regrasp-hem`: 좁은 입구가 포화되면 다른 가시적 경계·층으로 한쪽 재파지. E17 A 경로가23:37:50–23:51:35 UTC에 실행됐고5/50·452/452검사 통과로 종료.
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

## E17 A 경로 ·23:37:50–23:51:35 UTC 실제 실행

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
  --post-action-settle-steps 6 --decisions 50 --max-steps 1800 --model-timeout 600 \
  --profile-step-phases
```

main 게시 확인 후 위 명령을 새 run ID로 실행했고 아래 결과로 종료했다. 지지·입구·손 통과·평가 점수·학습 승인은 계속 분리해 기록한다.

## main 통합·E17 실행 출처

E16 공개 영상·분석·검증된 백업 receipt·선택형 픽셀 depth 조회를 main **98bb41ff6e83327a468abe5129517b4739ae33a1**에 통합했다. 원격 tree `ccdeeb65fc8327f93486bd42639f8f656602097b`와 검토한 로컬 tree가 일치하고 원격 README 첫15줄을 다시 읽어 상단 갤러리를 확인했다. 원래 로컬 병합 이력은 `local-prepublication-e16-20261106` 태그에 남겼다.

E17 시작 당시 source_snapshot commit은98bb41f, working_tree_modified=false다. prompt SHA256은 `a28744202f80eb8100268a4c99c66f529cae87a75c823632c4cf6a2778be672b`. main 통합 직전 A의 지지 조건만 보강했고 관련12개 검사를 통과했다. 현재 관측에서 안정적인 테이블 지지 또는 유용한 partner anchor를 확인한 뒤 한쪽을 바꿀 수 있다. partner grip이 불확실하면 재파지 중 테이블 지지를 유지하고 운반 전 양측 지지를 다시 확인한다. 실제 효과는 E17 종료 기록으로 검토한다.

시작 이후 현재 문서만 갱신하며 실행 코드는 바꾸지 않는다. E17 log는 `output/sessions/20261106-evening/e17-layer352-001.log`다. 직접 부모 E16·source group `20261106-coordinated-demo-methods`를 보존하며, 이 재실행을 독립 시연으로 세지 않는다.

모델 없는 질의 연결 시험의 [공개 수치 보고서](../../collection/assets/20261106-pixel-depth-query-candidate/model-free-gpu-wiring.json)와 [비공개 원본 재다운로드 검증](20261106-depth-query-wiring-backup-verification.json)도 보존했다. revision `639f3b434ad853a7690bab56d637bf50144ed89d`,9,574,896 bytes, SHA256 `45225bc9af7f4b84cd362e414645bbe42ca65ed64993bdf3d92b40d650991190`,23:35:34 UTC 검증이다.

## E17 종료 결과

- 원점수 **5/50(픽업5·첫 소매0·나머지0)**, success=false·no_contact/점수율null. 기존 최고5와 동일하며10점 미달성이다.
- **452/452기록 전수검사 통과**:352재실행+52모델행동+48제어기중립, 시뮬레이션22.6초.12호출/12판단=행동11+finish1.
- 실제824.157841227초(13분44초), 모델 호출 경로378.758640188초·환경400.041776980초. 내부 추론시간은 미제공이다.
- D0–3은 현재 지지·시야/형태 조정, D4 robot0개방, D5–6 다른 lower-rim 후보로 하강·손목방향·팔 배치 보정, D7닫기8기록, D8중립6, D9양측들기, D10지지미확인으로낮춤, D11자율종료다. 다른 후보 경계를 겨냥한 재파지 자체는 실제 수행했으나 **반대 입구 층이나 양측 독립 지지 확인을 뜻하지 않는다**.
- [공개 분석](../../collection/reviews/20261106-astra-layer352-001.ko.md) · [선별 공개 패키지](../../collection/attempts/20261106-astra-layer352-001/README.ko.md) · [영상](../../gallery/assets/20261106-e17-regrasp/event.mp4). 영상은392–452의61프레임/12.2초,4배 느리게이며 모델 대기 시간은 제외한다.
- 종료 원본 보존과 원격 백업 검증을 완료했다. 결과값5만으로 새파지성공을 판단하거나 한 번의 제한 시도로 A전체가 소진됐다고 결론내리지 않는다.

다음 E18 계획은 STATUS의 B 명령이다. E16의470경계·같은 새 replay의430/464경계 사진을 사용해 몸통 지지+소매 방향 가이드 파지를 비교하고, 선택형 공개 픽셀 depth 조회를 제공한다. 동시에 다른 역할과 입력 기능이 달라져 단일 변수 비교가 아님을 기록한다. 목 우선 착의는 별도 격리 후보 코드에서 준비 중이며 아직 실행하지 않았다. [공개 근거·기존 방법과의 구분](../../collection/research/2026-11-06-post-support-methods.ko.md)

E17 비공개 원본은 고정 HF revision `d5ba6c645232c7674d3861fdf65da3a26e9e1ea9`에서1,027,542,010 bytes를 재다운로드해 SHA256 `51acf732e6744dc979fe35ae61a9c04120b247606cd24138791135d0581cbcfb` 일치를23:55:15 UTC에 확인했다. [receipt](20261106-e17-backup-verification.json). 허용목록163개 archive member의 SHA도 모두 검증했고 인증·runtime·원시 추론·CLI 이벤트·simulator 로그는 제외했다.

E17 종료 후 목 우선 후보 커밋 `e2d9d3d84b17d0418e3cd902cd9472cd9212ca49`를 병합했다. 기존8전략 프롬프트를 유지한 별도목표 경로이며 실제 모델/GPU 적용은 아직 없다. 최초 후보검사의1실패는 A 지지 문구 승인후 예전05152fa 회귀문구가 남은 것이어서, 실행 oracle은유지하고 A문구만 고정공개75492d7 기준으로수정했다. 통합본 전체 **257개검사7.529초통과**, 로그`output/sessions/20261106-evening/cpu-neckline-integrated.log`, SHA256 `dc4a022373d51224482b6d661e04859db236f2b5b83f630cb6086b0368538d83`. [후보·검증범위](../../collection/research/2026-11-06-neckline-first-candidate.ko.md)

## E18 B 실제 시작

E17 갤러리·백업·목 우선 후보·257CPU검사를 main `499b3b8cb29568e6d5530d7ce8bf039c73cd8f6a`에 게시했다. 원격/검토 로컬 tree `d8bd4f55270e5a493856204175a6eba0a42f35c4` 일치를 확인했고, **23:58:53 UTC**에 STATUS의 E18 B 명령을 실행했다. run ID `20261106-astra-guide470-depth-001`, 시작 source_snapshot은499b3b8·working_tree_modified=false다.

실제 옵션은 `coordinated-support-guide`, E16직접부모/prefix470, 새재실행 과거430·464, 현재손목depth·pixel-depth-query ON, plan1·35판단·max1400·timeout180·settle6·review10·phase profile이다. 모델/CLI는 Astra/ultra·0.166.0/exec 그대로다. 첫공개 관측은현재5+과거10+depth패널1의16이미지이며 질의후속은같은현재관측·이미지를유지한다. **질의가능 설정과 실제질의 사용은 구분**하며 종료기록에서 실제사용·query물리0·판단/호출 수를 검토한다. 로그 `output/sessions/20261106-evening/e18-guide470-depth-001.log`. 아직 최종결과는없다.

## E18 마감·학습 검토 구간·명명 행동 비교

E18은2026-11-07 00:29:56 UTC에 감독SIGINT로마감했다. 같은 전진 설명에 robot1 wrist_roll=+1이 포함된D16,D21두번의 실제명령과D17–19,D22–24복구를분리했다. 끝모델호출29(D26)는최종응답이model_call에반환됐지만실행판단이벤트·로봇행동으로적용되지않았다. client130은요청된중단이고simulator0·finished/capture_complete=true·QC928/928통과다. 물리/행동기록을수정하지않았다. 요청근거는`output/sessions/20261106-evening/e18-supervisor-interruption.json`이다.

결과는픽업5/50·모든착의항목0·success=false·no_dressing_points/0.0points/s. 30호출시도/26실행act·질의3회(각물리0),470재실행+313모델+144제어기+1종료=928기록/46.4sim초다. 실제1862.365559초,모델호출경로1000.802692초·환경806.244306초다. 실제가이드재파지는0회였고,새로실행된것은공개depth조회·운반대형/접근시야변경이다.

사용자는이러한오류·복구과정도향후학습자료로가치있다고확인했다. [구간주석](../../collection/reviews/20261106-astra-guide470-depth-001-learning-segments.json)은정상접근·두추가roll·복구·질의·감독중단을연결하며원본과source group을유지한다. training_approval=unreviewed이며숨은평가기하를행동라벨로사용하지않는다.

E18종료후명명행동후보227186d를병합했다. 기본OFF이며정확한로봇2개×채널9개키를공식순서로값변경없이변환하고기존validator/dispatch를유지한다. raw named와mapping SHA및canonical action을보존한다. 전체269CPU검사9.569초통과후CLI합성2턴(16이미지동일·같은세션·물리0/GPU0)도17.881초에통과했다. 모델없는실제GPU named+query 연결`20261107-named-depth-wiring-001`은실모델0·fixture4호출·질의1회물리0·총3/3기록검사통과했다. 실제옷조작의오류감소는미검증이다.

다음은STATUS의E19계획이다. E18의첫roll직전801경계와새재실행771/787사진을사용하고B+query에named만추가한다. 의복조작전략을바꾼비교로세지않으며재실행은정확한물리복원이아니다. 목우선후보는아직미실행으로남긴다.

최신 전체검사는270개/10.077초통과,`output/sessions/20261106-evening/cpu-named-final.log`SHA256 `eef05f8da21a5f93da6882384a2a9917dce65232b9e929afd71bd0cf626d243e`. E18prefix801의닫힌전체928원본검사·출처·재실행입력검증도통과했다.

E18원본재다운로드검증완료:revision`44d01871f0099f8a537f1bdbfee06a404a95f38c`,2,167,209,525bytes,SHA256`bfce450c5725e79ef7cf878f6412cfe08f64cf68ab91d1cc267433c079ccf470`,2026-11-07T00:36:13.693113UTC. [receipt](20261107-e18-backup-verification.json). namedwiring도revision`7817a63289250cb40e94a50a9b816eb45a567660`,9,576,993bytes,SHA256`93837540ab791ca2749def44d9ee73732a8b92e71057f6f58071fb3d473310bd`로00:38:23UTC재다운로드검증했다. [wiringreceipt](20261107-named-depth-wiring-backup-verification.json).

## E19 이름 기반 명령 · 실제 시작

E18 영상·학습 검토 구간·백업 receipt와 명명 행동 코드/검증을 main `9aad60138dc5cded2e0e5219fc12395d4c37ff0a`에 통합했다. 원격과 검토한 로컬 tree의 동일성을 확인했고 로컬 병합 이력은 `local-prepublication-e18-20261107` 태그에 보존했다.

**2026-11-07 00:45:20 UTC**에 `20261107-astra-entry801-named-001`을 시작했다. source snapshot은9aad601·working_tree_modified=false다. STATUS에 기록한 명령 그대로 E18 직접부모/prefix801,새 재실행 과거771/787, B+depth질의+명명행동,40판단/max1600/timeout180/settle6/review10을 사용한다. 로그는 `output/sessions/20261106-evening/e19-entry801-named-001.log`다. 원본 source group은 `20261106-coordinated-demo-methods`를 유지한다.

E19는 첫 추가 roll 직전의 유용했던 손 접근에서 명령 표현의 효과를 비교하는 시도다. 실제 옷 조작 전략이 바뀐 것으로 세지 않으며 새 재실행의 현재 관측에서 파지·손 관계를 다시 판단한다. 시작 후 코드·물리·행동 한계를 바꾸지 않고 현재 문서만 갱신한다. 결과는 아직 없다.

E19 재실행 중 E18 학습 구간을 독립 재검수했다. 새458기록의 연속성과313모델+144settle+1감독중립 분해, query3쌍별 동일관측·물리0, 동일 source group 및 unreviewed 표기는 일치했다. 마지막D26의 반환 응답은 기록됐지만 실행되지 않았음을 정밀화했고, D24는 운동채널0·양측gripper+1의 닫기 유지로 구분했다. [다음 경로 선택 검토](../../collection/research/2026-11-07-post-named-route-choice.ko.md)는 E19의 명령 오류 수정 후에도 관계가 포화되는 경우 E18/470 목 우선 비교를 권고하며, 이는 실행 결과가 아닌 조건부 계획이다.

## E19 종료 · 세 접근 후 목 우선 방법으로 전환

2026-11-07 01:11:37 UTC에 모델이 후퇴 후 자율 종료했고 client0·complete·932/932기록 검사를 통과했다. raw5/50은 픽업5·착의0이며 success=false·no_dressing_points/0.0points/s다. 전체932=801재실행+59모델행동+72제어기정착,46.6sim초다. 14호출/13판단=12act+finish1,질의 추가1회는 물리0이다. 실제1577.537493795초,모델호출경로736.917914924초·환경793.905204795초다.

12개 행동의 named 값·공식 배열·최종 설명은 축이 일치했다. D6의 robot0 roll+.25는 의도된 회전이며 E18 오류와 구분한다. 첫 접근 뒤 가림으로 후퇴, 한쪽 높이를 바꾼 두 번째 접근과 후퇴, roll·상방·측면 시점을 실제 바꾼 세 번째 접근 뒤에도 손 통과는 미확인이었다. 현재 테이블 지지가 없어 공중 재파지를 강행하지 않고 종료했다. 새 release/regrasp는0회다. 세 접근과 회복은 같은 E07 출처 안의 연속 자료이며 독립 시연3개가 아니다.

[공개 검토](../../collection/reviews/20261107-astra-entry801-named-001.ko.md),[학습 구간](../../collection/reviews/20261107-astra-entry801-named-001-learning-segments.json),[전체 새구간 영상](../../gallery/assets/20261107-e19-named-entry/event.mp4)을 보존한다. 영상801–932의132프레임은26.4초·4배 느리게이며 원본에 없는 중간 프레임을 만들지 않았다. 학습 승인은unreviewed다.

다음 실제 계획은STATUS의E20 명령이다. E18/470 직접부모·hist430464·coordinated-neckline-first로 목표 입구와 착의 순서를 바꾸고 named+query를 유지한다. 소매 접근의 미세조정과 새 방법을 구분한다. E19 이후 실행 코드는 바꾸지 않았으며 전체270CPU 검증을 반복 실행했다고 쓰지 않는다. E18 수집 시간의 별도 검토에서도 채택할 신규 최적화는 발견하지 못했다.

E19 비공개 원본은 고정 revision `a5f9136d1479933b6c026465a8af0321bad1504c`에서 재다운로드 SHA를2026-11-07 01:16:34.148203 UTC에 검증했다. 2,130,731,675 bytes, SHA256 `b2fabcdba6d83418561925176a8fe48e02f9596a2e391d7132cf4f269ef03ab6`,173 archive member 전수검사다. [receipt](20261107-e19-backup-verification.json). 다음E20의E18prefix470 입력검증도 통과했고 현재 실행파일이 E19의 검증된 source snapshot과 모두 같음을 확인했다.

## E20 목 우선 · 실제 시작

E19 갤러리·분석·학습 구간·백업 receipt를 main `799fe804445c6e0fc401927f0ed82b4e5dd4f935`에 게시했다. 원격/검토 로컬 tree `154159c7b7ee503faf711fa4023d4637c14f94f0` 일치를 확인하고 로컬 이력은 `local-prepublication-e19-20261107` 태그에 보존했다. 원격 README 첫 화면도 E19 영상으로 확인했다.

**2026-11-07 01:18:21 UTC**에 `20261107-astra-neckline470-named-001`을 시작했다. source snapshot은799fe80·working_tree_modified=false다. STATUS의 명령 그대로 E18 직접부모/prefix470·hist430464,coordinated-neckline-first,named+query,40판단/max1400/timeout180/settle6/review10을 사용한다. 로그는 `output/sessions/20261106-evening/e20-neckline470-named-001.log`다. 현재 재실행을 진행 중이며 최종 결과는 없다.

이번 비교는 손 접근에서 기존 파지를 유지한 E19와 달리 목표 입구·첫 착의 순서를 바꾼다. 실제 목선 파지·역할 변경 여부는 수행된 행동과 현재 공개 관측으로 검토하며 후보 이름만으로 구조적 조작이 실행됐다고 세지 않는다. 모델/CLI/공식 물리/행동 한계는 유지하고 시작 이후 현재 문서만 갱신한다.

## 추가 사용자 요청 · 공식 시연과 BEHAVIOR 2026 우승 자료

사용자는 목 접근을 지지하고 공식 성공 시연과 유사하게 도전하며 `https://behavior1k-champion.com/`의 텍스트·이미지에서 향후 시연 수집에 참고할 방법을 분석·기록하도록 요청했다. [피드백 기록](../../collection/feedback/2026-11-07.jsonl)은 실제 발화시각을 추정하지 않고 기록시각만 남긴다. E20과10점 목표는 계속 유지했다.

공식 MP4를 재다운로드했고 기존2,230,083bytes·SHA256 `96ed735d0bca97eac758c534175133b1ea8dd01e11f59c376611c8a672b93c09`와 같았다. 넓은 가장자리의 양측 지지, 머리·팔 위 상승, 하강 안착이 보이지만 목선 재파지·머리 먼저 통과의 동일성은 확인할 수 없다. [순서·한계·후속 설계](../../collection/research/2026-11-07-official-demo-route-review.ko.md). 공식 유사 상방·하강 후보는 E20을 바꾸지 않는 격리 작업 트리에서 준비한다.

BEHAVIOR 자료는[텍스트·공식 집계](../../collection/research/2026-11-07-behavior-champion-text-review.ko.md),[5개 도표·선택 영상과 적용 가설](../../collection/research/2026-11-07-behavior-champion-visual-transfer.ko.md),[시각 자료 해시](../../collection/research/2026-11-07-behavior-champion-visual-sources.json)로 보존했다. 원문 미디어 재게시·외부 코드 설치·새 학습·E20코드변경은 없다. 사례74의 설명과 실제 연결영상 대상 불일치, 선택 프레임의 완료 판정 한계, BEHAVIOR훈련 정보 허용범위와PhyRC차이를 함께 기록했다.

E19의[공개 운동 수치](../../collection/reviews/20261107-astra-entry801-named-001-motion.ko.md)도 독립 대조했다. 세 접근은 실제44/67/55mm arm 이동이며 목표증가잘림근거없다. D7의base기준3.294mm와world3.774mm를구분하고, D8의world41.423mm이동으로위치보상이정확한고정이아님을명시했다. 그리퍼기준점은천접촉정답이아니다. 실행·관측·해석을분리하는후속절차카드의근거로연결한다.

## E20 종료 · 목선 재파지 준비와 다음 공식 유사 경로

2026-11-07 01:48:05 UTC에 모델이 테이블 지지 쪽으로 낮춘 뒤 자율 종료했다. client0·capture complete·전수QC726/726오류0이며, raw0/50·전항목0·success=false·no_contact/null이다. 전체726=470재실행+154모델+102정착,36.3sim초이며 새256전이12.8sim초다. 24판단은23act+finish,25호출은추가depth질의1회를 포함하고질의물리0이다. wall1783.289404705초(29분43초),모델호출경로1090.693712822초·환경640.649879246초다.

기존 밑단 파지 두 곳을 순차적으로 목선 후보로 바꿨다. robot0 국소 동행을 먼저 확인한 뒤 robot1을 옮겼으며 두 번째 확인은 양측 들기여서 독립 지지 시험과 구분한다. D14robot1roll+.47은 열린 그리퍼 접근 방향을 바꾸려는 의도적 회전이다. 이후 높이·간격·시점 보정에도 연속 목 개구부는 불명확해 운반 전에 마감했다. 실제 새 재파지와 그 뒤 미세조정 포화를 구분하며 머리 우선 착의 자체가 실행·실패했다고 확대하지 않는다.

[공개 리뷰](../../collection/reviews/20261107-astra-neckline470-named-001.ko.md),[학습 구간](../../collection/reviews/20261107-astra-neckline470-named-001-learning-segments.json),[영상](../../gallery/assets/20261107-e20-neckline-regrasp/event.mp4)을 보존한다. 470–726inclusive의257프레임/51.4초/5fps·4배느리게이며 원본에 없는 중간프레임은 생성하지 않았다. 같은E07 source group·unreviewed다.

E20 종료 뒤 별도 후보f148d6을 main에 병합했다. `coordinated-overhead-drape`는 몸통 입구의 상방 배치와 하강을 비교하고 목/첫소매의 선행완료를 강제하지 않는다. 실제통합 전체 **277CPU검사12.745초 통과**, 로그`output/sessions/20261106-evening/cpu-overhead-integrated.log` SHA256`ae4af21a8deafc14b4f69ffc0b17703e143761b799b155f57ebb59c79a36153f`다. 다른9전략의prompt/입력/schema/dispatch 불변과 신규선택지의query동결계약을 검증했고 실제천효과는 미검증이다. 독립프롬프트검토에서도 중대한 순서충돌·관측경계 문제는 찾지 못했다.

다음E21은STATUS의 명령으로E18/470·hist430464에서 공식유사경로를 비교할 계획이다. 원본 파지를 보존할 수 있는 출발을 선택했고 E20의 목선 재파지를 그대로 이어받는 분기가 아니다. 실제시작·소스는실행후별도로기록한다.

E20 비공개 원본은 고정HF revision `ad7b94f4dd65115082ad53527a48efbf99a5947d`에서 재다운로드 SHA검증을 완료했습니다. 1,721,601,271bytes·SHA256`b427dc7b27d14c933fa67f85df751379044163c05e849c84e7fb138f86b97096`,2026-11-07 01:53:01UTC 확인입니다. 272archive member 전수검사와 고정revision 강제재다운로드를 통과했다. [receipt](20261107-e20-backup-verification.json).

## E21 공식 유사 상방·하강 경로 · 실제 시작

E20 영상·분석·학습 구간·공개 운동 수치·원본 백업과 overhead 후보를 공개 main `d383063670085afccabfb51e6af530607d2efd44`에 통합했다. 검토 로컬/원격 tree `db5072f1451c5bd4de8585bea48d93d993abfa9e` 동일성을 확인하고 로컬 병합 이력을 `local-prepublication-e20-20261107` 태그에 보존했다. README 맨 위 E20 영상도 원격에서 확인했다.

**2026-11-07 01:56:25UTC**에 `20261107-astra-overhead470-named-001`을 실제 시작했다. source snapshot은d383063·working_tree_modified=false다. STATUS의 명령대로 E18 직접부모/prefix470·hist430464·coordinated-overhead-drape·named+query·plan1·40판단/max1400/timeout180/settle6/review10·profile을 사용한다. 로그는`output/sessions/20261106-evening/e21-overhead470-named-001.log`다. GPU는E20종료뒤순차실행이며초기화/재실행을진행한다. 최종 결과는아직없다.

E18/470의닫힌전체928원본검사·해시·계보를재검증한후시작했다. 현재관측에서유용한지지와몸통입구를다시판단하며, 재실행을정확한천checkpoint로설명하지않는다. 공식영상의프레임·좌표·궤적·평가값은actor입력에넣지않았다. 실행중코드는유지하고문서만현재화한다.

## 사용자 선호 수정 · 목선 파지의 어려움

사용자는 앞선 목 접근 선호를 수정하고 목으로 파지하는 것은 어려워 보인다고 평가를 요청했다. E20은 실제 목선 후보 두 재파지 이후에도 좁은 경계·겹친 천·닫힘/잔류운동 때문에 연속 입구를 확인하지 못했다. 현재 조건에서는 목선 우선 파지의 우선순위를 낮추되, 목 파지 일반이 불가능하다거나 머리 우선 착의 자체를 실행해 실패했다고 넓히지 않는다. 이미01:56:25UTC에 시작한 E21의 넓은 몸통 입구 상방·하강 경로는 그대로 진행하며 활성 코드·프롬프트는 바꾸지 않았다. 목선 위치 조정은 향후 부분 착의 뒤의 조건부 후보로 남긴다. [fb-20261107-002](../../collection/feedback/2026-11-07.jsonl)에 기록했다.

## 외부 참고 원본의 비공개 보존

BEHAVIOR 검토 원본19개(7,211,706bytes)와 출처/범위6파일을 unique20261107-champion-reference-v1 연구묶음으로 보존했다. archive6,879,270bytes·25member, 고정HF revision`427d3a150b48f2e522bbff30f9177d6a2722788d`, SHA256`e1b99b63d44673fdcced9e18ba97447fdb98e0dce24e616581880e307a831b15`다. 02:02:13UTC 고정revision 강제재다운로드·25member size/SHA 검증을 완료했다. 공식MP4/페이지HTML은 기존e1d32f9 백업의 동일SHA member여서 중복제외했고 receipt에 위치를 연결했다. 미검토poster·파생crop/frame·인증·actor이벤트는 포함하지 않았다. [receipt](20261107-champion-reference-backup-verification.json). 제3자 참고원본은비공개이며시연collection/actor/학습입력과분리했다. E21은변경하지않았다.

E16–E20의닫힌증거를[절차·복구카드초안](../../collection/research/2026-11-07-observable-procedure-cards.ko.md)5개로재구성했다. 실제명령→로봇실측→천관계→입구/통과를구분하며연구용분석이지성공정책·훈련승인·실행제어기가아니다. 배경/빈픽셀을입구필요조건으로삼지않고뒤몸판가설과입구미확인을구분했다. 현재E20/E21task에그런명시필수조건은없으며이번에는코드·프롬프트변경없이문서에만남겼다.

## 양측 지지 출발점DB와10점이후계속지시

사용자는양쪽가장자리지지를유지하는자료를출발점으로모아다음시도부터5→10의다양한방법을비교하고전체구분·조합을찾는DB를요청했다. 공개보고서21개와로컬attempt23개의합집합29실행을목록화했다. 연결시험·시작실패·실제시연, 의도prefix와실제replay완료, 시작점수와결과점수,지지시각근거와점수를각각분리한다. 검수5후보중E18/563·787·801과E19/801은5점,E18/470은0점대조다. E18/563앞의510–563표본3개와운반563–787/801표본을교차검토했고전프레임·독립하중지지검증으로확대하지않았다. [근거](../../collection/research/2026-11-07-support-startpoints-review.ko.md)·[목록](../../collection/catalog/README.ko.md).

명시적계획두건은E18/563에서overhead또는support-guide를named+query조건으로비교하는후보이며아직dispatch하지않았다. 실제선택과짧은판단예산은E21최종결과뒤정한다. E21자체는source d383063의실행을유지했다. 여러짧은하강뒤손끝가림,두손목시점변경과복구까지진행했으나최종결과미확정이다.

추가지시는Astra유지·기존실패활용·빠르고다양한분기·README상태갱신,10점확인뒤다음득점항목계속이다. 장기적으로0→5→10등방법구간을조합한합성자료확장을계획하되연결부의실제재검증·출처그룹분리·합성여부/불확실성·학습승인구분을유지한다. [장기계획](../../collection/research/2026-11-07-composable-scoring-data-plan.ko.md). 현재합성실행/학습은0이며기존실제수집을계속한다.

목록 도구8365f0d를 통합했고 전용CPU11검사와 정본/SQLite일치검사를 통과했다. 실제검색에서 준비조건+양측지지근거+시작5점은4건,조건부계획은2건이다. 활성E21의실행파일은변경하지않았다. [카탈로그 검증 기록](20261107-catalog-validation.json).

## E21 종료·다음 짧은 비교 준비 (2026-11-07)

E21은02:48:54UTC에40판단 예산으로마감했다. 원점수5/50(픽업5·착의0),success=false·no_dressing_points/0.0,QC1111/1111오류0·complete·client0다. **470재실행+412모델+228정착+1예산종료=1111전이55.55sim초**,새641전이32.05초. 40판단모두act,44모델호출중4추가질의29유효점·물리0,finish0·감독SIGINT0다. 실제3149.109434초,모델호출경로2160.241971초·환경926.844498초다.

두하강접근/시점·방향보정뒤손통과미확인으로테이블복귀했다. D36r1open→D37/38새위치정렬→D39close는실행됐으나마지막들기/유지검사가없다. 새파지지지·반대층선택을확정하지않고[15학습검토구간](../../collection/reviews/20261107-astra-overhead470-named-001-learning-segments.json)에실패·복구와함께보존했다. [영상2구간](../../gallery/20261107-astra-overhead470-named-001.ko.md)은702–856/155프레임31초와1018–1111/94프레임18.8초다. 전체overview도1111관측프레임55.55초·생략없음으로내보냈다.

[E21원본](20261107-e21-backup-verification.json)은2,428,228,014bytes·SHA35549015dd45b59321c8ab77efa512a7079ed0dfff1a9c1d1df3ae8dd840b0d3,고정revision45e6adf8586f935b3ca9f6d19ed3ec97371be44f에서강제재다운로드/416member검증02:55:33UTC완료다. 시작source d383063·clean을보존한다.

종료뒤entry-probe후보5559af6을통합했다. 전체295CPU검사18.451초통과. 같은파지의부분가림아래행동선택비교이며,조건부2–4step탐색1회와후속관측·새재파지0회지침이다. 실제물리효과미검증. E18/787의공개prefix787×2×9 float32와전체원본QC/hash를검증했고18판단분기를준비했다. 카탈로그E21완료와E22계획을분리한다. README에는최신GIF한개와두MP4·분석·피드백을두고예전영상은갤러리링크로정리했다.

## E22 실제 시작 (2026-11-07 03:01:21 UTC)

`20261107-astra-probe787-named-001`을공개source`11faab3797cacd0160a725578d4a9dc65c6b018f`·working_tree_modified=false에서시작했다. E18직접부모/prefix787·history719771·coordinated-entry-probe·named+query·plan1·18판단/max1300/timeout180/settle6/review10·profile이다. 로그`output/sessions/20261106-evening/e22-probe787-named-001.log`,초기화·재실행중이며최종결과는없다. E21은종료·QC·백업·영상게시완료뒤GPU를순차시작했다.

## E22 자율 종료와 정보 조건 재검토 (2026-11-07 03:18:34 UTC)

공식5/50(픽업5·착의0),success=false·no_contact/null·QC813/813오류0이다. 787재실행+14모델(4전진/4pitch/6zero)+12정착=813전이40.65초,새26전이1.3초다. 18판단예산중4판단(3act+finish)/5호출(query1·7valid·물리0)이며마감추가전이0이다. 실제1032.883288초·모델호출경로294.325561초·환경694.749380초다.

새손–경계관계를얻지못했고재파지금지범위에서같은탐색을반복하지않겠다는모델설명으로종료했다. 충분한진입/가려진안착을시험한결과가아니며,정보획득조건이목표진전을막았을가능성을비교할근거다. 다음coordinated-task-progress는현재목표관계로유한act를선택하고다음관측에서실제옷진전을평가하는후보로준비한다. 같은E18/787/hist719771·18판단으로비교하고물리/관절/20Hz/공식schema를바꾸지않는다.

attemptcompleted·capturecomplete/operator_finished·simulator_returncode0이지만hostexec61989는143을반환했다. 발신/원인은현재기록에서특정할수없고Pythonclient반환코드로단정하지않는다. root직접SIGINT/SIGTERM요청은없다. closedsourcecleanup에hostkill경로를찾지못했고runlog4행은정상판단진행이다. QC통과원본과이차이를함께보존한다. 최초validate_capture호출은--output누락으로CLI오류2였으며,이후새validation.json을지정한실제전수검사가0으로통과했다. 원본검사실패와잘못된검사호출을구분한다.

E21국소depth수치/표면해석한계와후속M1/M2/M3구분을추가기록했다. 검수출발점5개의공개원본15이미지·정확경계매핑·피드백동선도추가했다. 점수만으로구간을연결하거나층/접촉/성공라벨을생성하지않는다.

E22 [고정 원본 백업](20261107-e22-backup-verification.json)은revision`788a36ece3f606ca06dd0f20224910974dbe270e`에서강제재다운로드와92member해시검증을03:24:59UTC에완료했다. 1,854,271,559bytes·SHA`ea7ec4943649e31407a247af5aa2a6bff3adfb86d7a5576e227331207a5fe80c`이며host143와simulator0을receipt에분리보존했다.

E23 후보3873f90을통합했고전체302CPU검사23.432초통과했다. [검증기록](20261107-task-progress-validation.json). 기존11전략44조합의prompt/schema/images/dispatch불변·queryfrozen·20act/6settle/마감분리를확인했고실제모델·옷효과는아직미검증이다.

## E23 실제 시작 (2026-11-07 03:30:54 UTC)

`20261107-astra-progress787-named-001`은공개source`952ec8da68cdc0ef635d0d45329712eee006fd1f`·working_tree_modified=false에서시작했다. E18/787직접부모·history719771·coordinated-task-progress·named+query·plan1·18dec/max1300/timeout180/settle6/review10·profile이며E22와같은출발점의비교다. 로그`output/sessions/20261106-evening/e23-progress787-named-001.log`. E22exec반환의발신불확실성을구분하기위해호스트shell은Python명령이반환하면그값을별도local텍스트에기록하도록했다(반환전에는값없음). 정책/시뮬레이터/공식물리변경은없다.

E23 중간: 787재실행 뒤D0 base_forward+.25×20+6정착, D1+.18×16+6정착, D2양pitch−.1×12+6정착으로853경계까지 진행했다. 두전진과입구후보를손주위로올리는각도변경이실제수행됐고손–rim투영겹침이보이지만통과·최종평가는미확인이다. 0–2판단은깊이질의없이직접act였다. 이 진행은진전조건비교의관측근거이며시작천접힘차이를고려해야한다.

## E23 예산 종료와 연속 분기 준비 (2026-11-07 04:02:40 UTC)

공식5/50·픽업5·착의전항목0·success=false·no_dressing_points/final_score0.0이다.1180=787재실행+284모델+108정착+1예산마감,59sim초·새393전이19.65초,18act/18calls/query0/finish0이다. wall1906.180018124초·모델호출경로821.402335090초·환경1031.865205892초이며순수모델추론시간은미제공이다. QC1180/1180오류0,hostexec95905=0·shell관측Python0·simulator0·capturecomplete/operator_finished로닫혔다. source952ec8da68cdc0ef635d0d45329712eee006fd1f clean을보존한다.

D7반대span기울기뒤D8반전, D9/D10측면·전방접근, D11한쪽경계상승과D12측면진행뒤손·전완이천옆으로더드러나는변화가있었다. D13경계수평보정뒤D14/D15머리높이상승·접근, D16하강/D17pitch복구를실행했지만머리통과미확인이다. 공식착의0과화면의구멍후보를구분한다. E22같은prefix와시작천접힘차이가있어결과차이의단일인과를확정하지않는다.

Fullreport는첫생성이QC완료전시작되어qualitynull이었다. 미게시초안을output/reports/20261107-e23-before-qc-export에그대로보존하고,QC완료뒤새공식report를재생성해qualitytrue를확인했다. 전체1180frame/20fps/59s,hero1011–1180incl170frame/5fps/34s,방향937–1011incl75frame/5fps/15s다. 원본은변경하지않았다.

E24는E23/1179·history1077/1161·동일task-progress·30판단/max2000/settle6/review10후보를검수한다. 새파지방법이아니라진전이생긴동일방법의연속분기다. M1은별도후보, E15/367은대안원본복원·loader검증까지만완료했다.10점확인후에도다음득점으로계속한다.

E23[원본백업](20261107-e23-backup-verification.json)은고정revision`c1157513362e30d6a8306e7c8fd2ec0265e5db2c`·2,730,237,231bytes·SHA`a6a7850d6a510cf649795091b862d10f6c62043c2ea12edfa962059a40946072`이며04:09:08UTC강제재다운로드및218member전수해시검증을완료했다. E24/1179출발점은공개5뷰/잔류운동검수와공식loader/actionsfloat32(1179,2,9),E23실행소스22파일불변확인후채택했다. 아직새실행전이다.
