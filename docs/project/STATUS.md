# Project status

## 2026-10-27 visual documentation update / 시각자료 갱신

The English README now presents the October 26 human recordings with extracted stills, an English-captioned preview, a collection summary, participant workflow, data/action contract and measured runtime charts. [Visual provenance](assets/visual-20261027/provenance.json) records source video, snapshot, frame timestamps and asset hashes. No new collection, export, policy training or GPU evaluation was performed. Runtime counts and limits remain those in the October 26 handoff below. Korean status remains synchronized in README.ko.md.

영문 README에 기존 시연 장면과 실측 수치 기반 시각자료를 추가했습니다. 새 수집·RGB-D 변환·학습·평가는 수행하지 않았고, 사람 시연 4개 수집/6개 episode/5571전이 및 미완료 범위는 아래 기록과 같습니다.


## 2026-10-26 · owner-ended session / 오늘 종료

시연과 viewer를 정상 종료했고 GPU 0MiB 및 streaming listener 종료를 확인했습니다. 서버 power/deletion은 수행하지 않았습니다. 사용자는 UI가 조금 나아졌으나 개선할 점이 많다고 평가했고, 다음 클린 서버에서 같은 UI로 재시도·피드백하기로 했습니다. 오늘 작업을 자동 재개하지 않습니다.

4 complete human-practice collections / 6 episodes / 5571 transitions (278.55 simulation seconds); final retry 1851 transitions, complete raw archive. RGB-D training export/QC remains pending. The 2225-transition pickup/transport demo and 33-second edit are preserved; full dressing is unverified. HF upload, full immutable-revision re-download and SHA256 checks passed. [Final preservation and next commands](END_20261026.ko.md) · [Clean-server entry](START_HERE.ko.md).

이하 기록은 진행 중 메모를 포함한 역사적 근거이며 종료 상태를 대체하지 않습니다.


## 최신: 사람의 양팔 파지·들기·운반과 조작 UI 개선

사용자 시연 `20261026T061140_546693Z_ab9e06`을 complete=true로 보존했습니다. 2,225전이/111.25초 simulation, 1,168.119초 collection wall, 28,928 raw states. 원본 reader/hash 검사와 상태 재생을 마쳤고, 파지·들기·사람 쪽 운반을 실제 이미지에서 확인했습니다. [33초 편집 시연과 근거](DEMO_20261026.ko.md). 전체 착의와 공식 점수는 미확인입니다. RGB-D 학습 export와 원격 raw 업로드는 대기입니다.

새 Chrome UI: 로봇 좌표 투영 방향 화살표, 클릭 이동, 로봇별 큰 조작 버튼, 정밀 모드, 짧은 탭 최소 3 update 보존, 수신/반영 구분, blur/watchdog 우선 해제. 입력 상태 5개 단위 검사와 mocked Chromium 상호작용 검사 통과. 실제 두 로봇 투영 좌표/8개 방향 생성 확인 후 `20261026-live-controls-v2`로 재실행했습니다. 사용자의 실제 UX 개선 확인은 다음 피드백에서 판단합니다.

1280/기록 ON, 960/기록 ON, 1280/기록 OFF의 각 120-control-frame 진단은 모두 exit 0. 약 10초 warm 창의 RTF 0.1045/0.1067/0.1187. 단일 반복·동시 CPU 편집의 한계가 있으며 [성능 상세](PERFORMANCE.ko.md)에 구간별 수치를 기록했습니다. 진단 자료는 사람 시연 수량에 포함하지 않습니다. 실제 학습 정책 추론은 아직 미측정입니다.


## 2026-10-26 · 사람 시연 수집 재개

사용자 지시로 실제 착의 연습·사람 시연 수집을 재개했습니다. 최소 환경 점검과 크롬 접속을 먼저 준비하며, 학습·긴 정책 검사는 선행하지 않습니다. 공식 최신 upstream은 기존 `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`와 같음을 확인했습니다. 새 서버 prerequisite와 viewer build는 통과했고 공식 build/prepare는 exit 0(169.02초/8.81초), smoke도 355.79초, exit 0·`PHYRC-SMOKE-PASS`로 통과했습니다. 사용자가 실제 Chrome 두 로봇 조작을 확인했습니다. 첫 수집은 RAM 급증에 따른 kernel OOM으로 중단되어 complete=false입니다. 넓은 시점 재시작은 약 8.35GiB RSS로 정상 종료했고 3 episodes·727전이·36.35초 원본을 complete=true로 보존했습니다. 592개 청크·9462 raw frames의 checksum/연속성 통과, 비영 action 110개. RGB-D 변환과 학습 적합성 검수는 아직입니다. 이후 사용자 요청의 옷 옆 로봇/정면 카메라 고정 연습 배치로 새 수집을 시작했습니다. 공식 평가 기본 배치와 구분합니다. [성능 기록](PERFORMANCE.ko.md)을 추가했으며 실제 정책 추론과 고정-step GPU 진단은 미실행입니다. 오늘 사람 조작·export·착의 성공은 아직 확인 전입니다. [오늘 기록](sessions/20261026-live.md) · [크롬 안내](LIVE.ko.md) · [시연 결과](RESULTS.ko.md)

아래 10월 23일 중단 상태는 역사적 기록이며 오늘의 수집 재개 지시를 대체하지 않습니다.


Updated: **2026-10-23 · KST / UTC+09:00**  
Phase: **tests stopped by owner; restore/smoke and human format sample verified; full check incomplete**

[English overview](../../README.md) · [한국어](../../README.ko.md) · [Clean-server start](START_HERE.ko.md) / [Engineering sprint](ENGINEERING_SPRINT.ko.md) / [Evidence map](EVIDENCE_MAP.md)

## Final October 23 state / 오늘 종료 상태

- Owner requested stopping tests for review before a future clean server. Evaluation and viewer processes are stopped; GPU 0 MiB confirmed. Server power/deletion was not performed.
- Official build/prepare/smoke passed: 218.53/9.14/367.80 s. Core setup ~10 min, through policy/Chrome readiness ~14–15 min; initial downloads/build overlapped.
- Pinned data/model/train-state/ZIP recovery hashes passed. Short policy check: exit 0, 91.11 s wall, one action/0.05 simulation s, 0 points/no_contact. No optimizer continuation or new SFT.
- Owner confirmed real Chrome keyboard and robot movement. Bottom-right compact live control guide implemented; headless Chromium UI checks passed with mocked input. Full reconnect/gripper checklist remains unverified.
- Human ESC capture: complete raw 2419 transitions/120.95 simulation s. Full export deliberately interrupted after a rendered prefix of 364 transitions. A separate **format-only** motion sample of 3 clips/12 transitions/0.6 s passed original state/action, five RGB-D camera, timing, continuity and official loader checks. It is not approved SFT or dressing data.
- Full 900-second check deliberately interrupted: **1460 actions/73.0 simulation s**, run wall **1814.08 s**, no final score. Child process returned 0 on signal, but wrapper correctly reports verification failure 1 because `FINAL SCORE:` is absent; this is not a pass. Exact consumed 900-budget time is unknown because cumulative inference latency was not logged.
- Short profiler snapshot: evaluation/contact ~41%, physics/control ~39%, camera ~16%, inference ~4%. Hardware checks did not show RAM/GPU capacity pressure, thermal throttling, I/O wait, CPU quota/throttling or OOM. Pure CPU/GPU bottleneck and any tuning benefit remain unproven.
- Policy-alone 12 GB cap and RTX 3090 compatibility remain unverified. No official physics/evaluator/sensor timing changes made.
- Codabench unreachable from server and owner's Mac; follow-up deferred. No submission/acceptance/organizer score.
- Next server: follow READMEs and latest [session report](sessions/20261023-clean-start.md), restore pinned assets, short check, separate fixed 100–200-step warm diagnostic, then explicitly budget a full run. No task demos/new training until owner is ready.

검증된 결과는 클린 서버 복원·공식 smoke·Chrome 이동·최소 사람 데이터 포맷이다. 900초 전체 검사는 사용자 요청 중단이며 착의 성공·제출·학습 성능 향상은 없다. 아래 과거 스프린트보다 현재 사용자 범위가 우선한다.

Remote evidence: [E0](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/2234dfd306df355bf8a9f879b6b3aaae4c3b56f8/sessions/20261023-clean-start-e0), [human format sample](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/c31241f626c4cbf02c2bd69a10f70a3841fa58a3/samples/20261023-human-motion-format-test). Final raw source revision `32fc6d21c5d358caefd17c6aadfc4f25a843e368` and final interrupted-test evidence `93753f568811c5cfcd0235f5d8cb9940c5ce6a23` are recorded with restore commands in the session report. Final raw-source download/restore/re-derivation passed, with exact equality of all 171 public HDF5 datasets.

The following October 22 runtime tables and documentation-update notes are preserved as historical evidence; they do not supersede this new session.

## Documentation update and next execution

- No server, collection, training, or evaluation was run during this update. The runtime table remains the 2026-10-22 evidence.
- Active plan: [October 23–28 engineering sprint](ENGINEERING_SPRINT.ko.md). D0 is the actual next server session, not an assumed October 23 start.
- E0 restores pinned artifacts and checks smoke/offline execution. E1 obtains genuine human data. E2 checks synchronization and a few camera-local RGB-D samples. E3 uses a new human-data SFT run and short base/adapted evaluation on the same three practice seeds.
- Move the small learning/comparison loop to October 26–27; freeze evidence on October 28. SAM 2, GPT collection and FK/IK are optional. Full 900-second validation and submission follow this loop.
- Before human SFT: define human review/loader states, configure short-run LR, and start from `pi05_base` with train-only normalization. The historical self-check commit must be explicit for each package. These are pending implementation tasks, not fixes delivered here.
- [EVIDENCE_MAP](EVIDENCE_MAP.md) separates current CV-safe claims from conditional statements after future runs. Human collection, depth processing, improved manipulation and real-robot results remain unverified.
- Operational entry: `START_HERE.ko.md`. Artifact commands: `RECOVERY.ko.md`. `RGBD_TWO_WEEK_PLAN.ko.md` and `PLAN.ko.md` are archived plans.

## Reviewed planning baseline

- Reviewed the official simulator, data contract, rules, scoring, and submission process at upstream `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`.
- Preserved the original README separately and prepared this participant project's English/Korean overview.
- Defined Chrome human teleoperation and restricted Codex/GPT automatic collection as two proposed data sources.
- Planned a single-L40S π₀.₅ JAX LoRA baseline and an early offline deployment gate.
- Added first-session instructions, recovery requirements, and session/experiment templates.

## Runtime state

Evidence: [first server session](sessions/20261022-bootstrap.md), [measured run index](sessions/20261022-bootstrap-metrics.json).

| Item | State |
|---|---|
| Brev server | L40S ×1, 12 vCPU, approximately 70 GiB RAM; driver/container GPU verified |
| Official environment | build / prepare / actual PHYRC-SMOKE-PASS completed |
| Chrome streaming/keyboard | Viewer and launcher implemented; two failed attempts preserved, fixes pending full runtime test; remote Chrome not verified |
| Restricted recorder | 3 real-sensor scripted integration episodes, 63 synchronized transitions; official schema + continuity checks passed |
| Human / live GPT demonstrations | None; owner requested no extra billed GPT API and approved low-quality valid scripted data for pipeline testing |
| π₀.₅ JAX LoRA | 30 steps completed; 0.476 effective epochs; overfitting not established |
| Offline inference | Official-image base fixture passed without changing bundled torch/torchvision/NumPy; learned policy debug action ran |
| Debug score | Raw points 0, points/s 0, no_contact; no dressing success |
| Submission | Complete ZIP, fresh-clone unpack/build and 259 actions verified; 900-second test interrupted by owner, no valid final score; not submitted |
| Artifact preservation | HF data, full model/train state, ZIP and session evidence uploaded at immutable revisions; re-download checksums passed; CPU full-state restore at step 30 passed |
| New clean server | Not tested; same-server fresh-directory recovery passed |

## Next clean server

[Prioritized TODO with time estimates](TODO.ko.md) · [exact artifact restore commands](RECOVERY.ko.md).

At the end of the recorded 2026-10-22 runtime session, the owner requested preserving the quick, verified work. Active GPU processes and the temporary viewer were stopped then; the Brev server itself was not stopped or deleted. This documentation update did not inspect or change its current power state. Expected environment reconstruction on a comparable prepared Brev server: 20–40 minutes, allow 30–60 minutes for setup/download variation. Full 900-second evaluation is a separate roughly three-hour task at the observed rate.

The failed teleop archive is incomplete and the official exporter refused it; it remains failure evidence, not a finished human dataset. Codabench registration is recorded as complete; the prior session reported access failures from the owner and server. Access was not rechecked in this documentation update. No submission/accepted/scored status exists.

```bash
participant/ops/bootstrap.sh --check
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
```

## Open technical questions

| Question | How it will be resolved |
|---|---|
| Does WebRTC preserve PhyRC's keyboard events and app window on this server? | Two-robot movement, numpad mapping, key release, reconnect tests |
| Can genuine human data produce a useful small adaptation? | New human review schema, short-run LR, overfit/update checks, then matched three-seed runs |
| Does RGB-D analysis improve policy execution? | Not tested: E2 is offline diagnostics; a controlled depth-connected comparison is later work |
| Does π₀.₅ meet the judging hardware budget? | Official-image L40S fixture and learned-policy partial run passed; RTX 3090 and full 900-second checks remain pending |
| Can the AI operator generate useful demonstrations from allowed observations? | Short bounded trials, recorded inputs/actions, human review; no success assumption |
| Is automatic recording valid? | Live HDF5 schema/continuity passed for 63 transitions; raw/deferred parity is not claimed |
| How fast is clean-server recovery? | Measure download/build/compile/restore/smoke separately on a second clean server |

The automatic-demonstration rules interpretation is documented in [TELEOP.ko.md](TELEOP.ko.md). No organizer approval has been obtained or claimed.

## Update after each real session

Link the session record and experiment run IDs, state what was actually verified, preserve failures, and list the next commands and expected checks. Move an item out of pending only when its evidence exists. Keep README status consistent.


