# Clean-server session / 클린 서버 세션

| Item | Value |
|---|---|
| Session ID | `20261023-clean-start` |
| State | interrupted at owner request; no full 900-second pass |
| D0 / start | 2026-10-23 / 04:04 UTC (13:04 KST) |
| Source | `5a2ab4ec2b47d907198a171da35c17364e8a185c` (initially clean main) |
| Official upstream | `4dbbebcf93a06c1bfe12136eadc2e580f30125d6` |
| Host | Ubuntu 22.04.5, L40S 46068 MiB, driver 580.126.09, 12 vCPU, ~70 GiB RAM |
| Storage / Docker | 569 GiB initially free / Docker 29.1.5 |

## Final state after owner-requested stop

Tests stopped at 05:12:52–05:12:54 UTC (14:12 KST). Full-check snapshot: 1460 applied actions/73.0 simulation seconds; run wall 1814.08 s. No valid final JSON/score or full 900-second pass. Process signal shutdown returned 0, but `run.py` verification returncode is 1 because the success marker is absent. Do not infer success from child exit alone. GPU processes and viewer server ended; GPU 0 MiB checked. Server power/deletion not performed.

Completed: clean-server pinned recovery, official smoke, bounded offline policy, owner-reported Chrome keyboard/movement, compact control UI, independently verified format-only human motion clips and HF round-trip hashes. Deferred: actual task demonstrations, new SFT, full export, full self-check, policy-alone 12GB/RTX 3090 proof and Codabench submission.

Current scope and detailed next-server instructions are in both READMEs and STATUS. The working notes below record intermediate states chronologically; any earlier “running/pending” entry is superseded by this final state.

## Goal and verified work

Restore pinned artifacts, pass official smoke, rerun the existing policy briefly, then obtain one genuine human recording. GPU work runs sequentially.

- `participant/ops/bootstrap.sh --check`: passed.
- `participant/ops/bootstrap.sh --install`: build passed in 218.53 s; prepare passed in 9.14 s; smoke passed in 367.80 s with `PHYRC-SMOKE-PASS` and exit 0. Bootstrap run prefix: `20261023T040614Z-bootstrap`; official image is digest-pinned, unchanged.
- Dataset revision `057b59b1099407b20fe25dafa080285b34ab3aaa`: downloaded and `participant/ops/artifacts.py verify` passed.
- Model/train-state revision `cadbc22798387e4217497f61a196a801854853b2`: downloaded and artifact verification passed. This does not yet verify state loading or optimizer continuation on this server.
- Release ZIP revision `1ff737e560e7f4b2c9a29534ff4f907dc01a6a98`: downloaded; SHA256 `611ec928e35c4c446098de2e645cf4d7e332dc95b74e3fbeb54b14663df64871` passed. Extracted package manifest (98 files) also passed using its filename-to-SHA256 schema; the generic artifact verifier expects a different schema and was not applicable.
- `PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v`: 5 tests passed.
- `scripts/inspect_policy_dataset.py` on recovered HDF5: 63 samples, expected public observation shapes and 18D stored actions. These remain scripted integration fixtures, not human demonstrations.
- `python3 participant/streaming/prepare_viewer.py`: viewer build completed. Client-restricted IPv4 firewall and viewer HTTP server are ready; local HTTP response is 200. Browser connection and keyboard operation are unverified.

## Evidence and recovery

Local evidence: `output/sessions/20261023-clean-start/`; bootstrap command logs, wall times and resource sampling: `output/runs/20261023T040614Z-bootstrap-*`. Host manifest: `host.json`. Individual download wall durations were not instrumented and are not reported as measured durations.

Recovered artifacts: `output/recovered-data`, `output/recovered-model`, `output/recovered-release`. Original remote revisions remain immutable. E0 evidence uploaded and downloaded again at immutable revision `2234dfd306df355bf8a9f879b6b3aaae4c3b56f8`; artifact verification passed. Credentials and connection addresses must remain outside public reports.

Additive policy runtime image built in 68.40 s: `phyrc-recovered:20261023`, image SHA256 `9c94a27a0ec706d52b4aab5f75fc593e644323ba68c80f371180d89b01fba242`. Package source is historical `b51ca92b970c796ababa3c34268af2fb30c3536a`; openpi `215abfb217dbac7d5f1273282331b9b1866c0479`. Simulator source remains the main commit above. No simulator or policy code was modified.

## Remaining work

1. Wait for official build/prepare/smoke and inspect actual exit status and `PHYRC-SMOKE-PASS`.
2. Build the additive runtime from `output/recovered-release/bundle`, verify the extracted manifest, and run a bounded existing-policy evaluation in the official environment. Record the historical bundle source separately from current simulator source; do not run the historical full self-check helper implicitly.
3. Obtain current MacBook public IPv4, restrict the documented streaming ports, serve the built viewer, and launch the recording stream after evaluation exits.
4. Ask the human operator to test both robots, grippers, alternate numpad mapping, focus/disconnect key release, then ESC and wait for READY/complete export. No human-data training before valid collection.

No new policy performance, human data, full 900-second self-check or submission is claimed.

## Live viewer feedback update

Requested by owner: show live input keys/feedback. `participant/streaming/keyboard.js` now shows held keys, server-receipt status and HTTP round-trip time, focus/release notices, gripper-toggle requests, ESC/export reminder and a collapsible complete two-robot Mac key table. Syntax and viewer build passed. Headless Chromium exercised help visibility, held-key display, transmission, Mac number-row mapping and blur release with a mocked endpoint; no automated commands were sent to the simulator. Actual Mac Chrome/WebRTC operation remains pending. Server receipt is not confirmation of physical motion/gripper state.

## E0 bounded policy rerun

`PHYRC_IMAGE=phyrc-recovered:20261023 .venv/bin/python participant/ops/run.py --id 20261023-clean-start-policy-debug --success-marker 'FINAL SCORE:' -- ./run.sh python /scripts/evaluate_policy.py --policy /output/recovered-release/bundle/policy.py --seeds 42 --seconds 1 --output /output/evaluation/20261023-clean-start-policy-debug`

Exit 0, wall 91.11 s including startup/load/compile; one applied action (0.05 simulated seconds), raw points 0, aggregate 0 points/s, episode status `no_contact` with undefined contact-based episode rate, no dressing success. The cold first policy call consumed the one-second debug budget. This verifies offline load/interface only, not meaningful control, a 900-second check, or a performance gain. See original results under `output/evaluation/20261023-clean-start-policy-debug`.

Human streaming launched after policy evaluation exited; actual browser input and valid human export remain pending.

## Remote preservation and human handoff

[E0 evidence snapshot](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/2234dfd306df355bf8a9f879b6b3aaae4c3b56f8/sessions/20261023-clean-start-e0): 36 files including official run metadata/logs/resources, evaluation JSON, recovered-artifact verification and viewer checks. Re-download to `output/remote-evidence-check` and `artifacts.py verify` passed. Streaming connection addresses and live streaming logs were excluded. The snapshot captures the report at upload time; subsequent handoff notes are local.

The live stream reached `WebRTC enabled`, `keyboard bridge ready` and initial F1 save. Viewer listens on 8210, keyboard bridge on 8211, signaling on 49100. Human operator has been given the private connection URL and test instructions. Actual client video/keyboard validation and human READY/export remain pending.

## Operator feedback and compact control panel

Owner reported Chrome keyboard teleoperation works very well. This is user-reported browser keyboard success; complete two-robot release/reconnect checklist and human READY/export are still pending. At owner request, moved the viewer panel to bottom-right (12 px inset), reduced font from 14 to 13 px, used a compact 340 px layout and made the action/key table visible by default. Kept live held keys and input acknowledgment/latency; shortened explanatory text. Viewer rebuilt successfully. Headless Chromium with a mocked endpoint checked bottom-right bounds, 13 px font, visible mappings, key transmission, Mac number mapping and blur release. Existing live simulator and recording continue; refreshing the viewer loads the new assets.

Owner additionally confirmed robot movement works. Live capture remains in progress; no READY/export completion is inferred from movement.

## Human ESC capture confirmation

After the owner pressed ESC, the official recorder printed `CAPTURE SAVED`: 2419 transitions, 1172.859 s collection wall time, complete=True. `capture.json` is `status=awaiting_export`, `complete=true`; deferred export has started and rendered initial observations. This is a completed raw human capture, not yet READY or verified HDF5. Source is owner human keyboard operation for interface testing; task-success/useful SFT data quality is not established. Do not include automatically in SFT. Next: wait for `[Dataset export] READY`, then inspect/check the final dataset and preserve it remotely.

## Owner scope change: format and submission validation only

Owner is not ready to collect garment pickup/dressing demonstrations. No task demonstration collection, new SFT, or task-performance comparison is authorized in this session. Scope is a minimal motion sample, data format verification, existing package full self-check, and submission-route verification.

The full deferred export was intentionally interrupted with SIGINT after a rendered prefix of 364 transitions. Original raw capture stays complete and unchanged; the full exported dataset stays incomplete and is not labeled READY. `participant/ops/motion_sample.py` creates a separate derived dataset from fully written prefix rows, verifies public states against checksummed original archive chunks and actions against the original event journal, and selects only nonzero movement commands with measured public joint/base change. It preserves contiguous transitions within each clip and marks clip boundaries as truncations.

Result: three clips `[206,208)`, `[225,231)`, `[295,299)` from original `demo_0`, 12 transitions, 0.6 simulated seconds. Selection is from the already rendered prefix, not an exhaustive extract of all 314 movement-command transitions in the 2419-step capture. Labels: source `human`, purpose `teleoperation_format_test`, review `format_only_not_for_sft`, success unknown. Five-camera RGB-D validity, original public-state/action equality, obs/next_obs continuity, 0.05 s timing and official PolicyDataset load passed.

[Immutable sample](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/c31241f626c4cbf02c2bd69a10f70a3841fa58a3/samples/20261023-human-motion-format-test) downloaded again and all manifest hashes verified. Local data/report: `output/human-motion-sample/20261023-format-test/`.

Full 900-second self-check started as run `20261023-submission900`, fresh clone `output/selfcheck/20261023-pinned-release900`. This deliberately reproduces the existing release on helper-selected historical simulator commit `9d978072c0064f01fe13243def30c2766602e86d`; it does not test current main. Package source `b51ca92b970c796ababa3c34268af2fb30c3536a`, ZIP SHA256 `611ec928e35c4c446098de2e645cf4d7e332dc95b74e3fbeb54b14663df64871`. Fresh ZIP extraction hashes passed; image build and scene prepare completed. Full evaluation is running, not passed.

Codabench competition URL failed in web access and timed out in server HTTPS requests (www and apex host). Actual submission/acceptance is not established. Owner was asked to check Mac Chrome access while local verification continues. No credentials requested in chat.

## Runtime speed and competition timing audit

Rechecked official upstream HEAD `4dbbebcf93a06c1bfe12136eadc2e580f30125d6` and current official POLICY/RULES/interface on October 23. Current main/fresh-checkout `environment.py`, `sensors.py`, and `evaluate_policy.py` SHA256 are identical. The official interface uses 20 Hz policy, 60 Hz control and 240 Hz physics in simulation time; no real-time 20 FPS minimum was found in the reviewed official guides. Each step advances 0.05 simulated seconds, with 12 physics steps, five synchronous RGB-D cameras and four rendering subframes. The runner's 900 s budget adds policy-call wall duration and simulated duration; environment-step wall duration is outside that accumulator. No simulator/evaluator changes made.

A 10 s, 20 Hz py-spy sampling snapshot of the active evaluation main thread (199 samples) found approximately 41.2% official evaluation/contact measurement, 39.2% physics/control, 16.1% camera rendering, 3.5% policy inference. These are short-window sampled stack shares, not precise per-component wall timers or a hardware benchmark. Process continued running. Evidence: `output/sessions/20261023-clean-start/runtime-profile{,-summary.json,.log}` (raw stack file uses `.txt`). Recent total GPU residency ~17446 MiB includes simulator + policy; it does not establish policy-alone compliance with the hard 12 GB cap or RTX 3090 compatibility. Full-check exit/final valid JSON remain pending.

Measured episode average at 19.85 simulated seconds: 379.6 s wall, equivalent to ~19.1 wall minutes per simulated minute including first policy compile. Do not interpret this as actual video FPS or as exact 900-budget progress. The earlier ~3-hour total estimate is historical, not a measured ETA for this server. Codabench follow-up is deferred at owner's request.

## Hardware pressure check

Around 05:03 UTC: L40S ~39% utilization, 17446/46068 MiB resident, 38 C, P0/2520 MHz, no active clock slowdown reason. RAM ~49 GiB available; no active swapping, disk I/O wait or CPU steal in sampled vmstat. Xeon Platinum 8452Y, all 12 vCPUs allowed; process used ~2.19 cores over a 2 s sample, busiest thread ~64%. Container CPU/memory limits are unlimited, throttling/OOM counters zero. These observations do not indicate GPU/RAM capacity shortage, thermal throttling or container quota as the primary explanation. Sequential CPU evaluation/control and synchronization remain likely contributors, supported by the short stack profile, without proving a pure CPU hardware bottleneck. No hardware or simulator setting changed. RTX 3090 throughput remains unmeasured. Evidence: `hardware-diagnostics.json`.

## Exact interrupted-check command and next action

Executed from the repository root:

```bash
.venv/bin/python participant/ops/run.py --id 20261023-submission900 \
  --success-marker 'FINAL SCORE:' -- participant/ops/selfcheck.sh \
  output/recovered-release/submissions/20261022T0429Z-pi05-release.zip \
  20261023-pinned-release900 900
```

The helper deliberately selected simulator `9d978072c0064f01fe13243def30c2766602e86d`. Package source is `b51ca92b970c796ababa3c34268af2fb30c3536a`; openpi `215abfb217dbac7d5f1273282331b9b1866c0479`; ZIP SHA256 `611ec928e35c4c446098de2e645cf4d7e332dc95b74e3fbeb54b14663df64871`. Fresh runtime image: `sha256:cd2c3cb8760770bf1bf2d355442037e4c5271a4907f222795fc4d2171e04fd22`.

Do not automatically rerun this long command. On the next server, first inspect hardware, restore and smoke, then run a short diagnostic. A fixed-step warm component-timing helper does not yet exist; implement it as clearly separate diagnostic code before claiming timing coverage. Likewise explicit source-selection support in the historical self-check helper remains pending. Neither pending helper is described as already implemented.

Optimization review: avoid repeating full tests during development; reuse compatible compile/shader caches; benchmark thread counts and affinity/NUMA under identical fixed-step conditions; check host CPU performance settings if controllable. No candidate was applied/proven. More GPU/RAM/cores is not currently justified by measured pressure. Reducing model inference time can increase the number of expensive environment steps within the 900 budget, so it need not shorten wall time. Official physics/evaluator/geometry/camera alignment must remain unchanged. Upstream evaluator-copy/contact optimizations require organizer adoption and parity verification, not unilateral local self-check changes.

## Final remote preservation

- [Final interrupted-run/evidence snapshot](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/93753f568811c5cfcd0235f5d8cb9940c5ce6a23/sessions/20261023-final-evidence), revision `93753f568811c5cfcd0235f5d8cb9940c5ce6a23`: run metadata/resources/logs, partial evaluation trace, profiling/hardware diagnostics, source snapshot and stop report. Re-download and artifact-manifest verification passed. Source snapshot is the prepublication report state; final GitHub docs add these remote links and final restore outcomes.
- [Human source archive](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/32fc6d21c5d358caefd17c6aadfc4f25a843e368/captures/20261023-human-source), revision `32fc6d21c5d358caefd17c6aadfc4f25a843e368`: complete raw capture plus incomplete rendered prefix, archived as `20261023-human-source.tar.gz`. SHA256 `94dfa0238bfab003c255ea6d48f64e7b4b15e9e0e92293e5a360210514a47bd1`.
- Remote raw copy removes `STRETCH4_STREAM_HOST` from manifest metadata only. Original chunk/scene/event bytes and checksums are unchanged. `redaction.json` records original manifest SHA256 `8fb00dca88855db61fcb166e9c669677cec9ebbced328a148abaf426dc097a37`. The earlier derived-sample provenance refers to that original manifest; the preserved redacted manifest has a different hash by design. Original unredacted copy remains local, not publicly uploaded.
- `raw/` and audit contain privileged replay/evaluation data, never model inputs. No full sensor export or dressing-success evidence is inferred from this preservation.

Exact next-server source restore (after bootstrap; destination must not exist):

```bash
hf download leonayoon/phyrc-2027-phase1-data --type dataset \
  --revision 32fc6d21c5d358caefd17c6aadfc4f25a843e368 \
  --include 'captures/20261023-human-source/*' --local-dir output/recovered-human-source
.venv/bin/python participant/ops/artifacts.py verify \
  output/recovered-human-source/captures/20261023-human-source
.venv/bin/python participant/ops/artifacts.py restore output/restored-human-source \
  --archive output/recovered-human-source/captures/20261023-human-source/20261023-human-source.tar.gz
# Optional CPU-only re-derivation of the format sample, not model training:
.venv/bin/python participant/ops/motion_sample.py \
  --prefix output/restored-human-source/interrupted-rendered-prefix \
  --recording output/restored-human-source/raw --output output/rederived-human-format-sample
```

A historical package reproduction remains available through RECOVERY/selfcheck, but another long run is not automatically authorized by this handoff. First implement the separate fixed-step diagnostic and review wall-time budget with the owner. Server shutdown/deletion is deferred until the owner reviews the records.

### Final recovery verification outcome

The human source archive was re-downloaded from immutable HF revision `32fc6d21c5d358caefd17c6aadfc4f25a843e368`; outer artifact verification passed, then `artifacts.py restore` successfully extracted into a new directory and verified the inner manifest. CPU re-derivation produced the same three clips/12 transitions. All **171 public HDF5 datasets** (images, depth, state, action and termination arrays) were exactly equal to the previously verified sample. Metadata provenance differs because the raw manifest intentionally omits the private streaming host. This is a same-server remote round-trip recovery check, not another clean-server GPU reproduction.

Checks at publication: 5 existing CPU unit tests passed; JS syntax, Python compilation, whitespace and modified-document local links passed. Earlier Chromium checks verified the control overlay and key behavior using a mocked endpoint; owner separately confirmed actual Chrome movement. No GPU speed optimization was applied. Source addresses/tokens were excluded from publication.

After evidence preservation: no project GPU/container processes or streaming/viewer listeners remain; GPU 0 MiB. The physical/cloud server remains powered on for owner review. No server power/deletion action was executed.

[Remote download/restore/parity receipts](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/430d6dfa7f35802ad12be6d860d394957b486076/sessions/20261023-preservation-receipts), immutable revision `430d6dfa7f35802ad12be6d860d394957b486076`, records the outer/inner manifest verification and 171-dataset numerical parity.
