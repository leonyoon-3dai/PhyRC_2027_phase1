# Project status

Updated: **2026-10-22 · KST / UTC+09:00**  
Phase: **implementation and runtime verification on the existing Brev server**

[English overview](../../README.md) · [한국어](../../README.ko.md) · [First server session](START_HERE.ko.md)

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
| Submission | Complete ZIP built; fresh-clone 900-second official self-check running; not submitted |
| Artifact preservation | HF dataset and full model/train state uploaded at immutable revisions; download checksum restoration passed |
| New clean server | Not tested; same-server fresh-directory recovery passed |

## Current commands

```bash
cd /home/shadeform/workspace/PhyRC_2027_phase1
participant/ops/bootstrap.sh --check
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
tail -n 20 output/runs/20261022T0429Z-fresh-official-900/command.log
```

Do not start collection/training/GPU evaluation while the official 900-second check is active. Original logs and unfinished recordings remain on this server; do not delete it. Next gates: finish self-check, recover deferred export, verify Chrome keys, preserve the exact tested ZIP, and guide the owner through Codabench login/upload only when ready.

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
