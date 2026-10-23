# Working in this participant fork

This is Leonard Yoon's public PhyRC 2027 Phase 1 project. Read `README.md`, `docs/project/STATUS.md`, `docs/project/START_HERE.ko.md`, `docs/project/ENGINEERING_SPRINT.ko.md`, and `docs/project/EVIDENCE_MAP.md` before working. The 2026-10-23 update is documentation-only. The owner will review the plan before starting the next clean server; D0 is the actual session start, not an assumed calendar date. No new GPU execution is claimed by this update. Inspect the actual server and checkout before resuming. Run collection, training and GPU evaluation sequentially. Do not provision additional paid compute or delete/stop a server without an explicit request. Do not use extra billed GPT APIs without a separate request.

## Scope and truthfulness

- Keep the official simulator, physics, geometry, action limits, reset rules, and evaluation unchanged for the initial experiment. Add participant code in clearly named paths when implementation begins.
- Distinguish planned, implemented, runtime-verified, submitted/accepted, and organizer-scored. Do not mark a milestone complete without linked evidence.
- Do not present upstream demos, generic base checkpoints, or other robots' results as this project's results.
- Preserve `README.upstream.md` as the exact reviewed upstream README. Record any later refresh, upstream commit, and old snapshot history.
- Preserve `LICENSE`, `NOTICE`, and `THIRD_PARTY.md`. New documentation describes the participant work and credits upstream material.
- Keep the main README concise and accessible to external researchers and interviewers. Keep private recruiting logistics out of public project documents. Update English and Korean status together. Put operational detail under `docs/project/`.

## Active engineering sprint

- Follow `START_HERE.ko.md` for the current entry point and `ENGINEERING_SPRINT.ko.md` for the October 23–28 evidence sprint. Freeze evidence on October 28; if the server opens later, reduce scope without inventing completion. `RGBD_TWO_WEEK_PLAN.ko.md` and `PLAN.ko.md` are historical plans.
- First obtain a valid human-recorded episode after restore/smoke and a short existing-policy rerun. The 3 scripted episodes / 63 transitions are integration fixtures, not human demonstrations.
- Prioritize E0 clean-server recovery, E1 genuine human collection, E2 synchronized QC and small camera-local RGB-D diagnostics, and E3 human-data SFT with short matched three-seed evaluation. Keep SAM 2 and FK/IK optional. Counts and dates remain targets until evidence exists.
- Before human SFT, define a genuine-human review state in the loader/manifest and a short-run LR schedule. Start from pi05_base with train-only normalization, preserving the old integration checkpoint. Do not relabel human demonstrations as approved_pipeline_test.
- Record the source/base commit selected for each new self-check package. The historical helper pins 9d97807; do not silently describe it as testing current main. The full 900-second check follows the short evidence loop.
- Reuse the official recorder and existing participant helpers. Inspect implementation before replacing tools described as pending runtime validation.
- The current policy consumes three RGB views and a 32D robot state, returning 18D actions. Depth analysis is initially offline and does not by itself establish a policy-performance gain.
- Keep SAM 2 analysis separate from the official simulator environment. Do not treat camera audit matrices or reference overview pose as permitted per-episode world calibration.
- Historical recovery commits identify earlier experiments. Read the latest handoff first; use a separate worktree for an exact historical reproduction when needed.

## Public observation and action boundary

Read `docs/competition/RULES.md`, `POLICY.md`, and `config/policy_interface.json` at the selected revision before collection or training.

- Every automated operator/controller and learned model uses only the designated cameras and public robot observations. A human may use the official teleop interface, while training images remain the designated cameras. Never pass a whole Gym `info` dictionary, environment handle, raw archive, audit file, spawn seed, ground-truth geometry, or freely moved viewport to a policy or AI operator.
- Use the official normalized `float32 (2,9)` action. Gripper `0` means preserve intent. Record observations, applied actions, and next observations at the same 20 Hz simulation boundaries.
- Scores and success labels are for selection, reporting, or permitted training rewards, not policy observations or privileged action-label generation.
- GPT-driven collection from allowed observations is an interpretation of the rules; do not describe it as explicit organizer approval. Record controller source, model identifier, prompts, observation selection, action parameters, and corrections.
- Separate implementation/debugging access from the collection-time AI operator. Its tools should expose only the permitted observation/action boundary.

## Evidence and operations

- Use the session and experiment templates. Assign a unique UTC run ID; include KST display times in human reports if useful.
- Save code commit, dirty state, upstream revision, image digest, asset lock, dependency versions, dataset/model revisions, normalization, command, seeds, and hardware for each run.
- Keep seeds and evaluation metadata outside model inputs. Split datasets by episode and collection layout/source groups, not adjacent frames.
- Measure CPU, RAM, VRAM, storage I/O, simulation rate, inference latency, compile time, and warm training step time before scaling.
- Keep the SFT-only baseline. Compare changes on matched evaluation settings and include failures in averages.
- Separate wall time/cost, simulation time, official score time, and policy inference budget. Acceptance is not a performance result.
- Finish export and verify remote artifact hashes before a disposable server is deleted. Save full inference params/assets and optimizer/train state for learning resume. Do not promise dataloader-cursor or bitwise physics restoration without an explicit mechanism and verification.
- GitHub holds source and small reports; HF holds large artifacts with immutable revisions and checksums. No fabricated HF links or results. Preserve original evidence when revising reports.

## Submission and validation

- Use the official image. Participant Dockerfiles only add packages; do not replace existing torch/torchvision or other pinned packages.
- Validate the actual π₀.₅ path early: local tokenizer/config/norm stats, no evaluation downloads, official adapter, policy memory within 12 GB, and the full official self-check.
- Disable automatic JAX allocation as needed and measure actual residency; an L40S run is not proof of RTX 3090 compatibility.
- If converting LoRA, explicitly merge all learned parameters as required and compare output parity; generic conversion success alone is insufficient.
- Documentation-only changes need source/link/format checks, not invented GPU tests. Report precisely which checks ran.

## Public repository hygiene

Never commit credentials, `.env` files, SSH keys, auth caches, cloud access URLs, or unreviewed private logs. Public research outputs remain the default. Keep artifacts' source/license provenance; asset and pretrained-model terms are component-specific.

At session end update `docs/project/STATUS.md` with evidence, blockers, and the next concrete commands. Do not replace a real command with a hypothetical script name. Participant bootstrap, artifact, collection, training, streaming, and packaging code exists. Check STATUS and the recorded session for its actual runtime-verified scope; Chrome human collection, separate-server recovery, and full submission validation remain pending at this documentation update.

