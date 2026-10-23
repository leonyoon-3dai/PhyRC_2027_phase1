# Project status

Updated: **2026-10-23 · KST / UTC+09:00**  
Phase: **documentation-only reprioritization; clean server starts after owner review**

[English overview](../../README.md) · [한국어](../../README.ko.md) · [Clean-server start](START_HERE.ko.md) / [Engineering sprint](ENGINEERING_SPRINT.ko.md) / [Evidence map](EVIDENCE_MAP.md)

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

