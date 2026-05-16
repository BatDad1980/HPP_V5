# Named Baseline Sweep Summary

This sweep repeats the named-baseline attractor-recovery comparison across multiple seeds.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Seeds: `14, 21, 42, 77, 101, 133, 144, 199, 256, 314, 377, 512, 777, 1024, 1337`
- Classes: `24`
- Dimension: `384`
- Evaluation noise: `1.45`

## Result

- HPP MSE win rate: `0.0`
- HPP accuracy win rate: `1.0`
- Best-baseline-to-HPP MSE ratio mean: `0.91343651x`
- HPP accuracy minus best baseline mean: `0.03271123`
- Peak allocated CUDA memory max: `103.958 MB`
- HPP stored memory values: `9240`
- MLP parameters: `1181568`
- GRU parameters: `3249792`

## Interpretation

This setting separates coordinate reconstruction from pathway recognition. HPP did not win mean MSE here, but it did win the class/pathway recovery metric across the tested seeds.

## Boundary

This is still a synthetic mechanism sweep. It strengthens repeatability for this task only; it does not prove broad model superiority, language ability, production safety, or a fixed efficiency multiple.
