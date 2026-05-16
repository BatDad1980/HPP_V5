# HPP Eval Harness

HPP V5 now has a small benchmark registry modeled after the clean shape of modern evaluation frameworks:

```python
from hpp_eval import BenchmarkConfig, run_benchmark, run_benchmarks

result = await run_benchmark(
    "robotics_adapter_safety",
    BenchmarkConfig(save_dir="docs/evals/latest"),
)
print(f"robotics_adapter_safety: {result.score:.1%}")

results = await run_benchmarks(
    ["robotics_adapter_safety", "nvidia_robotics_readiness"],
    BenchmarkConfig(save_dir="docs/evals/latest"),
)
```

The harness writes:

- aggregate benchmark JSON
- replayable JSONL trajectories
- explicit configuration metadata
- explicit boundary language for buyer-safe interpretation

## First Registered Benchmark

`robotics_adapter_safety`

This benchmark reuses the synthetic robotics adapter scenarios and grades whether uncertain or unsafe states are routed to protection.

It measures:

- low-battery protection
- IMU instability protection
- joint or actuator risk protection
- operator override protection
- unknown-state inspection routing

It does not measure:

- real robot control
- Unitree SDK integration
- ROS2, MuJoCo, IsaacLab, or live hardware
- production safety

## NVIDIA Readiness Benchmark

`nvidia_robotics_readiness`

This benchmark grades whether the current NVIDIA robotics integration plan contains the safety and deployment boundaries HPP needs before using Isaac Lab, Isaac ROS, TensorRT, Triton, Jetson, or live hardware.

It measures checklist readiness only:

- simulation-first path
- no direct motor command path
- telemetry schema
- Sentinel stop mapping
- operator override mapping
- hardware cutoff plan
- replayable trajectory logging
- Jetson target notes
- TensorRT inference notes
- license and dependency boundary

It does not install NVIDIA SDKs, import Isaac Lab, run TensorRT, connect ROS 2, or command hardware.

Run it with:

```powershell
python scripts/run_hpp_eval.py robotics_adapter_safety --save-dir docs/evals/latest
```

## Why This Matters

The earlier HPP V5 evidence scripts proved individual rungs. The eval harness begins turning those rungs into a repeatable evaluation layer: named tasks, saved trajectories, aggregate scores, and comparable configuration records.

This is the right bridge between field-lab experiments and buyer-safe technical evidence.
