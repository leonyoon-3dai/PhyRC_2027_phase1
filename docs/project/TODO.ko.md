# 다음 클린 서버 TODO

2026-10-22 사용자의 요청에 따라 빠른 보존·기록 작업을 마치고, 장시간·불확실 작업은 다음 클린 서버로 이관했다. 현재 서버를 종료하거나 삭제하지 않았다. 900초 평가와 streaming 프로세스만 종료했으며 GPU 실행은 남아 있지 않다.

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
| 1 | 고정 코드·이미지·HF 산출물 복원 | artifact checksum, doctor와 smoke PASS | 환경 재구성 20–40분, 보수적으로 30–60분. 드라이버 설치·재부팅·인증 대기 제외 |
| 2 | 짧은 기존 정책 재실행 | offline load, bounded (2,9) actions, 유효한 결과 JSON | 환경 준비 후 약 2–5분 |
| 3 | 실제 optimizer step 재개 | 원격 checkpoint step 30 → 31, 새 checkpoint와 fixed-input 비교 | 약 5–15분 추정; 아직 미검증. dataloader cursor 동일 재개 아님 |
| 4 | Chrome 수집 경로 완성 | 실제 Chrome 영상, 두 로봇 모든 축·그리퍼·동시 입력·Mac 매핑·blur/disconnect·P/ESC·READY와 complete capture | 30–90분 이상, 네트워크/입력/권한 불확실성 있음. GPU 원격 데스크톱 대안도 별도 검증 |
| 5 | 작은 데이터 과적합 시험 개선 | 충분한 노출, action 연결·gripper intent·closed-loop 검증 | 30–120분 이상. 현재 30 step은 default warmup 1,000보다 작아 overfit 성공을 주장할 수 없음 |
| 6 | 공식 full 900초 self-check | fresh clone 실제 ZIP으로 900초 완료와 유효한 최종 JSON | 현재 측정 약 1.2–1.3 action step/wall-second 기준 약 3시간 전후. 900은 simulation+inference 예산이며 실제 대기 15분이 아님 |
| 7 | Codabench 첫 제출 | 검증 ZIP SHA256와 제출 ID, accepted 상태 기록 | 사이트 복구 후 작업 10–30분 + 약 6.34GB 전송·서버 처리 시간. 현재 사용자/서버 모두 접속 불가 |
| 8 | 일반 SFT·성능 개선 | 실패 포함 고정 배치에서 첫 소매 삽입 반복 | 별도 후속 연구. 현재 0점·실패 기록을 기준선으로 보존 |

기존 900초 실행은 사용자 요청으로 중단했다. 부분 기록은 259 action / simulation 12.95초이며 **유효한 최종 점수·공식 통과가 아니다**. simulator·규칙·평가를 바꿔 빠르게 완료한 것으로 처리하지 않는다.

## 실제 존재하는 재실행 명령

환경 복원은 [RECOVERY.ko.md](RECOVERY.ko.md)를 먼저 따른다. checkout당 GPU 작업 한 개만 실행한다.

```bash
participant/ops/bootstrap.sh --check
# 위 prerequisite 점검 후:
participant/ops/bootstrap.sh --install
```

HF에 저장된 정확한 ZIP으로 새 run ID를 사용한다. 이 helper는 fresh clone·unpack·checksum·build·정책 부분 실행까지 실제 수행했으며, 끝까지 900초를 통과한 도구로 표현하지 않는다.

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
