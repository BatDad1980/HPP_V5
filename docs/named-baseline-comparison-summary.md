# Named Baseline Comparison Summary

This synthetic harness compares HPP developmental memory against named baseline mechanisms on held-out noisy attractor recovery.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Classes: `24`
- Dimension: `192`
- Evaluation noise: `1.35`

## Baselines

- Nearest-centroid prototype memory
- One-pass MLP denoiser
- GRU recurrent refiner

## Result

- Best baseline by MSE: `gru_refiner`
- HPP MSE: `0.03431235`
- Best baseline MSE: `0.03751529`
- Best-baseline-to-HPP MSE ratio: `1.09334656x`
- HPP accuracy: `0.47222223`
- Best baseline accuracy: `0.40277779`
- HPP mean latency: `1.75630417 ms`
- HPP stored memory values: `4632`
- MLP parameters: `295872`
- GRU parameters: `813888`

## Boundary

This is mechanism evidence only. The HPP path receives trusted clean anchors after an early noisy period, while the MLP and GRU baselines receive supervised clean targets during gradient training. It compares toy attractor-recovery behavior under synthetic noise. It does not prove language ability, general intelligence, production safety, or a fixed efficiency multiple.
