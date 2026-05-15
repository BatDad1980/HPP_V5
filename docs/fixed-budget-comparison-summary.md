# Fixed-Budget Comparison Summary

Generated from `scripts/compare_fixed_budget.py`.

This diagnostic compares a 14-pass recurrent workshop against a one-pass baseline with approximately the same parameter budget.

It is intentionally included even though it does not favor the recurrent model. Evidence is useful when it tells us where the architecture does and does not currently win.

## Probe Shape

- Input dimension: 128
- Batch: 8
- Recurrent passes: 14
- Recurrent parameters: 99,072
- One-pass baseline hidden width: 108
- One-pass baseline parameters: 98,516
- Parameter ratio: 0.994x baseline to recurrent

## Plugged Mode

Source log: `docs/fixed-budget-comparison-plugged.json`

- Device: NVIDIA GeForce RTX 4050 Laptop GPU
- Recurrent mean latency: 3.9997 ms
- One-pass baseline mean latency: 0.4726 ms
- Recurrent target MSE: 2.197196
- One-pass baseline target MSE: 0.369598

## Battery Mode

Source log: `docs/fixed-budget-comparison-battery.json`

- Device: CPU
- Recurrent mean latency: 4.9285 ms
- One-pass baseline mean latency: 0.4882 ms
- Recurrent target MSE: 2.10932
- One-pass baseline target MSE: 0.35325

## Early Read

This probe does not demonstrate a recurrent advantage under a same-parameter one-pass comparison.

That is not a failure of the HPP thesis. It shows that an arbitrary one-step target proxy is not the right place to expect recurrent depth to win. A one-pass model is naturally faster on a one-pass target, especially before any training or stabilization logic exists.

## What This Teaches V5

The HPP advantage should be tested where recurrence matters:

- iterative refinement
- noisy-input stabilization
- repeated exposure
- convergence over passes
- pathway protection after repeated success
- stress routing under changed conditions

## Next Harness

The next comparison should use an iterative stability task:

1. Start with noisy input.
2. Define a stable attractor target.
3. Let the recurrent model refine over multiple passes.
4. Compare against a one-pass same-budget model.
5. Measure convergence slope, final error, latency, and parameter count.

That will better test whether recurrent depth buys useful adaptive behavior rather than simply spending more time.
