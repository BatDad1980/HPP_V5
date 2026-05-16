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

Artifacts:

- `docs/recurrent-vs-stack-summary.md`
- `docs/recurrent-vs-unique-stack-scaling-summary.md`

Result:

- Shared recurrent workshop: 99,072 parameters
- Fourteen-layer unique stack: 1,387,008 parameters
- Unique stack uses 14.0x more parameters for the same effective depth
- Scaled dimension 4,096 shared recurrent parameters: 100,687,872
- Scaled dimension 4,096 unique stack parameters: 1,409,630,208
- Scaled dimension 4,096 unique stack peak memory: 5,386.688 MB
- Scaled dimension 4,096 shared recurrent peak memory: 393.469 MB
- Scaled dimension 8,192 shared recurrent completed with 402,702,336 parameters and 1,545.812 MB peak memory
- Scaled dimension 8,192 unique stack hit CUDA OOM

Meaning:

For a fixed effective refinement depth, shared recurrence can provide depth without multiplying stored parameter count. At larger dimensions, the unique stack's repeated parameters become a practical GPU memory limit while the shared recurrent path continues to run.

Boundary:

The unique stack can be latency-competitive at smaller sizes. The measured win is compactness and memory headroom, not universal speed.

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

## Ladder 6: Habit-14 Can Protect A Core Without Freezing Context

Artifacts:

- `scripts/compare_changed_context_memory.py`
- `docs/changed-context-habit-memory-summary.md`
- `docs/changed-context-habit-memory-plugged.json`

Result:

- Before 14 exposures: no protection and no adaptive improvement
- At 14 exposures: shifted-context adaptive recall improved over noisy baseline by 9.75428669x
- At 14 exposures: shifted-context adaptive recall improved over rigid lock by 2.96621249x
- At 21 exposures: shifted-context adaptive recall improved over noisy baseline by 47.17974545x
- At 21 exposures: shifted-context adaptive recall improved over rigid lock by 17.01315969x
- Plugged device: NVIDIA GeForce RTX 4050 Laptop GPU

Meaning:

This moves Habit-14 beyond identical-signal recall. The harness separates a protected core from a changing context and shows that context-aware protection can outperform a rigid full-pattern lock under shifted-context probes.

Boundary:

The context vector is known to the adaptive memory. This proves a design mechanism for context-aware protection, not autonomous context discovery or broad reasoning.

## Ladder 7: Original Branch Speech Adapter Is Improving

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

## Ladder 8: Staged Developmental Curriculum Beats A Flat Prototype On A Toy Task

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

## Ladder 9: Stress-Aware Routing Beats Fixed Response Modes

Artifacts:

- `scripts/compare_stress_routing.py`
- `scripts/summarize_stress_routing_sweep.py`
- `docs/stress-routing-summary.md`
- `docs/stress-routing-sweep-summary.md`
- `docs/stress-routing-plugged.json`

Result:

- Single plugged run router versus nurture under stress: 6.88084155x
- Single plugged run router versus sentinel under calm: 2.57655435x
- Single plugged run router versus best fixed overall: 1.09107701x
- Single plugged run router failure rate: 0.0
- Ten-seed sweep router versus nurture under stress mean: 6.80870099x
- Ten-seed sweep router versus sentinel under calm mean: 2.61898962x
- Ten-seed sweep router versus best fixed overall mean: 1.09279677x
- Ten-seed sweep router failure rate mean: 0.0
- Plugged device: NVIDIA GeForce RTX 4050 Laptop GPU

Meaning:

This is the first explicit HPP V5 nurture-versus-sentinel routing harness. In calm probes, the router preserves the richer nurture path. Under stress probes, it switches to a protected sentinel path. Across ten plugged seeds, the mixed policy outperformed either fixed strategy alone.

Boundary:

The stress score is provided by the harness. This tests stress-aware routing behavior, not autonomous stress detection or real-world safety.

## Ladder 10: Inferred Stress Routing Supports Tolerance Profiles

Artifacts:

- `scripts/compare_inferred_stress_routing.py`
- `docs/inferred-stress-routing-summary.md`
- `docs/inferred-stress-routing-profile-summary.md`
- `docs/inferred-stress-profile-sweep-summary.md`
- `docs/tapout-boundary-sweep-summary.md`
- `docs/inferred-stress-routing-plugged.json`

Result:

- Inferred route accuracy: 0.90
- Standard profile inferred router versus nurture under stress: 6.92724491x
- Standard profile inferred router failure rate: 0.20
- Standard profile tap-out router versus inferred router overall: 2.41826887x
- Standard profile tap-out router failure rate: 0.0
- Low-tolerance profile tap-out rate: 0.20
- Standard profile tap-out rate: 0.20
- High-intensity profile tap-out rate: 0.0
- High-intensity profile tap-out failure rate: 0.20
- Five-seed profile sweep low-tolerance tap-out failure rate mean: 0.0
- Five-seed profile sweep standard tap-out failure rate mean: 0.0
- Five-seed profile sweep high-intensity tap-out failure rate mean: 0.20
- Five-seed profile sweep standard tap-out versus inferred mean: 2.49136496x
- Tap-out boundary sweep low-tolerance first tap-out noise: 2.0
- Tap-out boundary sweep standard first tap-out noise: 2.0
- Tap-out boundary sweep high-intensity first tap-out noise: 2.8
- High-intensity max no-tapout noise: 2.4
- Plugged device: NVIDIA GeForce RTX 4050 Laptop GPU

Meaning:

This moves stress routing beyond an oracle stress value. The harness estimates stress from state telemetry and adds an out-of-distribution tap-out path. It also introduces tolerance profiles: the same noise can trigger tap-out in a standard profile while remaining within operating range for a high-intensity profile. The first five-seed sweep preserved this split, and the boundary sweep found that the high-intensity profile tolerated a higher unfamiliar-noise band before tapping out.

Boundary:

The stress and OOD estimators are hand-built and calibrated to this synthetic harness. This is not real-world mental-state detection, clinical safety, or autonomous risk assessment.

## Ladder 11: Recurrent Workshop Scales Into Billion-Parameter Inference On Field GPU

Artifacts:

- `scripts/sweep_recurrent_gpu_scale.py`
- `docs/recurrent-gpu-scaling-summary.md`
- `docs/recurrent-gpu-scaling-plugged.json`

Result:

- Plugged device: NVIDIA GeForce RTX 4050 Laptop GPU
- Passes per run: 14
- Largest successful dimension: 19,456
- Largest successful batch: 2
- Largest successful parameter count: 2,271,332,352
- FP32 parameter footprint at largest size: 8,664.445 MB
- Peak allocated CUDA memory at largest size: 8,674.609 MB
- Mean latency at largest size: 8,555.7338 ms
- Largest practical faster point before the sharp slowdown: 15,360 dimension, 1,415,669,760 parameters, 457.0935 ms mean latency, 5,410.297 MB peak allocated

Meaning:

This is the first deliberate GPU ceiling probe for the HPP recurrent workshop. It shows that the field laptop can execute very large shared-weight recurrent inference in FP32, including billion-parameter-scale workshop instances, without training or optimizer state.

Boundary:

This is inference-only scaling evidence. It does not prove model quality, training feasibility, optimizer memory fit, checkpoint practicality, or an efficiency multiple. The sharp latency jump after the 15,360-dimension point suggests the practical edge arrives before absolute allocation failure.

## Ladder 12: HPP Beats Named Baselines On A Bounded Attractor-Recovery Task

Artifacts:

- `scripts/compare_named_baselines.py`
- `scripts/sweep_named_baselines.py`
- `docs/named-baseline-comparison-summary.md`
- `docs/named-baseline-comparison-plugged.json`
- `docs/named-baseline-sweep-summary.md`
- `docs/named-baseline-sweep-plugged.json`
- `docs/named-baseline-sweep-big-summary.md`
- `docs/named-baseline-sweep-plugged-big.json`

Result:

- Named baselines: nearest-centroid prototype memory, one-pass MLP denoiser, GRU recurrent refiner
- Best baseline by MSE: `gru_refiner`
- HPP developmental memory MSE: `0.03431235`
- Best baseline MSE: `0.03751529`
- Best-baseline-to-HPP MSE ratio: `1.09334656x`
- HPP accuracy: `0.47222223`
- Best baseline accuracy: `0.40277779`
- HPP stored memory values: `4,632`
- One-pass MLP parameters: `295,872`
- GRU parameters: `813,888`
- Peak allocated CUDA memory: `39.811 MB`
- Ten-seed sweep HPP MSE win rate: `1.0`
- Ten-seed sweep HPP accuracy win rate: `1.0`
- Ten-seed best-baseline-to-HPP MSE ratio mean: `1.08667083x`
- Ten-seed HPP accuracy minus best baseline mean: `0.02821181`
- Larger 15-seed sweep dimension: `384`
- Larger 15-seed sweep HPP MSE win rate: `0.0`
- Larger 15-seed sweep HPP accuracy win rate: `1.0`
- Larger 15-seed sweep HPP accuracy minus best baseline mean: `0.03271123`
- Larger 15-seed sweep peak allocated CUDA memory: `103.958 MB`

Meaning:

This is the first HPP V5 harness that uses named baseline mechanisms instead of only internal comparisons. In this synthetic attractor-recovery task, HPP developmental memory recovered the target with lower mean error and higher pathway recognition accuracy than the best trained baseline, while using a much smaller stored-memory footprint. The ten-seed plugged sweep preserved the result across all tested seeds. A larger 15-seed sweep split the result: trained neural baselines won raw coordinate MSE, while HPP won pathway-recognition accuracy across all tested seeds.

Boundary:

This is mechanism evidence only. The HPP path receives trusted clean anchors after an early noisy period, while the MLP and GRU baselines receive supervised clean targets during gradient training. It does not prove language ability, broad reasoning, production safety, or a fixed efficiency multiple. The larger sweep shows that recognition and reconstruction should be measured separately.

## Current Buyer-Safe Claim

HPP V5 has early measured evidence for:

- low-footprint recurrent execution on an RTX 4050-class laptop GPU
- parameter reuse through shared recurrent depth
- larger-dimension shared recurrence continuing after the unique-depth stack hits CUDA OOM
- stronger noisy-state stabilization through repeated loops
- Habit-14-style protected recall after repeated exposure
- context-aware Habit-14 recall under shifted context
- staged developmental exposure outperforming a flat prototype on a toy recovery task
- stress-aware routing outperforming fixed nurture or sentinel modes in a toy harness
- inferred stress routing with profile-dependent tap-out behavior
- billion-parameter-scale recurrent workshop inference on the field RTX 4050 GPU
- a first named-baseline attractor-recovery comparison
- a plausible speech-adapter path in the original branch

HPP V5 should not yet claim:

- a fixed 3000x efficiency multiple
- full LLM replacement
- human-equivalent cognition
- production-safe autonomous agency
- mature conversational fluency

## Next Evidence Rungs

1. Add transcript logging for the original speech branch.
2. Build a held-out speech regression suite.
3. Expand named-baseline comparisons across more seeds and harder changed-context tasks.
4. Add power and CUDA memory logs for split-cycle training runs.
5. Add autonomous stress-signal estimation instead of harness-provided stress values.
