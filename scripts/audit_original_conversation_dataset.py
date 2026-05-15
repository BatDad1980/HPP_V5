"""Audit the original HPP conversational dataset.

This is read-only. It helps explain speech behavior before spending GPU cycles:
category balance, duplicate pressure, wrapper leakage, and vocabulary drift.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from hashlib import sha256
from pathlib import Path
from statistics import mean, median
from typing import Any


DEFAULT_DATASET = Path(
    r"C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP"
    r"\datasets\hf_local\CONVERSATIONAL_FLUENCY.jsonl"
)

FORMAT_MARKERS = ("### Instruction", "### Response", "Instruction:", "Response:")
DRIFT_TERMS = (
    "architect",
    "creator",
    "masamune",
    "servo",
    "servos",
    "jaxson",
    "journee",
    "sovereign",
    "mission anchor",
    "bushido",
    "shop",
    "robotic",
    "nineteen",
    "japanese",
)


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z']+", text.lower())


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            row["_line"] = line_number
            rows.append(row)
    return rows


def hash_pair(row: dict[str, Any]) -> str:
    payload = json.dumps(
        {
            "instruction": row.get("instruction", ""),
            "response": row.get("response", ""),
            "category": row.get("category", ""),
        },
        sort_keys=True,
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def audit(rows: list[dict[str, Any]]) -> dict[str, Any]:
    categories = Counter(str(row.get("category", "unknown")) for row in rows)
    pair_hashes = Counter(hash_pair(row) for row in rows)
    duplicate_rows = sum(count - 1 for count in pair_hashes.values() if count > 1)
    duplicate_groups = sum(1 for count in pair_hashes.values() if count > 1)

    category_lengths: dict[str, list[int]] = defaultdict(list)
    marker_rows = []
    drift_counts = Counter()
    ordinary_dialogue_rows = 0

    for row in rows:
        category = str(row.get("category", "unknown"))
        response = str(row.get("response", ""))
        text = str(row.get("text", ""))
        category_lengths[category].append(len(words(response)))

        if any(marker in text for marker in FORMAT_MARKERS):
            marker_rows.append(row["_line"])

        lowered = response.lower()
        for term in DRIFT_TERMS:
            if term in lowered:
                drift_counts[term] += 1

        if category == "conversation" and not any(term in lowered for term in DRIFT_TERMS):
            ordinary_dialogue_rows += 1

    length_summary = {
        category: {
            "rows": len(lengths),
            "mean_response_words": round(mean(lengths), 2),
            "median_response_words": round(median(lengths), 2),
        }
        for category, lengths in sorted(category_lengths.items())
    }

    total = len(rows)
    return {
        "total_rows": total,
        "categories": dict(categories),
        "category_percent": {
            category: round(count / total * 100, 2)
            for category, count in categories.items()
        },
        "duplicate_exact_rows": duplicate_rows,
        "duplicate_exact_groups": duplicate_groups,
        "format_marker_rows": len(marker_rows),
        "format_marker_percent": round(len(marker_rows) / total * 100, 2) if total else 0.0,
        "response_length_by_category": length_summary,
        "identity_drift_terms_in_responses": dict(drift_counts.most_common()),
        "ordinary_conversation_rows_without_drift_terms": ordinary_dialogue_rows,
        "ordinary_conversation_percent_of_dataset": round(ordinary_dialogue_rows / total * 100, 2) if total else 0.0,
        "recommendations": [
            "Do not train the literal wrapper tokens unless inference is expected to output them.",
            "Prefer response-only loss masking so prompts condition the answer without teaching the model to emit `### Response`.",
            "Reduce duplicate identity/protection rows during speech-cleanup cycles.",
            "Add more ordinary dialogue that does not mention the creator, body, servos, shop, or architecture.",
            "Keep identity/protection as a separate adapter or lower-weight slice after basic conversational form improves.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--out", type=Path, default=Path("docs/original-conversation-dataset-audit.json"))
    args = parser.parse_args()

    rows = load_jsonl(args.dataset)
    report = {
        "dataset": str(args.dataset),
        "audit": audit(rows),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report["audit"], indent=2))
    print(f"wrote={args.out}")


if __name__ == "__main__":
    main()
