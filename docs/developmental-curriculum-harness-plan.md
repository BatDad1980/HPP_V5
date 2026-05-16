# Developmental Curriculum Harness Plan

## Purpose

This harness is the next clean HPP V5 experiment.

The goal is to test whether a staged developmental curriculum can produce more stable behavior than flat training under the same small hardware budget.

The harness should stay light enough to run on the field laptop and explicit enough to produce buyer-safe logs.

## Core Question

Does a model trained through staged plasticity, repetition, stabilization, and filtering recover signal better than a model trained on the same data without developmental staging?

## Conditions

### Flat Baseline

- one training phase
- same total examples
- same parameter budget target
- same optimizer budget when possible
- no maturity-dependent filtering
- no Habit-14 protection

### Context-Aware Flat Baseline

- receives oracle target/distractor labels
- ignores known distractor events
- uses the same flat recall blend
- has no staged maturity
- has no Habit-14 protection

### HPP Developmental Path

- infant stage: high noise, broad input, no hard filtering
- nurture stage: repeated safe signal exposure
- scaffold stage: early pathway preference after repeated success
- myelinated stage: protected pathway after Habit-14 threshold
- guardian stage: stress/noise challenge against mature pathway

## Metrics

Record at minimum:

- parameter count
- device name
- CUDA availability
- GPU memory allocated when CUDA is active
- wall-clock training time
- inference latency
- final reconstruction or classification error
- noise recovery score
- stability score across repeated prompts or probes
- degradation under shifted context

## First Toy Task

Start with a synthetic signal-recovery task because it is simple, measurable, and close to the current evidence ladder.

Input:

- noisy vector state
- hidden attractor pattern
- context marker
- occasional distractor signal

Target:

- recover the attractor
- preserve correct context
- ignore distractors only after maturity

The important design rule:

Early stages should not over-filter. Filtering should become stronger only after repeated evidence.

## Habit-14 Gate

The harness should expose the same pathway at least 14 times before marking it protected.

Before 14 successful exposures:

- no pathway protection
- no mature filtering
- no guardian routing

At or after 14 successful exposures:

- protect the repeated pathway
- reduce distractor influence
- measure whether protected recall improves

## Buyer-Safe Success Criteria

The harness produces a useful result if it can show one of the following:

- HPP staging improves noise recovery versus flat training.
- HPP staging reaches similar quality with less stored parameter growth.
- HPP staging produces better shifted-context stability after Habit-14.
- HPP staging fails on the first design, but the logs identify why.

Negative evidence is acceptable. The point is to build a real ladder, not marketing fog.

## Implementation Notes

Keep the first implementation small:

- PyTorch
- explicit seed control
- CPU fallback
- CUDA only when available and requested
- JSON log output under `docs/`
- markdown summary after each run

Suggested script:

`scripts/compare_developmental_curriculum.py`

Suggested outputs:

- `docs/developmental-curriculum-plugged.json`
- `docs/developmental-curriculum-battery.json`
- `docs/developmental-curriculum-summary.md`

Initial implementation status:

- `scripts/compare_developmental_curriculum.py` exists.
- Default mode is `demo`, which forces CPU for a safe smoke run.
- Use `--mode plugged` only when the machine is powered and CUDA use is intentional.
- First `demo` and `plugged` runs have been captured under `docs/`.
- First ten-seed plugged sweep with a context-aware flat baseline is summarized in `docs/developmental-curriculum-sweep-summary.md`.
