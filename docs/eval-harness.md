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
    ["robotics_adapter_safety"],
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

Run it with:

```powershell
python scripts/run_hpp_eval.py robotics_adapter_safety --save-dir docs/evals/latest
```

## Why This Matters

The earlier HPP V5 evidence scripts proved individual rungs. The eval harness begins turning those rungs into a repeatable evaluation layer: named tasks, saved trajectories, aggregate scores, and comparable configuration records.

This is the right bridge between field-lab experiments and buyer-safe technical evidence.
