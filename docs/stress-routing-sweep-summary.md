# Stress Routing Sweep Summary

This summary captures a plugged multi-seed sweep of the HPP stress-routing harness.

## Setup

- Script: `scripts/compare_stress_routing.py`
- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- Seeds: `101, 133, 14, 144, 199, 21, 256, 314, 42, 77`
- Runs: `10`

## Results

| Seed | Router/nurture stress | Router/sentinel calm | Router/best-fixed overall | Router failure rate |
| ---: | ---: | ---: | ---: | ---: |
| 101 | 6.65223459x | 2.79391435x | 1.09855609x | 0.000000 |
| 133 | 6.70373888x | 2.85292824x | 1.10800913x | 0.000000 |
| 14 | 6.88084155x | 2.57655435x | 1.09107701x | 0.000000 |
| 144 | 6.72130071x | 2.68048402x | 1.09387545x | 0.000000 |
| 199 | 6.95004535x | 2.47202209x | 1.08792409x | 0.000000 |
| 21 | 6.94747427x | 2.32794682x | 1.07487940x | 0.000000 |
| 256 | 6.66440336x | 2.90892218x | 1.10496448x | 0.000000 |
| 314 | 6.92114569x | 2.55932479x | 1.08996855x | 0.000000 |
| 42 | 6.76350531x | 2.48579114x | 1.08515466x | 0.000000 |
| 77 | 6.88232019x | 2.53200819x | 1.09355881x | 0.000000 |

## Aggregate

- Router versus nurture under stress mean: `6.80870099x`
- Router versus sentinel under calm mean: `2.61898962x`
- Router versus best fixed overall mean: `1.09279677x`
- Router failure rate mean: `0.0`

## Interpretation

The router preserves the reflective nurture path during calm probes and switches to the protected sentinel path during stress probes. In this toy setup, that mixed policy outperforms either fixed strategy alone.

## Boundary

This is mechanism evidence. The harness provides the stress value, so this tests routing behavior rather than autonomous stress detection.
