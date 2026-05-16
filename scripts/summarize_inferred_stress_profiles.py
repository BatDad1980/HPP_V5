"""Summarize inferred-stress routing profile artifacts."""

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
                "profile": data["tolerance_profile"],
                "tolerance_shift": data["tolerance_shift"],
                "route_accuracy": data["route_accuracy"],
                "tapout_rate": data["tapout_rate"],
                "ood_mean": data["ood_score"]["value_mean"],
                "ood_max": data["ood_score"]["value_max"],
                "inferred_failure_rate": comparison["inferred_failure_rate"],
                "tapout_vs_inferred": comparison["tapout_vs_inferred_overall"],
                "tapout_failure_rate": comparison["tapout_failure_rate"],
            }
        )
    return rows


def write_markdown(summary: dict[str, Any], output_path: Path) -> None:
    lines = [
        "# Inferred Stress Profile Sweep Summary",
        "",
        "This summary captures a multi-seed sweep of inferred stress routing with tolerance profiles.",
        "",
        "## Setup",
        "",
        "- Script: `scripts/compare_inferred_stress_routing.py`",
        f"- Mode: `{summary['mode']}`",
        f"- Device: `{summary['device_name']}`",
        f"- Profiles: `{', '.join(summary['profiles'])}`",
        f"- Seeds: `{', '.join(str(seed) for seed in summary['seeds'])}`",
        "",
        "## Aggregate",
        "",
        "| Profile | Tap-out mean | Inferred failure mean | Tap-out failure mean | Tap-out/inferred mean | Route accuracy mean |",
        "| :--- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for profile in summary["profiles"]:
        m = summary["metrics_by_profile"][profile]
        lines.append(
            f"| {profile} | {m['tapout_rate']['mean']} | "
            f"{m['inferred_failure_rate']['mean']} | "
            f"{m['tapout_failure_rate']['mean']} | "
            f"{m['tapout_vs_inferred']['mean']}x | "
            f"{m['route_accuracy']['mean']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "The profile sweep tests whether the same extreme noise is treated differently by different operating-band assumptions. Low and standard profiles should tap out more readily; high-intensity profiles should tolerate more noise but may preserve higher failure risk.",
            "",
            "## Boundary",
            "",
            "This is synthetic mechanism evidence. The stress and OOD estimators are hand-built and calibrated to this toy harness.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pattern",
        default="docs/inferred-stress-routing-plugged-profile-*.json",
    )
    parser.add_argument(
        "--json-output",
        default="docs/inferred-stress-profile-sweep-summary.json",
    )
    parser.add_argument(
        "--md-output",
        default="docs/inferred-stress-profile-sweep-summary.md",
    )
    args = parser.parse_args()

    rows = load_rows(args.pattern)
    if not rows:
        raise SystemExit(f"no files matched pattern: {args.pattern}")

    profiles = sorted(set(row["profile"] for row in rows))
    seeds = sorted(set(row["seed"] for row in rows))
    metrics_by_profile = {}
    for profile in profiles:
        selected = [row for row in rows if row["profile"] == profile]
        metrics_by_profile[profile] = {
            "route_accuracy": metric([row["route_accuracy"] for row in selected]),
            "tapout_rate": metric([row["tapout_rate"] for row in selected]),
            "inferred_failure_rate": metric(
                [row["inferred_failure_rate"] for row in selected]
            ),
            "tapout_failure_rate": metric(
                [row["tapout_failure_rate"] for row in selected]
            ),
            "tapout_vs_inferred": metric(
                [row["tapout_vs_inferred"] for row in selected]
            ),
        }

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "pattern": args.pattern,
        "mode": "plugged",
        "device_name": "NVIDIA GeForce RTX 4050 Laptop GPU",
        "profiles": profiles,
        "seeds": seeds,
        "rows": rows,
        "metrics_by_profile": metrics_by_profile,
    }

    json_path = Path(args.json_output)
    md_path = Path(args.md_output)
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary, md_path)
    print(json.dumps(metrics_by_profile, indent=2))
    print(f"wrote={json_path}")
    print(f"wrote={md_path}")


if __name__ == "__main__":
    main()
