# Superlinear / Subquadratic Integration Note

## Source

- Hugging Face model: https://huggingface.co/concavity-ai/superlinear-exp-v0.1
- GitHub repo: https://github.com/concavity-ai/superlinear

## What It Is

Superlinear is a research-preview long-context inference stack built around Superlinear Multi-Step Attention.

The key architectural idea is to reformulate causal self-attention as a multi-step search problem:

- accumulate prefix context,
- search a sublinear number of candidate spans,
- attend within selected spans,
- combine span outputs.

The current baseline implementation is described as `O(L^(3/2))` for span search and span attention, while preserving random context access through content-dependent routing.

## What HPP Cares About

HPP does not need the released model weights.

The useful asset is the code pattern:

- routed span search,
- local sliding-window attention,
- selected-span attention,
- top-k span aggregation,
- grouped-query attention support,
- Triton kernels,
- hardware-aware fallback choices,
- stateful sessions,
- snapshots,
- explicit KV/cache lifetime management.

That code points toward how HPP could build a long-sequence memory layer without dense quadratic attention.

## Current Practical Boundary

The released model is not a laptop-scale HPP component today and should not be the first integration target.

Important constraints:

- 32B parameter experimental model,
- custom remote code required,
- CUDA-only path,
- model weights require roughly 60GB VRAM at 16-bit precision,
- KV cache uses roughly 6GB per million tokens per active session,
- B200 / large-memory GPU class is the current natural target,
- release is an architecture and systems feasibility artifact, not production-quality.

Do not represent the released model as ready to run on the RTX 4050 HPP field laptop.

The codebase itself is Apache-2.0, while the released model weights use NVIDIA's open model license. Keep those separate.

## Why It Matters To HPP

The mechanism is highly relevant to HPP because HPP needs long-sequence memory without brute-force dense attention.

Potential HPP insertion points:

1. **Telemetry Sequence Memory**
   - long HPP state logs,
   - robotics telemetry,
   - soft-stop history,
   - repeated route transitions.

2. **Sentinel Trend Prediction**
   - detect drift toward instability,
   - identify pre-failure sequences,
   - distinguish normal high-intensity operation from real redline behavior.

3. **Robotics Episode Review**
   - inspect long Unitree / LeRobot / simulation episodes,
   - find failure precursors,
   - summarize intervention points,
   - preserve long-range context without dropping early events.

4. **IP Portfolio Memory**
   - search across long patent, architecture, source, and evidence documents,
   - preserve random access to older context,
   - support buyer-room diligence without re-prefilling every turn.

5. **Codebase Memory**
   - large repository analysis,
   - multi-file architectural reasoning,
   - session/snapshot reuse across development work.

## HPP Landing-Pad Plan

HPP should prepare an interface and local toy implementation path rather than depend on their model.

### Stage 1: Abstract Sequence Memory Interface

Define an HPP interface that can accept:

- state sequence,
- timestamps,
- event tags,
- evidence hashes,
- optional text context,
- query.

Return:

- relevant spans,
- risk score,
- summary,
- recommended HPP route,
- evidence references.

### Stage 2: Local Baseline

Implement a small local baseline first:

- sliding window,
- GRU/refiner,
- simple retrieval over event chunks,
- HPP developmental memory.

### Stage 3: HPP Span-Router Prototype

Build a small HPP-native prototype inspired by the public Superlinear code pattern:

- represent HPP events as embeddings,
- maintain recent local window access,
- score candidate historical anchors,
- choose top-k spans,
- summarize selected spans,
- route through Sentinel/BACL.

The first version can be pure PyTorch and CPU/CUDA-light. Triton kernels are a later optimization, not the starting point.

### Stage 4: Optional Superlinear Code Adapter

When hardware or quantized release permits:

- inspect Apache-2.0 code modules directly,
- reuse or adapt only pieces that fit HPP,
- keep attribution and license boundaries,
- benchmark against the HPP-native prototype.

### Stage 5: Evidence Comparison

Compare:

- local window baseline,
- GRU sequence baseline,
- retrieval baseline,
- HPP developmental memory,
- HPP span-router prototype,
- optional Superlinear-code adapter.

Metrics:

- max context length,
- prefill cost,
- decode latency,
- GPU memory,
- retrieval accuracy,
- soft-stop prediction quality,
- route accuracy,
- session resume behavior.

## Safety Boundary

Superlinear should not be placed in a live robot control loop.

The correct placement is above control:

`telemetry / evidence -> long-context sequence memory -> HPP route -> Sentinel/BACL gate -> approved high-level policy`

It may help decide when to pause, inspect, summarize, or route. It should not directly produce motor commands.

## Buyer-Safe Claim

HPP V5 has identified a plausible public subquadratic code pattern for evidence memory, robotics episode review, and Sentinel trend prediction.

HPP V5 has not yet integrated or benchmarked Superlinear code locally.

HPP V5 does not need the released Superlinear model weights for this path.
