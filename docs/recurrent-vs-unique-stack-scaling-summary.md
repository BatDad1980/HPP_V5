# Recurrent vs Unique Stack Scaling Summary

This benchmark compares shared recurrent depth against a unique-layer stack at the same effective pass count.

## Run

- Mode: `plugged`
- Device: `NVIDIA GeForce RTX 4050 Laptop GPU`
- CUDA available: `True`
- Passes/depth: `14`
- Batch: `2`

## Results

| Dim | Recurrent params | Unique params | Param ratio | Recurrent peak MB | Unique peak MB | Latency ratio | Status |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |
| 1024 | 6297600 | 88166400 | 14.0 | 33.211 | 345.516 | 0.780173 | both ok |
| 2048 | 25178112 | 352493568 | 14.0 | 105.297 | 1353.906 | 1.067306 | both ok |
| 4096 | 100687872 | 1409630208 | 14.0 | 393.469 | 5386.688 | 1.145424 | both ok |
| 8192 | 402702336 | - | - | 1545.812 | - | - | recurrent=ok, unique=cuda_oom |

## Largest Size Where Both Ran

- Dimension: `4096`
- Shared recurrent parameters: `100687872`
- Unique stack parameters: `1409630208`
- Parameter ratio: `14.0x`
- Peak memory ratio: `13.690248x`

## Largest Recurrent Size

- Dimension: `8192`
- Shared recurrent parameters: `402702336`
- Shared recurrent peak memory: `1545.812 MB`

## Boundary

This is inference-only scaling evidence. It does not measure training, optimizer state, learned quality, or production deployment efficiency.
