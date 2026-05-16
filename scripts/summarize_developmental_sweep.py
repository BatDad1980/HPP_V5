"""Summarize developmental curriculum sweep JSON artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any


def metric(values: list[float]) -> dict[str, float | int]:
    summary: dict[str, float | int] = {
        "runs": len(values),
        "min": round(min(values), 8),
        "mean": round(mean(values), 8),
        "median": round(median(values), 8),
        "max": round(max(values), 8),
    }
    summary["stdev"] = round(stdev(values), 8) if len(values) > 1 else 0.0
    return summary


def load_rows(pattern: str) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(Path().glob(pattern)):
        data = json.loads(path.read_text(encoding="utf-8"))
        comparison = data["comparison"]
        rows.append(
            {
                "file": str(path),
                "seed": data["seed"],
                "mode": data["mode"],
                "device_name": data["device_name"],
                "hpp_locked": comparison["hpp_locked"],
                "hpp_protection": comparison["hpp_protection"],
                "hpp_vs_flat_clean": comparison["clean_context_hpp_vs_flat_mean"],
                "hpp_vs_flat_shifted": comparison["shifted_context_hpp_vs_flat_mean"],
                "hpp_vs_context_flat_clean": comparison[
                    "clean_context_hpp_vs_context_aware_flat_mean"
                ],
                "hpp_vs_context_flat_shifted": comparison[
                    "shifted_context_hpp_vs_context_aware_flat_mean"
                ],
            }
        )
    return rows


def write_markdown(summary: dict[str, Any], output_path: Path) -> None:
    rows = summary["rows"]
    lines = [
        "# Developmental Curriculum Sweep Summary",
        "",
        "This summary captures a plugged multi-seed sweep of the HPP developmental curriculum harness.",
        "",
        "## Setup",
        "",
        "- Script: `scripts/compare_developmental_curriculum.py`",
        f"- Mode: `{summary['mode']}`",
        f"- Device: `{summary['device_name']}`",
        f"- Seeds: `{', '.join(str(row['seed']) for row in rows)}`",
        f"- Runs: `{len(rows)}`",
        f"- Habit-14 lock rate: `{summary['lock_count']}/{len(rows)}`",
        "",
        "## Results",
        "",
        "| Seed | HPP/flat clean | HPP/flat shifted | HPP/context-flat clean | HPP/context-flat shifted | Locked |",
        "| ---: | ---: | ---: | ---: | ---: | :--- |",
    ]

    for row in rows:
        lines.append(
            f"| {row['seed']} | {row['hpp_vs_flat_clean']:.8f}x | "
            f"{row['hpp_vs_flat_shifted']:.8f}x | "
            f"{row['hpp_vs_context_flat_clean']:.8f}x | "
            f"{row['hpp_vs_context_flat_shifted']:.8f}x | "
            f"{str(row['hpp_locked']).lower()} |"
        )

    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- HPP versus flat clean mean: `{summary['metrics']['hpp_vs_flat_clean']['mean']}x`",
            f"- HPP versus flat shifted mean: `{summary['metrics']['hpp_vs_flat_shifted']['mean']}x`",
            f"- HPP versus context-aware flat clean mean: `{summary['metrics']['hpp_vs_context_flat_clean']['mean']}x`",
            f"- HPP versus context-aware flat shifted mean: `{summary['metrics']['hpp_vs_context_flat_shifted']['mean']}x`",
            f"- Context-aware shifted standard deviation: `{summary['metrics']['hpp_vs_context_flat_shifted']['stdev']}`",
            "",
            "## Interpretation",
            "",
            "The stronger context-aware flat baseline receives oracle target/distractor labels and ignores distractor events. HPP still retains a positive margin in this toy setup because maturity-dependent protection changes recall behavior after the Habit-14 lock.",
            "",
            "## Boundary",
            "",
            "This remains mechanism evidence. The benchmark is synthetic and should be used to guide the next harness, not as a broad capability claim.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pattern",
        default="docs/developmental-curriculum-plugged-seed-*.json",
    )
    parser.add_argument(
        "--json-output",
        default="docs/developmental-curriculum-sweep-summary.json",
    )
    parser.add_argument(
        "--md-output",
        default="docs/developmental-curriculum-sweep-summary.md",
    )
    args = parser.parse_args()

    rows = load_rows(args.pattern)
    if not rows:
        raise SystemExit(f"no files matched pattern: {args.pattern}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pattern": args.pattern,
        "mode": rows[0]["mode"],
        "device_name": rows[0]["device_name"],
        "lock_count": sum(1 for row in rows if row["hpp_locked"]),
        "rows": rows,
        "metrics": {
            "hpp_vs_flat_clean": metric([row["hpp_vs_flat_clean"] for row in rows]),
            "hpp_vs_flat_shifted": metric([row["hpp_vs_flat_shifted"] for row in rows]),
            "hpp_vs_context_flat_clean": metric(
                [row["hpp_vs_context_flat_clean"] for row in rows]
            ),
            "hpp_vs_context_flat_shifted": metric(
                [row["hpp_vs_context_flat_shifted"] for row in rows]
            ),
        },
    }

    json_path = Path(args.json_output)
    md_path = Path(args.md_output)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary, md_path)
    print(json.dumps(summary["metrics"], indent=2))
    print(f"wrote={json_path}")
    print(f"wrote={md_path}")


if __name__ == "__main__":
    main()
