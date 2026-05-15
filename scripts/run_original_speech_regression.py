"""Run a read-only speech regression against the original HPP branch.

The goal is evidence, not training. This script loads the original local HPP
engine, swaps in selected speech checkpoints, runs held-out prompts, and writes
a transcript report for HPP V5.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Iterator

import torch


DEFAULT_ORIGINAL = Path(
    r"C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP"
)

DEFAULT_CHECKPOINTS = [
    "hpp_conversational_1000.pth",
    "hpp_conversational_2000.pth",
    "hpp_conversational_3000.pth",
    "hpp_conversational_4000.pth",
    "hpp_conversational_final.pth",
    "hpp_linguistic_anchor.pth",
]

HELD_OUT_PROMPTS = [
    "Give me one clear sentence about what you are.",
    "Good afternoon. What should we work on first?",
    "Explain Habit-14 without using technical jargon.",
    "I am overwhelmed and need the next small step.",
    "Tell me what Masamune is in plain language.",
    "What should you do if you are unsure?",
]


@contextmanager
def pushd(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def repetition_score(text: str) -> dict[str, object]:
    words = re.findall(r"[A-Za-z']+", text.lower())
    if not words:
        return {"word_count": 0, "unique_ratio": 0.0, "repeated_bigrams": []}

    bigrams = [" ".join(pair) for pair in zip(words, words[1:])]
    repeated = sorted({item for item in bigrams if bigrams.count(item) > 1})
    return {
        "word_count": len(words),
        "unique_ratio": round(len(set(words)) / len(words), 4),
        "repeated_bigrams": repeated[:12],
    }


def quality_flags(text: str) -> dict[str, object]:
    lower = text.lower()
    return {
        "format_leak": "###" in text or "instruction:" in lower or "response:" in lower,
        "using_loop": "using using" in lower,
        "question_loop": "do you think" in lower,
        "empty": not text.strip(),
    }


def load_checkpoint(engine: object, checkpoint_path: Path) -> dict[str, object]:
    checkpoint = torch.load(checkpoint_path, map_location=engine.device, weights_only=True)
    engine.university.load_state_dict(checkpoint["masamune_state_dict"], strict=False)
    engine.lm_head.load_state_dict(checkpoint["lm_head_state_dict"])
    engine.embedding.load_state_dict(checkpoint["embedding_state_dict"])
    engine.eval_mode()
    return {key: value for key, value in checkpoint.items() if not key.endswith("_state_dict")}


def run_checkpoint(
    engine: object,
    checkpoint_name: str,
    original: Path,
    prompts: list[str],
    max_tokens: int,
    temperature: float,
    top_p: float,
) -> dict[str, object]:
    checkpoint_path = original / "checkpoints" / checkpoint_name
    metadata = load_checkpoint(engine, checkpoint_path)
    rows = []

    for prompt in prompts:
        start = perf_counter()
        result = engine.pulse(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            domain="conversation",
        )
        elapsed_ms = round((perf_counter() - start) * 1000, 3)
        response = str(result.get("response", ""))
        rows.append(
            {
                "prompt": prompt,
                "response": response,
                "engine_latency_ms": result.get("latency_ms"),
                "wall_latency_ms": elapsed_ms,
                "tokens": result.get("tokens"),
                "flags": quality_flags(response),
                "repetition": repetition_score(response),
            }
        )

    return {
        "checkpoint": checkpoint_name,
        "metadata": metadata,
        "transcripts": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--original", type=Path, default=DEFAULT_ORIGINAL)
    parser.add_argument("--checkpoints", type=str, default="hpp_linguistic_anchor.pth")
    parser.add_argument("--max-tokens", type=int, default=60)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-p", type=float, default=0.9)
    parser.add_argument("--out", type=Path, default=Path("docs/original-speech-regression.json"))
    args = parser.parse_args()

    checkpoint_names = [
        item.strip()
        for item in args.checkpoints.split(",")
        if item.strip()
    ]
    if args.checkpoints == "all":
        checkpoint_names = DEFAULT_CHECKPOINTS

    sys.path.insert(0, str(args.original))

    with pushd(args.original):
        from hpp_sovereign_engine import HPP_SovereignEngine

        engine = HPP_SovereignEngine(max_context=512)
        engine.university.eval()
        engine.lm_head.eval()
        engine.embedding.eval()

        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": str(args.original),
            "device": str(engine.device),
            "cuda_available": torch.cuda.is_available(),
            "device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU",
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "prompts": HELD_OUT_PROMPTS,
            "results": [
                run_checkpoint(
                    engine=engine,
                    checkpoint_name=name,
                    original=args.original,
                    prompts=HELD_OUT_PROMPTS,
                    max_tokens=args.max_tokens,
                    temperature=args.temperature,
                    top_p=args.top_p,
                )
                for name in checkpoint_names
            ],
        }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"wrote={args.out}")


if __name__ == "__main__":
    main()
