# Desktop Project Findings

Source analyzed read-only:

`C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP`

This appears to be a later HPP V3 "Sovereign Kinetic" branch, with Claude-era experimentation around agency, embodiment, shop-server deployment, and Masamune robot control.

Generated inventory:

`docs/desktop-hpp-asset-inventory.json`

The desktop source contains 12 PyTorch checkpoints totaling about 2.486 GB, including conversational, linguistic-anchor, and university-specialization checkpoints not present in the protected data-room copy.

## Useful New Material Not Fully Captured In The Data Room Copy

### Sovereign Engine

File: `hpp_sovereign_engine.py`

Useful concepts:

- full developmental stack wiring
- explicit CUDA device selection
- checkpoint priority order
- mission-anchor pass before inference
- university/domain routing
- agency and body-controller hooks
- max-context handling

V5 use:

- keep as architecture reference
- do not import wholesale yet
- harvest checkpoint loading strategy and domain-routing ideas

### Shop Server And Body Split

Files:

- `sovereign_server.py`
- `masamune_main.py`

Useful concepts:

- shop server runs heavyweight cognition
- Jetson body runs real-time control
- WebSocket bridge between brain and body
- REST endpoints for pulse, agency, kinetic commands, proprioception, and status
- body loop at 50 Hz
- network loop at 5 Hz
- autonomous fallback when disconnected
- local pre-programmed stances

V5 use:

- create future robotics adapter boundary
- preserve simulation-first deployment
- keep cognition and safety-critical servo control separated

### Robotics Safety Layer

Files:

- `core/hal/safety_governor.py`
- `core/hal/servo_interpolator.py`
- `core/hal/config/masamune_servo_map.yaml`

Useful concepts:

- soft-touch protocol
- contact force cap
- default speed limits
- proximity speed scaling
- acceleration limiting
- thermal shutdown
- E-stop/watchdog hooks
- cubic interpolation between brain ticks and servo updates
- 19-element command vector
- simulated-by-default servo map

V5 use:

- this is the strongest robotics inheritance
- carry forward as a safety-first contract
- no live hardware path without explicit simulation/live mode separation

### University Cortex And Structural Compass

File: `core/university_core.py`

Useful concepts:

- sinusoidal plus learned positional encoding
- blend gate for fixed/learned position awareness
- domain specialization layers
- soft routing across domains
- output normalization for speech stability

V5 use:

- consider a clean Structural Compass module in the kernel roadmap
- domain routing fits buyer demo and private operating core

### Agency Cortex

File: `core/agency_core.py`

Useful concepts:

- latent action classifier
- argument context vector
- tool registry

Risk:

- direct `exec`
- file writing
- auto-execution threshold
- robot movement action

V5 use:

- preserve as inspiration for private operating core only
- buyer demo must be non-destructive and simulation-only
- all action execution needs permission gates, scopes, audit logs, and dry-run mode

### Mission Anchor

File: `core/mission_anchor.py`

Useful concepts:

- explicit mission constraints
- creator/legacy/protector framing
- deterministic latent filter concept

V5 use:

- translate into configurable values/policy layer
- keep buyer-facing language disciplined
- avoid hardcoded private details in public artifacts

### BACL Vault

File: `core/bacl_vault.py`

Useful concepts:

- integrity verification
- environmental key idea
- checkpoint sealing language

Risk:

- current implementation is a simulated hash/signature pattern, not real tensor encryption

V5 use:

- preserve as future security/integrity module idea
- label clearly as integrity/sealing roadmap until implemented

### TensorRT / Jetson Path

File: `utils/export_tensorrt.py`

Useful concepts:

- ONNX export target
- Jetson Orin NX deployment path
- separate brain/body controller export
- FP16 TensorRT goal

V5 use:

- useful for future robotics deployment roadmap
- do not claim TensorRT speedups until measured in V5

## Strongest Harvest For HPP V5

1. Robotics should be a separate adapter layer, not mixed into the core app.
2. All embodied control must be simulation-first.
3. Safety governor is non-negotiable.
4. Agency must be permissioned, scoped, and auditable.
5. The shop-server/Jetson split is architecturally sound.
6. Domain routing and Structural Compass are worth reimplementing cleanly.
7. BACL should become a security/integrity roadmap module, with honest claim boundaries.

## V5 Guardrail

The desktop project contains powerful private-workbench ideas, but some are too permissive for buyer-facing code.

V5 should preserve the vision while tightening the implementation:

- no uncontrolled `exec`
- no unrestricted file writes
- no live robot commands by default
- no private mission details in public demo layer
- no hardware-safety claims without test evidence
