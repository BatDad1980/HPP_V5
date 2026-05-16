# Named Baseline Sweep Summary

This sweep repeats the named-baseline attractor-recovery comparison across multiple seeds.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Seeds: `14, 21, 42, 77, 101, 133, 144, 199, 256, 314`
- Classes: `24`
- Dimension: `192`
- Evaluation noise: `1.35`

## Result

- HPP MSE win rate: `1.0`
- HPP accuracy win rate: `1.0`
- Best-baseline-to-HPP MSE ratio mean: `1.08667083x`
- HPP accuracy minus best baseline mean: `0.02821181`
- Peak allocated CUDA memory max: `39.811 MB`
- HPP stored memory values: `4632`
- MLP parameters: `295872`
- GRU parameters: `813888`

## Boundary

This is still a synthetic mechanism sweep. It strengthens repeatability for this task only; it does not prove broad model superiority, language ability, production safety, or a fixed efficiency multiple.
