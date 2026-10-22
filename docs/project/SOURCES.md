# Sources and reviewed revisions

Reviewed on **2026-10-22**. These are source-review references, not evidence that this participant fork has run on a GPU.

## Official PhyRC snapshot

- Repository: [rirolab/PhyRC_2027_Challenge](https://github.com/rirolab/PhyRC_2027_Challenge)
- Reviewed commit: [`4dbbebcf93a06c1bfe12136eadc2e580f30125d6`](https://github.com/rirolab/PhyRC_2027_Challenge/commit/4dbbebcf93a06c1bfe12136eadc2e580f30125d6), 2026-10-21 18:52:54 UTC.
- Original README blob: `db6ddd6e90124b01ce7dc71f7e349f5b5ae9b6cd`; copied to [README.upstream.md](../../README.upstream.md).
- Initial documentation changes do not modify the simulator, competition guides, evaluation, asset lock, or root Dockerfile.

| Reference | What it establishes |
|---|---|
| [SETUP.md](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/docs/competition/SETUP.md) | Official install, local desktop scope, smoke, export completion |
| [DATA.md](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/docs/competition/DATA.md) | Public HDF5, audit separation, alignment and data checks |
| [RULES.md](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/docs/competition/RULES.md) | Permitted observations/actions and prohibited privileged information |
| [POLICY.md](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/docs/competition/POLICY.md) | Adapter, RTX 3090/12 GB policy budget, offline ZIP, dependencies and self-check |
| [EVALUATION.md](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/docs/competition/EVALUATION.md) | Pickup-excluded points/s, failures, raw points and full success |
| [policy_interface.json](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/config/policy_interface.json) | Five cameras, 20/60/240 Hz, `(2,9)` actions and access contract |
| [environment.py](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/src/PhyRC_Sim/Policy/environment.py) | Public `obs`, privileged `info`, exact 0.05 s environment step |
| [training_dataset.py](https://github.com/rirolab/PhyRC_2027_Challenge/blob/4dbbebcf93a06c1bfe12136eadc2e580f30125d6/src/PhyRC_Sim/Policy/training_dataset.py) | DatasetWriter and transition checks that can be reused |

## Model and remote tools

| Reference | Findings and limits |
|---|---|
| [openpi at `215abfb`](https://github.com/Physical-Intelligence/openpi/tree/215abfb217dbac7d5f1273282331b9b1866c0479) | Reviewed for π₀.₅/JAX/LoRA. README estimates >8 GB inference, >22.5 GB LoRA, >70 GB full tuning. These are not PhyRC-specific measurements |
| [openpi model config](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/models/pi0_config.py) | Custom robot adaptation and LoRA freeze settings; no ready PhyRC expert |
| [openpi tokenizer](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/models/tokenizer.py) | Tokenizer download must be eliminated from the offline evaluation path |
| [openpi checkpoints](https://github.com/Physical-Intelligence/openpi/blob/215abfb217dbac7d5f1273282331b9b1866c0479/src/openpi/training/checkpoints.py) | Inference params and train state; do not assume dataloader-cursor recovery |
| [Isaac Sim 6.0.1 livestream clients](https://docs.isaacsim.omniverse.nvidia.com/6.0.1/installation/manual_livestream_clients.html) | Chromium viewer exists; PhyRC integration and keyboard behavior still need testing |
| [Codex MCP](https://developers.openai.com/codex/mcp/) | Tools can connect a local Codex operator to a restricted observation/action service |
| [OpenAI image inputs](https://developers.openai.com/api/docs/guides/images-vision) and [function calling](https://developers.openai.com/api/docs/guides/function-calling) | Image-driven tool execution is available; this does not establish robotic precision or dressing success |

## Competition schedule

The [challenge website](https://emprise.cs.cornell.edu/phyrc/challenge-2027/) and [Codabench](https://www.codabench.org/competitions/18366/) are authoritative for current announcements. Reviewed dates: Nov 17, Dec 1/4/8/12 checkpoints; Dec 15 final, all 23:59 AoE (UTC−12). Nov 17 23:59 AoE corresponds to Nov 18 20:59 KST; the participant's internal target is earlier, Nov 16 KST. Recheck before submission.

## Updating upstream

Keep `origin` for this participant fork and `upstream` for RIRO Lab. Before a sync, inspect changes to rules, interface, Dockerfile, assets and scoring; record the new upstream commit and rerun affected checks. Preserve the reviewed source revision for every historical experiment. Refresh the preserved README deliberately rather than silently replacing the source snapshot.

For research references, see [RESEARCH.md](RESEARCH.md). For implementation status, use [STATUS.md](STATUS.md), not the presence of a source link.
