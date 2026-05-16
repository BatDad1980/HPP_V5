# HPP V5 Buyer Evidence Packet Index

## Purpose

This index gives a serious reviewer the fastest path through the HPP V5 evidence without reading every lab note first.

HPP V5 should be reviewed as an early post-LLM architecture prototype with measured mechanism evidence, not as a completed replacement for large language models.

## One-Line Position

HPP V5 explores whether useful adaptive behavior can be grown through shared recurrent depth, developmental staging, Habit-14 stabilization, context-aware memory, and stress-aware routing on modest local hardware.

## Best First Reading Order

1. `docs/central-hypothesis.md`
2. `docs/evidence-ladder.md`
3. `docs/recurrent-vs-unique-stack-scaling-summary.md`
4. `docs/recurrent-gpu-scaling-summary.md`
5. `docs/habit-memory-summary.md`
6. `docs/changed-context-habit-memory-summary.md`
7. `docs/developmental-curriculum-sweep-summary.md`
8. `docs/stress-routing-sweep-summary.md`
9. `docs/inferred-stress-routing-profile-summary.md`
10. `docs/tapout-boundary-sweep-summary.md`
11. `docs/named-baseline-comparison-summary.md`
12. `docs/soft-stop-guardian-principle.md`
13. `docs/grow-first-freeze-later.md`

## Strongest Current Proof Points

### Shared Depth Delays The Memory Wall

Artifact:

- `docs/recurrent-vs-unique-stack-scaling-summary.md`

Result:

- At dimension `4,096`, shared recurrence used `100,687,872` parameters and `393.469 MB` peak CUDA memory.
- At dimension `4,096`, the equivalent 14-layer unique stack used `1,409,630,208` parameters and `5,386.688 MB` peak CUDA memory.
- At dimension `8,192`, shared recurrence completed while the equivalent unique stack hit CUDA OOM.

Buyer-safe claim:

Shared recurrent depth can preserve effective depth while reducing stored parameter growth and delaying the GPU memory wall.

### Billion-Parameter Recurrent Inference On Field Hardware

Artifact:

- `docs/recurrent-gpu-scaling-summary.md`

Result:

- RTX 4050 laptop GPU
- Largest completed shared recurrent probe: `2,271,332,352` FP32 parameters
- `14` recurrent passes
- Peak allocated CUDA memory: `8,674.609 MB`
- Practical faster point: about `1.416B` parameters at `457.0935 ms`

Buyer-safe claim:

The field laptop can execute billion-parameter-scale shared recurrent inference. This is inference-only architecture telemetry, not training or model-quality evidence.

### Repeated Loops Stabilize Noisy State

Artifact:

- `docs/iterative-stability-summary.md`

Result:

- Recurrent final MSE: `0.002078`
- One-pass final MSE: `0.361852`
- One-pass final error was `174.135x` higher

Buyer-safe claim:

When the task requires iterative stabilization, repeated shared loops can strongly reduce noisy-state error without adding stored parameters.

### Habit-14 Creates Protected Recall

Artifact:

- `docs/habit-memory-summary.md`

Result:

- Before 14 exposures: no protection
- At 14 exposures: protected noisy recall improved `12.73755424x`
- At 21 exposures: protected noisy recall improved `89.63142983x`

Buyer-safe claim:

Repeated exposure can create a protected pathway in a toy mechanism harness.

### Context-Aware Memory Avoids Rigid Lock

Artifact:

- `docs/changed-context-habit-memory-summary.md`

Result:

- At 21 exposures, shifted-context adaptive recall improved over noisy baseline by `47.17974545x`.
- At 21 exposures, shifted-context adaptive recall improved over rigid lock by `17.01315969x`.

Buyer-safe claim:

HPP-style protection can preserve a core signal without freezing every surrounding context.

### Developmental Curriculum Beats Flat Prototype

Artifact:

- `docs/developmental-curriculum-sweep-summary.md`

Result:

- Ten-seed HPP versus context-aware flat clean mean: `2.20191598x`
- Ten-seed HPP versus context-aware flat shifted mean: `2.03043896x`
- Habit-14 lock rate: `10/10`

Buyer-safe claim:

In the first synthetic curriculum task, staged developmental exposure outperformed flat prototype learning under clean and shifted-context probes.

### Stress Routing Beats Fixed Modes

Artifact:

- `docs/stress-routing-sweep-summary.md`

Result:

- Router versus nurture under stress mean: `6.80870099x`
- Router versus sentinel under calm mean: `2.61898962x`
- Router failure rate mean: `0.0`

Buyer-safe claim:

State-aware routing can outperform fixed response modes in a toy Nurture/Sentinel harness.

### Profile-Aware Tap-Out Thresholds

Artifacts:

- `docs/inferred-stress-routing-profile-summary.md`
- `docs/tapout-boundary-sweep-summary.md`

Result:

- Low-tolerance and standard profiles first tapped out at extreme-noise scale `2.0`.
- High-intensity profile first tapped out at extreme-noise scale `2.8`.
- High-intensity profile tolerated a higher unfamiliar-noise band before conservative fallback engaged.

Buyer-safe claim:

HPP can model profile-dependent redlines: the same noise does not mean the same thing for every system.

### Named Baseline Attractor Recovery

Artifact:

- `docs/named-baseline-comparison-summary.md`
- `docs/named-baseline-sweep-summary.md`

Result:

- Best baseline by MSE: `gru_refiner`
- HPP MSE: `0.03431235`
- Best baseline MSE: `0.03751529`
- Best-baseline-to-HPP MSE ratio: `1.09334656x`
- HPP accuracy: `0.47222223`
- Best baseline accuracy: `0.40277779`
- HPP stored memory values: `4,632`
- GRU parameters: `813,888`
- Ten-seed HPP MSE win rate: `1.0`
- Ten-seed HPP accuracy win rate: `1.0`
- Ten-seed best-baseline-to-HPP MSE ratio mean: `1.08667083x`
- Ten-seed HPP accuracy minus best baseline mean: `0.02821181`

Buyer-safe claim:

On a bounded synthetic attractor-recovery task, HPP developmental memory beat the best named baseline in mean recovery error and pathway recognition accuracy while using a much smaller stored-memory footprint. The first plugged sweep repeated that win across ten seeds.

## Current Boundaries

Do not claim:

- HPP V5 replaces all LLMs.
- HPP V5 proves human-equivalent cognition.
- HPP V5 proves a fixed `3000x` efficiency multiple.
- The stress/OOD harnesses perform real-world clinical detection.
- The billion-parameter recurrent run proves training feasibility or model quality.
- The original speech branch is buyer-safe conversational evidence.
- The named-baseline result is a general benchmark win beyond the stated synthetic task.

Do claim:

- HPP V5 has reproducible local evidence harnesses.
- HPP V5 measures shared recurrent depth, memory pressure, stabilization, Habit-14 protection, context-aware recall, developmental curriculum behavior, and stress routing.
- HPP V5 now includes a first named-baseline synthetic comparison.
- HPP V5 explicitly records hardware, CUDA mode, parameter count, memory, latency, and boundary notes.

## Suggested Technical Review Questions

Ask:

- Can the harnesses be rerun on the same hardware?
- What happens with named public baselines?
- Which toy mechanisms transfer to real tasks?
- Where does latency become impractical?
- What can be trained, not just inferred, on the field rig?
- Which parts are patent-backed, patent-adjacent, or trade-secret implementation?

## Licensing / Evaluation Path

For licensing or paid evaluation discussions, use:

- `X:\Licensing_Opportunities\START_HERE_FOR_RACHEL_OR_REP.md`
- `X:\Licensing_Opportunities\HPP_ONE_PAGE_OFFER.md`
- `X:\Licensing_Opportunities\FAST_LICENSE_MENU.md`

Preferred first commercial structure:

`$10,000 - $25,000` for a 30-day private evaluation / option package, subject to written terms and diligence scope.
