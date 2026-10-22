# First Brev implementation session — 2026-10-22

Status: in progress. Owner authorized the transition from planning to implementation, installation, collection, training, publication and submission. No server stop or deletion is authorized or performed.

Initial fork: `9d978072c0064f01fe13243def30c2766602e86d`, clean main. Upstream fetch: `4dbbebcf93a06c1bfe12136eadc2e580f30125d6`, unchanged from reviewed snapshot. No upstream simulator, competition rule, asset lock, physics or evaluation code was changed. Implementation commits: `850db17`, `b51ca92`. See [execution lock](../../../config/execution_lock.json).

Hardware measured: L40S 46,068 MiB ×1; Intel Xeon Platinum 8452Y, 12 vCPU; approximately 70 GiB RAM; initial free disk 569 GiB. Ubuntu 22.04.5, driver 580.126.09, Docker 29.1.5 with NVIDIA runtime, overlay2 storage. No local DISPLAY. GPU/Vulkan worked in the real official smoke. The initial base image digest is fixed in Dockerfile; built official image ID `sha256:854d69a337d042827b49cc9b5f4de4f35c3b725534b25fe02f24f1fc7d82dcaa`.

## Verified so far

- `./run.sh doctor`, `build` (164 seconds), `prepare` (8.64 seconds), `smoke` (342.83 seconds) completed. Actual `PHYRC-SMOKE-PASS`: robot motion, gripper toggle, save/load, finite cloth. Smoke reached 12 busy CPU cores and 8,001 MiB device memory; these are whole-host/device measurements.
- Live automatic recorder reuses upstream DatasetWriter. Three actual simulator episodes, 21 steps each, 63 transitions, 3.15 simulation seconds. All five RGB-D sensors recorded at official boundaries; action/state continuity and official PolicyDataset inspection passed. Recorder does not produce a raw archive or claim deferred-export verification.
- Source is `integration_test`, controller is a Codex-authored bounded script. It is neither human teleoperation nor live GPT API collection. The owner explicitly requested proceeding without an extra billed GPT API on this date. These low-quality, non-dressing episodes are approved only for pipeline testing; not general SFT evidence.
- Dataset uploaded and restored from immutable [HF revision 057b59b](https://huggingface.co/datasets/leonayoon/phyrc-2027-phase1-data/commit/057b59b1099407b20fe25dafa080285b34ab3aaa); all SHA256 entries matched. Pack/restore into a new local directory also passed. This is not a second-server recovery test.
- Official-image pi0.5 base dependency/offline fixture passed using local params and tokenizer. Existing torch 2.11.0+cu128, torchvision 0.26.0+cu128 and NumPy 2.3.1 were preserved. Additional packages are installed with `--no-deps`, not by installing openpi's training requirements over the official image. JAX 0.5.3: model load 8.57 seconds; first inference including compile 20.87 seconds; next calls 87.6 and 83.8 ms. JAX peak bytes in use 7,117,784,320; process/device totals differ. This synthetic fixture is not a rollout or RTX 3090 measurement.
- JAX LoRA completed 30 optimizer steps, batch 1, 30 processed samples / 63 transitions = 0.476 effective epochs, wall 157.80 seconds including startup/checkpoint writing. The default upstream warmup is 1,000 steps; this is a wiring test and has not established overfitting. Full LoRA architecture/params are retained; no merge/conversion was used.
- Whole params, optimizer/train state, step and normalization were saved in checkpoint folder `29` (train state step 30), with local tokenizer and input manifest. [HF model revision cadbc22](https://huggingface.co/leonayoon/phyrc-2027-phase1-pi05/commit/cadbc22798387e4217497f61a196a801854853b2). Dataloader cursor is not restored; RNG basis is upstream deterministic seed + saved train step.
- Learned policy ran in the official environment in a short `--seconds 1` debug run: raw points 0, points/s 0, no_contact, no dressing success. First compilation consumes the debug inference budget, so this is an interface/one-action check, not the 900-second submission test.
- An actual self-contained ZIP was built. A fresh clone / full 900-second official test is in progress; no Codabench submission or accepted status exists yet.

## Failures preserved

WebRTC launcher attempt 1 failed because runpy did not register the teleop module as `__main__`; fixed with `alter_sys=True`. Attempt 2 reached the actual scene and signaling listener but the completed recording could not write its export request into a host-created directory; group write permission and umask were fixed. No remote Chrome keyboard success is claimed. A complete 25-transition raw capture remains awaiting export and must be recovered explicitly.

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

The implemented bootstrap `--install` rebuilds official build/prepare/smoke after prerequisites; only `--check` plus the individual real build/prepare/smoke were exercised this session. See actual run metadata for commands. No claim of a tested clean-server bootstrap, full training resume, final submission validation or organizer scoring is made.
