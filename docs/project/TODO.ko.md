# 다음 클린 서버 TODO

**10월 23일 실행 종료 인계가 우선합니다.** [오늘 보고서](sessions/20261023-clean-start.md)와 README를 먼저 읽으세요. 복원/smoke/Chrome 이동/최소 사람 이동 포맷은 확인했고, 전체 검사는 1460 actions/73.0 simulation seconds에서 중단했습니다. 다음 서버에서는 짧은 offline 확인과 별도 고정-step warm 시간 진단이 우선입니다. 옷 시연·새 SFT와 Codabench 확인은 현재 보류입니다. 아래 날짜 스프린트는 후속 참고이며 자동 재개 지시가 아닙니다.

문서 갱신: **2026-10-23**. 문서만 변경했고 실행 결과는 추가하지 않았다. 현재 기준은 [ENGINEERING_SPRINT](ENGINEERING_SPRINT.ko.md)와 [EVIDENCE_MAP](EVIDENCE_MAP.md)다. D0는 실제 다음 클린 서버 개설일이다.

**현재 시작점은 [START_HERE](START_HERE.ko.md), 일정은 [실행 스프린트](ENGINEERING_SPRINT.ko.md)다.** 사용자가 다음 서버를 열면 복원과 smoke 후 짧은 정책 실행, 유효한 사람 시연 1개, QC부터 진행한다. 아래 항목은 미해결 기술 작업의 근거와 명령을 보존한다.

## 2026-10-22 실행 세션에서 확인한 것

- 공식 doctor/build/prepare/smoke와 실제 `PHYRC-SMOKE-PASS`.
- 실제 RGB-D·공개 로봇 상태·정규화 action의 3 episode / 63 transition 수집과 시간 정렬 검사.
- API 과금 없는 Codex 작성 제한 명령 사용. source=`integration_test`; 인간 또는 live GPT 시연이라고 표시하지 않음.
- π₀.₅ JAX LoRA 30 step, 전체 checkpoint 저장, 공식 이미지의 오프라인 로딩 및 학습 정책 debug 실행(0점, no_contact).
- ZIP 제작·fresh clone unpack/checksum·정책 부분 실행. 공식 900초 검증은 미완료.
- HF 데이터·모델·제출 ZIP·실행 증거를 고정 revision에서 재다운로드하고 checksum 확인.
- 원격 모델로부터 CPU에서 전체 params·optimizer/train state와 step 30 복원. optimizer step 재개 또는 dataloader cursor 복원 검증은 아님.
- GitHub 공개 기록과 복원 도구. [세션 결과](sessions/20261022-bootstrap.md) · [복원 명령](RECOVERY.ko.md).

## 우선순위와 예상 시간

아래는 다음 실행의 목표·작업 예산이며 완료 시간이 아니다. 같은 L40S/12-vCPU급 서버를 가정하되 다운로드·build·compile·export·학습·평가 대기를 별도로 측정한다. GPU 작업은 순차 실행한다.

| 순서 | 작업 | 완료 기준 | 범위 제한 |
|---|---|---|---|
| E0 | 고정 환경·자료 복원, smoke, 기존 정책 짧은 실행 | checksum, 실제 smoke PASS, offline action, 새 서버 시간표 | 1–2시간 집중 작업 + 대기. step 30→31은 별도 선택 시험 |
| E1 | Chrome 입력·사람 시연 | 두 로봇 입력/release, READY/complete, 출처, 유효 데이터 | 3–4시간. Chrome 수정은 우선 2시간; 시연 3–5개·실패 1–2개 목표 |
| E2 | 시간 정렬·RGB-D 진단 | 20Hz obs/action/next_obs, 단위, optical-Z, camera-local 점군 | 2–3시간. 2–3시점부터, SAM/IK 필수 아님 |
| E3a | 인간 데이터 학습 준비 | 새 검수 상태/loader, train-only 통계, 짧은 LR schedule | fixture 상태로 인간 데이터를 위장하지 않음 |
| E3b | 작은 overfit·단일 SFT | pi05_base에서 새 run, 실제 update·노출량, checkpoint reload | E3 전체 3–5시간 집중 작업 + 대기 |
| E3c | 같은 조건 base/adapted 평가 | 같은 practice seed 3개, 짧은 동일 예산, 원본 실패 포함 | 10/26–27 목표. 튜닝 seed는 untouched test 아님 |
| 정리 | 결과·영상·복원 명령 고정 | E0–E3 실제 범위, 실패, 60–90초 영상, 원격 checksum | 10/28 목표. 예산 지연 시 선택 기능 축소 |
| 후속 | 전체 900초 self-check | 새 패키지의 source/base commit, ZIP SHA256, valid 완결 결과 | 과거 helper의 9d97807 고정 수정/명시. 기존 속도 약 3시간 추정 |
| 후속 | Codabench·착의 성능 | 실제 제출 ID/상태, 3–5배치, 첫 소매까지 시연 확대 | 내부 11/16 제출 목표. 수량은 실적 아님 |

집중 작업 합계 12–18시간을 제안한다. 코드 변경 전 확인할 세 항목은 `data.py`의 `approved_pipeline_test` 전용 loader, 짧은 30-step 학습과 1,000-step warmup, `selfcheck.sh`의 역사적 checkout이다. 이번 문서 갱신에서는 이 코드를 수정하지 않았다.

기존 900초 실행은 사용자 요청으로 중단했다. 부분 기록은 259 action / simulation 12.95초이며 **유효한 최종 점수·공식 통과가 아니다**. simulator·규칙·평가를 바꿔 빠르게 완료한 것으로 처리하지 않는다.

## 실제 존재하는 재실행 명령

환경 복원은 [RECOVERY.ko.md](RECOVERY.ko.md)를 먼저 따른다. checkout당 GPU 작업 한 개만 실행한다.

```bash
participant/ops/bootstrap.sh --check
# 위 prerequisite 점검 후:
participant/ops/bootstrap.sh --install
```

HF에 저장된 정확한 ZIP으로 새 run ID를 사용한다. 이 helper는 고정 기반 commit의 fresh clone에 ZIP을 풀어 checksum, build, 정책 부분 실행까지 수행했다. 최신 main 전체를 검사하는 경로가 아니며 900초 통과도 아직 아니다. 새 패키지 검사 시 helper의 고정 commit과 ZIP을 함께 기록한다.

```bash
hf download leonayoon/phyrc-2027-phase1-pi05 \
  submissions/20261022T0429Z-pi05-release.zip \
  --type model --revision 1ff737e560e7f4b2c9a29534ff4f907dc01a6a98 \
  --local-dir output/recovered-submission
sha256sum output/recovered-submission/submissions/20261022T0429Z-pi05-release.zip
# Expected SHA256:
# 611ec928e35c4c446098de2e645cf4d7e332dc95b74e3fbeb54b14663df64871

.venv/bin/python participant/ops/run.py --id "$(date -u +%Y%m%dT%H%M%SZ)-official900" \
  --success-marker 'FINAL SCORE:' -- participant/ops/selfcheck.sh \
  output/recovered-submission/submissions/20261022T0429Z-pi05-release.zip \
  "$(date -u +%Y%m%dT%H%M%SZ)-fresh900" 900
```

최종 성공 판정에는 marker뿐 아니라 실제 exit 상태·900초 설정·완결된 valid 결과 JSON을 함께 확인한다. partial trace나 accepted/Scoring 상태를 착의 성능 완료로 표시하지 않는다.

Chrome 재시도 시 먼저 새 클라이언트 IP로 `participant/streaming/firewall.py`를 설정하고 `prepare_viewer.py`로 viewer를 재생성한다. 접속 정보는 공개 GitHub에 남기지 않는다. 이전 raw archive는 incomplete여서 공식 exporter가 거부했다. metadata를 고쳐 강제로 유효하게 만들지 말고 실패 자료로 보존한 채 새 짧은 recording을 정상 종료한다.

