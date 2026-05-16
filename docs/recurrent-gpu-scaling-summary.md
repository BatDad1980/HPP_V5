# Recurrent GPU Scaling Summary

This benchmark probes the HPP recurrent workshop envelope on the local plugged-in GPU.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Passes: `14`
- Runs per size: `1`

## Results

| Dim | Batch | Parameters | Mean ms | Peak MB | Steps/sec | Status |
| ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 4096 | 2 | 100687872 | 114.3853 | 393.438 | 244.787 | ok |
| 8192 | 2 | 402702336 | 141.8474 | 1545.75 | 197.395 | ok |
| 12288 | 2 | 906043392 | 318.0524 | 3466.062 | 88.036 | ok |
| 15360 | 2 | 1415669760 | 457.0935 | 5410.297 | 61.257 | ok |
| 17408 | 2 | 1818335232 | 4306.4649 | 6946.453 | 6.502 | ok |
| 18432 | 2 | 2038542336 | 6240.978 | 7786.531 | 4.486 | ok |
| 19456 | 2 | 2271332352 | 8555.7338 | 8674.609 | 3.273 | ok |

## Largest Successful Size

- Dimension: `19456`
- Batch: `2`
- Parameters: `2271332352`
- FP32 parameter footprint: `8664.445 MB`
- Mean latency: `8555.7338 ms`
- Peak allocated CUDA memory: `8674.609 MB`

## Boundary

This is inference-only scaling evidence. It does not measure training, optimizer state, checkpoint loading, or model quality.
