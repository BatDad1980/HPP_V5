# Iterative Stability Summary

Generated from `scripts/compare_iterative_stability.py`.

This harness tests a narrow HPP mechanism: repeated shared loops moving a noisy state toward a stored stable attractor.

It is not a trained model-quality benchmark. The attractor is explicit by design so the mechanism and result are inspectable.

## Probe Shape

- Dimension: 128
- Batch: 8
- Noise: 0.75
- Step size: 0.18
- Recurrent passes: 14
- Warmups: 3
- Measured runs: 10
- Recurrent parameters: 129
- One-pass parameters: 129

## Plugged Mode

Source log: `docs/iterative-stability-plugged.json`

- Device: NVIDIA GeForce RTX 4050 Laptop GPU
- Initial noisy MSE: 0.53815031
- Recurrent final MSE: 0.002078
- One-pass final MSE: 0.361852
- Recurrent improvement ratio: 258.947795x
- One-pass improvement ratio: 1.48721x
- Final MSE ratio, one-pass to recurrent: 174.135x
- Recurrent mean latency: 3.0818 ms
- One-pass mean latency: 0.3766 ms
- Latency ratio, recurrent to one-pass: 8.183x

## Battery Mode

Source log: `docs/iterative-stability-battery.json`

- Device: CPU
- Initial noisy MSE: 0.55714619
- Recurrent final MSE: 0.002152
- One-pass final MSE: 0.374625
- Recurrent improvement ratio: 258.947796x
- One-pass improvement ratio: 1.48721x
- Final MSE ratio, one-pass to recurrent: 174.082x
- Recurrent mean latency: 0.7028 ms
- One-pass mean latency: 0.0739 ms
- Latency ratio, recurrent to one-pass: 9.51x

## Early Read

This is the first V5 harness that directly supports the HPP-shaped mechanism:

With the same stored attractor and the same parameter count, repeated shared loops stabilized noisy input far closer to the target than a one-pass update.

The cost is latency. This does not prove free speed or model intelligence. It proves that recurrent passes can buy stabilization without increasing stored parameters.

## Why It Matters

This maps cleanly to the original HPP hypothesis:

- repeated loops reduce noise
- stable attractors can guide recovery
- Habit-14-style repetition can produce a protected pathway
- the win is not brute parameter scale
- the evidence is measurable

## Next Step

Add a Habit-14 memory harness:

1. Repeat the same noisy pattern across exposures.
2. Track whether the attractor becomes protected.
3. Compare a protected recurrent path against an unprotected path.
4. Record improvement across exposures, not only within one run.
