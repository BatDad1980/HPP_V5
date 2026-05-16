# HPP V5 Model Kernel Spec

This document defines the first clean model-side target for HPP V5.

The prior HPP proved a model-centric prototype. V5 should extract the core ideas into a cleaner, measurable kernel that can support both buyer demos and private operating use.

## Hypothesis

A post-LLM system can achieve useful adaptive behavior with less brute-force scale by combining:

- recurrent depth through shared weights
- stabilization gates
- adaptive pruning/protection
- stress-aware routing
- staged curriculum growth
- explicit telemetry

The efficiency claim must be treated as a measurement target, not a slogan.

## Kernel Components

### 1. Shared Workshop

A compact neural block reused across multiple passes.

Purpose:

- reduce unique parameter count
- increase effective reasoning depth
- expose loop telemetry
- allow power-aware pass budgeting

### 2. Habit Gate

A stabilization layer inspired by Habit-14.

Purpose:

- count successful repetitions
- prevent unstable loops from being treated as permanent
- distinguish plastic, scaffolded, myelinated, and guardian pathways

### 3. Protection Filter

A telemetry and gating layer derived from the previous `KarmicMicrogliaFilter`.

Purpose:

- track noisy pathways
- protect stable pathways
- expose pruning/protection metrics
- support buyer-facing explanation of adaptive efficiency

Developmental rule:

Filtering should emerge with maturity. Infant-like states should be receptive and noisy; stable repeated pathways should gain protection and stronger noise rejection over time.

### 4. Router

A mode selector derived from nurture/sentinel routing.

Purpose:

- use reflective loops in safe conditions
- use low-complexity paths under stress
- support battery-safe, plugged-in, and demo execution

First evidence:

- `scripts/compare_stress_routing.py`
- `docs/stress-routing-sweep-summary.md`

The first toy harness uses a provided stress score to switch between nurture and sentinel strategies. This proves routing behavior only; autonomous stress detection remains future work.

## Scaling Probe

Artifact:

- `scripts/sweep_recurrent_gpu_scale.py`
- `docs/recurrent-gpu-scaling-summary.md`

The first plugged RTX 4050 scaling probe measures inference-only recurrent workshop size. The largest completed probe used a 19,456-dimensional workshop with 2,271,332,352 parameters and 14 recurrent passes. The practical latency edge appeared earlier, around the 15,360-dimensional probe with 1,415,669,760 parameters.

This should be treated as hardware envelope evidence only. Training, optimizer state, and useful learned behavior require separate tests.

### 5. Evidence Harness

A measurement wrapper around every run.

Purpose:

- record device
- record parameter count
- record pass count
- record latency
- record memory use
- record output quality proxy
- preserve enough context to repeat the measurement

## Power-Aware Execution

### Battery Safe

- CPU preferred.
- Very small tensors only.
- No training.
- No checkpoint loading unless explicitly needed.
- Maximum pass count should be low.

### Plugged In

- CUDA allowed.
- Check `torch.cuda.is_available()`.
- Log device name.
- Log allocated and reserved GPU memory.
- Use small measured experiments before larger runs.

### Demo

- Deterministic input.
- Small fixed model.
- Sanitized output.
- Buyer-safe telemetry.

## First Measurement Targets

V5 should eventually measure:

- parameters versus effective depth
- latency per recurrent pass
- memory use per pass
- CPU versus CUDA behavior
- output stability across repeated loops
- quality before and after Habit-14-style stabilization
- shared recurrent depth versus a unique-layer stack
- shared recurrent depth versus a baseline with the same parameter budget
- iterative stabilization under controlled noise
- Habit-14 memory/protection across repeated exposures
- rigidity risk after over-protection or excessive lock strength

## Guardrail

Do not claim a fixed efficiency multiple without a benchmark that states:

- baseline model
- hardware
- task
- metric
- method
- run date
- power mode
- reproducibility notes
