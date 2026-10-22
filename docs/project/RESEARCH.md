# Research notes behind the initial plan

Source review as of **2026-10-22**. This note records useful references and the limits of their reuse. None is an experimental result of this participant project.

## Stretch 4 resources

| Resource | Verified scope | Relevance to this project |
|---|---|---|
| [Hello Robot grasping demo](https://github.com/hello-robot/stretch4_grasping_demo) | Molmo 2 + SAM 2/2.1 + FSM visual servoing for Stretch 4 grasping | Observation-driven behavior design; not a learned dressing action checkpoint |
| [Flying Gripper](https://github.com/hello-robot/stretch4_flying_gripper) and [Kinematics](https://github.com/hello-robot/stretch4_kinematics) | Jacobian-based Cartesian control, FK/IK and tracking | Reference for interpreting robot motion; any port must output official PhyRC actions |
| [Human Perception](https://github.com/hello-robot/stretch4_human_perception) | SAM 3.1 follow-person and fist-bump examples; other perception utilities | Human-relative visual control examples, not two-robot dressing policies |
| [Autodocking](https://github.com/hello-robot/stretch4_docking) | Geometric LiDAR localization, servoing and MPPI | Model-based control reference; its LiDAR pipeline is not a PhyRC input |
| [Stretch 4 MuJoCo](https://github.com/hello-robot/stretch4_mujoco) | Simulation and teleoperation stack | Separate environment; not a substitute for the official PhyRC physics or evaluator |
| [geodex](https://github.com/utiasSTARS/geodex) · [paper](https://arxiv.org/abs/2610.09165) | Motion-planning library with built-in Stretch 3 and Stretch 4 robot models | Planner/model support is confirmed; real Stretch 4 hardware experiments were not verified |
| [Official PhyRC environment](https://github.com/rirolab/PhyRC_2027_Challenge) | Two-robot simulated dressing, collection and evaluation | Primary runtime and data contract for this project |

This review did not verify a public Stretch 4 π₀.₅ checkpoint or a learned two-Stretch-4 dressing expert. This is a search finding, not a claim that no such work exists. Stretch 3 checkpoints and older Stretch research do not establish compatibility with Stretch 4's base, sensors, control stack, or PhyRC action convention.

## Baseline choice

Start from [openpi's π₀.₅ base](https://github.com/Physical-Intelligence/openpi), using JAX LoRA and this environment's own permitted demonstrations. A single central policy will predict the 18 normalized commands. The first image mapping is overview + two wrist cameras, with matching transformations at training and inference.

The critical early experiment is deployment feasibility: dependency compatibility, all-local assets including tokenizer and normalization, and actual memory/latency in the official image. Model padding is an adapter detail, not evidence of task transfer. The pretrained robot's delta-action or gripper conventions must not overwrite PhyRC's velocity/intent convention.

## What carries forward from BEHAVIOR

The [BEHAVIOR 2026 project](https://github.com/leonyoon-3dai/behavior-submission-2026) motivates four operational decisions:

1. Profile CPU, rendering and data transfer before increasing GPU count; prior L40S scaling was limited by the surrounding system.
2. Preserve the original SFT baseline and use matched comparisons before introducing action editing or RL. The prior public pilot did not show an overall improvement from RT.
3. Track samples processed and effective epochs as data grows; a fixed step count alone does not describe training exposure.
4. Publish failed runs and original evidence, and distinguish portal acceptance, local measurement and organizer verification.

[FlashSAC](https://github.com/Holiday-Robot/FlashSAC) and EXPO-style refinement remain later research options. Neither is required to test collection, small-data SFT, offline execution and the first submission. No RL result is claimed here.
