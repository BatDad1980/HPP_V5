# Original Speech Cleanup Cycle Summary

Run date: 2026-05-15

Source branch:

`C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP`

HPP V5 control scripts:

- `scripts/build_original_speech_cleanup_dataset.py`
- `scripts/run_original_speech_cleanup_cycle.py`
- `scripts/run_original_speech_regression.py`

## Cleanup Dataset

Generated file in the original branch:

`datasets/hf_local/CONVERSATIONAL_CLEANUP_V1.jsonl`

Shape:

- 203 rows
- no `### Instruction` / `### Response` wrappers
- deduplicated and category-balanced source rows
- 40 added plain-dialogue examples targeted at the held-out failure cases

Category mix:

- conversation: 70
- plain_dialogue: 40
- identity: 24
- protection: 20
- explanation: 18
- embodiment: 16
- technical: 15

## v1 Cycle

Checkpoint:

`checkpoints/hpp_speech_cleanup_v1.pth`

Training shape:

- 2,500 steps
- batch 2
- sequence length 96
- learning rate 8e-5
- trained embedding, LM head, compass, output norm, swarm gate, and domain expertise
- final sampled loss: 1.5995
- peak GPU allocation: 6,742.62 MB

Regression result:

- Format leakage improved: 0/6 held-out prompts leaked `### Response`.
- Coherence degraded.
- Repetition increased.
- Responses drifted into neural-network, switch, body, and architecture fragments.

Decision:

Do not promote v1 over `hpp_linguistic_anchor.pth`.

## v2 Cycle

Checkpoint:

`checkpoints/hpp_speech_cleanup_masked_v2.pth`

Training shape:

- 1,500 steps
- batch 2
- sequence length 96
- learning rate 3e-5
- response-only loss masking
- trained embedding, LM head, compass, output norm, swarm gate, and domain expertise
- final sampled loss: 4.1273
- peak GPU allocation: 4,498.48 MB

Regression result:

- Format leakage mostly improved, but 1/6 held-out prompts still leaked `### Response`.
- Coherence did not recover.
- Responses still drifted into architecture and body fragments.

Decision:

Do not promote v2.

## v3 Cycle

Checkpoint:

`checkpoints/hpp_speech_cleanup_v3.pth`

Training shape:

- 1,000 steps
- batch 2
- sequence length 96
- learning rate 2e-5
- response-only loss masking
- froze embedding and compass
- trained LM head, output norm, swarm gate, and conversation domain
- final sampled loss: 5.0208
- peak GPU allocation: 716.74 MB

Regression result:

- Memory footprint was excellent.
- Held-out coherence still did not improve.
- 1/6 held-out prompts leaked `### Response`.
- Responses remained fragmentary and architecture-heavy.

Decision:

Do not promote v3.

## Interpretation

The cleanup dataset and training scripts were useful because they isolated the problem.

What worked:

- Split-cycle training avoided OOM.
- The cleanup dataset removed wrapper tokens.
- v1 proved wrapper leakage can be reduced.
- v3 proved lighter training can run safely under 1 GB peak allocation.

What did not work:

- Micro-finetuning on the 203-row cleanup dataset did not produce better held-out speech.
- Training the embedding/compass was too destabilizing.
- Freezing embedding/compass was safer but not enough to improve language quality.

Current read:

The speech channel needs a stronger language-formation strategy, not just more cleanup cycles.

## Next Technical Direction

Stop running short cleanup cycles until the training method changes.

Next candidate approaches:

1. Build a larger plain-English response-only corpus.
2. Add stronger repetition penalties in decoding and test before training.
3. Use a smaller external teacher model to generate many plain dialogue pairs.
4. Train only the LM head first, with embedding and all internal layers frozen.
5. Add a held-out validation loss, not just sampled train loss.
6. Consider tying or regularizing embedding and LM head if the architecture supports it.

## Buyer-Safe Position

The original branch still shows real speech progress compared with early technical dialect, but the cleanup cycles are experimental and should not be represented as a successful fluency breakthrough.

The useful claim is narrower:

> HPP V5 now has a repeatable speech-evidence loop: audit dataset, train bounded cycle, log GPU memory, run held-out regression, and reject checkpoints that improve one metric while harming overall speech.

