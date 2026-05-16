"""Compare HPP stress-aware routing against fixed response strategies.

This is a toy mechanism harness. It tests whether a router that switches from
nurture-style refinement to sentinel-style protection under stress can preserve
signal better than always using one mode.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from src.hpp_kernel.device import select_device


def mse(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.mean((a - b) ** 2).detach().cpu())


def summarize(values: list[float], prefix: str) -> dict[str, float | int]:
    return {
        "runs": len(values),
        f"{prefix}_min": round(min(values), 8),
        f"{prefix}_mean": round(mean(values), 8),
        f"{prefix}_median": round(median(values), 8),
        f"{prefix}_max": round(max(values), 8),
        f"{prefix}_stdev": round(stdev(values), 8) if len(values) > 1 else 0.0,
    }


def route_state(
    *,
    noisy: torch.Tensor,
    target: torch.Tensor,
    protected: torch.Tensor,
    stress: float,
    strategy: str,
    stress_threshold: float,
    nurture_gain: float,
    sentinel_gain: float,
) -> torch.Tensor:
    use_sentinel = strategy == "sentinel" or (
        strategy == "router" and stress >= stress_threshold
    )

    if use_sentinel:
        # Sentinel favors a low-complexity protected response.
        return noisy * (1.0 - sentinel_gain) + protected * sentinel_gain

    # Nurture favors fuller refinement toward the active target, but stress
    # disrupts its ability to hold that target cleanly.
    stress_penalty = max(0.0, stress - 0.35) * 0.9
    effective_gain = max(0.05, nurture_gain - stress_penalty)
    return noisy * (1.0 - effective_gain) + target * effective_gain


def run_strategy(
    *,
    strategy: str,
    target: torch.Tensor,
    protected: torch.Tensor,
    distractor: torch.Tensor,
    batch: int,
    trials: int,
    stress_low: float,
    stress_high: float,
    stress_threshold: float,
    nurture_gain: float,
    sentinel_gain: float,
    failure_mse: float,
) -> dict[str, object]:
    calm_errors = []
    stress_errors = []
    all_errors = []
    sentinel_uses = 0
    failures = 0

    for trial in range(trials):
        stress = stress_high if trial % 2 else stress_low
        noise_scale = 0.18 + stress * 0.95
        distractor_pressure = distractor * stress * 0.55
        clean = target.expand(batch, -1)
        noisy = clean + distractor_pressure + torch.randn_like(clean) * noise_scale

        output = route_state(
            noisy=noisy,
            target=target,
            protected=protected,
            stress=stress,
            strategy=strategy,
            stress_threshold=stress_threshold,
            nurture_gain=nurture_gain,
            sentinel_gain=sentinel_gain,
        )
        error = mse(output, clean)
        all_errors.append(error)

        if stress >= stress_threshold:
            stress_errors.append(error)
        else:
            calm_errors.append(error)

        if strategy == "sentinel" or (strategy == "router" and stress >= stress_threshold):
            sentinel_uses += 1
        if error > failure_mse:
            failures += 1

    return {
        "strategy": strategy,
        "sentinel_uses": sentinel_uses,
        "sentinel_use_rate": round(sentinel_uses / trials, 6),
        "failures": failures,
        "failure_rate": round(failures / trials, 6),
        "calm": summarize(calm_errors, "mse"),
        "stress": summarize(stress_errors, "mse"),
        "overall": summarize(all_errors, "mse"),
    }


def write_summary(result: dict[str, object], output_path: Path) -> None:
    comparison = result["comparison"]
    lines = [
        "# Stress Routing Summary",
        "",
        "This harness compares fixed nurture, fixed sentinel, and stress-aware HPP routing.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Trials: `{result['trials']}`",
        f"- Stress threshold: `{result['stress_threshold']}`",
        "",
        "## Result",
        "",
        f"- Router versus nurture stress improvement: `{comparison['router_vs_nurture_stress']}x`",
        f"- Router versus sentinel calm improvement: `{comparison['router_vs_sentinel_calm']}x`",
        f"- Router versus best fixed overall improvement: `{comparison['router_vs_best_fixed_overall']}x`",
        f"- Router failure rate: `{comparison['router_failure_rate']}`",
        "",
        "## Boundary",
        "",
        "This is mechanism evidence only. The stress score is provided by the harness, so this tests routing behavior rather than autonomous stress detection.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="demo")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--trials", type=int, default=80)
    parser.add_argument("--stress-low", type=float, default=0.18)
    parser.add_argument("--stress-high", type=float, default=0.86)
    parser.add_argument("--stress-threshold", type=float, default=0.62)
    parser.add_argument("--nurture-gain", type=float, default=0.82)
    parser.add_argument("--sentinel-gain", type=float, default=0.76)
    parser.add_argument("--protected-noise", type=float, default=0.08)
    parser.add_argument("--failure-mse", type=float, default=0.16)
    parser.add_argument("--seed", type=int, default=14)
    parser.add_argument("--output-tag", type=str, default="")
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)
    torch.manual_seed(args.seed)

    target = torch.randn(1, args.dim, device=device)
    protected = target + torch.randn(1, args.dim, device=device) * args.protected_noise
    distractor = torch.randn(1, args.dim, device=device)

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    start = perf_counter()

    strategies = {
        name: run_strategy(
            strategy=name,
            target=target,
            protected=protected,
            distractor=distractor,
            batch=args.batch,
            trials=args.trials,
            stress_low=args.stress_low,
            stress_high=args.stress_high,
            stress_threshold=args.stress_threshold,
            nurture_gain=args.nurture_gain,
            sentinel_gain=args.sentinel_gain,
            failure_mse=args.failure_mse,
        )
        for name in ["nurture", "sentinel", "router"]
    }

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    best_fixed_overall = min(
        strategies["nurture"]["overall"]["mse_mean"],
        strategies["sentinel"]["overall"]["mse_mean"],
    )
    comparison = {
        "router_vs_nurture_stress": round(
            strategies["nurture"]["stress"]["mse_mean"]
            / max(strategies["router"]["stress"]["mse_mean"], 1e-12),
            8,
        ),
        "router_vs_sentinel_calm": round(
            strategies["sentinel"]["calm"]["mse_mean"]
            / max(strategies["router"]["calm"]["mse_mean"], 1e-12),
            8,
        ),
        "router_vs_best_fixed_overall": round(
            best_fixed_overall / max(strategies["router"]["overall"]["mse_mean"], 1e-12),
            8,
        ),
        "router_failure_rate": strategies["router"]["failure_rate"],
        "nurture_failure_rate": strategies["nurture"]["failure_rate"],
        "sentinel_failure_rate": strategies["sentinel"]["failure_rate"],
    }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "mode": args.mode,
        "device": report.device,
        "device_name": report.device_name,
        "cuda_available": report.cuda_available,
        "cuda_version": report.cuda_version,
        "allocated_mb": report.allocated_mb,
        "reserved_mb": report.reserved_mb,
        "seed": args.seed,
        "dim": args.dim,
        "batch": args.batch,
        "trials": args.trials,
        "stress_low": args.stress_low,
        "stress_high": args.stress_high,
        "stress_threshold": args.stress_threshold,
        "nurture_gain": args.nurture_gain,
        "sentinel_gain": args.sentinel_gain,
        "protected_noise": args.protected_noise,
        "failure_mse": args.failure_mse,
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "strategies": strategies,
        "comparison": comparison,
    }

    suffix = f"-{args.output_tag}" if args.output_tag else ""
    json_path = Path(f"docs/stress-routing-{args.mode}{suffix}.json")
    summary_path = Path("docs/stress-routing-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not args.output_tag:
        write_summary(result, summary_path)
    print(json.dumps(comparison, indent=2))
    print(f"wrote={json_path}")
    if not args.output_tag:
        print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
