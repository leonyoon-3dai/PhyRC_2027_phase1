# First Brev implementation session — 2026-10-22

Status: closed at the owner’s request after preserving the quick, verified work. The overall pipeline is not complete. Owner authorized the transition from planning to implementation, installation, collection, training, publication and submission. No server stop or deletion is authorized or performed.

Initial fork: `9d978072c0064f01fe13243def30c2766602e86d`, clean main. Upstream fetch: `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`, unchanged from reviewed snapshot. No upstream simulator, competition rule, asset lock, physics or evaluation code was changed. Implementation commits: `850db17`, `b51ca92`. See [execution lock](../../../config/execution_lock.json).

Hardware measured: L40S 46,068 MiB ×1; Intel Xeon Platinum 8452Y, 12 vCPU; approximately 70 GiB RAM; initial free disk 569 GiB. Ubuntu 22.04.5, driver 580.126.09, Docker 29.1.5 with NVIDIA runtime, overlay2 storage. No local DISPLAY. GPU/Vulkan worked in the real official smoke. The initial base image digest is fixed in Dockerfile; built official image ID `sha256:854d69a337d042827b49cc9b5f4de4f35c3b725534b25fe02f24f1fc7d82dcaa`.

## Verified so far

- `./run.sh doctor`, `build` (164 seconds), `prepare` (8.64 seconds), `smoke` (342.83 seconds) completed. Actual `PHYRC-SMOKE-PASS`: robot motion, gripper toggle, save/load, finite cloth. Smoke reached 12 busy CPU cores and 8,001 MiB device memory; these are whole-host/device measurements.
- Live automatic recorder reuses upstream DatasetWriter. Three actual simulator episodes, 21 steps each, 63 transitions, 3.15 simulation seconds. All five RGB-D sensors recorded at official boundaries; action/state continuity and official PolicyDataset inspection passed. Recorder does not produce a raw archive or claim deferred-export verification.
- Source is `integration_test`, controller is a Codex-authored bounded script. It is neither human teleoperation nor live GPT API collection. The owner explicitly requested proceeding without an extra billed GPT API on this date. These low-quality, non-dressing episodes are approved only for pipeline testing; not general SFT evidence.
- Dataset uploaded and restored from immutable [HF revision 057b59b](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/commit/057b59b1099407b20fe25dafa080285b34ab3aaa); all SHA256 entries matched. Pack/restore into a new local directory also passed. This is not a second-server recovery test.
- Official-image pi0.5 base dependency/offline fixture passed using local params and tokenizer. Existing torch 2.11.0+cu128, torchvision 0.26.0+cu128 and NumPy 2.3.1 were preserved. Additional packages are installed with `--no-deps`, not by installing openpi's training requirements over the official image. JAX 0.5.3: model load 8.57 seconds; first inference including compile 20.87 seconds; next calls 87.6 and 83.8 ms. JAX peak bytes in use 7,117,784,320; process/device totals differ. This synthetic fixture is not a rollout or RTX 3090 measurement.
- JAX LoRA completed 30 optimizer steps, batch 1, 30 processed samples / 63 transitions = 0.476 effective epochs, wall 157.80 seconds including startup/checkpoint writing. The default upstream warmup is 1,000 steps; this is a wiring test and has not established overfitting. Full LoRA architecture/params are retained; no merge/conversion was used.
- Whole params, optimizer/train state, step and normalization were saved in checkpoint folder `29` (train state step 30), with local tokenizer and input manifest. [HF model revision cadbc22](https://huggingface.co/leonayoon/phyrc-2027-phase1-pi05/commit/cadbc22798387e4217497f61a196a801854853b2). Dataloader cursor is not restored; RNG basis is upstream deterministic seed + saved train step. CPU restoration from downloaded HF state subsequently restored all 3,403,421,456 parameter elements, 20 LoRA leaves, optimizer arrays and step 30. This is not an optimizer-step continuation test. The upstream freeze filter leaves vision/projection parameters trainable: 466,957,072 elements were trainable; this is not adapter-only training.
- Learned policy ran in the official environment in a short `--seconds 1` debug run: raw points 0, points/s 0, no_contact, no dressing success. First compilation consumes the debug inference budget, so this is an interface/one-action check, not the 900-second submission test.
- An actual self-contained ZIP was built. A fresh clone unpacked and verified every file, built its Dockerfile, and executed 259 actions / 12.95 simulation seconds. The owner requested stopping the long test and deferring uncertain work: **no completed 900-second check or valid final score exists**. Codabench is inaccessible from both the owner and server; no submission or accepted status exists.

## Failures preserved

WebRTC launcher attempt 1 failed because runpy did not register the teleop module as `__main__`; fixed with `alter_sys=True`. Attempt 2 reached the actual scene and signaling listener but the completed recording could not write its export request into a host-created directory; group write permission and umask were fixed. No remote Chrome keyboard success is claimed. The policy capture metadata lists 25 transitions, but its raw archive is incomplete following the close error. A later official exporter retry refused it. It is preserved as failure evidence and excluded from training; its metadata was not modified to force validity.

Early pi0.5 image attempts missed importlib_resources, protobuf, tqdm and tqdm_loggable. All failures remain in local logs. Isaac fast shutdown initially returned exit code 0 on these exceptions: reports classify them as failures based on missing success artifacts. The launcher now propagates errors and the operation wrapper can require a success marker. Do not infer success from exit status alone.

Chrome viewer is built locally from NVIDIA `create-ov-web-rtc-app@1.14.2` / streaming library 5.17.0. Its generated proprietary-licensed assets remain in ignored output/. Only participant patches and lockfile are committed. Ports 49100/TCP, 47998/UDP, 8210/TCP and 8211/TCP are restricted by the host firewall to the owner's supplied client IP and loopback. Private connection details stay outside public records. Remote browser, full key coverage, disconnect release and complete human export remain pending.

## Evidence and operation commands

[Measured run index](20261022-bootstrap-metrics.json). Local original logs: `output/sessions/20261022T035730Z-bootstrap/`; detailed run metadata, resource samples and logs: `output/runs/<run-id>/`. These local locations require remote preservation before server disposal.

```bash
cd /home/shadeform/workspace/PhyRC_2027_phase1
participant/ops/bootstrap.sh --check
PYTHONPATH=.:src/PhyRC_Sim .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python participant/ops/artifacts.py verify output/collections/20261022T0409Z-integration
```

The implemented bootstrap `--install` rebuilds official build/prepare/smoke after prerequisites; only `--check` plus the individual real build/prepare/smoke were exercised this session. See actual run metadata for commands. No claim of a tested clean-server bootstrap, optimizer-step resume, completed final submission validation or organizer scoring is made.


## Handoff and immutable remote evidence

- [Reviewed session logs, partial evaluation and incomplete teleop failure](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/69234efea487f083f37bd062835ced8f99e6e9f0/sessions/20261022-bootstrap): re-downloaded and every manifest checksum verified.
- [Exact submission ZIP and checksum](https://huggingface.co/leonayoon/phyrc-2027-phase1-pi05/tree/1ff737e560e7f4b2c9a29534ff4f907dc01a6a98/submissions): re-download matches SHA256 `611ec928e35c4c446098de2e645cf4d7e332dc95b74e3fbeb54b14663df64871`, 6,340,722,353 bytes. Full official check is incomplete.
- [Local Git history bundle](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/blob/ae4ec1e514fcd2483c483d90d469106091e4713e/sources/20261022-session.bundle): SHA256 `785932942cfa777be29409354623281e2456af9f34d4923f30f7a288b76e7f46`. Public GitHub `7c4cfd4` had the identical tree to local `5dd4227`; old local commits were preserved rather than reset.
- [Designated-camera video and frames](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/tree/da172805036d5e53daf1834f32baf367820f9183/derived/20261022T0409Z-integration) show the scripted recorder test, not learned dressing.

The 900-second attempt consumed 708.95 wall seconds including a cold cache initialization. Its process exited with code 0 on interrupt, but the missing required success marker made the wrapper fail; the run is explicitly classified as **owner-interrupted**, not passed. Partial trace: 260 samples including the initial state, 259 actions, 12.95 simulated seconds. Warm speed was approximately 1.2–1.3 actions/wall-second. A full run is estimated around three hours, not measured to completion.

The owner requested completing only quick, deterministic tasks and moving slow or uncertain work to the next clean server. [TODO](../TODO.ko.md) and [recovery guide](../RECOVERY.ko.md) define the handoff. Environment reconstruction estimate is 20–40 minutes, conservatively 30–60 minutes, assuming a comparable Brev host with working Docker/NVIDIA and sufficient network. This excludes experiments, browser debugging and site outages. Billing rate and total cost were not measured; compile and optimizer-step timings were not instrumented separately from the full training wall time.

At handoff, Docker had no active project containers, streaming ports had no listeners, and nvidia-smi showed 0 MiB in use. The server was not stopped or deleted. Final source checks preserve the official simulator, competition documents, action interface, asset lock, Dockerfile and run.sh unchanged. Unit tests (5), Python compilation, shell syntax and local documentation links were checked.
