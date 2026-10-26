# 다음 클린 서버에서 시작하기

> **2026-10-26 우선 지시:** 사용자가 실제 사람 시연 수집을 재개했습니다. 최소 환경 확인 → 크롬 연결 → 두 로봇 연습·수집을 우선합니다. 아래 10월 23일 수집 보류와 긴 정책 검증 순서는 과거 인계입니다. 오늘 수집에는 기존 모델 복원·정책 평가가 필요하지 않습니다. [오늘 실행 안내](LIVE.ko.md) · [오늘 기록](sessions/20261026-live.md)


최종 인계: **2026-10-23 실제 클린 서버 테스트를 사용자 요청으로 종료**했습니다. 상세 결과·성능 분석·검증 한계는 [README.ko.md](../../README.ko.md)와 [오늘 세션](sessions/20261023-clean-start.md)을 먼저 읽으세요. 기본 환경 약 10분/Chrome 준비까지 약 14–15분, 실제 smoke 통과와 사람 조작을 확인했습니다. 전체 900초 검사는 1,460 action/73.0 simulation seconds에서 중단됐고 통과가 아닙니다.

**현재 사용자 범위는 포맷·기존 패키지 검증입니다.** 실작업 사람 시연·새 학습·이전 날짜 스프린트를 자동 재개하지 않습니다. 다음 서버에서는 고정 자료 복원→smoke→짧은 offline 실행→별도 고정 step warm 진단을 우선하고, 그 뒤 전체 검사의 예상 wall 시간을 다시 산정합니다. Codabench 확인은 보류합니다. 아래 수집·학습 절차는 후속 준비 시 사용할 참고이며 현재 실행 지시가 아닙니다.

[현재 상태](STATUS.md) · [자료 복원](RECOVERY.ko.md) · [오늘 중단/복원 근거](sessions/20261023-clean-start.md)

## 1. 읽을 순서

1. 루트 [AGENTS.md](../../AGENTS.md): 실행 범위, 관측 제한, 기록 원칙.
2. [STATUS](STATUS.md): 실제 검증과 미완료 항목.
3. 이 문서: 새 서버에서 재개할 순서.
4. [ENGINEERING_SPRINT](ENGINEERING_SPRINT.ko.md)와 [EVIDENCE_MAP](EVIDENCE_MAP.md): E0–E3, 10/28 결과 고정, 기술 증거와 주장 범위.
5. [RECOVERY](RECOVERY.ko.md)와 [TODO](TODO.ko.md): 고정 HF revision, checksum, 존재하는 실행 명령.
6. [RULES](../competition/RULES.md), [DATA](../competition/DATA.md), [POLICY](../competition/POLICY.md).

`PLAN.ko.md`와 `RGBD_TWO_WEEK_PLAN.ko.md`는 과거 설계·일정의 보존본이다. 현재 우선순위는 위 10월 23일 종료 인계와 사용자가 좁힌 범위를 따른다. ENGINEERING_SPRINT의 날짜별 수집/학습은 후속 계획이다. 이전 세션의 권한이나 살아 있는 서버를 추정하지 않는다.

## 2. 현재 상태를 확인하는 시작 명령

새 위치에 clone한다. 이미 checkout이 있으면 무조건 덮어쓰거나 reset하지 말고 현재 branch와 변경 사항부터 확인한다.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git branch --show-current
git rev-parse HEAD
```

최신 `main`의 인계 문서를 읽은 뒤 사용할 실행 revision을 기록한다. `RECOVERY.ko.md`의 `7c4cfd4...`는 **이전 실험의 고정 코드**다. 인계 문서를 읽기 전에 무조건 해당 commit으로 checkout하지 않는다. 이전 실험을 정확히 재현해야 한다면 별도 worktree/clone에서 수행하고, 새 실험의 source commit과 혼합하지 않는다.

[세션 템플릿](templates/SESSION.md)을 복사해 UTC run ID를 만들고 GPU, CPU, RAM, 디스크, driver, OS, Docker 상태를 기록한다. 공식 [SETUP](../competition/SETUP.md)의 host prerequisite를 확인한다.

```bash
participant/ops/bootstrap.sh --check
# 위 점검에서 빠진 prerequisite를 해결한 뒤 실행:
participant/ops/bootstrap.sh --install
```

`--check`는 prerequisite 명령과 장치를 확인하지만 GPU/Vulkan 정상 동작은 smoke로 확인해야 한다. `--install`은 host helper용 Python 3.12 환경과 HF CLI를 준비하고 공식 doctor/build/prepare/smoke를 실행한다. 10월 23일 실제 클린 서버에서 --install과 smoke까지 통과했다. 개별 시간은 README/세션 기록에 있으며 다른 서버의 성공을 보장하지 않는다. host driver, Docker, uv와 openpi 학습 환경을 모두 자동 설치하는 도구가 아니다. 이미지 버전을 임의로 `latest`로 바꾸거나 공식 torch/torchvision/NumPy를 교체하지 않는다.

## 3. 첫 실행 세션의 순서와 완료 조건

| 순서 | 작업 | 확인할 증거 |
|---|---|---|
| 1 | 새 서버 환경과 공식 smoke | 실제 `PHYRC-SMOKE-PASS`, 로그와 환경 명세 |
| 2 | 기존 dataset/model 복원 | RECOVERY의 고정 revision 다운로드와 checksum |
| 3 | 기존 정책 짧은 재실행 | offline load, 유효한 `(2,9)` 행동, 결과와 영상 |
| 4 | Chrome 원격 입력 | 두 로봇 움직임, 숫자키 대체, gripper, blur/disconnect의 key release |
| 5 | 짧은 사람 시연 1개 | 정상 종료, READY, complete=true, 데이터 검사 |
| 6 | QC와 다음 실행 기록 | 원본/실패 구분, 다음 실제 명령, 원격 보존 근거 |

새 서버의 다운로드/설치 시간을 따로 기록한다. 이전 서버의 예상 시간을 새 서버에서 측정한 시간처럼 쓰지 않는다. GPU 작업은 하나씩 실행한다. 첫 시연이 준비되지 않으면 대량 수집과 본학습으로 넘어가지 않는다.

기존 정책의 debug 실행 명령은 [첫 세션](sessions/20261022-bootstrap.md)과 현재 `participant/policy.py`, `scripts/evaluate_policy.py`의 CLI를 대조해 복원 경로에 맞춘다. 없는 helper 이름이나 가상의 명령을 실행 지침에 넣지 않는다.

## 4. Chrome과 사람 시연

`participant/streaming/`의 viewer/keyboard/launcher는 구현되어 있으나 실제 Chrome 통합 검증은 미완료다. 새 서버의 주소와 현재 클라이언트 IP로 설정을 갱신한다. 접속 주소, 토큰, 인증 캐시는 공개 저장소에 쓰지 않는다.

공식 GUI 명령만으로 Chrome streaming이 자동 시작되지는 않는다. 현재 `participant/streaming/start.sh`, `prepare_viewer.py`, `firewall.py`와 [TELEOP](TELEOP.ko.md)를 읽고 실제 옵션을 확인한다. 사람이 키를 조작해야 하는 단계에서는 조작 방법과 필요한 확인을 사용자에게 전달한다.

1. 현재 클라이언트 IPv4를 확인한 뒤 `firewall.py --client-ip`로 기존 PhyRC streaming 포트만 제한하고 `--check`로 확인한다. IP를 추측하지 않는다.
2. Node/npm을 별도로 확인하고 `prepare_viewer.py`로 viewer를 build한다. bootstrap은 npm을 검사하지 않는다.
3. 생성한 `output/webrtc/viewer/dist`를 제한된 8210 포트에서 별도 serve한다. build helper는 HTTP server를 시작하지 않는다.
4. 새 서버의 advertised IPv4를 `STRETCH4_STREAM_HOST`로 설정한 뒤 `participant/streaming/start.sh`를 실행한다. 이 경로는 recording과 deferred export를 설정한다.
5. 실제 Chrome에서 키 입력을 확인하고 새 recording을 정상 종료한다. 첫 연결 성공만으로 전체 조작 검증을 완료 처리하지 않는다.

Chrome 수정은 첫 2시간으로 제한한다. 계속 막히면 실패 로그와 원인을 보존하고 다른 GPU 원격 데스크톱 경로를 검토한다. 대체 수집 성공을 Chrome 성공으로 기록하지 않는다.

아래 GUI 명령은 로컬 화면 또는 별도 원격 데스크톱 경로를 사용할 때의 공식 수집 예다. Chrome streaming helper와 동시에 두 번째 simulator를 시작하지 않는다.

```bash
# 로컬 GUI / 별도 원격 데스크톱 경로의 공식 수집 명령:
./run.sh gui --training-record 1 --evaluate 1
```

ESC 후 창이 닫혀도 `[Dataset export] READY`까지 기다린다. `capture.json`의 `status=ready`, `complete=true`와 `policy.hdf5`를 확인한다. [DATA](../competition/DATA.md)의 inspect/deferred 검사에 실제 run 경로를 넣는다. 이전 incomplete archive는 실패 근거로 보존하며 강제로 complete로 바꾸지 않는다.

## 5. 이후 연결

- 유효한 사람 시연 뒤 E1/QC → 작은 E2 → E3로 이어간다. 10/26–27 소량 학습·같은 3개 practice seed 비교, 10/28 증거 고정이 목표다.
- 학습 전 `participant/pi05/data.py`의 `approved_pipeline_test` 전용 조건에 인간 데이터용 검수 상태를 명세한다. 인간 데이터를 fixture로 재분류하지 않는다.
- 짧은 학습 LR schedule을 별도로 정하고 실제 update·노출량을 검사한다. 새 인간 SFT는 `pi05_base`와 train-only 정규화로 새 run을 만든다.
- step 30→31 재개는 선택적인 별도 복원 실험이며 기존 checkpoint를 덮어쓰지 않는다. 인간 데이터 학습을 대신하지 않는다.
- RGB-D 도구는 신규 구현 대상이다. camera-local 진단으로 제한하고 SAM/새 IK 설치로 E3를 미루지 않는다. 현재 정책에는 depth가 입력되지 않는다.
- `participant/ops/selfcheck.sh`는 과거 `9d97807`을 checkout한다. 새 ZIP에는 검사 source/base commit을 명시하고 실제 검사 대상을 확인하도록 수정한다. 이 문서는 변경된 CLI가 이미 존재한다고 주장하지 않는다.
- 전체 900초 self-check는 짧은 비교 뒤 별도 슬롯에 수행한다. Codabench 접근이 가능하면 검증 ZIP의 실제 ID/상태를 남긴다. 미접근·미검증은 그대로 기록한다.

## 6. 다음 서버의 Codex에 붙여넣을 요청

```text
이 저장소의 2026-10-23 종료 인계를 이어갑니다.
AGENTS.md, README.ko.md, README.md, STATUS, 오늘 세션
(docs/project/sessions/20261023-clean-start.md), START_HERE와 RECOVERY를 읽으세요.

이전 날짜 스프린트보다 현재 사용자 범위가 우선입니다.
지금은 데이터 포맷과 기존 패키지/제출 검증만 수행합니다.
실작업 사람 시연 수집, 새 SFT, SAM/FK/IK를 자동 시작하지 마세요.
Codabench 접속 확인도 사용자가 다시 요청할 때까지 보류합니다.

오늘 smoke와 Chrome 이동은 통과했고, raw 사람 조작 2419 transition을 기록했습니다.
전체 export는 중단했으며 별도 이동 샘플 3 clip/12 transition만 포맷 검증했습니다.
사람 샘플은 format_only_not_for_sft이고 실제 착의 시연/학습 데이터가 아닙니다.
전체 900초 검사는 1460 actions/73.0 simulation seconds, wall 1814.08 s에서
사용자 요청으로 중단했습니다. full pass나 유효한 최종 점수는 없습니다.

새 서버 환경과 checkout을 확인하고 고정 자료 checksum, 공식 smoke,
기존 정책 짧은 offline 실행부터 검증하세요. GPU 작업은 순차로 수행합니다.
긴 검사를 바로 재개하지 말고 고정 100–200 step warm 진단을 별도로 준비하세요.
이 고정-step helper와 self-check source-selection 개선은 아직 구현되지 않았습니다.
simulation time, policy-call time, 환경 step wall, compile/시작, 총 wall,
CPU/GPU/RAM을 따로 측정하고 다음 전체 검사 시간을 다시 산정하세요.
이전 약 3시간 추정은 다음 서버의 확정 ETA가 아닙니다.

현재 selfcheck.sh는 simulator 9d97807을 선택합니다.
기존 ZIP 재현과 새 main 검사를 구별하고 source/base/ZIP/image를 기록하세요.
공식 물리·형상·action·평가기·센서 정렬은 바꾸지 마세요.
현재 병목은 평가/물리/렌더링 쪽 표본이 크지만 정확한 CPU/GPU 원인은 미확정입니다.
스레드/NUMA/cache 후보는 아직 적용하거나 효과를 검증하지 않았습니다.
12GB 정책 메모리와 RTX 3090 호환성도 미검증입니다.

소스와 실패 기록, 원본 checkpoint를 보존하고 원격 revision/checksum을 확인하세요.
추가 유료 API/서버를 열거나 서버를 종료/삭제하지 마세요.
확인하지 않은 실행을 통과로 쓰지 말고 README/STATUS에 실제 결과를 남기세요.
```

## 7. 종료 전

export와 checkpoint 저장이 끝났는지 확인하고 선택한 산출물만 HF에 보존한다. 원격 revision/checksum을 확인한 뒤 코드와 세션 기록을 반영한다. 다음 run의 정확한 명령과 blockers를 남긴다. 서버 종료/삭제는 별도의 사용자 요청이 있을 때만 수행한다.
