"""Inspect original HPP speech checkpoints without modifying them.

This script is intentionally metadata-only. It reads checkpoint structure,
parameter counts, file sizes, timestamps, and phase metadata from the active
original HPP lab branch.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any

import torch


DEFAULT_ORIGINAL = Path(
    r"C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP"
)

SPEECH_CHECKPOINTS = [
    "hpp_conversational_1000.pth",
    "hpp_conversational_2000.pth",
    "hpp_conversational_3000.pth",
    "hpp_conversational_4000.pth",
    "hpp_conversational_final.pth",
    "hpp_conversational_progress.pth",
    "hpp_linguistic_anchor.pth",
]


def summarize_state_dict(state_dict: Any) -> dict[str, int]:
    if not isinstance(state_dict, dict):
        return {"tensors": 0, "parameters": 0}

    tensors = 0
    parameters = 0
    for value in state_dict.values():
        if hasattr(value, "numel"):
            tensors += 1
            parameters += int(value.numel())
    return {"tensors": tensors, "parameters": parameters}


def summarize_checkpoint(path: Path) -> dict[str, Any]:
    stat = path.stat()
    checkpoint = torch.load(path, map_location="cpu", weights_only=True)

    metadata = {}
    if isinstance(checkpoint, dict):
        metadata = {
            key: value
            for key, value in checkpoint.items()
            if not key.endswith("_state_dict")
        }

    return {
        "name": path.name,
        "path": str(path),
        "exists": True,
        "size_mb": round(stat.st_size / 1024 / 1024, 3),
        "last_modified_epoch": stat.st_mtime,
        "last_modified_utc": datetime.fromtimestamp(
            stat.st_mtime, tz=timezone.utc
        ).isoformat(),
        "metadata": metadata,
        "state_dicts": {
            "masamune": summarize_state_dict(checkpoint.get("masamune_state_dict")),
            "lm_head": summarize_state_dict(checkpoint.get("lm_head_state_dict")),
            "embedding": summarize_state_dict(checkpoint.get("embedding_state_dict")),
        },
    }


def inspect(original: Path) -> dict[str, Any]:
    checkpoint_dir = original / "checkpoints"
    results = []

    for name in SPEECH_CHECKPOINTS:
        path = checkpoint_dir / name
        if path.exists():
            results.append(summarize_checkpoint(path))
        else:
            results.append({"name": name, "path": str(path), "exists": False})

    return {
        "source": str(original),
        "checkpoint_dir": str(checkpoint_dir),
        "inspected": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect original HPP speech checkpoint metadata."
    )
    parser.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    report = inspect(args.original)
    text = json.dumps(report, indent=2)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + os.linesep, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
