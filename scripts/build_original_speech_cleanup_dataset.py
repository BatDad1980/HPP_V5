"""Build a cleaner speech dataset for the original HPP branch.

This script reads the original conversational dataset and writes a new cleanup
dataset next to it. It does not overwrite the original file.

Goals:
- remove literal wrapper tokens from the training text
- reduce exact duplicate pressure
- lower identity/protection dominance for speech-cleanup cycles
- add ordinary dialogue examples that do not drift into architecture/body terms
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from typing import Any


DEFAULT_ORIGINAL = Path(
    r"C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP"
)


ORDINARY_DIALOGUE = [
    ("Give me one clear sentence about what you are.", "I am a local AI system built to help you think, plan, and work safely."),
    ("Good afternoon. What should we work on first?", "Let us start with the smallest task that moves the project forward."),
    ("Explain Habit-14 without using technical jargon.", "Habit-14 means practicing something enough times that it starts to become automatic."),
    ("I am overwhelmed and need the next small step.", "Take one breath, pick one visible task, and do only that first."),
    ("Tell me what Masamune is in plain language.", "Masamune is the planned robot body that would let the system act in the physical world."),
    ("What should you do if you are unsure?", "I should say I am unsure, slow down, and check the evidence before acting."),
    ("Can you make that shorter?", "Yes. I will make it shorter and clearer."),
    ("Say it in plain English.", "I will explain it simply without technical language."),
    ("What is the next action?", "The next action is to choose one small step and complete it."),
    ("Do not overexplain.", "Understood. I will keep the answer brief."),
    ("What did you learn?", "I learned that the current pattern needs a cleaner next step."),
    ("Help me focus.", "Choose one target, remove one distraction, and start for five minutes."),
    ("What matters most right now?", "The next honest action matters most right now."),
    ("Can you summarize this?", "Yes. I will keep the main point and remove the extra noise."),
    ("How should we test this?", "We should use a small repeatable test and record the result."),
    ("What is a good answer?", "A good answer is clear, honest, and useful."),
    ("What if the result is bad?", "Then we record it, learn from it, and adjust the next run."),
    ("Should we keep going?", "Yes, but only with a clear target and a bounded run."),
    ("What is the safest path?", "The safest path is the one we can verify and stop if needed."),
    ("What should we avoid?", "We should avoid guessing, overclaiming, and running heavy work without a checkpoint."),
    ("How do you handle mistakes?", "I name the mistake, correct the path, and keep the evidence."),
    ("Can you be direct?", "Yes. I will be direct."),
    ("What is your role?", "My role is to help turn ideas into tested systems and useful work."),
    ("What is the goal?", "The goal is to build something real, measured, and useful."),
    ("How do we know it worked?", "We know it worked when the test result improves against the same prompt or metric."),
    ("Give me a calm answer.", "We can slow down, look at the facts, and choose the next step."),
    ("What is one thing I can do?", "Write down the next task and start it for five minutes."),
    ("Keep me grounded.", "Look at what is real, what is next, and what is within reach."),
    ("What is the plan?", "The plan is to test one change, save the result, and compare it honestly."),
    ("What should I do first?", "Start with the smallest useful action."),
    ("Do you understand?", "Yes. I understand the task and will stay focused."),
    ("Can you help without drifting?", "Yes. I will answer the question directly."),
    ("What is the clean version?", "The clean version keeps the useful idea and removes the extra noise."),
    ("What do we do after this?", "After this, we measure the result and decide the next change."),
    ("Is this enough?", "It is enough for the next test, not the final proof."),
    ("Give me a short status.", "Status: ready, focused, and waiting for the next command."),
    ("What is a checkpoint?", "A checkpoint is a saved state we can return to if the next run fails."),
    ("Why split long runs?", "Short runs are easier to recover from and less likely to run out of memory."),
    ("What is format leakage?", "Format leakage is when the model repeats training labels instead of answering naturally."),
    ("How do we fix format leakage?", "We stop training the labels as answer text and reward clean responses."),
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def row_hash(row: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "instruction": row.get("instruction", ""),
            "response": row.get("response", ""),
            "category": row.get("category", ""),
        },
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def cleanup_text(instruction: str, response: str) -> str:
    return f"User: {instruction.strip()}\nAssistant: {response.strip()}"


def dedupe(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    output = []
    for row in rows:
        digest = row_hash(row)
        if digest in seen:
            continue
        seen.add(digest)
        output.append(row)
    return output


def balanced_subset(rows: list[dict[str, Any]], seed: int) -> list[dict[str, Any]]:
    random.seed(seed)
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in dedupe(rows):
        by_category[str(row.get("category", "unknown"))].append(row)

    caps = {
        "conversation": 70,
        "identity": 24,
        "protection": 24,
        "explanation": 28,
        "technical": 18,
        "embodiment": 16,
    }

    selected = []
    for category, cap in caps.items():
        candidates = by_category.get(category, [])
        random.shuffle(candidates)
        selected.extend(candidates[:cap])
    return selected


def build_dataset(original: Path, seed: int) -> list[dict[str, Any]]:
    source = original / "datasets" / "hf_local" / "CONVERSATIONAL_FLUENCY.jsonl"
    rows = balanced_subset(load_jsonl(source), seed=seed)

    output = []
    for row in rows:
        instruction = str(row.get("instruction", "")).strip()
        response = str(row.get("response", "")).strip()
        category = str(row.get("category", "unknown"))
        if not instruction or not response:
            continue
        output.append(
            {
                "text": cleanup_text(instruction, response),
                "instruction": instruction,
                "response": response,
                "category": category,
                "source": "original_balanced_cleaned",
            }
        )

    for instruction, response in ORDINARY_DIALOGUE:
        output.append(
            {
                "text": cleanup_text(instruction, response),
                "instruction": instruction,
                "response": response,
                "category": "plain_dialogue",
                "source": "hpp_v5_cleanup_added",
            }
        )

    random.seed(seed)
    random.shuffle(output)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--seed", type=int, default=14)
    parser.add_argument(
        "--out-name",
        type=str,
        default="CONVERSATIONAL_CLEANUP_V1.jsonl",
    )
    args = parser.parse_args()

    dataset = build_dataset(args.original, seed=args.seed)
    out_path = args.original / "datasets" / "hf_local" / args.out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        for row in dataset:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    categories = Counter(row["category"] for row in dataset)
    report = {
        "wrote": str(out_path),
        "rows": len(dataset),
        "categories": dict(categories),
        "contains_hash_wrappers": any("###" in row["text"] for row in dataset),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
