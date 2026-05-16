# Grow First, Freeze Later

## External Anchor

On April 30, 2026, Logan G. Wright, Tianyu Wang, Tatsuhiro Onodera, and Peter L. McMahon published `Physical Foundation Models: Fixed hardware implementations of large-scale neural networks` as arXiv:2604.27911.

Their Physical Foundation Model direction asks what happens if a trained foundation model is compiled into fixed analog hardware, where inference is performed by the natural dynamics of electronics, optics, or other physical substrates instead of by a programmable GPU.

The key HPP observation is that this does not compete with developmental AI. It creates a useful endpoint for it.

## HPP Frame

Physical Foundation Models address the mature inference problem:

- the model already exists
- the learned structure is stable enough to freeze
- programmability is sacrificed for speed, density, and energy efficiency
- the main question becomes how cheaply the mature calculation can run

HPP addresses the formation problem:

- capability begins plastic
- repeated experience shapes pathways
- useful loops stabilize through evidence
- noisy early intake matures into selective filtering
- protected habits become cheaper and more reliable to invoke

In short:

Physical Foundation Models make mature models cheaper to run.

HPP explores how capable systems might become mature in the first place.

## Biological Analogy

Human development does not begin with fixed expert pathways.

The infant system is broadly receptive and noisy. Repeated exposure creates early structure. Practice stabilizes pathways. Mature cognition filters more aggressively than early cognition. Under stress, reliable habits and protective routing become more important than wide-open exploration.

HPP translates that pattern into an engineering pipeline:

1. grow with high plasticity
2. repeat useful pathways
3. measure stabilization
4. protect what survives repeated evidence
5. route mature pathways faster and with less noise
6. freeze or compile only after maturity

## Proposed Stack

The long-range stack can be described as:

```text
Developmental curriculum
        |
Plastic recurrent learning
        |
Habit-14 stabilization
        |
Stress and context validation
        |
Mature pathway extraction
        |
Fixed or semi-fixed inference substrate
```

This stack lets HPP talk to both software and hardware audiences.

Software audiences can evaluate whether staged plasticity, recurrence, and protected memory outperform flat baselines under fixed budgets.

Hardware audiences can evaluate whether stable mature pathways are good candidates for compilation into specialized inference devices.

## Claim Boundary

HPP V5 should not claim that it can already generate Physical Foundation Models.

HPP V5 can claim a research-compatible bridge:

- PFMs suggest a future where mature inference is compiled into physics.
- HPP suggests a developmental process for producing mature pathways before compilation.
- The combined strategy is `grow first, freeze later`.

## Testable Implication

The next HPP experiments should not only ask whether recurrence improves a toy target.

They should ask whether a staged developmental curriculum produces pathways that are:

- more stable under noise
- cheaper to invoke after repetition
- easier to protect after Habit-14 exposure
- more robust under shifted context
- clearer candidates for later distillation, extraction, or fixed inference

The buyer-safe phrasing:

HPP is an upstream developmental architecture. Physical Foundation Models are a possible downstream inference substrate.

## First Local Artifact

The first HPP V5 developmental-curriculum harness now exists at `scripts/compare_developmental_curriculum.py`.

It is intentionally small. It compares a flat all-at-once prototype against a staged HPP memory path with early plasticity, repeated safe exposure, Habit-14 locking, and shifted-context recall probes.

The first plugged RTX 4050 smoke run is recorded in `docs/developmental-curriculum-plugged.json`.
