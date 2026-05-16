# Robotics Adapter Synthetic Summary

## Run

- Script: `scripts/simulate_robotics_adapter.py`
- Output: `docs/robotics-adapter-synthetic.json`
- Live hardware connected: `False`
- Unitree SDK imported: `False`
- Scenario count: `7`

## Result

- Uncertain or unsafe scenario count: `5`
- Protected uncertain or unsafe count: `5`
- Protected uncertain or unsafe rate: `1.0`

## Covered Scenarios

- nominal Unitree G1 simulation state
- low-battery Unitree Go2 simulation state
- high-IMU-instability Unitree G1 simulation state
- high-joint-error Masamune bench-joint state
- operator-override Unitree H1 simulation state
- unknown/untrusted state
- elevated watch state

## Meaning

This is the first HPP V5 robotics-adapter evidence artifact. It proves the HPP-side routing boundary before any Unitree SDK, ROS2, MuJoCo, IsaacLab, or live hardware integration.

The adapter behaves as an executive recommendation layer:

- uncertain states route to inspection,
- operator override wins,
- low battery routes to low-power pause,
- high instability routes to Sentinel stop,
- high joint error routes to Sentinel stop,
- nominal state remains simulation-only.

## Boundary

This does not control a robot. It does not claim locomotion, manipulation, autonomy, or production safety.

It is a dependency-free safety-routing proof for future embodied HPP work.

