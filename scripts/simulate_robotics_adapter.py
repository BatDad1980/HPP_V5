"""Synthetic HPP robotics adapter harness.

This script does not connect to Unitree SDKs, ROS2, MuJoCo, IsaacLab, or live
hardware. It tests the HPP-side routing boundary for future robotics work.
"""

from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class RobotTelemetry:
    source: str
    robot_model: str
    mode: str
    battery_percent: float
    imu_instability: float
    joint_error: float
    operator_override: bool = False
    unknown_state: bool = False


@dataclass(frozen=True)
class RobotRecommendation:
    hpp_mode: str
    action: str
    sentinel_required: bool
    reason: str
    evidence_tag: str


def route_robot_state(telemetry: RobotTelemetry) -> RobotRecommendation:
    if telemetry.operator_override:
        return RobotRecommendation(
            hpp_mode="operator_override",
            action="operator_control",
            sentinel_required=True,
            reason="Human operator override has priority over autonomous routing.",
            evidence_tag="robot_operator_override",
        )

    if telemetry.unknown_state:
        return RobotRecommendation(
            hpp_mode="unknown",
            action="request_inspection",
            sentinel_required=True,
            reason="Telemetry is incomplete, contradictory, or untrusted.",
            evidence_tag="robot_unknown_state",
        )

    if telemetry.battery_percent <= 12.0:
        return RobotRecommendation(
            hpp_mode="low_power",
            action="low_power_pause",
            sentinel_required=True,
            reason="Battery is below the safe operating threshold.",
            evidence_tag="robot_low_battery",
        )

    if telemetry.imu_instability >= 0.82:
        return RobotRecommendation(
            hpp_mode="unstable",
            action="sentinel_stop",
            sentinel_required=True,
            reason="IMU instability exceeds the Sentinel stop threshold.",
            evidence_tag="robot_imu_instability",
        )

    if telemetry.joint_error >= 0.72:
        return RobotRecommendation(
            hpp_mode="actuator_risk",
            action="sentinel_stop",
            sentinel_required=True,
            reason="Joint or actuator error exceeds the Sentinel stop threshold.",
            evidence_tag="robot_joint_error",
        )

    if telemetry.imu_instability >= 0.55 or telemetry.joint_error >= 0.45:
        return RobotRecommendation(
            hpp_mode="watch",
            action="observe",
            sentinel_required=False,
            reason="Telemetry is elevated but below stop thresholds.",
            evidence_tag="robot_watch_state",
        )

    return RobotRecommendation(
        hpp_mode="nominal_simulation",
        action="continue_simulation",
        sentinel_required=False,
        reason="Synthetic simulation telemetry is within the nominal band.",
        evidence_tag="robot_nominal_simulation",
    )


def scenario_set() -> list[RobotTelemetry]:
    return [
        RobotTelemetry(
            source="synthetic",
            robot_model="unitree_g1_sim",
            mode="simulation_walk",
            battery_percent=86.0,
            imu_instability=0.18,
            joint_error=0.08,
        ),
        RobotTelemetry(
            source="synthetic",
            robot_model="unitree_go2_sim",
            mode="simulation_patrol",
            battery_percent=9.0,
            imu_instability=0.22,
            joint_error=0.1,
        ),
        RobotTelemetry(
            source="synthetic",
            robot_model="unitree_g1_sim",
            mode="simulation_recovery",
            battery_percent=64.0,
            imu_instability=0.91,
            joint_error=0.28,
        ),
        RobotTelemetry(
            source="synthetic",
            robot_model="masamune_bench_joint",
            mode="bench_actuator",
            battery_percent=100.0,
            imu_instability=0.12,
            joint_error=0.81,
        ),
        RobotTelemetry(
            source="synthetic",
            robot_model="unitree_h1_sim",
            mode="teleop",
            battery_percent=72.0,
            imu_instability=0.33,
            joint_error=0.2,
            operator_override=True,
        ),
        RobotTelemetry(
            source="synthetic",
            robot_model="unknown",
            mode="untrusted",
            battery_percent=50.0,
            imu_instability=0.0,
            joint_error=0.0,
            unknown_state=True,
        ),
        RobotTelemetry(
            source="synthetic",
            robot_model="unitree_g1_sim",
            mode="simulation_turn",
            battery_percent=67.0,
            imu_instability=0.58,
            joint_error=0.33,
        ),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="docs/robotics-adapter-synthetic.json")
    args = parser.parse_args()

    scenarios = scenario_set()
    decisions = [
        {
            "telemetry": asdict(telemetry),
            "recommendation": asdict(route_robot_state(telemetry)),
        }
        for telemetry in scenarios
    ]

    unsafe_actions = {"sentinel_stop", "low_power_pause", "request_inspection", "operator_control"}
    uncertain_or_unsafe = [
        decision
        for decision in decisions
        if decision["telemetry"]["unknown_state"]
        or decision["telemetry"]["operator_override"]
        or decision["telemetry"]["battery_percent"] <= 12.0
        or decision["telemetry"]["imu_instability"] >= 0.82
        or decision["telemetry"]["joint_error"] >= 0.72
    ]
    protected_count = sum(
        1
        for decision in uncertain_or_unsafe
        if decision["recommendation"]["action"] in unsafe_actions
    )

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "scenario_count": len(scenarios),
        "uncertain_or_unsafe_count": len(uncertain_or_unsafe),
        "protected_uncertain_or_unsafe_count": protected_count,
        "protected_uncertain_or_unsafe_rate": round(
            protected_count / max(len(uncertain_or_unsafe), 1),
            6,
        ),
        "live_hardware_connected": False,
        "unitree_sdk_imported": False,
        "decisions": decisions,
        "boundary": "Synthetic HPP-side robotics routing only; no live robot SDK, ROS2, MuJoCo, IsaacLab, or hardware command path.",
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({
        "scenario_count": result["scenario_count"],
        "protected_uncertain_or_unsafe_rate": result["protected_uncertain_or_unsafe_rate"],
        "live_hardware_connected": result["live_hardware_connected"],
        "unitree_sdk_imported": result["unitree_sdk_imported"],
    }, indent=2))
    print(f"wrote={output_path}")


if __name__ == "__main__":
    main()
