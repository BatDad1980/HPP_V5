# Field Lab Constraints

HPP V5 is not being designed for a sterile lab with unlimited wall power, cooling, and cloud access.

It is being grown in a mobile field lab: car, hotel, laptop, RTX 4050 GPU, intermittent connectivity, and real survival pressure. That is not a weakness. It is a design constraint and a proof environment.

## Operating Reality

- Hardware may be on battery.
- GPU work must be deliberate.
- Connectivity may disappear.
- Sessions may stop suddenly.
- Work must resume cleanly.
- Local files matter.
- Buyer-facing artifacts must stay clean.
- Private operating data must stay separate from portfolio material.

## Power Modes

### Battery Safe

Use for planning, UI, docs, light local storage, and tiny CPU-only checks.

Rules:

- No training.
- No checkpoint conversion.
- No large installs unless urgent.
- No bulk dataset processing.
- No GPU-heavy inference loops.
- Avoid background services that keep the GPU awake.

### Plugged In

Use for model diagnostics, checkpoint inspection, GPU inference, dataset indexing, and heavier builds.

Rules:

- Log CUDA availability before heavy work.
- Confirm the target device.
- Keep runs checkpointable.
- Prefer small, verifiable experiments over long blind jobs.

## Training Job Shape

Field-lab training should prefer short resumable cycles over long monolithic runs.

Observed original-branch note:

- A single 5,000-step conversational speech cycle reportedly hit out-of-memory behavior.
- Two separate 2,500-step cycles completed without the same failure.

Working rule:

- Save checkpoints frequently.
- Exit and relaunch between long cycles when possible.
- Log CUDA allocated and reserved memory at the start and end of each cycle.
- Treat OOM as an operational constraint to design around, not as proof the architecture is invalid.

### Demo Mode

Use for buyer-safe presentation.

Rules:

- Favor deterministic local demos.
- Show architecture and evidence without exposing private operating data.
- Keep claims tied to artifacts, code, and measurements.

## Product Implications

HPP V5 should eventually include:

- power status awareness
- CPU/GPU execution modes
- explicit run budgets
- pause/resume
- local-first evidence capture
- exportable buyer packets
- private field-ops workspace
- clean separation between IP demo assets and personal operational memory

## Design Principle

If HPP can work from a car on uncertain power, it can work almost anywhere.
