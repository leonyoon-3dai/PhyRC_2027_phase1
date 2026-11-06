# 현재 상태와 다음 작업

**2026-11-06 저녁 · E16 종료:** 원점수 **0/50**, 첫 소매 **0**, `success=false`. 최고 기록은 **5/50**이며 **10점은 아직 달성하지 못했습니다.** 클린 L40S 복원 후 실험을 재개했습니다. E16 결과와 소스를 main 통합본에 정리했으며 원본의 고정 HF revision 재다운로드 SHA256 검증을 마쳤습니다.

[최신 영상·피드백](../gallery/README.ko.md) · [E16 세 구간](../gallery/20261106-astra-support264-002.ko.md) · [원인 검토](../collection/reviews/20261106-astra-support264-002.ko.md) · [이번 세션 기록](sessions/20261106-evening-resume.ko.md) · [메인 README](../../README.md)

## 최신 확인 결과

| 구분 | 확인한 내용 |
|---|---|
| 마지막 과제 시도 | E16 `20261106-astra-support264-002`, 각 파지의 순차 지지 진단 |
| 종료 | 운반 없이 모델 자율 종료. 34호출·34판단 |
| 공식 평가 | **0/50 · 첫 소매0 · `success=false` · `no_contact / null`** |
| 완결 데이터 | **516/516전이 전수 검사 통과** |
| 전이 출처 | **E07 재실행264 + 새 모델156 + 제어기 중립96 = 516** |
| 실제 시간 | **22:46:26–23:19:06 UTC · 1,959.821초** |
| 시간 구분 | 모델 호출 경로1,451.035초 · 환경 요청456.810초 |
| 입력 | 현재 RGB5장 + 손목 depth 패널1장 + 공개 로봇 상태·depth 요약. 픽셀 질의 미사용 |
| 실행 소스 | `05152fa4bf250257481cae988b6f8f26c817084a` |
| 현재 소스 정리 | 사용자 요청에 따른 main 통합본. E16 실행 소스05152fa와 이후 통합 소스를 구분 |
| 학습 승인 | `unreviewed`; 기술 검사 통과가 성공 시연·학습 승인을 대신하지 않음 |
| 관찰 방식 | Chrome·WebRTC OFF, README 상단과 갤러리의 실제 GIF/MP4 |

모델 호출 경로에는 입력 준비·Docker/CLI·서비스 응답이 포함되며 순수 추론시간은 제공되지 않습니다. `no_contact / null`은 평가기의 점수율 상태이며0과 다릅니다. 위 결과는 로컬 공식 평가기 결과이며 Codabench 제출·공식 순위를 뜻하지 않습니다.

E16 첫 run ID `20261106-astra-support264-001`은 재실행 부모 인자 불일치로 시작 전에 차단됐습니다. 모델·GPU 호출과 capture가 없었습니다. 실제 E16은 부모를 E07로 수정한 `-002`이며 E15는 비교 대상입니다.

## 관측·해석·다음 방법

| 구분 | 내용 |
|---|---|
| 실제 수행 | 양쪽을 따로 시험하고 로봇0을 재파지한 뒤 국소 천 동행을 관측. 입구 준비 후 운반 없이 종료 |
| 확인되지 않은 것 | 두 지지점 사이의 통과 가능한 연속 입구, 손 진입·첫 소매 통과. 국소 동행은 시각적 지지 근거이며 닫기 명령·목표 잔차만으로 판정한 것이 아님 |
| 비교의 한계 | E15와 시작 이후 행동·시간이 달라 단일 요인 성능 비교가 아님. E16 원점수0과 과거 최고5를 혼동하지 않음 |
| 다음 선택 | E16의352경계부터 다른 가시 입구 경계·층에서 한쪽 재파지를 비교하는 E17 A 경로 준비. 아직 실행하지 않음 |

같은 실패가 반복되는지, 실제로 파지 위치·층·로봇 역할이 달라졌는지는 최종 행동과 공개 관측으로 판단합니다. 프롬프트 문구 변경만으로 새로운 조작 방법을 실행했다고 기록하지 않습니다. [방법 전환 기준](sessions/20261106-method-switch-matrix.ko.md) · [E16 상세 검토](../collection/reviews/20261106-astra-support264-002.ko.md)

## 구현·검증 단계

| 항목 | 구현·검증 상태 | 과제 성능과 구분 |
|---|---|---|
| 복원·기본 연결 | 고정 자산·E07 원본 복원, prepare·smoke·Astra 실제 wiring 완료 | 환경 연결 확인이며 착의 성공 아님 |
| 순차 지지 전략 | E16에 실제 적용 | 원점수0, 운반 없이 종료 |
| 다른 입구 재파지·지지/가이드 전략 | 코드·CPU 검사, 후속 비교 준비 | 새 과제 결과 없음 |
| 공개 관측 진단 | 한쪽/정지측 변위·그리퍼 상태·lift 목표 잔차 분석 가능 | 파지 성공을 자동 판정하지 않음 |
| 픽셀 depth 질의 | CPU·합성 이미지 실제 CLI 2턴 통과. 모델 없는 GPU 수집 연결3/3전이 통과; 그 시험은 실모델 호출0·질의1회·질의 중 물리 진행0 | **E16 미사용**, 착의 개선 효과 미측정 |
| 원본 보존 | 닫힌 capture·전수검사·SHA와 허용목록을 확인해 새 staging 생성. wiring 원격 검증 완료 | E16 고정 revision 재다운로드 SHA 검증 완료 |

최신 전체 CPU 검사는 **251개 통과(7.369초)**입니다. 이 수치를 E16 실행 당시의 소스 검사 수로 소급하지 않습니다. E09 종료 프로토콜 수정은 이미 완료됐습니다. 새 기본 환경을 다시 만들거나 과거 오류 수정을 반복할 필요는 없습니다.

## 다음 작업과 명령

E16 정리·원본 보존을 기준으로 main 게시를 확인한 뒤 A 경로를 별도 새 run ID로 실행합니다. 사용자가 화면을 지켜볼 필요는 없습니다. GPU 수집·평가·학습은 순차 실행하며 종료 원본을 덮어쓰지 않습니다.

아래는 **main 통합 후 실행할 E17 계획 명령이며 아직 실행하지 않았습니다.** E16의352전이를 재실행하고,264·346경계의 사진도 새 재실행에서 다시 얻습니다. 과거 원본 이미지를 현재 상태로 간주하지 않고 현재 지지를 재판단합니다. 픽셀 depth 질의는 끕니다.

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

실제 실행 시 소스·명령·출처를 [세션 기록](sessions/20261106-evening-resume.ko.md)에 남깁니다. 기존 E16 원본에 이어 쓰지 않습니다.

## 보존·복원 근거

비공개 HF 저장소 `leonayoon/phyrc-2027-phase1-private-backup`을 사용합니다. audit·평가·배치 metadata는 비공개 검수 자료이며 actor에 연결하지 않습니다.

| 묶음 | 상태·근거 |
|---|---|
| 초기 자산·E07 | [초기 고정 백업](sessions/20261106-remote-backup-verification.json), [이번 서버 복원 검증](sessions/20261106-evening-restore-validation.json). 자산8개 일치·E07 1,067/1,067전이 검사 통과 |
| E10~E14 | [고정 revision과 검증 목록](START_HERE.ko.md#보존-위치와-고정-revision) |
| E15 | [원본 검증](sessions/20261106-e15-backup-verification.json), revision `ba753c41cf64c361ae91aae9e31f9236106bc4ad` |
| 연구 후보 | [선별 원본 백업](sessions/20261106-private-research-backup-verification.json). 후보 복원과 실제 적용을 구분 |
| 이번 wiring | [실제 모델 기본 연결 백업](sessions/20261106-evening-wiring-backup-verification.json) · [모델 없는 질의 연결 백업](sessions/20261106-depth-query-wiring-backup-verification.json), 각각 고정 revision 재다운로드 검증 |
| E16 | [원격 백업·재다운로드 SHA 검증 완료](sessions/20261106-e16-backup-verification.json). revision `1ad0f8ba3cc71ab80962907c713357fbd4005e3f`, 1,181,871,453 bytes. 23:24:18 UTC 확인 |

E07 행동 재실행은 정확한 천 physics checkpoint 복원과 다릅니다. 같은 source group의 분기와 중복 prefix를 새 독립 시연으로 세지 않습니다. E09 불완전 기록은 오류 근거로 보존하며 정상 복원 출처로 사용하지 않습니다. [재실행·분기 가이드](../collection/guides/continuation-and-branches.ko.md) · [클린 서버 명령](START_HERE.ko.md)

## 남은 일과 이전 기록

E16 시각 검수·학습 승인, 승인 시연을 사용한 새 π₀.₅ 학습·성능 검증, RL·다른 VLA·world model 과제 실험은 완료하지 않았습니다. [연구 로드맵](RESEARCH_ROADMAP.ko.md)

[E15 종료 검토](../collection/reviews/20261106-astra-opening264-001.ko.md) · [E15 마감 결론](SESSION_WRAPUP_20261106.ko.md) · [E10~E15 실제 일지](sessions/20261106-resume10.ko.md) · [개편 전 상세 상태](STATUS.before-reorganization-20261106.ko.md) · [개발 이력](HISTORY.ko.md) · [수집 안내](../collection/README.ko.md)

이전 문서의 일시 중지·미실행 문구는 당시 이력입니다. 현재 실행 상태는 이 문서와 이번 세션 기록을 기준으로 확인합니다.
