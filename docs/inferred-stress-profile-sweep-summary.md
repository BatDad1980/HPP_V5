# Inferred Stress Profile Sweep Summary

This summary captures a multi-seed sweep of inferred stress routing with tolerance profiles.

## Setup

- Script: `scripts/compare_inferred_stress_routing.py`
- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- Profiles: `high-intensity, low-tolerance, standard`
- Seeds: `14, 21, 42, 77, 101`

## Aggregate

| Profile | Tap-out mean | Inferred failure mean | Tap-out failure mean | Tap-out/inferred mean | Route accuracy mean |
| :--- | ---: | ---: | ---: | ---: | ---: |
| high-intensity | 0.0 | 0.2 | 0.2 | 1.0x | 0.9 |
| low-tolerance | 0.2 | 0.2 | 0.0 | 2.49136496x | 0.9 |
| standard | 0.2 | 0.2 | 0.0 | 2.49136496x | 0.9 |

## Interpretation

The profile sweep tests whether the same extreme noise is treated differently by different operating-band assumptions. Low and standard profiles should tap out more readily; high-intensity profiles should tolerate more noise but may preserve higher failure risk.

## Boundary

This is synthetic mechanism evidence. The stress and OOD estimators are hand-built and calibrated to this toy harness.
