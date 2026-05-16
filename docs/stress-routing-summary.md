# Stress Routing Summary

This harness compares fixed nurture, fixed sentinel, and stress-aware HPP routing.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Trials: `80`
- Stress threshold: `0.62`

## Result

- Router versus nurture stress improvement: `6.88084155x`
- Router versus sentinel calm improvement: `2.57655435x`
- Router versus best fixed overall improvement: `1.09107701x`
- Router failure rate: `0.0`

## Boundary

This is mechanism evidence only. The stress score is provided by the harness, so this tests routing behavior rather than autonomous stress detection.
