# Soft-Stop Guardian Principle

## Core Statement

Just because a system can keep going does not mean it should keep going.

HPP treats that as an architecture principle, not a motivational slogan.

High-intensity systems can continue operating in noise levels that would force other systems to stop. That tolerance can be useful in harsh environments, but it can also hide risk. If a system only stops when the substrate fails, the guardian layer has waited too long.

## Design Translation

HPP should distinguish:

- tolerance: the system can continue
- safety judgment: the system should continue
- soft stop: the system should pause, route down, or request help before failure
- hard stop: the system must stop because the substrate or mission is at risk
- resume path: the system can return after recovery or context repair

## Why It Matters

Many systems fail before physical collapse. They fail through:

- cognitive overload
- emotional overload
- motivational collapse
- context confusion
- unsafe escalation
- repeated operation outside a stable band

Other systems do the opposite. They continue through overload until the body, hardware, or operating environment pays the cost.

HPP should handle both patterns.

## Profile-Aware Redlines

The same noise does not mean the same thing for every system.

A low-tolerance profile may need early protection.

A standard profile may need balanced exploration and fallback.

A high-intensity profile may operate productively under conditions that look extreme from the outside.

But high tolerance is not the same as safety.

The guardian layer should learn the difference between a system's normal storm and a true substrate-threatening signal.

## Current Evidence

Related artifacts:

- `docs/inferred-stress-routing-profile-summary.md`
- `docs/inferred-stress-profile-sweep-summary.md`
- `docs/tapout-boundary-sweep-summary.md`

Current toy evidence:

- low-tolerance and standard profiles first tapped out at extreme-noise scale `2.0`
- high-intensity profile first tapped out at extreme-noise scale `2.8`
- high-intensity profile tolerated a larger unfamiliar-noise band before conservative fallback engaged

## Engineering Rule

Do not wait for hardware failure to prove the system needs protection.

For AI systems, that means monitoring uncertainty, stress, novelty, memory drift, resource pressure, and failure patterns before catastrophic output or runtime failure.

For field-lab execution, that means bounded runs, frequent commits, CUDA memory checks, and resumable experiments.

For future embodied systems, that means watchdogs, E-stops, local governors, and conservative fallback before body-level risk.

## Buyer-Safe Boundary

This principle is architecture guidance.

It does not claim clinical diagnosis, human mental-state detection, or production safety. It describes how HPP separates high operating tolerance from mature guardian judgment.

