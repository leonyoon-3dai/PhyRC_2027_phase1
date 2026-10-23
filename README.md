# PhyRC 2027 Phase 1

[![Original README - official participant guide](docs/project/assets/original-readme-button.svg)](README.upstream.md)

**Cooperative robot dressing with RGB-D observation processing and VLA adaptation.**

Leonard Yoon, Ph.D. | Independent research project  
[한국어](README.ko.md) / [Current status](docs/project/STATUS.md) / [Clean-server start](docs/project/START_HERE.ko.md) / [Engineering sprint](docs/project/ENGINEERING_SPRINT.ko.md) / [Evidence map](docs/project/EVIDENCE_MAP.md)

This participant fork develops a reproducible workflow for two Stretch 4 robots in the official PhyRC Isaac Sim environment: collect demonstrations, validate observations and actions, adapt π₀.₅, evaluate policy execution, and preserve the submission artifacts.

> **Documentation update: October 23, 2026.** Priorities now follow the October 23–28 evidence sprint. The owner will start a clean server after reviewing this plan. This is a documentation-only update; the measured baseline below is unchanged. Human demonstrations, full 900-second validation, submission, and recovery on a separate clean server remain unverified.

## Start here on a clean server

Read `AGENTS.md`, [STATUS](docs/project/STATUS.md), [START_HERE](docs/project/START_HERE.ko.md), and the [engineering sprint](docs/project/ENGINEERING_SPRINT.ko.md). The start guide contains a paste-ready Codex handoff, existing commands, and the first session's completion criteria.

```bash
git clone https://github.com/leonyoon-3dai/PhyRC_2027_phase1.git
cd PhyRC_2027_phase1
git status --short
git rev-parse HEAD
# Read the documents above before installing or starting GPU work.
participant/ops/bootstrap.sh --check
```

First session: inspect the new server, restore pinned artifacts, pass the official smoke test, rerun the existing policy briefly, and obtain **one valid human-recorded episode** through Chrome. Run collection, training, and GPU evaluation sequentially. Historical recovery commits describe previous runs; read the latest handoff before checking out an old snapshot.

## Verified baseline

Measured on October 22 on one L40S, 12 vCPU, and approximately 70 GiB RAM. Source: [session report](docs/project/sessions/20261022-bootstrap.md).

| Item | Verified scope |
|---|---|
| Official environment | Build, prepare, and actual `PHYRC-SMOKE-PASS` |
| Synchronized recording | 3 scripted episodes, 63 transitions, 5 RGB-D cameras; schema and continuity checks |
| π₀.₅ training | JAX LoRA configuration, 30 updates / 0.476 effective epochs; overfitting not established |
| Offline execution | Official-image load and debug policy execution; **0 points / no_contact** |
| Preservation | HF data, full model/training state, ZIP and evidence; download checksums and CPU state restore at step 30 |
| Submission path | ZIP unpack/build and 259 actions in a fresh clone; **full 900-second check incomplete, not submitted** |

The recorded data is a **Codex-authored bounded script**, labeled `integration_test`. It is neither human demonstration nor live GPT operation. No dressing success or policy improvement is claimed. The upstream freeze filter also leaves some vision/projection parameters trainable; the run is not described as training only small LoRA matrices.

![Actual designated overview camera from the recorder integration test; not a dressing success](docs/project/assets/first-recorder-test.png)

[Three-camera test video](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/resolve/da172805036d5e53daf1834f32baf367820f9183/derived/20261022T0409Z-integration/integration-public-cameras.mp4) / [Data](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data) / [Model and training state](https://huggingface.co/leonayoon/phyrc-2027-phase1-pi05) / [Exact recovery revisions](docs/project/RECOVERY.ko.md)

## Evidence sprint: October 23–28

Complete one small **human collection → dataset QC → π₀.₅ SFT → matched rollout** loop before expanding the system. Dates and counts below are targets, not results. D0 is the day the owner actually starts the next clean server; no server is assumed to have started on October 23.

| Evidence | Scope | Gate |
|---|---|---|
| E0 · Restore | Pinned artifacts, official smoke, bounded offline execution | New-server logs, checksums and measured recovery times |
| E1 · Human collection | Validate Chrome input/export; target 3–5 useful short demonstrations and 1–2 failures | Genuine human source, READY/complete, reviewed dataset |
| E2 · Data and geometry | 20 Hz alignment, units, valid depth, camera-local surface points | QC report and 2–3 reviewed RGB-D examples |
| E3 · Adapt and compare | Small human-data overfit, one SFT configuration, base vs adapted policy | Reloaded checkpoint and same three practice seeds, including failures |

| Target dates | Priority |
|---|---|
| Oct 23–24, if a server is ready | E0 and the first valid human recording |
| Oct 25 | Data QC and a small camera-local RGB-D diagnostic |
| Oct 26–27 | Human-data SFT and short paired evaluation; stop adding features |
| Oct 28 | Freeze evidence, a 60–90 second video, limitations and recovery instructions |
| Oct 29 onward | Full 900-second check, submission and dressing-performance work |

Budget **12–18 focused hours plus measured download/build/compile/export/GPU waits**. Reduce scope if the server opens later. Cap initial Chrome debugging at two focused hours, then document the blocker and consider another remote desktop path. SAM 2, automatic GPT collection, and FK/IK extensions are optional.

Before human SFT, explicitly support reviewed human episodes in the loader and configure an appropriate short-run learning-rate schedule. Start the new human-data run from `pi05_base`; preserve the old integration checkpoint. The self-check helper's historical base commit must also be distinguished from the selected source for a new package. These are planned code changes, not fixes made by this documentation update.

RGB-D is initially an **offline diagnostic**. The current policy consumes three RGB views and robot state; depth diagnostics alone do not demonstrate a policy gain. The initial manipulation segment is approach, grasp and briefly lift while retaining both robots' interface. Full dressing and positive official points/s remain later goals.

Details: [engineering sprint](docs/project/ENGINEERING_SPRINT.ko.md) · [evidence and claim map](docs/project/EVIDENCE_MAP.md). The previous [two-week plan](docs/project/RGBD_TWO_WEEK_PLAN.ko.md) is archived; its dates and 60–70 hour scope no longer govern execution.

## Observation and policy contract

| Interface | Current implementation |
|---|---|
| Available cameras | Overview, robot_0/robot_1 wrist, robot_0/robot_1 head; native 256×256 RGB-D |
| Depth | Optical-axis Z in metres; invalid=0 with `depth_valid=false` |
| Current policy images | Overview + each robot's wrist RGB; depth and head images unused |
| Policy state | 32D: 26 joint positions + 2 fingertip distances + 2 gripper intents + 2 previous grip commands |
| Action | 18 normalized values, padded to 32 for the model and restored to `float32 (2,9)` |
| Timing | 20 Hz policy, 60 Hz control, 240 Hz physics; one action spans 0.05 simulated seconds |

The 32D representation is not a robot DoF count. Gripper zero preserves intent. Camera-local geometry is the first RGB-D target; robot/world transforms require validated FK and static calibration from permitted data. Audit camera matrices, cloth ground truth, object poses, seeds, and raw simulator state are not policy inputs.

Sources: [DATA](docs/competition/DATA.md), [RULES](docs/competition/RULES.md), [interface configuration](config/policy_interface.json), [shared preprocessing](participant/pi05/preprocessing.py).

## Execution and evaluation limits

- Preserve the official physics, action limits, reset rules, and evaluator. Keep SAM 2 analysis, JAX training, and the official simulator environments separate.
- Preserve the base policy and compare on matched seeds, controller, action rate, adapter, normalization, and horizon. Loss, segment completion, raw points, points/s, and full-dressing success are separate metrics.
- Pickup alone can yield zero dressing points/s. Retain failed rollouts and report the small evaluation sample size.
- The full official check has a 900-second simulation-plus-inference budget. At the earlier observed speed, approximately three hours of wall time was estimated; reserve a separate slot and remeasure.
- L40S execution does not verify the judging RTX 3090 24GB or the policy's 12GB budget. The package must load offline with weights, tokenizer, normalization, and code.
- Restricted Codex/GPT collection remains an optional research path. No extra billed API usage is planned, and no organizer approval of that interpretation is claimed.
- Preserve pinned artifacts before ending a disposable session. Do not provision additional compute or stop/delete a server without the owner's request.

After this evidence sprint, continue the same data and experiment workflow toward repeatable dressing progress before the November 17 checkpoint, with an internal submission target of November 16. These remain planned milestones.

## Read and continue

| Document | Purpose |
|---|---|
| [START_HERE](docs/project/START_HERE.ko.md) | Current clean-server entry point and Codex prompt |
| [Engineering sprint](docs/project/ENGINEERING_SPRINT.ko.md) | Active priorities, daily gates, scope limits and evaluation |
| [Evidence map](docs/project/EVIDENCE_MAP.md) | Engineering competencies, verified claims and portfolio updates |
| [Previous two-week plan](docs/project/RGBD_TWO_WEEK_PLAN.ko.md) | Archived schedule; superseded by the active sprint |
| [STATUS](docs/project/STATUS.md) | Measured state and unresolved items |
| [RECOVERY](docs/project/RECOVERY.ko.md) / [TODO](docs/project/TODO.ko.md) | Pinned HF revisions, actual commands, remaining work |
| [TELEOP](docs/project/TELEOP.ko.md) | Human and restricted AI collection design |
| [Experiment register](experiments/README.md) | Session/experiment templates and run index |
| [Initial plan archive](docs/project/PLAN.ko.md) | Original pre-implementation design, retained for history |
| [Sources](docs/project/SOURCES.md) | Reviewed official references and revisions |

## Task and attribution

<details>
<summary>Organizers' cooperative dressing demonstration</summary>

![Organizers' teleoperation demonstration, not this project's result](docs/videos/Back_Front_32x.gif)

Official upstream demonstration at 32× speed, showing two Stretch 4 robots dressing a seated manikin. This is not a learned-policy result from this fork.

</details>

This is Leonard Yoon's participant project, not an organizer repository. [README.upstream.md](README.upstream.md) preserves the reviewed guide at upstream `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`. Official simulation, assets, evaluation, and demonstrations retain their attribution. See [LICENSE](LICENSE), [NOTICE](NOTICE), and [THIRD_PARTY.md](THIRD_PARTY.md).

Official challenge: https://emprise.cs.cornell.edu/phyrc/challenge-2027/  
Official code: https://github.com/rirolab/PhyRC_2027_Challenge  
Codabench: https://www.codabench.org/competitions/18366/  
Previous BEHAVIOR project: https://github.com/leonyoon-3dai/behavior-submission-2026

<details>
<summary>Original guide compatibility anchors</summary>

<a id="1-install-and-run"></a>
[Install and run](README.upstream.md#1-install-and-run)

<a id="2-teleop-controls"></a>
[Teleop controls](README.upstream.md#2-teleop-controls)

<a id="3-collect-training-data"></a>
[Collect training data](README.upstream.md#3-collect-training-data)

<a id="4-observations"></a>
[Observations](README.upstream.md#4-observations)

<a id="5-actions"></a>
[Actions](README.upstream.md#5-actions)

<a id="6-train-and-run-a-policy"></a>
[Train and run a policy](README.upstream.md#6-train-and-run-a-policy)

<a id="7-scoring-and-pointss"></a>
[Scoring and points/s](README.upstream.md#7-scoring-and-pointss)

<a id="8-allowed-information-and-fair-play"></a>
[Allowed information and fair play](README.upstream.md#8-allowed-information-and-fair-play)

</details>
