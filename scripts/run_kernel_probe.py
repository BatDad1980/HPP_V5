"""Run a small repeatable HPP V5 kernel probe.

This is a diagnostic benchmark, not a training run. It keeps tensors small,
uses warmups, and writes a JSON log that can become the seed of the HPP evidence
trail.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.hpp_kernel.tiny_recurrent import run_probe


def summarize(runs: list[dict[str, object]]) -> dict[str, object]:
    timings = [float(run["elapsed_ms"]) for run in runs]
    return {
        "runs": len(runs),
        "elapsed_ms_min": round(min(timings), 3),
        "elapsed_ms_mean": round(mean(timings), 3),
        "elapsed_ms_median": round(median(timings), 3),
        "elapsed_ms_max": round(max(timings), 3),
        "last_run": runs[-1],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="plugged")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--passes", type=int, default=14)
    parser.add_argument("--warmups", type=int, default=2)
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    for _ in range(args.warmups):
        run_probe(mode=args.mode, dim=args.dim, batch=args.batch, passes=args.passes)

    runs = [
        run_probe(mode=args.mode, dim=args.dim, batch=args.batch, passes=args.passes)
        for _ in range(args.runs)
    ]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "mode": args.mode,
        "dim": args.dim,
        "batch": args.batch,
        "passes": args.passes,
        "warmups": args.warmups,
        "summary": summarize(runs),
        "runs": runs,
    }

    output_path = Path(f"docs/kernel-probe-log-{args.mode}.json")
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], indent=2))
    print(f"wrote={output_path}")


if __name__ == "__main__":
    main()
