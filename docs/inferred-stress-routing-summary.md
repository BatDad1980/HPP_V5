# Inferred Stress Routing Summary

This harness tests HPP routing when stress is estimated from state telemetry rather than supplied directly.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Trials: `100`
- Route accuracy: `0.9`
- Tap-out rate: `0.2`
- Tolerance profile: `standard`

## Result

- Inferred router versus nurture under stress: `6.92724491x`
- Inferred router versus sentinel under calm: `1.0542901x`
- Inferred router versus best fixed overall: `1.01968925x`
- Inferred router versus oracle overall: `0.84259185x`
- Inferred router failure rate: `0.2`
- Tap-out router versus inferred overall: `2.41826887x`
- Tap-out router failure rate: `0.0`

## Boundary

This is still synthetic mechanism evidence. The stress and OOD estimators use hand-built telemetry features calibrated to this toy harness.
