# Recurrent Versus Unique Stack Summary

Generated from `scripts/compare_recurrent_vs_stack.py`.

This is an early diagnostic comparison for the HPP V5 post-LLM efficiency thesis. It compares a shared recurrent workshop against a conventional unique-layer stack using the same tensor size and the same number of effective refinement passes.

It is not a final benchmark and does not measure task quality yet.

## Probe Shape

- Dimension: 128
- Batch: 8
- Effective refinement passes: 14
- Warmups: 3
- Measured runs: 10

## Shared Recurrent Workshop

The recurrent model uses one workshop and one gate repeatedly.

- Parameters: 99,072

## Unique-Layer Stack

The stack model uses fourteen separate workshop/gate blocks.

- Parameters: 1,387,008

## Plugged Mode

Source log: `docs/recurrent-vs-stack-plugged.json`

- Device: NVIDIA GeForce RTX 4050 Laptop GPU
- Recurrent mean latency: 3.004 ms
- Unique stack mean latency: 2.907 ms
- Parameter ratio: 14.0x more parameters in the unique stack
- Mean latency ratio: unique stack was 0.968x the recurrent latency

## Battery Mode

Source log: `docs/recurrent-vs-stack-battery.json`

- Device: CPU
- Recurrent mean latency: 6.052 ms
- Unique stack mean latency: 5.74 ms
- Parameter ratio: 14.0x more parameters in the unique stack
- Mean latency ratio: unique stack was 0.948x the recurrent latency

## Early Read

This diagnostic supports the first narrow V5 efficiency claim:

For the same effective refinement depth in this tiny probe, a shared recurrent workshop used 14x fewer parameters than a unique-layer stack.

It does not yet support a speed claim. At this scale, latency was similar and the unique stack was slightly faster in these runs. That is acceptable evidence discipline: the first measured win is compactness and parameter reuse, not runtime superiority.

## Next Comparison

The next harness should measure:

- pass-count scaling
- dimension scaling
- memory pressure at larger batch sizes
- recurrent shared-depth versus unique-depth under a fixed parameter budget
- a quality proxy where repeated passes can improve output stability

## Scaled GPU Follow-Up

Artifact:

- `docs/recurrent-vs-unique-stack-scaling-summary.md`

The scaled follow-up compares the same effective depth at larger dimensions on the RTX 4050 Laptop GPU.

Key result:

- At dimension 4,096, the shared recurrent model used 100,687,872 parameters and 393.469 MB peak CUDA memory.
- At dimension 4,096, the unique stack used 1,409,630,208 parameters and 5,386.688 MB peak CUDA memory.
- Parameter ratio: 14.0x
- Peak memory ratio: 13.690248x
- At dimension 8,192, shared recurrence completed with 402,702,336 parameters and 1,545.812 MB peak CUDA memory.
- At dimension 8,192, the unique stack hit CUDA OOM.

Interpretation:

At tiny sizes, the unique stack can be latency-competitive. At larger sizes, the memory cost of unique depth becomes the limiting factor. This supports the HPP claim that shared recurrent depth can preserve effective depth while delaying the hardware wall.
