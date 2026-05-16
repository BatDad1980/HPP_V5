# Developmental Curriculum Sweep Summary

This summary captures a plugged multi-seed sweep of the HPP developmental curriculum harness.

## Setup

- Script: `scripts/compare_developmental_curriculum.py`
- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- Seeds: `101, 133, 14, 144, 199, 21, 256, 314, 42, 77`
- Runs: `10`
- Habit-14 lock rate: `10/10`

## Results

| Seed | HPP/flat clean | HPP/flat shifted | HPP/context-flat clean | HPP/context-flat shifted | Locked |
| ---: | ---: | ---: | ---: | ---: | :--- |
| 101 | 2.27694201x | 2.12874872x | 2.24671439x | 2.03739148x | true |
| 133 | 2.28180370x | 2.13359157x | 2.23771760x | 2.02236966x | true |
| 14 | 2.09890963x | 2.02085768x | 2.09151815x | 1.95518574x | true |
| 144 | 2.20699428x | 2.09318582x | 2.18398875x | 2.01532336x | true |
| 199 | 2.28357421x | 2.14301017x | 2.26268289x | 2.07410327x | true |
| 21 | 2.22746360x | 2.07077445x | 2.20215769x | 2.00804799x | true |
| 256 | 2.22065039x | 2.16745310x | 2.19996737x | 2.06691066x | true |
| 314 | 2.22790222x | 2.09808163x | 2.21766564x | 2.02765789x | true |
| 42 | 2.15610204x | 2.07322928x | 2.15273420x | 2.02287084x | true |
| 77 | 2.24202786x | 2.13714097x | 2.22401315x | 2.07452869x | true |

## Aggregate

- HPP versus flat clean mean: `2.22223699x`
- HPP versus flat shifted mean: `2.10660734x`
- HPP versus context-aware flat clean mean: `2.20191598x`
- HPP versus context-aware flat shifted mean: `2.03043896x`
- Context-aware shifted standard deviation: `0.03613556`

## Interpretation

The stronger context-aware flat baseline receives oracle target/distractor labels and ignores distractor events. HPP still retains a positive margin in this toy setup because maturity-dependent protection changes recall behavior after the Habit-14 lock.

## Boundary

This remains mechanism evidence. The benchmark is synthetic and should be used to guide the next harness, not as a broad capability claim.
