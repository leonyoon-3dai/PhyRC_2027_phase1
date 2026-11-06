# 현재 상태와 다음 작업

**최신 종료 E17: 5/50(픽업5·첫 소매0), `success=false`.** 최고 기록은5/50이며 **10점은 아직 미달성**입니다. 다른 lower-rim 후보를 겨냥한 실제 재파지를 수행했지만, 반대 입구 층과 두 지지·연속 입구는 확인하지 못해 모델이 종료했습니다.

[최신 영상·피드백](../gallery/README.ko.md) · [E17 상세](../gallery/20261106-astra-layer352-001.ko.md) · [공개 관측 분석](../collection/reviews/20261106-astra-layer352-001.ko.md) · [실행 일지](sessions/20261106-evening-resume.ko.md) · [README](../../README.md)

## 실제 확인 결과

| 항목 | E17 확인값 |
|---|---|
| run ID | `20261106-astra-layer352-001` |
| 실제 방법 | A: 한쪽을 열고 다른 가시 경계에 두 번 배치 보정→닫기→짧은 동시 들기→지지 미확인으로 낮춤·종료 |
| 원점수 | **5/50 · 픽업5 · 착의 항목0 · `success=false`** |
| 점수율 | `no_contact / null`; 픽업5점만으로 양의 착의 순위 점수가 생기지 않음 |
| 기술 검사 | **452/452기록 통과**, complete·학습 승인 `unreviewed` |
| 기록·시간 | **352 재실행 +52 모델 행동 +48 제어기 중립 =452**, 시뮬레이션22.6초 |
| 모델 판단 | **12회**(행동11회+종료1회), Astra/ultra·고정 CLI0.166.0/exec |
| 실제 시간 | **23:37:50–23:51:35 UTC,824.158초**(약13분44초) |
| 경로 시간 | 모델 호출378.759초·환경 요청400.042초. 순수 내부 추론시간은 미제공 |
| 실행 소스 | 공개 main `98bb41ff6e83327a468abe5129517b4739ae33a1`, 시작 당시 작업 트리 수정 없음 |
| 직접 부모 | E16 `20261106-astra-support264-002`의352기록. source group은E07 계열 유지 |
| 입력 | 현재 RGB5장·공개 로봇 상태·depth 요약·손목 depth 패널. 첫 호출에 같은 새 replay의264·346경계 RGB10장 추가, 총16이미지 |
| 픽셀 질의 | **E16·E17에는 미사용** |
| 관찰 | Chrome·WebRTC OFF, 닫힌 기록의 GIF/MP4로 검토 |

기록1개(전이)는 관측→행동→다음 관측의0.05초이며, 실험/모델 판단 횟수가 아닙니다. 중립 명령 중에도 목표 추종 운동이 남을 수 있습니다. 기술 검사·착의 성공·학습 승인은 별도입니다. 이 점수는 로컬 공식 평가기 결과이며 Codabench 제출·공식 순위를 뜻하지 않습니다.

## 분석과 다음 비교

E16은 같은 오른쪽 가장자리 회복 뒤 국소 천 동행을 관측했지만0/50으로 종료했습니다. E17은 다른 아래 경계 후보를 겨냥해 접근 방향·위치를 바꾸는 재파지 사이클을 수행했습니다. 양측 동시 들기 후 robot0의 경계가 물러나는 듯한 관측이 있어 두 지지를 확인하지 못했습니다. **5점은 새 파지나 반대층 확보의 증명이 아닙니다.** 제한된 한 번의 시도로 A 전체가 소진됐다고 결론내리지 않습니다.

다음은 **B: 몸통 지지 + 소매 방향 가이드로 한쪽 실제 파지·역할 변경**입니다. E16의470경계에서 현재 지지를 다시 확인합니다. 보이는 표면의 거리 모호함에는 선택형 픽셀 depth 질의를 처음 과제에 제공할 계획이며, 가려진 층·입구·접촉을 알아내는 기능으로 취급하지 않습니다. 이 비교는 파지 전략과 입력 기능이 함께 달라져 단일 요인 비교가 아닙니다.

별도로 **목둘레부터 입히는 순서**를 선택형 전략 `coordinated-neckline-first`로 통합했습니다. 공개 평가 설명에는 첫 소매의 필수 선행 조건이 없습니다. 실제 머리 통과·몸통 내부 관계를 목표로 하며 목선 접촉이나 앞면 방향만으로 성공을 주장하지 않습니다. 아직 실행하지 않았습니다.

[방법 전환 기준](sessions/20261106-method-switch-matrix.ko.md) · [기존 들기와 새 역할/목 우선 후보 구분](../collection/research/2026-11-06-post-support-methods.ko.md) · [E16 대기 시간 분석](../collection/research/2026-11-06-e16-neutral-call-timing.ko.md)

## E18 B 계획 · 아직 미실행

아래 명령은 E17 마감·main 갤러리 반영 뒤 새 run ID로 실행할 계획입니다. 실제 시작 여부와 소스는 일지에 기록합니다. GPU 작업은 순차 실행합니다. 원본 재실행은 정확한 천 checkpoint 복원이 아니며 과거 사진은 현재 지지 증거를 대신하지 않습니다.

```bash
export PATH="$PWD/.runtime/codex-0.166.0/node_modules/.bin:$PATH"
unset STRETCH4_PRACTICE_LAYOUT STRETCH4_RANDOMIZE
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m participant.collection.codex_client \
  --run-id 20261106-astra-guide470-depth-001 --mode dressing \
  --strategy coordinated-support-guide --actor-backend exec \
  --model gpt-6-astra --effort ultra --plan-size 1 --review-points 10 \
  --replay-prefix-run 20261106-astra-support264-002 --replay-prefix-steps 470 \
  --parent-attempt 20261106-astra-support264-002 \
  --retry-reason support_and_sleeve_guide_with_public_pixel_depth \
  --replay-observe-steps 430 464 --wrist-depth-panel --pixel-depth-query \
  --post-action-settle-steps 6 --decisions 35 --max-steps 1400 --model-timeout 180 \
  --profile-step-phases
```

## 구현·검증·보존

- 기본 환경 복원·prepare·smoke·실제 Astra wiring을 완료했습니다. E09의 종료 응답 순서 오류는 이미 수정됐습니다.
- 최신 통합본 전체 CPU **257개 통과(7.529초)**. 목 우선 후보와 기존8전략 불변·depth OFF/ON 경로를 포함합니다. 이를 E16/E17 실행 당시 소스의 검사 수로 소급하지 않습니다.
- 픽셀 질의는 CPU·합성 실제 CLI2턴·모델 없는 실제 GPU3기록 전수검사까지 완료했습니다. fixture 질의1회·실모델 호출0·질의 물리 진행0이며 실제 착의 효과는 아직 미검증입니다. [검증 범위](../collection/research/2026-11-06-pixel-depth-query-candidate.ko.md)
- E16 원본은 고정 HF revision `1ad0f8ba3cc71ab80962907c713357fbd4005e3f`의 재다운로드 SHA 검증 완료입니다. [E16 receipt](sessions/20261106-e16-backup-verification.json)
- E17 원본은 고정 revision `d5ba6c645232c7674d3861fdf65da3a26e9e1ea9`에서 재다운로드 SHA 검증을 완료했습니다. [E17 receipt](sessions/20261106-e17-backup-verification.json),1,027,542,010 bytes,23:55:15 UTC 확인.
- 실제 모델 기본 wiring과 모델 없는 query wiring도 각각 [기본 receipt](sessions/20261106-evening-wiring-backup-verification.json), [query receipt](sessions/20261106-depth-query-wiring-backup-verification.json)로 원격 검증했습니다.

비공개 HF dataset은 `leonayoon/phyrc-2027-phase1-private-backup`입니다. audit·평가·배치 metadata는 검수 전용이며 actor 입력에 연결하지 않습니다. 공개 GitHub에는 코드·문서·선별 공개 관측만 게시하고 인증·원시 추론·CLI 이벤트·simulator 로그는 게시하지 않습니다.

[클린 서버 복원](START_HERE.ko.md) · [초기 자산·E07 복원 검증](sessions/20261106-evening-restore-validation.json) · [E16 분석](../collection/reviews/20261106-astra-support264-002.ko.md) · [E15 마감 이력](SESSION_WRAPUP_20261106.ko.md) · [전체 개발 이력](HISTORY.ko.md)

새 정책 학습·RL/VLA 성능 검증·학습 승인은 완료하지 않았습니다. 이전 문서의 일시 중지·미실행 문구는 당시 이력이며 현재 실행 상태는 이 문서와 최신 일지를 우선합니다.
