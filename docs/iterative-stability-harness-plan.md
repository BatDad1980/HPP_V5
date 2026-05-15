# Iterative Stability Harness Plan

The fixed-budget comparison showed that a one-pass target is not the right task for proving recurrent depth.

The next harness should test where HPP should plausibly win: repeated refinement under noisy conditions.

## Test Question

Can a shared recurrent workshop use repeated passes to stabilize noisy input toward a target more effectively than a one-pass same-budget baseline?

## Task Shape

1. Generate a clean latent vector.
2. Add controlled noise.
3. Define the clean latent vector as the attractor target.
4. Run the recurrent model for multiple passes.
5. Run a one-pass same-budget baseline.
6. Measure error from the clean target.

## Metrics

- parameter count
- device
- latency
- initial noisy MSE
- recurrent MSE per pass
- final recurrent MSE
- one-pass baseline MSE
- convergence slope
- memory use

## Why This Fits HPP

HPP is not just "do one transformation fast."

The thesis is about:

- repeated loops
- stabilization
- signal protection
- refinement under uncertainty
- safe repetition becoming a stronger path

An iterative denoising/stabilization harness is a better proxy than a one-step target.

## Future Habit-14 Extension

After the basic stability harness works, add a Habit-14 layer:

- run the same noisy pattern repeatedly
- track whether error improves over exposures
- protect the successful pathway
- compare against a baseline with no stabilization memory

That is the first small bridge from toy kernel to the original HPP thesis.
