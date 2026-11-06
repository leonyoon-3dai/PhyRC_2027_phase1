# 다음 작업 상태

## 2026-11-06 재개 · 목표 10점

사용자의 재개 요청으로 이전 중지 상태를 해제했습니다. 새 L40S 환경·E07 원본 복원·종료 오류 수정을 마치고 E10~E13을 비교했습니다. 최신 **E13도5/50·첫 소매0·success=false**,18회 모델 호출 뒤 자율 종료했고 **810/810전이·비공개 원본 원격 재다운로드 해시 검증**을 통과했습니다. [E13 영상·E12 비교](../gallery/20261106-astra-hem-depth-001.ko.md)를 공개합니다. 사용자의 방향 전환 요청으로 E14는2움직임·2정착 뒤721/721전이로 중단 보존했습니다. 다음 [E15](../collection/experiments/2026-11-06-opening-first.ko.md)는264경계에서 운반 전 펼침·파지를 먼저 확인합니다. 전략과 trusted 단계 계측의 전체208개 CPU 검사·모델 없는6/6전이 연결 검사를 통과했고,11:55:47 UTC에 소스`fa3fb85`로 E15를 시작했습니다. 현재 새 에피소드 행동 재실행 단계이며 준비 개선·새 득점은 미측정입니다. 사용자 요청으로 Stretch4와 Georgia Tech Astra 연구를 병행 조사하며 Chrome·WebRTC는 사용하지 않습니다. **최고점5/50,10점 미달성**입니다. 최신 실행 상태와 명령은 [재개 기록](sessions/20261106-resume10.ko.md)을 따릅니다. 아래는 재개 전 인계 기록입니다.

**사용자 요청으로 수집을 일시 중지하고 클린 서버 인계를 준비합니다.** E07은 정상 종료·1,067/1,067전이 검사 통과, 공식 부분 점수 **5/50·착의 success=false·no_dressing_points·rate 0점/초**입니다. E08은 설정 누락으로 시작 전에 실패했습니다. E09는 사용자 중지 후 종료 응답 순서 오류를 남겨 **불완전 파일·기술 검사 실패**로 보존했습니다. 현재 새 수집·설치·재시도는 진행하지 않습니다.

[세션 정리·다음 목표](SESSION_WRAPUP_20261106.ko.md) · [현재 기술문서](../../README.md) · [상세 수집 과정](../collection/README.ko.md) · [수집 일지](../collection/sessions/2026-11-06.md) · [서버 준비](START_HERE.ko.md) · [작업 지침](../../AGENTS.md)

## 다음에 할 일

재개 요청 이후의 첫 순서는 **종료 프로토콜 수정·CPU 회귀 검사 → 클린 서버 환경·원본 복원 검증 → 작은 wiring → E07의 운반 경계 700전이 행동 재실행 검토 → 공개 관측으로 소매 통과 시도**입니다. E07의 협력 과정과 실패 분석을 유지하며 장기적으로 다양한 50점 시연을 수집합니다. [서버 복원·재개 명령](START_HERE.ko.md)을 따릅니다. [Stanford OpenWAM](../collection/research/openwam-feasibility.ko.md)은 분석 전용이며 설치·실행·현재 수집 적용은 하지 않았습니다.

| 항목 | 현재 상태 |
|---|---|
| 볼 자료 | [E07 종료 검토](../collection/reviews/20261106-astra-coordinated-fresh-001.ko.md) · [첫 5점·700전이 정확 원본 프레임](../collection/milestones/20261106-astra-coordinated-fresh-001/README.ko.md) · [공동 운반 관측](../collection/experiments/2026-11-06-coordinated-first5-review.ko.md) |
| 종료한 E07 | 04:40:12–06:04:06 UTC, 73호출·80결정·1,067전이·53.35 simulation초. 정상 마감·전수 검사 통과, 부분 점수 5점·전체 착의 실패 |
| 실패한 E08 | `branch700-001`: 스트림 설정 누락, 환경·기록기·actor 시작 전 실패. 0.465758초·exit 1·모델 호출/전이 0 |
| [중지한 E09](../collection/reviews/20261106-astra-coordinated-branch700-002.ko.md) | `branch700-002`: 06:15:37–06:18:57 UTC. 사용자 SIGTERM 뒤 종료 응답 불일치. 재실행 ACK 120·저장 141전이·모델 0, 불완전 파일 3오류로 검사 실패 |
| 다음 서버의 기준 | 완결·검사 통과한 E07 전체 원본과 prefix 700 후보. 원격 자료 복원·SHA·전수 검사 필수. E09는 실패 보존용이며 정상 재개 지점 아님 |
| 병행 연구 | [B1~B1c 공개 RGB-D 비교](../collection/research/2026-11-06-perception-baselines.ko.md) 완료. 후보 배치 개선·판단 보류와 실제 파지 성공을 구분. 추가 추정 모델은 미실행 |
| 보존한 E06 | 사용자 전략 변경으로 중단·04:34:37 UTC 마감. [최종 386/386전이 검사](../collection/reviews/20261106-astra-dressing-continue-001.ko.md), 부분 점수 5점·success=false. [중간 스냅샷](../collection/experiments/2026-11-06-dressing-continuation.ko.md) 별도 보존 |
| 관찰·측정 | 관찰 패널 배포 완료. 스트리밍 4회·260전이 검사 완료, 실제 시청 비용은 미확인 |
| 아직 미검증·계획 | 종료 프로토콜 수정·회귀 검사, 클린 서버 자료 복원, E07 prefix 700 재실행, 소매 통과, 후속 VLA·RL·world model 학습. 정확한 물리 checkpoint 복원은 미검증 |

<details>
<summary>확보한 5점과 이전 시도의 종료 경계</summary>

E05 `20261106-astra-pickup-hold5-001`이 **공식 pickup 5점·누적 5점·success=false**로 끝났습니다. 내장 감시가 03:56:23 UTC 행동 응답 경계에서 발동했고 `review_ready`로 종료했습니다. 18개 결정·253전이·12.65 simulation초, 전체 828.2998초를 기록했고 전수 검사 253/253 전이·오류 없음입니다. 이 종료는 당시 첫 5점 감시 조건의 결과입니다. 이후 사용자가 추가 피드백 없이 50점까지 계속 시도하도록 승인했습니다. [방법별 현재 상태·측정·한계](../collection/experiments/2026-11-06-method-comparison.ko.md)

첫 착의 시도 `20261106-astra-dressing-001`은 02:45:03 UTC에 SIGTERM으로 중단됐습니다. 완료 결정 15개·167전이·8.35 simulation초를 정상 보존·검사했습니다. 공식 평가는 유효한 0점·success=false이며 5점 도달 종료가 아닙니다. 이 원본은 후속 실험과 분리해 보존합니다.

E07의 협력 운반·E08 초기화 실패·E09 중지와 파일 미완료를 보존합니다. 이전 50점 계속 수집 승인은 이번 명시적 중지 요청으로 일시 중단됐으며 새 모델·GPU 실행을 시작하지 않습니다. 누적 50점·착의 success·기술 검사·학습 승인은 각각 판정합니다. 상세 과정과 다음 서버의 복원 조건은 [수집 일지](../collection/sessions/2026-11-06.md)에 남깁니다.

</details>

<details>
<summary>확인한 결과</summary>

## 확인한 결과

| 검사 | 결과와 범위 |
|---|---|
| 환경 복원 | L40S, 드라이버 580.126.09, Docker 29.1.5. build 186.18초·prepare 8.41초·smoke 355.67초, 종료 코드 0과 `PHYRC-SMOKE-PASS` |
| 초기 기록 연결 | 3개 에피소드·63전이·3.15 simulation초 저장·정합성 검사. 과제 성공 자료로 집계하지 않음 |
| 화면 연결 | 맥북 Chrome에서 기존 WebRTC 실시간 영상 확인. 자동 수집 모드에서는 관찰 전용이며 사람 제어권 전환은 미구현 |
| CPU 검사 | 05:14 UTC 기존 수집·기타 110개와 연구 31개, 합계 141개 통과. 실제 GPU·과제 성공 검증과 구분 |
| actor 격리 | 고정 digest Python 컨테이너, 공개 입력·전용 home만 연결. 직접 인터넷·호스트 서비스 차단, 허용 모델 origin 통신, repo·Docker socket·호스트 메타데이터 부재 확인 |
| 실제 CLI | 0.166.0, `gpt-6-astra`/`ultra`. 합성 색상 이미지 2턴·JSON·명시적 동일 세션 재개 통과. 총 actor 호출 13.1566초는 준비·Docker/CLI·요청/응답 포함 |
| 모델 없는 GPU wiring | 3전이·0.15 simulation초, 10초 관찰 대기 중 물리 시계 유지, 전체 전이 검사 통과. 공식 평가 0점·success=false·`no_contact` |
| 실제 로봇 모델 wiring | r5에서 3개 결정·3전이·0.15초, 정상 종료·전수 검사. 전체85.7008초, actor24.0452초. 공식0점·success=false |
| 첫 착의 시도 | `20261106-astra-dressing-001`, source=gpt. SIGTERM 중단, 전체 973.8618초, 167전이 기술 검사 통과. 유효 0점·success=false·no_contact |
| E01·E03 실제 GPU | 각각 3/3전이·0.15초 검사 통과. 모델 호출 3회→1회, 공식 평가는 모두 0점·success=false. 단일 wiring 한 쌍으로 일반 성능 향상을 주장하지 않음 |
| E02 상주 App Server | r1~r5, 모델 요청 시도 3회·승인 응답 0개. 실제 2턴 호환성 실패로 보류, 새 수집에 사용하지 않음 |
| E04 픽업 시도 | 13호출·168전이·8.4초 검사 통과. 모델의 완료 판단과 별도로 공식 0점·success=false. 유효 유지 2.9초 |
| E05 한 로봇 픽업 부분 점수 5점 | 18호출·18결정, 공식 5점·success=false. 감시 경계 252전이 뒤 중립 정리 1전이, 총253전이 검사 통과. 협력 들기 성공 아님 |
| E07 협력 들기·운반 시도 | 73호출·80결정·1,067전이 검사 통과. 공식 5점·success=false·no_dressing_points·최종 rate 0점/초. 학습 승인 unreviewed |

HF CLI `huggingface_hub==2.2.0`의 인증을 확인하고 사용자 승인으로 [비공개 백업 저장소](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-private-backup)를 생성했습니다. **11.78GB 업로드·고정 revision `e1d32f9f9ea82438f90bc379452abf83a150999b`의 재다운로드 SHA256 검증을 06:37:37 UTC에 완료**했습니다. 로컬의 새 폴더 복원·전체 파일 해시·E07 prefix700 입력 검사도 통과했습니다. 기존 공개 HF 자료와 구분하며 기존 서버 원본은 유지합니다. 새 서버 GPU 실행은 아직입니다. [보존 상태](SESSION_WRAPUP_20261106.ko.md) · [검증 기록](sessions/20261106-remote-backup-verification.json)

</details>

<details>
<summary>실패와 재시도 근거</summary>

## 실패와 재시도 근거

- 첫 합성 이미지 CLI 시험은 정상 응답 뒤 시작 안내를 도구 오류로 분류하여 실패했습니다. turn 시작 전 알려진 비실행 안내만 허용하도록 수정했고 `20261106-codex-cli-probe-r2`가 통과했습니다.
- 첫 모델 없는 GPU wiring은 native stdout 혼입·Docker stdin·종료 큐 정체로 실패했습니다. 중립 1전이와 `complete=false` 원본을 보존했으며 `20261106-auto-runtime-wiring-r2`에서 다시 검증했습니다.
- 실제 로봇 모델 wiring r1~r4는 긴 inline prompt 조건에서 native 초기화 실패를 재현했습니다. `sys.argv` 정리·초기화 순서 변경만으로 해결되지 않았고, 제한된 `--prompt-file` 전달 후 r5가 완료됐습니다. native 내부 원인 확정과 재현 조건 회피를 구분하며 실패 원본을 보존합니다.

로컬 근거는 `output/sessions/20261106-codex-cli-probe-r2/result.json`, `output/collections/20261106-auto-runtime-wiring-r2/validation.json`, `output/collections/20261106-codex-robot-wiring-r5/validation.json` 및 각 `output/operator-traces/<run-id>/attempt.json`입니다. 연결 주소·인증 정보·원본 로그는 공개 문서에 포함하지 않습니다.

</details>

<details>
<summary>현재 구현과 남은 범위</summary>

## 현재 구현과 남은 범위

| 항목 | 현재 상태 |
|---|---|
| `codex_actor.py` | 기본 backend `exec`, 별도 Docker의 명시적 `resume`, 공개 이미지·JSON, timeout·도구 실행 거부. 입력 준비·프로세스·결과 해석 구간 계측 |
| `codex_client.py`·`plans.py` | 공개 입력, 최대 3개의 고정 행동 목록·전체 사전 검사, thread 누계 차분 usage v2, 원본 입력과 실행 직전 관측 구분. 조건부 복구는 미구현 |
| 내장 5점 감시 | 이전 외부 watch 대체. 착의·픽업 모드에서 행동 응답 후 점수 확인, 미실행 계획 폐기·정상 종료·리뷰. 점수는 actor 입력에서 제외 |
| `codex_app_actor.py` | 상주 backend의 실험 코드·CPU 검사 있음. 실제 호환성 미통과로 사용 보류 |
| `evaluation.py` | 같은 시도의 공식 점수·획득 이벤트·success를 신뢰된 수집기 측에 기록. 행동 입력에 전달하지 않음 |
| `validate_capture.py` | 해시·완료 상태·모든 관측/행동·0.05초/12 ticks·연속성·평가 라벨 기술 검사 |
| `collector_stream.py` | 자동 수집 WebRTC 관찰과 물리 시계를 진행하지 않는 렌더링. 브라우저 로봇 제어 미적용 |
| 시연 승인·효율 분석 | 과제 시연의 시각적 검수, 승인 구간과 단계별 도달률·재시도 효율 집계는 남아 있음 |
| 학습·제출 | π₀.₅ 학습·추론·포장 코드 있음. 실제 승인 자료로 학습·검증·제출한 결과는 아직 없음 |

E07의 종료 후 전체 검사와 [전체 영상·최종 결과 패키지](../collection/attempts/20261106-astra-coordinated-fresh-001/README.ko.md)를 보존했습니다. **현재는 사용자 요청으로 중지 상태**이며 다음 GPU 실행 전에 E09의 진행 중 응답과 종료 요청 충돌을 수정·CPU 검증해야 합니다. E09 저장 141전이는 원본 재실행 140전이와 중립 1전이이며 새 모델 행동이 아닙니다. 700전이 재현은 완료하지 못했습니다. E07을 복원해 소매 통과를 이어가는 것은 재개 이후의 계획이고, `complete`·기술 검사·5점·착의 성공·학습 승인은 별도로 확인합니다. 후속 VLA·RL·world model 학습은 미실행입니다.

같은 관찰 페이지에서 프롬프트·최종 응답·기록·공식 점수를 확인하도록 화면을 배포했고 로봇 제어 버튼은 제거했습니다. 이번 변경의 Mac 원격 확인은 사용자 응답을 기다리며, 모델 입력에는 평가 표시를 전달하지 않습니다. 중립 스트리밍 4회 비교는 04:08:11–04:17:14 UTC에 실행을 마쳤으며 [별도 계획](../collection/experiments/2026-11-06-streaming-benchmark-plan.ko.md)을 따릅니다. [실측 결과](../collection/experiments/2026-11-06-streaming-benchmark-result.ko.md)는 260/260전이 검사 통과와 20 step 요청·응답 ON 평균 +5.80%를 기록했습니다. 조건당 2회이며 실제 영상 수신은 확인되지 않아 시청 중 비용이나 전체 AI 속도로 일반화하지 않습니다. [행동 재실행·분기 가이드](../collection/guides/continuation-and-branches.ko.md)에서 E06의 재개 방식과 한계를 확인합니다. [이전 서버와 오늘 실행 경로 비교](../collection/experiments/2026-11-06-server-comparison.ko.md)

검토 자료를 생성했습니다: [첫 시도 이미지·영상·프롬프트·행동](../collection/attempts/20261106-astra-dressing-001/README.ko.md), [종료 검토](../collection/reviews/20261106-astra-dressing-001.ko.md), [사용량 정정](../collection/corrections/20261106-token-accounting.ko.md), [호출 지연 개선 가이드](../collection/guides/call-latency-options.ko.md). 원래 시도 기록을 보존하며 가이드의 제안과 실제 적용·검증 결과는 별도 기록합니다.

과거 세션의 명령·자료·측정은 [세션 기록](sessions/), [11월 3일 종료 기록](END_20261103.ko.md), [이전 결과](RESULTS.ko.md)에 남아 있습니다. 당시 우선순위는 현재 README를 대체하지 않습니다.

</details>
