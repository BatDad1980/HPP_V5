"""Summarize stress-routing sweep JSON artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any


def metric(values: list[float]) -> dict[str, float | int]:
    return {
        "runs": len(values),
        "min": round(min(values), 8),
        "mean": round(mean(values), 8),
        "median": round(median(values), 8),
        "max": round(max(values), 8),
        "stdev": round(stdev(values), 8) if len(values) > 1 else 0.0,
    }


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
                "router_vs_nurture_stress": comparison["router_vs_nurture_stress"],
                "router_vs_sentinel_calm": comparison["router_vs_sentinel_calm"],
                "router_vs_best_fixed_overall": comparison["router_vs_best_fixed_overall"],
                "router_failure_rate": comparison["router_failure_rate"],
                "nurture_failure_rate": comparison["nurture_failure_rate"],
                "sentinel_failure_rate": comparison["sentinel_failure_rate"],
            }
        )
    return rows


def write_markdown(summary: dict[str, Any], output_path: Path) -> None:
    rows = summary["rows"]
    lines = [
        "# Stress Routing Sweep Summary",
        "",
        "This summary captures a plugged multi-seed sweep of the HPP stress-routing harness.",
        "",
        "## Setup",
        "",
        "- Script: `scripts/compare_stress_routing.py`",
        f"- Mode: `{summary['mode']}`",
        f"- Device: `{summary['device_name']}`",
        f"- Seeds: `{', '.join(str(row['seed']) for row in rows)}`",
        f"- Runs: `{len(rows)}`",
        "",
        "## Results",
        "",
        "| Seed | Router/nurture stress | Router/sentinel calm | Router/best-fixed overall | Router failure rate |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]

    for row in rows:
        lines.append(
            f"| {row['seed']} | {row['router_vs_nurture_stress']:.8f}x | "
            f"{row['router_vs_sentinel_calm']:.8f}x | "
            f"{row['router_vs_best_fixed_overall']:.8f}x | "
            f"{row['router_failure_rate']:.6f} |"
        )

    metrics = summary["metrics"]
    lines.extend(
        [
            "",
            "## Aggregate",
            "",
            f"- Router versus nurture under stress mean: `{metrics['router_vs_nurture_stress']['mean']}x`",
            f"- Router versus sentinel under calm mean: `{metrics['router_vs_sentinel_calm']['mean']}x`",
            f"- Router versus best fixed overall mean: `{metrics['router_vs_best_fixed_overall']['mean']}x`",
            f"- Router failure rate mean: `{metrics['router_failure_rate']['mean']}`",
            "",
            "## Interpretation",
            "",
            "The router preserves the reflective nurture path during calm probes and switches to the protected sentinel path during stress probes. In this toy setup, that mixed policy outperforms either fixed strategy alone.",
            "",
            "## Boundary",
            "",
            "This is mechanism evidence. The harness provides the stress value, so this tests routing behavior rather than autonomous stress detection.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", default="docs/stress-routing-plugged-seed-*.json")
    parser.add_argument("--json-output", default="docs/stress-routing-sweep-summary.json")
    parser.add_argument("--md-output", default="docs/stress-routing-sweep-summary.md")
    args = parser.parse_args()

    rows = load_rows(args.pattern)
    if not rows:
        raise SystemExit(f"no files matched pattern: {args.pattern}")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pattern": args.pattern,
        "mode": rows[0]["mode"],
        "device_name": rows[0]["device_name"],
        "rows": rows,
        "metrics": {
            "router_vs_nurture_stress": metric(
                [row["router_vs_nurture_stress"] for row in rows]
            ),
            "router_vs_sentinel_calm": metric(
                [row["router_vs_sentinel_calm"] for row in rows]
            ),
            "router_vs_best_fixed_overall": metric(
                [row["router_vs_best_fixed_overall"] for row in rows]
            ),
            "router_failure_rate": metric([row["router_failure_rate"] for row in rows]),
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
