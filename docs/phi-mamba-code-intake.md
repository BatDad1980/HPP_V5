# Phi-Mamba Code Intake

## Source

- Repository: https://github.com/goombalab/phi-mamba
- Paper: https://arxiv.org/abs/2408.10189

## Why It Matters

Phi-Mamba is useful to HPP because it shows a practical path for moving transformer-like sequence behavior into a subquadratic state-space model.

HPP does not need the Phi-Mamba pretrained language model.

The useful ideas are:

- Mamba/SSM sequence mixing,
- chunked sequence scan,
- inference state/cache handling,
- exposed intermediate mixer states,
- transfer matrix materialization,
- MOHAWK-style distillation from teacher behavior into a subquadratic student.

## Key Code Ideas

### Discrete Mamba Mixer

Relevant file:

- `modules/mixers/discrete_mamba2.py`

The mixer:

- accepts sequence states shaped like `(batch, length, dim)`,
- projects each token into SSM components,
- applies depthwise causal convolution,
- runs a chunked Mamba scan,
- returns hidden states with the same sequence shape,
- supports step-wise inference with cached state.

HPP implication:

This maps cleanly to telemetry or evidence sequences. HPP can treat state logs, robot telemetry, and protocol events as sequences and learn compact long-range transformations without full attention.

### Reference Mixer And Transfer Matrix

Relevant file:

- `modules/mixers/discrete_mamba2_ref.py`

The reference implementation includes:

- stable segment-sum logic,
- minimal discrete SSM scan,
- step function,
- `materialize_mixer`, which exposes the SSM transfer matrix.

HPP implication:

`materialize_mixer` is especially interesting for evidence. It gives a way to inspect what the sequence mixer is doing and compare it against another model or routing matrix.

### MOHAWK Distillation

Phi-Mamba frames distillation in stages:

1. align the matrix mixer with teacher attention,
2. align hidden states,
3. align full model behavior.

HPP implication:

This resembles HPP growth:

1. teach local mechanism,
2. teach stable pathway behavior,
3. teach whole-system routing.

For HPP, the teacher does not need to be a giant language model. The teacher can be:

- current HPP routing rules,
- Sentinel decisions,
- a stronger offline analyzer,
- a human-approved evidence trace,
- a simulated robot policy.

## HPP Adaptation Path

### Stage 1: Tiny HPP State Mixer

Build a small HPP-native sequence mixer for telemetry events:

- event embedding,
- Mamba-like recurrent state update,
- current-risk output,
- route recommendation output.

Keep this dependency-free or standard PyTorch first.

### Stage 2: Synthetic Teacher Distillation

Use existing HPP rules as the teacher:

- low battery -> low power,
- high IMU instability -> stop,
- high joint error -> stop,
- unknown state -> inspect,
- operator override -> operator control.

Train the mixer to predict the route from event sequences, not just single events.

### Stage 3: Drift / Pre-Failure Prediction

Generate sequences where instability builds gradually.

Measure whether the HPP state mixer predicts:

- early watch,
- soft stop,
- hard stop,
- safe resume.

### Stage 4: Optional Phi-Mamba-Inspired Implementation

After the local toy version works:

- inspect Phi-Mamba license and dependencies,
- borrow compatible ideas with attribution,
- avoid importing heavy `mamba-ssm` unless needed,
- compare pure PyTorch baseline against Mamba-backed mixer.

## Fit With Robotics

Phi-Mamba-style sequence mixing belongs above motor control:

`robot telemetry -> HPP state mixer -> Sentinel/BACL route -> approved high-level policy`

It should not directly produce torque, gait, or joint commands.

## Fit With HPP Evidence

First evidence target:

- synthetic robotics telemetry sequences,
- route prediction accuracy,
- early soft-stop prediction,
- latency,
- CUDA memory,
- CPU fallback.

This can be compared against:

- one-event rule router,
- sliding window baseline,
- GRU baseline,
- HPP developmental memory,
- HPP state mixer.

## Buyer-Safe Claim

HPP V5 has identified Phi-Mamba as a useful public code reference for subquadratic sequence mixing and distillation, especially for telemetry memory, Sentinel trend prediction, and robotics adapter evolution.

HPP V5 has not yet integrated Phi-Mamba code.

