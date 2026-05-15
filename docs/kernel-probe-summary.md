# Kernel Probe Summary

Generated from `scripts/run_kernel_probe.py`.

This is an early diagnostic measurement, not a final benchmark. It exists to prove the HPP V5 evidence workflow: named hardware, named mode, explicit pass count, parameter count, latency, memory, and reproducible scripts.

## Probe Shape

- Kernel: `TinyRecurrentWorkshop`
- Parameters: 99,072
- Dimension: 128
- Batch: 8
- Recurrent passes: 14
- Warmups: 2
- Measured runs: 5

## Plugged Mode

Source log: `docs/kernel-probe-log-plugged.json`

- Device: NVIDIA GeForce RTX 4050 Laptop GPU
- Device route: `cuda:0`
- Mean latency: 2.653 ms
- Median latency: 2.415 ms
- Min latency: 2.266 ms
- Max latency: 3.776 ms
- Allocated GPU memory: 8.51 MB
- Reserved GPU memory: 22.0 MB

## Battery Mode

Source log: `docs/kernel-probe-log-battery.json`

- Device: CPU
- Mean latency: 5.3 ms
- Median latency: 5.095 ms
- Min latency: 4.711 ms
- Max latency: 6.453 ms
- Allocated GPU memory: 0.0 MB
- Reserved GPU memory: 0.0 MB

## Early Read

The first tiny recurrent probe shows that HPP V5 can execute a 14-pass shared-workshop loop on the RTX 4050 with low single-digit millisecond latency and very small GPU memory allocation.

This does not prove the full efficiency thesis yet. It proves that the V5 measurement path is alive and that the architecture can be evaluated under explicit power modes.

## Next Measurement Questions

- How does latency scale with pass count?
- How does memory change with dimension and batch size?
- How does recurrent depth compare to equivalent unique-layer depth?
- What quality proxy should be measured before and after Habit-14 stabilization?
- What buyer-safe benchmark best expresses the post-LLM efficiency claim?
