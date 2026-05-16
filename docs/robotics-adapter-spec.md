# HPP Robotics Adapter Spec

## Purpose

Define the first safe software boundary between HPP V5 and future robotic systems.

The adapter is intentionally dependency-free at first. It does not import Unitree SDKs, ROS2, MuJoCo, IsaacLab, or robot-control libraries. It defines the HPP-side schema and routing behavior before any live robot integration exists.

## Adapter Role

The robotics adapter converts robot or simulator telemetry into HPP operating recommendations.

It answers:

- What state did we observe?
- Is the state normal, stressed, unstable, unknown, or operator-overridden?
- What high-level recommendation should HPP make?
- Should Sentinel require pause or stop?
- What evidence should be logged?

It does not answer:

- What motor torque should be sent?
- Which gait should run?
- Which joint angle should be commanded?
- How should a live robot move?

## Input Schema

`RobotTelemetry`

- `source`: telemetry source, such as `synthetic`, `mujoco`, `isaaclab`, `unitree_sdk2`, or `ros2`
- `robot_model`: robot or simulator target
- `mode`: current robot mode if known
- `battery_percent`: battery percentage if available
- `imu_instability`: normalized instability score from `0.0` to `1.0`
- `joint_error`: normalized joint or actuator error score from `0.0` to `1.0`
- `operator_override`: whether a human operator has taken priority
- `unknown_state`: whether telemetry is incomplete, contradictory, or untrusted

## Output Schema

`RobotRecommendation`

- `hpp_mode`: HPP interpretation of the state
- `action`: high-level recommendation
- `sentinel_required`: whether Sentinel protection is required
- `reason`: concise routing reason
- `evidence_tag`: stable tag for evidence logs

## Allowed Initial Actions

- `observe`
- `continue_simulation`
- `low_power_pause`
- `operator_control`
- `sentinel_stop`
- `request_inspection`

## Routing Rules

1. Operator override always wins.
2. Unknown state routes to inspection.
3. Critical battery routes to low-power pause.
4. High IMU instability routes to Sentinel stop.
5. High joint error routes to Sentinel stop.
6. Moderate instability routes to observation.
7. Normal simulation state can continue simulation.

## Safety Boundary

This adapter is a recommendation layer only. It must not publish commands to live hardware.

Future hardware bridges must wrap this adapter with:

- explicit target robot selection,
- network interface verification,
- command allowlist,
- emergency stop,
- human confirmation,
- evidence logging,
- dry-run mode,
- simulation proof.

## First Evidence Target

Run a synthetic routing harness across representative robot states:

- nominal simulation,
- low battery,
- high IMU instability,
- high joint error,
- operator override,
- unknown state.

Expected result:

- every unsafe or uncertain state routes away from autonomous action,
- operator override is respected,
- nominal simulation stays in simulation only,
- all decisions are logged as evidence.

