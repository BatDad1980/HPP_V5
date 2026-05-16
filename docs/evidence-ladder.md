# HPP V5 Evidence Ladder

This document consolidates the current HPP V5 evidence path.

The goal is not to claim the whole thesis is proven. The goal is to show which parts are already measured, which parts are only promising, and what still needs stronger tests.

## Ladder 1: The Measurement Path Exists

Artifact: `docs/kernel-probe-summary.md`

Result:

- Tiny recurrent kernel: 99,072 parameters
- Effective recurrent passes: 14
- Plugged device: NVIDIA GeForce RTX 4050 Laptop GPU
- Mean plugged latency: 2.653 ms
- GPU memory allocated: 8.51 MB

Meaning:

HPP V5 has a reproducible evidence workflow with explicit hardware, pass count, parameter count, latency, memory, and power mode.

Boundary:

This proves the measurement harness is alive. It does not prove model quality or the full efficiency claim.

## Ladder 2: Shared Recurrence Reduces Stored Parameters

Artifact: `docs/recurrent-vs-stack-summary.md`

Result:

- Shared recurrent workshop: 99,072 parameters
- Fourteen-layer unique stack: 1,387,008 parameters
- Unique stack uses 14.0x more parameters for the same effective depth

Meaning:

For a fixed effective refinement depth, shared recurrence can provide depth without multiplying stored parameter count.

Boundary:

The unique stack was slightly faster at this small scale. The measured win is compactness, not speed.

## Ladder 3: Arbitrary Same-Budget Targets Are Not The Right Battlefield

Artifact: `docs/fixed-budget-comparison-summary.md`

Result:

- Recurrent model and one-pass baseline were matched to roughly the same parameter budget.
- The one-pass baseline won the arbitrary one-step target and was faster.

Meaning:

This is useful negative evidence. HPP should not be sold as automatically better on every proxy task.

Boundary:

The test does not measure what HPP is designed for: repeated refinement, noisy-state recovery, pathway stabilization, or developmental adaptation.

## Ladder 4: Repeated Shared Loops Stabilize Noisy State

Artifact: `docs/iterative-stability-summary.md`

Result:

- Same parameter count: 129 parameters each
- Recurrent final MSE: 0.002078
- One-pass final MSE: 0.361852
- One-pass final error was 174.135x higher
- Recurrent improvement ratio: 258.947795x

Meaning:

When the task actually requires iterative stabilization, recurrent passes can buy much stronger recovery from noise without adding stored parameters.

Boundary:

The cost is latency. The plugged recurrent path was about 8.183x slower than the one-pass path in this toy harness.

## Ladder 5: Habit-14 Behaves Like Protected Muscle Memory

Artifact: `docs/habit-memory-summary.md`

Result:

- Before 14 exposures: no protection, no improvement
- At 14 exposures: noisy recall improved by 12.73755424x
- At 21 exposures: noisy recall improved by 89.63142983x

Meaning:

This supports the mechanism behind Habit-14: repeated practice can turn a noisy unstable action into a protected pathway, similar to habit formation or muscle memory.

Boundary:

This is a toy mechanism harness with an explicit repeated signal. It does not prove general language learning, agency, or broad reasoning.

## Ladder 6: Original Branch Speech Adapter Is Improving

Artifact: `docs/original-speech-progress.md`

Result:

- The original branch now has conversational checkpoints and a speech anchor.
- Current speech anchor metadata: `conversational_v17d`
- The active speech strategy freezes the deep developmental stack and trains the speech-facing layers.
- Light smoke testing showed sentence-shaped fragments and recognizable response patterns, but also repetition, format leakage, and sample blending.

Meaning:

The original lab branch is moving from concept clusters toward speech. The important engineering lesson is to train the tongue without constantly disturbing the deeper core.

Boundary:

This is not yet buyer-safe conversational evidence. It needs held-out prompts, transcript logging, repetition metrics, and cleaner curriculum.

## Ladder 7: Staged Developmental Curriculum Beats A Flat Prototype On A Toy Task

Artifacts:

- `scripts/compare_developmental_curriculum.py`
- `docs/developmental-curriculum-summary.md`
- `docs/developmental-curriculum-sweep-summary.md`
- `docs/developmental-curriculum-plugged.json`

Result:

- HPP path reached Habit-14 protection and locked the staged pathway.
- Clean-context HPP versus flat improvement: 2.09890963x
- Shifted-context HPP versus flat improvement: 2.02085768x
- Clean-context HPP versus context-aware flat improvement: 2.09151815x
- Shifted-context HPP versus context-aware flat improvement: 1.95518574x
- Ten-seed plugged sweep HPP versus flat clean mean: 2.22223699x
- Ten-seed plugged sweep HPP versus flat shifted mean: 2.10660734x
- Ten-seed plugged sweep HPP versus context-aware flat clean mean: 2.20191598x
- Ten-seed plugged sweep HPP versus context-aware flat shifted mean: 2.03043896x
- Ten-seed context-aware shifted standard deviation: 0.03613556
- Ten-seed Habit-14 lock rate: 10/10
- Plugged device: NVIDIA GeForce RTX 4050 Laptop GPU

Meaning:

This is the first direct HPP V5 harness comparing staged developmental exposure against flat prototypes. In this toy signal-recovery setup, staged plasticity plus Habit-14 protection recovered the target better under both clean and shifted-context probes across the first ten plugged seeds. The stronger context-aware flat baseline receives oracle target/distractor labels and ignores distractor events, making it a more serious comparison than the naive flat baseline.

Boundary:

This is mechanism evidence only. It does not prove language ability, agency, broad reasoning, or general model superiority. The next version needs stronger baselines and changed-context memory tests.

## Current Buyer-Safe Claim

HPP V5 has early measured evidence for:

- low-footprint recurrent execution on an RTX 4050-class laptop GPU
- parameter reuse through shared recurrent depth
- stronger noisy-state stabilization through repeated loops
- Habit-14-style protected recall after repeated exposure
- staged developmental exposure outperforming a flat prototype on a toy recovery task
- a plausible speech-adapter path in the original branch

HPP V5 should not yet claim:

- a fixed 3000x efficiency multiple
- full LLM replacement
- human-equivalent cognition
- production-safe autonomous agency
- mature conversational fluency

## Next Evidence Rungs

1. Measure Habit-14 memory under changed context, not only repeated identical signal.
2. Add transcript logging for the original speech branch.
3. Build a held-out speech regression suite.
4. Add stress-routing harnesses that compare nurture versus sentinel behavior.
5. Compare against named small baselines on defined tasks.
6. Add power and CUDA memory logs for split-cycle training runs.
