# Original Conversation Dataset Audit

Run date: 2026-05-15

Artifacts:

- Script: `scripts/audit_original_conversation_dataset.py`
- JSON report: `docs/original-conversation-dataset-audit.json`
- Source dataset: `C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP\datasets\hf_local\CONVERSATIONAL_FLUENCY.jsonl`

## Why This Audit Exists

The original branch speech regression showed sentence-shaped output, but also:

- `### Response` leakage
- topic blending
- overuse of architecture, Masamune, Creator, shop, and servo vocabulary

The audit checks whether the dataset itself is teaching those behaviors.

## Findings

Dataset size: 273 rows

Category mix:

| Category | Rows | Percent |
|---|---:|---:|
| conversation | 85 | 31.14% |
| identity | 75 | 27.47% |
| protection | 60 | 21.98% |
| embodiment | 20 | 7.33% |
| explanation | 18 | 6.59% |
| technical | 15 | 5.49% |

Structural findings:

- 100.0% of rows contain the `### Instruction` / `### Response` wrapper.
- 90 exact duplicate rows were found across 45 duplicate groups.
- Ordinary conversation rows without identity/body/shop drift terms make up only 23.81% of the full dataset.

Most common drift terms in responses:

| Term | Response count |
|---|---:|
| architect | 46 |
| creator | 34 |
| shop | 25 |
| sovereign | 21 |
| masamune | 19 |
| servo | 16 |
| mission anchor | 15 |

## Interpretation

The current speech behavior is curriculum-shaped.

The model leaks `### Response` because every training row teaches that token sequence as part of the text. It drifts into identity, architecture, and embodiment because almost half the dataset is identity/protection, and those rows are intentionally duplicated for emphasis.

That emphasis makes sense for mission anchoring, but it is too strong for the current goal: clean sentence formation and ordinary dialogue.

## Next Training Recommendation

The next original-branch speech cycles should not simply add more steps.

Recommended cycle:

1. Keep the deep HPP stack frozen.
2. Use response-only loss masking, or remove the wrapper tokens from the loss target.
3. Reduce duplicate identity/protection emphasis during speech-cleanup.
4. Add more ordinary dialogue where the correct answer does not mention Creator, Masamune, shop, servos, or architecture.
5. Run `scripts/run_original_speech_regression.py` after each cycle.
6. Track format leakage as a first-class metric.

Success criteria for the next speech pass:

- 0 of 6 held-out prompts leak `### Response`.
- At least 4 of 6 held-out prompts answer the actual user request.
- No response repeats a bigram more than twice.
- Plain-language prompts produce plain-language answers.

