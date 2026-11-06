# 다음 작업 상태

**정리일: 2026-11-06. 현재 우선순위: 안정적인 수집 시스템·다양한 방법의 순차 실험·빈번한 과정 기록. Astra/ultra와 첫 5점 리뷰 조건은 유지합니다.**

[현재 기술문서](../../README.md) · [상세 수집 과정](../collection/README.ko.md) · [수집 일지](../collection/sessions/2026-11-06.md) · [서버 준비](START_HERE.ko.md) · [작업 지침](../../AGENTS.md)

## 다음에 할 일

`gpt-6-astra`/`ultra`의 실제 로봇 wiring과 전수 기술 검사를 완료했습니다. 첫 착의 시도 `20261106-astra-dressing-001`은 02:45:03 UTC에 SIGTERM으로 중단됐습니다. 완료 결정 15개·167전이·8.35 simulation초를 정상 보존했고 전체 검사도 통과했습니다. 최종 공식 평가는 유효한 0점·success=false이며 5점 게이트 도달로 종료된 것이 아닙니다. 최신 피드백에 따라 계측 수정 → 상주 호출 pilot → 짧은 다중 행동의 순차 실험을 진행할 계획입니다. 완료 여부는 각 실험 결과로 별도 기록합니다.

빠른 성공보다 수집 시스템과 과정의 신뢰도를 우선하며 첫 5점을 중간 리뷰 기준으로 유지합니다. 50점·착의 `success=true`와 다양한 완주 경로 수집은 이후 목표입니다. 실패·재시도·부분 성공도 구간 라벨과 시간·출처를 연결해 보존하고 최초 프롬프트를 소급 수정하지 않습니다. 메인 README에는 상태와 링크를 요약하고 상세 과정은 [수집 일지](../collection/sessions/2026-11-06.md)에 한국어로 갱신합니다.

## 확인한 결과

| 검사 | 결과와 범위 |
|---|---|
| 환경 복원 | L40S, 드라이버 580.126.09, Docker 29.1.5. build 186.18초·prepare 8.41초·smoke 355.67초, 종료 코드 0과 `PHYRC-SMOKE-PASS` |
| 초기 기록 연결 | 3개 에피소드·63전이·3.15 simulation초 저장·정합성 검사. 과제 성공 자료로 집계하지 않음 |
| 화면 연결 | 맥북 Chrome에서 기존 WebRTC 실시간 영상 확인. 자동 수집 모드에서는 관찰 전용이며 사람 제어권 전환은 미구현 |
| CPU 검사 | 공개 패키지 도구를 포함해 56개 통과. 실제 GPU·과제 성공 검증과 구분 |
| actor 격리 | 고정 digest Python 컨테이너, 공개 입력·전용 home만 연결. 직접 인터넷·호스트 서비스 차단, 허용 모델 origin 통신, repo·Docker socket·호스트 메타데이터 부재 확인 |
| 실제 CLI | 0.166.0, `gpt-6-astra`/`ultra`. 합성 색상 이미지 2턴·JSON·명시적 동일 세션 재개 통과. 총 actor 호출 13.1566초는 준비·Docker/CLI·요청/응답 포함 |
| 모델 없는 GPU wiring | 3전이·0.15 simulation초, 10초 관찰 대기 중 물리 시계 유지, 전체 전이 검사 통과. 공식 평가 0점·success=false·`no_contact` |
| 실제 로봇 모델 wiring | r5에서 3개 결정·3전이·0.15초, 정상 종료·전수 검사. 전체85.7008초, actor24.0452초. 공식0점·success=false |
| 첫 착의 시도 | `20261106-astra-dressing-001`, source=gpt. SIGTERM 중단, 전체 973.8618초, 167전이 기술 검사 통과. 유효 0점·success=false·no_contact |

HF CLI `huggingface_hub==2.2.0` 설치·실행을 확인했으며 HF 로그인 완료 여부는 별도로 확인해야 합니다. 과거 자료의 원격 보존은 이번에 다시 검증하지 않았습니다.

## 실패와 재시도 근거

- 첫 합성 이미지 CLI 시험은 정상 응답 뒤 시작 안내를 도구 오류로 분류하여 실패했습니다. turn 시작 전 알려진 비실행 안내만 허용하도록 수정했고 `20261106-codex-cli-probe-r2`가 통과했습니다.
- 첫 모델 없는 GPU wiring은 native stdout 혼입·Docker stdin·종료 큐 정체로 실패했습니다. 중립 1전이와 `complete=false` 원본을 보존했으며 `20261106-auto-runtime-wiring-r2`에서 다시 검증했습니다.
- 실제 로봇 모델 wiring r1~r4는 긴 inline prompt 조건에서 native 초기화 실패를 재현했습니다. `sys.argv` 정리·초기화 순서 변경만으로 해결되지 않았고, 제한된 `--prompt-file` 전달 후 r5가 완료됐습니다. native 내부 원인 확정과 재현 조건 회피를 구분하며 실패 원본을 보존합니다.

로컬 근거는 `output/sessions/20261106-codex-cli-probe-r2/result.json`, `output/collections/20261106-auto-runtime-wiring-r2/validation.json`, `output/collections/20261106-codex-robot-wiring-r5/validation.json` 및 각 `output/operator-traces/<run-id>/attempt.json`입니다. 연결 주소·인증 정보·원본 로그는 공개 문서에 포함하지 않습니다.

## 현재 구현과 남은 범위

| 항목 | 현재 상태 |
|---|---|
| `codex_actor.py` | 별도 Docker에서 `exec`/명시적 `resume`, 공개 이미지·JSON, timeout·도구 실행 거부. API로 자동 전환하지 않음 |
| `codex_client.py` | RGB 5장·전체 공개 상태·16×16 depth 중앙값, 행동 검사, 단계·재시도·시간·출처 기록. 원래 depth는 별도 보존 |
| `evaluation.py` | 같은 시도의 공식 점수·획득 이벤트·success를 신뢰된 수집기 측에 기록. 행동 입력에 전달하지 않음 |
| `validate_capture.py` | 해시·완료 상태·모든 관측/행동·0.05초/12 ticks·연속성·평가 라벨 기술 검사 |
| `collector_stream.py` | 자동 수집 WebRTC 관찰과 물리 시계를 진행하지 않는 렌더링. 브라우저 로봇 제어 미적용 |
| 시연 승인·효율 분석 | 과제 시연의 시각적 검수, 승인 구간과 단계별 도달률·재시도 효율 집계는 남아 있음 |
| 학습·제출 | π₀.₅ 학습·추론·포장 코드 있음. 실제 승인 자료로 학습·검증·제출한 결과는 아직 없음 |

다음 산출물은 **계측 정정 검증, 상주 호출 pilot의 독립 비교, 짧은 다중 행동 실험별 기록**입니다. 세션 누적 usage 중복 합산은 정정 자료와 분리하며 기존 합계를 비용 근거로 사용하지 않습니다. 모델·추론 설정을 유지하고 한 변경씩 확인합니다. `complete`·기술 검사 통과·공식 착의 성공은 서로 다른 상태입니다. 후속 VLA baseline·RL·world model 학습은 아직 실행하지 않았습니다.

검토 자료를 생성했습니다: [첫 시도 이미지·영상·프롬프트·행동](../collection/attempts/20261106-astra-dressing-001/README.ko.md), [종료 검토](../collection/reviews/20261106-astra-dressing-001.ko.md), [사용량 정정](../collection/corrections/20261106-token-accounting.ko.md), [호출 지연 개선 가이드](../collection/guides/call-latency-options.ko.md). 원래 시도 기록을 보존하며 가이드의 제안과 실제 적용·검증 결과는 별도 기록합니다.

과거 세션의 명령·자료·측정은 [세션 기록](sessions/), [11월 3일 종료 기록](END_20261103.ko.md), [이전 결과](RESULTS.ko.md)에 남아 있습니다. 당시 우선순위는 현재 README를 대체하지 않습니다.
