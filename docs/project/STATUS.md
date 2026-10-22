# Project status

Updated: **2026-10-22 · KST / UTC+09:00**  
Phase: **documentation-only planning update; next clean-server session planned for 2026-10-23**

[English overview](../../README.md) · [한국어](../../README.ko.md) · [Clean-server start](START_HERE.ko.md) / [Two-week plan](RGBD_TWO_WEEK_PLAN.ko.md)

## Documentation update and next execution

- No new server, collection, training, or evaluation was run during this documentation update. The measured runtime table below remains the 2026-10-22 first-session evidence.
- Next session: restore pinned artifacts, pass official smoke, rerun the existing policy briefly, and validate Chrome control with one complete human episode.
- Active plan: RGB-D/replay QC, prompted offline garment masks, camera-frame point clouds, one pi0.5 SFT setting, and matched evaluation over a two-week target window (2026-10-23 through 2026-11-05).
- Human-demo counts, mask/point-cloud modules, new SFT results, and benchmark numbers are planned work, not completed capabilities.
- Operational entry: `START_HERE.ko.md`. Artifact commands: `RECOVERY.ko.md`. The archived `PLAN.ko.md` is retained as history.

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

The failed teleop archive is incomplete and the official exporter refused it; it remains failure evidence, not a finished human dataset. Codabench registration is complete but the site is inaccessible from both the owner and server. No submission/accepted/scored status exists.

```bash
participant/ops/bootstrap.sh --check
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
```

## Open technical questions

| Question | How it will be resolved |
|---|---|
| Does WebRTC preserve PhyRC's keyboard events and app window on this server? | Two-robot movement, numpad mapping, key release, reconnect tests |
| Does π₀.₅ meet the judging hardware budget? | Official-image L40S fixture and learned-policy partial run passed; RTX 3090 and full 900-second checks remain pending |
| Can the AI operator generate useful demonstrations from allowed observations? | Short bounded trials, recorded inputs/actions, human review; no success assumption |
| Is automatic recording valid? | Live HDF5 schema/continuity passed for 63 transitions; raw/deferred parity is not claimed |
| How fast is clean-server recovery? | Measure download/build/compile/restore/smoke separately on a second clean server |

The automatic-demonstration rules interpretation is documented in [TELEOP.ko.md](TELEOP.ko.md). No organizer approval has been obtained or claimed.

## Update after each real session

Link the session record and experiment run IDs, state what was actually verified, preserve failures, and list the next commands and expected checks. Move an item out of pending only when its evidence exists. Keep README status consistent.

