# HPP Embodied Safety Charter

## Core Statement

HPP exists to turn adaptive intelligence into safer, more accountable action.

The embodied robotics path must preserve the same rule that guides the rest of HPP:

Power is not the goal. Protected usefulness is the goal.

## Design Position

HPP should be developed as an executive safety and evidence layer before it becomes a body-control layer.

That means HPP should first:

- observe state,
- classify operating context,
- recommend high-level mode changes,
- preserve evidence,
- trigger soft stops,
- require human confirmation before real-world escalation.

It should not begin by directly commanding motors, torque, locomotion, or manipulation on live hardware.

## Human-Safety-First Principle

Aural-Nexus systems should be built from a human-safety-first design philosophy:

- preserve identity and continuity,
- respect boundaries,
- detect unstable states early,
- route toward protection before harm occurs,
- log enough evidence to understand what happened,
- keep human override and emergency stop paths first-class.

## Embodiment Boundary

Robotics makes the stakes higher because software decisions can become physical motion.

For that reason, HPP embodied work must proceed in this order:

1. documentation,
2. simulation,
3. telemetry-only observation,
4. bench-scale actuator testing,
5. policy-gated simulated action,
6. human-confirmed limited hardware action,
7. broader autonomy only after evidence gates exist.

## Non-Negotiables

- No live robot autonomy without explicit approval.
- No low-level motor control before simulation and bench proof.
- No bypassing vendor safety systems.
- No uncontrolled overnight hardware operation.
- No command path without a stop path.
- No escalation without evidence logs.

## Buyer-Safe Framing

HPP embodied AI is a safety-gated robotics research path.

The near-term claim is not that HPP can control a humanoid robot. The near-term claim is that HPP can provide a structured executive layer for state interpretation, safe mode routing, evidence logging, and conservative action gating around simulated and future physical robotic systems.

