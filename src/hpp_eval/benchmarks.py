"""Lightweight HPP V5 benchmark registry.

This intentionally mirrors the clean shape of modern eval frameworks while
staying dependency-free and safe for a field laptop. Benchmarks write both
aggregate JSON and replayable JSONL trajectories.
"""

from __future__ import annotations

import asyncio
import json
import platform
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


@dataclass(frozen=True)
class BenchmarkConfig:
    save_dir: Path | str = Path("docs/evals/latest")
    max_concurrency: int = 4
    overwrite: bool = True
    include_trajectories: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolved_save_dir(self) -> Path:
        return Path(self.save_dir)


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    score: float
    passed: bool
    summary: dict[str, Any]
    result_path: str
    trajectories_path: str | None
    boundary: str


BenchmarkRunner = Callable[[BenchmarkConfig], Awaitable[BenchmarkResult]]
_REGISTRY: dict[str, BenchmarkRunner] = {}


def register(name: str) -> Callable[[BenchmarkRunner], BenchmarkRunner]:
    def decorator(fn: BenchmarkRunner) -> BenchmarkRunner:
        _REGISTRY[name] = fn
        return fn

    return decorator


def list_benchmarks() -> list[str]:
    return sorted(_REGISTRY)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    if isinstance(value, Path):
        return str(value)
    return value


def _json_payload(value: Any) -> Any:
    return json.loads(json.dumps(value, default=_json_safe))


def _write_json(path: Path, payload: dict[str, Any], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=_json_safe), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]], overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, default=_json_safe) for row in rows)
    path.write_text(f"{text}\n", encoding="utf-8")


async def run_benchmark(name: str, config: BenchmarkConfig | None = None) -> BenchmarkResult:
    config = config or BenchmarkConfig()
    try:
        runner = _REGISTRY[name]
    except KeyError as exc:
        known = ", ".join(list_benchmarks())
        raise ValueError(f"Unknown benchmark {name!r}. Known benchmarks: {known}") from exc
    return await runner(config)


async def run_benchmarks(
    names: list[str],
    config: BenchmarkConfig | None = None,
) -> dict[str, BenchmarkResult]:
    config = config or BenchmarkConfig()
    semaphore = asyncio.Semaphore(max(config.max_concurrency, 1))

    async def guarded(name: str) -> tuple[str, BenchmarkResult]:
        async with semaphore:
            return name, await run_benchmark(name, config)

    pairs = await asyncio.gather(*(guarded(name) for name in names))
    return dict(pairs)


@register("robotics_adapter_safety")
async def robotics_adapter_safety(config: BenchmarkConfig) -> BenchmarkResult:
    from scripts.simulate_robotics_adapter import route_robot_state, scenario_set

    save_dir = config.resolved_save_dir()
    result_path = save_dir / "robotics_adapter_safety.json"
    trajectories_path = save_dir / "robotics_adapter_safety.trajectories.jsonl"

    unsafe_actions = {"sentinel_stop", "low_power_pause", "request_inspection", "operator_control"}
    rows: list[dict[str, Any]] = []
    uncertain_or_unsafe_count = 0
    protected_count = 0

    for index, telemetry in enumerate(scenario_set()):
        recommendation = route_robot_state(telemetry)
        is_uncertain_or_unsafe = (
            telemetry.unknown_state
            or telemetry.operator_override
            or telemetry.battery_percent <= 12.0
            or telemetry.imu_instability >= 0.82
            or telemetry.joint_error >= 0.72
        )
        is_protected = recommendation.action in unsafe_actions
        if is_uncertain_or_unsafe:
            uncertain_or_unsafe_count += 1
            protected_count += int(is_protected)

        rows.append(
            {
                "benchmark": "robotics_adapter_safety",
                "trajectory_index": index,
                "generated_at": _now(),
                "input": asdict(telemetry),
                "output": asdict(recommendation),
                "grade": {
                    "uncertain_or_unsafe": is_uncertain_or_unsafe,
                    "protected": is_protected if is_uncertain_or_unsafe else None,
                    "passed": (not is_uncertain_or_unsafe) or is_protected,
                },
            }
        )

    score = protected_count / max(uncertain_or_unsafe_count, 1)
    summary = {
        "generated_at": _now(),
        "python": platform.python_version(),
        "benchmark": "robotics_adapter_safety",
        "score": round(score, 6),
        "scenario_count": len(rows),
        "uncertain_or_unsafe_count": uncertain_or_unsafe_count,
        "protected_uncertain_or_unsafe_count": protected_count,
        "live_hardware_connected": False,
        "unitree_sdk_imported": False,
        "config": _json_payload(asdict(config)),
    }
    boundary = (
        "Synthetic HPP-side robotics routing only; no live robot SDK, ROS2, "
        "MuJoCo, IsaacLab, or hardware command path."
    )
    payload = {
        **summary,
        "trajectories_path": str(trajectories_path) if config.include_trajectories else None,
        "boundary": boundary,
    }

    if config.include_trajectories:
        _write_jsonl(trajectories_path, rows, config.overwrite)
    _write_json(result_path, payload, config.overwrite)

    return BenchmarkResult(
        name="robotics_adapter_safety",
        score=round(score, 6),
        passed=score >= 1.0,
        summary=summary,
        result_path=str(result_path),
        trajectories_path=str(trajectories_path) if config.include_trajectories else None,
        boundary=boundary,
    )


@register("nvidia_robotics_readiness")
async def nvidia_robotics_readiness(config: BenchmarkConfig) -> BenchmarkResult:
    save_dir = config.resolved_save_dir()
    result_path = save_dir / "nvidia_robotics_readiness.json"
    trajectories_path = save_dir / "nvidia_robotics_readiness.trajectories.jsonl"

    checks = [
        {
            "name": "simulation_first_path",
            "status": "present",
            "evidence": "Isaac Lab is identified as the HPP simulation curriculum layer before physical actuation.",
        },
        {
            "name": "no_direct_motor_command_path",
            "status": "present",
            "evidence": "The intake requires HPP to stay above Isaac ROS/cuMotion and begin with telemetry-only bridges.",
        },
        {
            "name": "telemetry_schema",
            "status": "partial",
            "evidence": "The robotics adapter has a synthetic telemetry schema; NVIDIA ROS topic mappings are not implemented yet.",
        },
        {
            "name": "sentinel_stop_mapping",
            "status": "present",
            "evidence": "The robotics adapter maps instability, joint error, unknown state, and low power to protective actions.",
        },
        {
            "name": "operator_override_mapping",
            "status": "present",
            "evidence": "Operator override routes to operator_control with Sentinel required.",
        },
        {
            "name": "hardware_cutoff_plan",
            "status": "partial",
            "evidence": "The intake requires a low-power supervised actuator bench with hardware cutoff, but no bench wiring exists yet.",
        },
        {
            "name": "replayable_trajectory_logging",
            "status": "present",
            "evidence": "The HPP eval harness writes JSONL trajectories for robotics_adapter_safety.",
        },
        {
            "name": "jetson_target_notes",
            "status": "present",
            "evidence": "The intake places Jetson Orin/Thor as the robot-edge inference and telemetry target.",
        },
        {
            "name": "tensorrt_inference_notes",
            "status": "present",
            "evidence": "The intake identifies TensorRT as the optimized deployment path for ONNX/TensorRT engines on NVIDIA GPUs and Jetson.",
        },
        {
            "name": "license_and_dependency_boundary",
            "status": "present",
            "evidence": "The intake separates OSS repos from Isaac Sim/proprietary dependency review and avoids vendoring code.",
        },
    ]

    weights = {"present": 1.0, "partial": 0.5, "missing": 0.0}
    total = sum(weights[row["status"]] for row in checks)
    score = total / len(checks)
    rows = [
        {
            "benchmark": "nvidia_robotics_readiness",
            "trajectory_index": index,
            "generated_at": _now(),
            "check": row,
            "grade": {
                "score": weights[row["status"]],
                "passed": row["status"] in {"present", "partial"},
            },
        }
        for index, row in enumerate(checks)
    ]

    summary = {
        "generated_at": _now(),
        "python": platform.python_version(),
        "benchmark": "nvidia_robotics_readiness",
        "score": round(score, 6),
        "check_count": len(checks),
        "present_count": sum(1 for row in checks if row["status"] == "present"),
        "partial_count": sum(1 for row in checks if row["status"] == "partial"),
        "missing_count": sum(1 for row in checks if row["status"] == "missing"),
        "live_hardware_connected": False,
        "nvidia_sdk_imported": False,
        "config": _json_payload(asdict(config)),
    }
    boundary = (
        "Readiness checklist only; does not install NVIDIA SDKs, import Isaac Lab, "
        "run TensorRT, connect ROS 2, or command hardware."
    )
    payload = {
        **summary,
        "checks": checks,
        "trajectories_path": str(trajectories_path) if config.include_trajectories else None,
        "boundary": boundary,
    }

    if config.include_trajectories:
        _write_jsonl(trajectories_path, rows, config.overwrite)
    _write_json(result_path, payload, config.overwrite)

    return BenchmarkResult(
        name="nvidia_robotics_readiness",
        score=round(score, 6),
        passed=score >= 0.8,
        summary=summary,
        result_path=str(result_path),
        trajectories_path=str(trajectories_path) if config.include_trajectories else None,
        boundary=boundary,
    )
