# 다음 클린 서버 TODO

2026-10-22 실행 세션에서 보존과 기록을 마치고 장시간 작업을 다음 클린 서버로 이관했다. 당시 900초 평가와 streaming 프로세스를 종료했지만 서버 자체는 종료/삭제하지 않았다. 이번 문서 업데이트에서는 현재 서버 상태를 재검사하거나 변경하지 않았다.

**현재 시작점은 [START_HERE](START_HERE.ko.md), 일정은 [2주 실행 계획](RGBD_TWO_WEEK_PLAN.ko.md)이다.** 10월 23일 새 서버에서 복원과 smoke 후 짧은 정책 실행, 유효한 사람 시연 1개, RGB-D QC를 우선한다. 아래 항목은 미해결 기술 작업의 근거와 명령을 보존한다.

## 이번 세션에서 끝낸 것

- 공식 doctor/build/prepare/smoke와 실제 `PHYRC-SMOKE-PASS`.
- 실제 RGB-D·공개 로봇 상태·정규화 action의 3 episode / 63 transition 수집과 시간 정렬 검사.
- API 과금 없는 Codex 작성 제한 명령 사용. source=`integration_test`; 인간 또는 live GPT 시연이라고 표시하지 않음.
- π₀.₅ JAX LoRA 30 step, 전체 checkpoint 저장, 공식 이미지의 오프라인 로딩 및 학습 정책 debug 실행(0점, no_contact).
- ZIP 제작·fresh clone unpack/checksum·정책 부분 실행. 공식 900초 검증은 미완료.
- HF 데이터·모델·제출 ZIP·실행 증거를 고정 revision에서 재다운로드하고 checksum 확인.
- 원격 모델로부터 CPU에서 전체 params·optimizer/train state와 step 30 복원. optimizer step 재개 또는 dataloader cursor 복원 검증은 아님.
- GitHub 공개 기록과 복원 도구. [세션 결과](sessions/20261022-bootstrap.md) · [복원 명령](RECOVERY.ko.md).

## 우선순위와 예상 시간

아래는 실측 완료 시간이 아니라 다음 작업의 추정이다. 동일한 L40S/12-vCPU급 Brev 서버, 작동하는 Docker/NVIDIA runtime, 충분한 네트워크를 전제로 한다. GPU 작업은 순차 실행한다.

| 순서 | 다음 작업 | 완료 기준 | 예상 / 불확실성 |
|---|---|---|---|
| 1 | 고정 환경과 HF 산출물 복원 | checksum, doctor와 실제 smoke PASS | 20-40분 추정, 다운로드/설치 변동 포함 30-60분 여유. 새 서버 실측 전 |
| 2 | 기존 정책의 짧은 재실행 | offline load, bounded (2,9) actions, 결과 JSON | 환경 준비 후 약 2-5분 추정 |
| 3 | Chrome과 사람 시연 확보 | 두 로봇 입력, key release, READY, complete, public HDF5 검사 | 30-90분 이상. 실제 원격 조작 미검증 |
| 4 | RGB-D replay와 데이터 QC | 시간 정합, 유효 depth, camera-local 점군과 mask 검수 | 신규 구현. 2주 계획의 D3-D6 |
| 5 | optimizer step 재개 시험 | 고정 원본 자료로 step 30→31, 새 checkpoint와 출력 | 5-15분 추정. dataloader cursor 동일 재개는 아님 |
| 6 | 유효 시연의 overfit와 단일 SFT | 학습 대상 확인, 노출 기록, 재로딩과 closed-loop 실행 | 기존 30 step은 warmup 1,000 미만. 새 데이터는 별도 run |
| 7 | 동일 조건 평가와 full 900초 self-check | 짧은 paired 비교 후 실제 ZIP의 완결된 valid 결과 | 전체 검사는 기존 관측 속도에서 약 3시간 추정 |
| 8 | Codabench 첫 제출 | 검증 ZIP SHA256, 제출 ID와 실제 accepted 상태 | 사이트 접근 재확인 필요. 약 6.34GB 전송 시간 별도 |
| 9 | 후속 성능 연구 | 여러 배치에서 반복 가능한 첫 소매 삽입 등 | 2주 기준선 이후. 현재 0점/실패 기록 보존 |


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

