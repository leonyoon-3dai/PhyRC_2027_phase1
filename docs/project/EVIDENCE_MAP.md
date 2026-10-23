# Robot learning capability and evidence

Updated: **2026-10-23**. Review baseline: repository documentation at `ee7e891`. Individual runtime revisions and artifacts are recorded in the [first-session report](sessions/20261022-bootstrap.md) and [metrics](sessions/20261022-bootstrap-metrics.json).

This page connects engineering capabilities to observable evidence and bounded claims. Source code, a completed runtime check, task performance, submission acceptance, and real-robot validation are different evidence levels. Use the [current plan entry](../../README.md) and [status](STATUS.md) before starting work.

## What the current evidence supports

| Capability | Current verified evidence | Next measurement | Claim boundary |
|---|---|---|---|
| Simulator integration | Official build, prepare, and smoke passed on one L40S, 12 vCPU, approximately 70 GiB RAM | E0: restore on a new clean server, smoke, short policy rerun | Simulator integration is demonstrated on the recorded server; second-server recovery remains unverified |
| Synchronized data | Three bounded scripted fixtures, 63 transitions, five RGB-D cameras; schema and continuity checks | E1: genuine human operation, complete export, episode QC and replay | These fixtures validate a recorder path; they are not human demonstrations or dressing experts |
| Remote operation | Streaming/viewer/keyboard implementation exists; full Chrome operation is not verified | E1: both robots, key release, numpad mapping, reconnect and one valid human episode | Code availability does not establish working browser teleoperation |
| RGB-D processing | Recorded RGB-D observations are available | E2: reviewed masks or explicitly labelled manual ROIs, valid depth, camera-local surface points and failure examples | Depth availability is not verified 3D perception, complete reconstruction, or a policy gain |
| State/action adaptation | Three RGB views + 32D robot state mapped to 18 normalized action values | Mapping checks, public-state FK where justified, unit/frame/latency report | 32D is a representation size, not a robot DoF count; depth is not a current policy input |
| Policy learning | JAX LoRA configuration ran for 30 steps, 0.476 effective epochs | E3: train from `pi05_base` on newly reviewed human data; verify updates, reload and rollouts | Overfitting and useful task adaptation have not been established |
| Trainable model scope | Recorded trainable count is **466,957,072** | Reproduce the count and publish parameter groups for each training setting | This is not an adapter-matrices-only training run |
| Offline deployment | Fixed-input offline inference and a one-action official debug run were recorded; score 0/no_contact | E3: paired short policy runs, memory/latency; later complete official self-check | Offline load is evidence of deployment plumbing, not dressing success or judging-hardware compatibility |
| Evaluation/submission | A fresh-clone package run reached 259 actions; the configured 900-second test was interrupted | Complete the full check in a separate budgeted run, then record actual portal status | No full 900-second pass, valid final score, or Codabench submission is established |
| Recovery | HF artifact re-download and CPU state restoration at step 30 were checked | E0: new-server GPU rerun; separate optimizer step 30→31 test | CPU restoration is not second-server recovery, optimizer continuation, or bit-identical training |
| Sim-to-Real | No physical robot validation in this project | Document the adapter, frames, timing, actuator and sensing assumptions | Interface preparation may be described; transfer success and hardware success rates may not |

The [session report](sessions/20261022-bootstrap.md) and [recovery record](RECOVERY.ko.md) are the evidence sources. This documentation update performs no new GPU experiment. A debug zero score is retained as a result, not omitted from the record.

## Evidence to add next

The experiment identifiers below follow the revised short-scope plan. Every target remains pending until a run record exists.

| Experiment | Minimum useful evidence | What it enables |
|---|---|---|
| E0 — clean restore | Pinned artifacts, new hardware/driver manifest, actual smoke, short existing-policy rerun | A defensible claim of clean-server reproducibility within the tested scope |
| E1 — human data and QC | Actual operator input, READY/complete export, synchronized replay, episode-level QC, source/split manifest | A valid human demonstration pipeline with measurable data quality |
| E2 — camera-local RGB-D | Explicitly labeled manual ROIs or reviewed mask samples, valid-depth statistics, optical-Z deprojection, normal/occluded examples | A bounded 3D observation-processing result; optional public FK/Jacobian checks if calibrated |
| E3 — SFT and paired evaluation | New human data, one training configuration, checkpoint reload, base/adapted runs on the same three seeds | A measured comparison, including failures and uncertainty from the small sample |

Use the same adapter, permitted observations, train-derived normalization, controller, action rate, start seeds and short evaluation budget for the E3 pair. Record the compared checkpoint, inference noise/seed handling, raw outputs and timing. Do not call repeatedly tuned development seeds an untouched test.

E2 initially analyzes depth offline. E3 initially uses the existing RGB/state policy. E2 and E3 occurring in the same project does not show that depth caused a policy improvement. A depth-connected policy requires its own input definition, training path and controlled comparison.

## Claims that can grow with the evidence

These are conditional CV/project-description examples. Add numerical fields only from linked completed experiments; keep any negative result and its denominator. They do not amend a CV automatically.

**Current measured scope — usable now**

> Isaac Sim 기반 두 모바일 매니퓰레이터 환경에 공개 관측·행동 기록과 π₀.₅ JAX LoRA 학습·오프라인 실행 경로를 연동했다. Scripted fixture 63개 transition으로 기록 정합성을 확인하고 30-step 학습과 초기 정책 실행을 검증했으며, 착의 성능 검증은 진행 중이다.

This describes integration work. Do not replace “scripted fixture” with “human demonstration,” “30-step learning” with a successful adapted expert, or “JAX” with PyTorch RL.

**After E1 passes — not yet a current result**

> 원격 조작으로 두 로봇의 RGB-D·상태·행동 시연 [N]개를 수집하고, 20Hz 관측·행동·다음 관측의 시간 정렬과 episode 완결성을 검증했다. 검수 결과와 제외 사유, 데이터 분할 및 재현 가능한 저장 이력을 구축했다.

Use “Chrome” only after browser keyboard operation is verified. Use the actual operator/source and recorded QC results. E1 does not by itself establish successful learning or automatic demonstration generation.

**After E3 completes — not yet a current result**

> 검수한 인간 시연으로 π₀.₅를 LoRA 설정에서 미세조정하고, 동일한 3개 초기 배치와 실행 예산에서 base 정책과 비교했다. [보조 구간 완료 x/3 대 y/3, raw points, points/s, 지연·메모리]를 기록하고 실패 원인을 데이터·전처리·제어·정책 관점에서 분석했다.

Use “improved” only if the matched results support that wording, with sample size and conditions. A small or negative comparison remains valid engineering evidence. Full self-check, accepted submission, organizer score and real-robot validation need separate evidence.

## Engineering questions the evidence should answer

| Topic | What to explain with code or measurements |
|---|---|
| Frames and calibration | Define `T_AB` and multiplication direction, metres/radians, quaternion order, camera optical X-right/Y-down/Z-forward, and static versus per-episode transforms |
| RGB-D geometry | Optical-Z versus ray length, invalid depth handling, resize/intrinsics consistency, visible surface versus whole-garment geometry; self-reprojection is not independent accuracy validation |
| FK, IK and Jacobian | Map public joints and fixed robot geometry to an end-effector pose/velocity; distinguish measured joints from independent DoF; explain damping, singularities, limits and feedback |
| Control and timing | Explain 20/60/240Hz, normalized velocity commands, gripper hold intent, chunk execution, observation freshness and actual inference latency |
| SFT versus RL | Explain demonstration action supervision versus reward-driven policy improvement; a LoRA SFT run is not PPO/SAC training |
| Task design | State which observations/actions/rewards/termination/randomization the official task fixes; discuss potential training designs while preserving evaluation and privileged-information restrictions |
| Failure analysis | Separate sensing/mask/depth error, frame or action mapping error, control tracking, garment contact and policy distribution shift using synchronized evidence |
| Sim-to-Real readiness | Identify camera/time calibration, robot API conventions, latency, actuator response, saturation, contact/friction and reset differences still requiring real hardware tests |

Public robot geometry and permitted observations can support FK/control work. Do not use audit camera matrices, hidden object poses, cloth state, evaluator geometry or simulator link transforms to generate policy inputs or automatic demonstration targets. See [RULES](../competition/RULES.md).

The current learning path is JAX π₀.₅ LoRA. Adding a new PyTorch model only to enlarge the stack list is outside the short-scope plan. Framework claims should follow actual implementation and tests.

## Publishing the result

A five-minute technical walkthrough should connect the following evidence rather than list tools: the dressing/data problem and official constraints; synchronized collection and QC; one frame/geometry example; the actual SFT setting and matched comparison; a failure, a deployment limitation and the next test. Use only completed evidence in the present tense. Keep the same links and numbers in the README, experiment report and CV statement.

For each claim, link its code commit, dataset/model revision, commands, hardware, score files, original video/stills, failure cases and recovery scope. Summarize the outcome in [STATUS](STATUS.md) and the [experiment register](../../experiments/README.md).

Keep the public story technical: problem, implementation choice, evidence, limitation and next measurement. Preserve original results when revising an explanation. The record should remain useful when a planned experiment fails, a server is replaced, or a later model supersedes the baseline.
