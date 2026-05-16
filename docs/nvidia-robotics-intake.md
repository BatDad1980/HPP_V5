# NVIDIA Robotics Intake

This note captures the first HPP V5 intake of NVIDIA public robotics and inference assets.

The goal is not to clone the whole NVIDIA ecosystem. The goal is to identify the parts that can become a clean bridge from HPP V5 evidence to simulation, robot perception, edge deployment, and safety-gated embodied AI.

## Primary Sources

- NVIDIA GitHub organization: https://github.com/NVIDIA
- NVIDIA Isaac ROS organization: https://github.com/NVIDIA-ISAAC-ROS
- NVIDIA Isaac organization: https://github.com/nvidia-isaac
- Isaac Lab: https://github.com/isaac-sim/IsaacLab
- Triton Inference Server: https://github.com/triton-inference-server/server

## Highest-Fit Repositories

### Isaac Lab

Repository: https://github.com/isaac-sim/IsaacLab

Fit:

- robot-learning simulation
- reinforcement learning
- imitation learning
- motion planning experiments
- sim-to-real staging

HPP use:

Isaac Lab is the best candidate for a future HPP simulation curriculum. It can provide simulated episodes before any real robot is allowed to move. HPP can sit above policies as a developmental executive, reading episode telemetry, grading state transitions, and enforcing Sentinel tap-out behavior.

Boundary:

Isaac Lab depends on Isaac Sim and GPU-heavy simulation. It is not the first thing to run on the current laptop during battery/mobile work. It belongs in the plugged-in desktop/server or Jetson lab roadmap.

### Isaac ROS

Organization: https://github.com/NVIDIA-ISAAC-ROS

Fit:

- ROS 2 robotics packages
- Jetson-targeted acceleration
- perception, localization, mapping, manipulation, teleoperation

HPP use:

Isaac ROS is the deploy-side bridge. Once HPP has a stable simulated robotics adapter, Isaac ROS can provide the robot middleware layer that connects perception, odometry, planning, and actuator-side control.

Boundary:

HPP should not call Isaac ROS control or motion packages directly at first. The first bridge should be telemetry-only, then simulation-only action proposals, then supervised physical testing.

### Isaac ROS Visual SLAM

Repository: https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_visual_slam

Fit:

- visual-inertial odometry
- GPS-denied localization
- camera plus IMU sensor fusion

HPP use:

This is a strong source for future robot self-location telemetry. HPP does not need to implement SLAM. HPP needs to know when odometry is reliable, inconsistent, degraded, or unsafe.

Boundary:

SLAM is perception infrastructure, not cognition. HPP should consume summarized confidence and drift signals before it ever consumes raw camera streams.

### Isaac ROS Nvblox

Repository: https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_nvblox

Fit:

- GPU-accelerated 3D scene reconstruction
- navigation costmaps
- obstacle and free-space reasoning

HPP use:

Nvblox can become the future spatial-risk source. HPP can use costmap or obstacle summaries to route between continue, observe, pause, and Sentinel stop.

Boundary:

The first HPP V5 robotics benchmark should stay synthetic. Nvblox belongs after simulation and sensor-stack setup.

### Isaac ROS cuMotion

Repository: https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_cumotion

Fit:

- arm motion planning
- inverse kinematics
- MoveIt 2 integration
- simulated and physical robot trajectories

HPP use:

cuMotion is a candidate for Masamune arm planning or bench-actuator development. HPP should sit above it as a permissioning and evaluation layer, not replace the motion planner.

Boundary:

No unsupervised physical actuation. First use should be visualization, then Isaac Sim trajectory execution, then benched low-power tests with physical cutoff.

### Isaac ROS DNN Inference

Repository: https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_dnn_inference

Fit:

- TensorRT and Triton-backed DNN inference in ROS 2
- robot perception model deployment
- Jetson and CUDA-capable x86 targets

HPP use:

This is useful when HPP needs a perception model in the robot loop. HPP can treat DNN outputs as evidence signals rather than letting perception output directly become action.

Boundary:

DNN perception confidence is not safety. HPP should require cross-checks, Sentinel thresholds, and operator override paths.

### Triton Inference Server

Repository: https://github.com/triton-inference-server/server

Fit:

- multi-backend inference serving
- TensorRT, ONNX, PyTorch, Python backend
- dynamic batching, model control, metrics
- cloud, edge, embedded deployment

HPP use:

Triton is a deployment candidate for HPP-adjacent models, perception models, and future state estimators. Its Python backend could host HPP evaluation or routing components while heavier neural pieces run through TensorRT or ONNX.

Boundary:

Triton is infrastructure. It does not validate the HPP hypothesis by itself. Use it only when the project needs serving, metrics, model lifecycle control, or multi-model composition.

## Recommended HPP Stack Shape

1. HPP V5 Eval Harness

   Named benchmarks, trajectories, aggregate scores, and boundary language.

2. Synthetic Robotics Adapter

   Current dependency-free safety routing.

3. Isaac Lab / MuJoCo Simulation

   Episode generation, simulated policies, safe action proposals, no physical robot.

4. Isaac ROS Telemetry Bridge

   ROS 2 topics summarized into HPP-safe state packets.

5. Triton / TensorRT Inference Cell

   Optional serving layer for perception or HPP-adjacent models.

6. Jetson Edge Deployment

   Orin/Thor class target for robot-local inference and telemetry routing.

7. Physical Actuator Bench

   Low-power supervised test rig with hardware cutoff, logging, and operator override.

## HPP Design Rule

NVIDIA provides the body-side nervous system:

- perception
- localization
- mapping
- simulation
- motion planning
- model serving
- edge acceleration

HPP provides the executive layer:

- developmental memory
- Habit-14 stabilization
- stress/tolerance profile routing
- Sentinel tap-out
- BACL-aligned evidence logging
- operator override respect
- no-action decisions

The clean architecture is not HPP versus NVIDIA. It is HPP above NVIDIA: a safety-gated developmental executive sitting on top of proven robotics infrastructure.

## Near-Term Action

Add an `nvidia_robotics_readiness` benchmark later that does not install or run NVIDIA SDKs. It should grade whether a proposed robotics integration includes:

- simulation-first path
- no direct motor command path
- telemetry schema
- Sentinel stop mapping
- operator override mapping
- hardware cutoff plan
- replayable trajectory logging
- Jetson target notes

This keeps the next step buyer-safe, laptop-safe, and aligned with the current HPP evidence harness.
