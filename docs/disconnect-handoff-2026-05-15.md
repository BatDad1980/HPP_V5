# Disconnect Handoff

Date: 2026-05-15

Purpose:

Prepare HPP V5 and the original HPP branch for a clean pause while Brent is away from the workstation.

## Current State

HPP V5 is clean, pushed, and has a working evidence trail.

Latest major commits:

- `e4d0730` Run original speech cleanup experiments
- `c24bba6` Audit original speech curriculum
- `3bb7feb` Add original speech regression harness
- `513b4da` Add HPP evidence ladder
- `84ec808` Add Habit-14 memory harness

## Strongest HPP V5 Evidence

Current buyer-safe evidence:

- RTX 4050 kernel probe with explicit latency and memory logs.
- Shared recurrent workshop uses 14x fewer stored parameters than a 14-layer unique stack in the tiny comparison.
- Iterative stability harness shows repeated shared loops greatly reduce noisy-state error versus one pass with the same parameter count.
- Habit-14 memory harness shows protected recall appears only after the repeated-exposure threshold.
- Evidence ladder consolidates both positive and negative results.

Do not claim:

- full LLM replacement
- human-equivalent cognition
- mature conversational fluency
- a fixed 3000x efficiency number

## Original Branch Speech Work

Original branch:

`C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP`

Current best speech checkpoint remains:

`checkpoints/hpp_linguistic_anchor.pth`

Experimental cleanup checkpoints were created:

- `checkpoints/hpp_speech_cleanup_v1.pth`
- `checkpoints/hpp_speech_cleanup_masked_v2.pth`
- `checkpoints/hpp_speech_cleanup_v3.pth`

Decision:

Do not promote those cleanup checkpoints. They improved some narrow metrics but did not improve held-out speech quality.

## What Worked Today

- Built repeatable speech regression harness.
- Built original dataset audit.
- Built cleanup dataset generator.
- Proved split-cycle training avoids OOM better than monolithic long runs.
- Logged CUDA memory usage for cleanup training.
- Rejected weak checkpoints honestly.

## What To Do Next

When work resumes:

1. Keep HPP V5 as the clean rebuild.
2. Treat the original branch as the fast lab branch.
3. If more speech work happens, run the regression harness after every candidate checkpoint.
4. Do not run another cleanup cycle until the method changes.
5. Next likely speech direction: larger plain-English corpus, stronger held-out validation, and decoding/repetition fixes before additional training.

Useful commands from `X:\HPP_V5`:

```powershell
python scripts\run_original_speech_regression.py --checkpoints hpp_linguistic_anchor.pth --out docs\original-speech-regression.json
python scripts\audit_original_conversation_dataset.py
python scripts\inspect_original_speech_checkpoints.py --out docs\original-speech-checkpoint-inspection.json
npm run build
```

## Power Rule

If unplugged or mobile:

- docs only
- no training
- no checkpoint conversion
- no long inference loops

If plugged in:

- run bounded experiments
- save checkpoints frequently
- log CUDA memory
- prefer restartable cycles

