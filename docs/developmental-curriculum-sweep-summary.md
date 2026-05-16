# Developmental Curriculum Sweep Summary

This summary captures the first five-seed plugged sweep of the HPP developmental curriculum harness.

## Setup

- Script: `scripts/compare_developmental_curriculum.py`
- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- Seeds: `14`, `21`, `42`, `77`, `101`
- Habit threshold: `14`
- HPP exposures per run: `19`
- HPP protection per run: `0.805`

## Results

| Seed | Clean-context HPP/flat | Shifted-context HPP/flat | Locked |
| ---: | ---: | ---: | :--- |
| 14 | 2.09890963x | 2.02085768x | true |
| 21 | 2.22746360x | 2.07077445x | true |
| 42 | 2.15610204x | 2.07322928x | true |
| 77 | 2.24202786x | 2.13714097x | true |
| 101 | 2.27694201x | 2.12874872x | true |

## Aggregate

- Clean-context improvement range: `2.09890963x` to `2.27694201x`
- Clean-context mean improvement: `2.200289028x`
- Shifted-context improvement range: `2.02085768x` to `2.13714097x`
- Shifted-context mean improvement: `2.08615022x`
- Habit-14 lock rate: `5/5`

## Interpretation

The first sweep suggests the staged HPP path is not a one-seed accident in this toy setup. Across five seeds, staged plasticity plus Habit-14 protection consistently outperformed the flat prototype on both clean and shifted-context recall.

## Boundary

This remains mechanism evidence. The harness is intentionally simple and should not be described as language ability, agency, or general intelligence. The next step is to make the baseline stronger and test changed-context memory rather than only attractor recovery.

