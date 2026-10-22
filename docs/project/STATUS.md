# Project status

Updated: **2026-10-22 · KST / UTC+09:00**  
Phase: **pre-server planning and documentation**

[English overview](../../README.md) · [한국어](../../README.ko.md) · [First server session](START_HERE.ko.md)

## Completed in this documentation stage

- Reviewed the official simulator, data contract, rules, scoring, and submission process at upstream `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`.
- Preserved the original README separately and prepared this participant project's English/Korean overview.
- Defined Chrome human teleoperation and restricted Codex/GPT automatic collection as two proposed data sources.
- Planned a single-L40S π₀.₅ JAX LoRA baseline and an early offline deployment gate.
- Added first-session instructions, recovery requirements, and session/experiment templates.

## Runtime state

| Item | State | Evidence |
|---|---|---|
| Project Brev/GPU server | Not started | Server is not available yet |
| Official environment smoke on project server | Not run | None |
| Chrome streaming and keyboard | Not implemented or tested | Source review only |
| AI operator bridge and dataset recorder | Not implemented or tested | Design only |
| Own demonstrations / HF dataset | None | No artifact repository yet |
| π₀.₅ converter/config/adapter | Not implemented | Design only |
| Trained policy / HF model | None | No checkpoint |
| Local dressing evaluation | Not run | No measured score |
| Codabench submission | Not made | No submission ID |
| Fresh-server recovery | Not tested | Procedure only |

The empty [experiment index](../../experiments/index.csv) is intentional. Upstream demos and sample data are not runs of this project.

## Next actions

1. Review this public repository and incorporate owner feedback while no GPU server is running.
2. When a clean server becomes available, clone this fork and follow [START_HERE.ko.md](START_HERE.ko.md). Capture hardware/driver/container details before installation changes.
3. Obtain the official smoke pass, then validate a short remote recording and the π₀.₅ offline inference path before expanding collection.

## Open technical questions

| Question | How it will be resolved |
|---|---|
| Does WebRTC preserve PhyRC's keyboard events and app window on this server? | Two-robot movement, numpad mapping, key release, reconnect tests |
| Does the chosen π₀.₅ JAX/LoRA inference fit the submission image and 12 GB policy budget? | Official-image load, offline fixed-input inference, actual memory/latency measurement |
| Can the AI operator generate useful demonstrations from allowed observations? | Short bounded trials, recorded inputs/actions, human review; no success assumption |
| Can the automatic collector reproduce the public dataset contract? | `DatasetWriter` checks, independent transition/episode validation, source audit |
| How fast is clean-server recovery? | Measure download/build/compile/restore/smoke separately on a second clean server |

The automatic-demonstration rules interpretation is documented in [TELEOP.ko.md](TELEOP.ko.md). No organizer approval has been obtained or claimed.

## Update after each real session

Link the session record and experiment run IDs, state what was actually verified, preserve failures, and list the next commands and expected checks. Move an item out of pending only when its evidence exists. Keep README status consistent.
