# Inferred Stress Routing Profile Summary

This follow-up tests HPP stress routing when the router must infer stress from state telemetry and decide whether to keep operating or tap out under extreme out-of-distribution noise.

## Setup

- Script: `scripts/compare_inferred_stress_routing.py`
- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- Trials per profile: `100`
- Route accuracy: `0.90`
- Extreme-noise probe rate: `20%`

## Profiles

| Profile | Tolerance shift | Tap-out rate | OOD mean | OOD max | Inferred failure rate | Tap-out failure rate |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| low-tolerance | -0.22 | 0.20 | 0.17586813 | 0.93628640 | 0.20 | 0.00 |
| standard | 0.00 | 0.20 | 0.13586813 | 0.73628640 | 0.20 | 0.00 |
| high-intensity | 0.48 | 0.00 | 0.04859540 | 0.29992277 | 0.20 | 0.20 |

## Interpretation

The same noise does not mean the same thing for every system.

The low-tolerance and standard profiles detect the extreme noise as out-of-distribution and tap out on 20% of trials. In this synthetic harness, that reduces the tap-out router failure rate to `0.0`.

The high-intensity profile treats the same signal as tolerable operating noise. It does not tap out, which preserves continuous operation but also preserves the inferred router's `0.20` failure rate.

This matches the HPP biological framing:

- a nervous system can adapt to higher baseline intensity
- high tolerance can be useful, especially in harsh or chaotic environments
- high tolerance is not the same as safety
- mature routing needs personalized thresholds, not one universal redline

## Design Lesson

HPP should not assume one global tap-out threshold.

Stress and OOD routing should eventually support profiles such as:

- low tolerance / high protection
- standard tolerance
- high-intensity tolerance
- recovery mode
- guardian mode

The goal is not to force every system into quiet. The goal is to know when a system's normal intensity is still productive, and when the signal has crossed into unsafe novelty.

## Boundary Sweep Follow-Up

Artifact:

- `docs/tapout-boundary-sweep-summary.md`

The first boundary sweep increased extreme-noise scale from `0.8` to `4.0` across three seeds.

Result:

- low-tolerance first tap-out noise: `2.0`
- standard first tap-out noise: `2.0`
- high-intensity first tap-out noise: `2.8`
- low-tolerance max no-tapout noise: `1.6`
- standard max no-tapout noise: `1.6`
- high-intensity max no-tapout noise: `2.4`

Interpretation:

The high-intensity profile tolerated one extra band of unfamiliar noise before tapping out. This supports the idea that profile-specific operating bands need different redlines.

## Boundary

This is synthetic mechanism evidence. The stress and OOD estimators are hand-built telemetry functions calibrated to this toy harness. It does not prove real-world mental-state detection or autonomous clinical safety.
