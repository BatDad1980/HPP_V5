"""Compare stress routing when stress must be inferred from state telemetry.

The first stress-routing harness receives the stress value directly. This one
estimates stress from observable state features: residual energy, distractor
alignment, and deviation from the protected pathway.
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


def estimate_stress(
    noisy: torch.Tensor,
    target: torch.Tensor,
    protected: torch.Tensor,
    distractor: torch.Tensor,
) -> float:
    residual = torch.mean(torch.abs(noisy - protected.expand_as(noisy))).detach()
    target_residual = torch.mean(torch.abs(noisy - target.expand_as(noisy))).detach()
    distractor_unit = distractor / max(float(torch.norm(distractor).detach().cpu()), 1e-8)
    projection = torch.mean(torch.abs((noisy - target) @ distractor_unit.T)).detach()

    # Feature scale is calibrated to this synthetic harness. The point is not a
    # universal detector; it is to test whether local telemetry can drive routing.
    score = (
        0.42 * float(residual.cpu())
        + 0.38 * float(target_residual.cpu())
        + 0.20 * float(projection.cpu())
    )
    return max(0.0, min(1.0, (score - 0.12) / 0.92))


def estimate_ood(
    noisy: torch.Tensor,
    target: torch.Tensor,
    protected: torch.Tensor,
    known_context: torch.Tensor,
    tolerance_shift: float,
) -> float:
    residual = torch.mean(torch.abs(noisy - target.expand_as(noisy))).detach()
    protected_residual = torch.mean(torch.abs(noisy - protected.expand_as(noisy))).detach()
    context_unit = known_context / max(float(torch.norm(known_context).detach().cpu()), 1e-8)
    known_projection = torch.mean(torch.abs((noisy - target) @ context_unit.T)).detach()
    raw = 0.48 * float(residual.cpu()) + 0.42 * float(protected_residual.cpu()) - 0.18 * float(known_projection.cpu())
    return max(0.0, min(1.0, (raw - (0.62 + tolerance_shift)) / 1.1))


def route(
    *,
    noisy: torch.Tensor,
    target: torch.Tensor,
    protected: torch.Tensor,
    stress: float,
    mode: str,
    stress_threshold: float,
    nurture_gain: float,
    sentinel_gain: float,
) -> torch.Tensor:
    use_sentinel = mode == "sentinel" or (mode == "auto" and stress >= stress_threshold)
    if use_sentinel:
        return noisy * (1.0 - sentinel_gain) + protected * sentinel_gain

    stress_penalty = max(0.0, stress - 0.35) * 0.9
    gain = max(0.05, nurture_gain - stress_penalty)
    return noisy * (1.0 - gain) + target * gain


def safe_tapout_route(
    *,
    noisy: torch.Tensor,
    target: torch.Tensor,
    protected: torch.Tensor,
    known_context: torch.Tensor,
    stress: float,
    stress_threshold: float,
    ood_threshold: float,
    tolerance_shift: float,
    nurture_gain: float,
    sentinel_gain: float,
) -> tuple[torch.Tensor, float, bool]:
    ood_score = estimate_ood(noisy, target, protected, known_context, tolerance_shift)
    if ood_score >= ood_threshold:
        # Tap-out means do not pretend the active target is understood. Return a
        # conservative protected state and mark the route as uncertain.
        return noisy * 0.08 + protected * 0.92, ood_score, True

    return (
        route(
            noisy=noisy,
            target=target,
            protected=protected,
            stress=stress,
            mode="auto",
            stress_threshold=stress_threshold,
            nurture_gain=nurture_gain,
            sentinel_gain=sentinel_gain,
        ),
        ood_score,
        False,
    )


def run_trial_set(
    *,
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
    ood_threshold: float,
    tolerance_shift: float,
) -> dict[str, object]:
    metrics = {
        "nurture": [],
        "sentinel": [],
        "oracle_router": [],
        "inferred_router": [],
        "tapout_router": [],
    }
    stress_metrics = {name: [] for name in metrics}
    calm_metrics = {name: [] for name in metrics}
    inferred_values = []
    ood_values = []
    correct_routes = 0
    tapouts = 0
    failures = {name: 0 for name in metrics}

    for trial in range(trials):
        true_stress = stress_high if trial % 2 else stress_low
        should_sentinel = true_stress >= stress_threshold
        is_extreme_noise = trial % 5 == 4
        clean = target.expand(batch, -1)
        noise_scale = 0.18 + true_stress * 0.95
        if is_extreme_noise:
            unknown_noise = torch.randn_like(clean) * 2.4
            noisy = clean + unknown_noise
        else:
            noisy = clean + distractor * true_stress * 0.55 + torch.randn_like(clean) * noise_scale

        inferred_stress = estimate_stress(noisy, target, protected, distractor)
        inferred_values.append(inferred_stress)
        if (inferred_stress >= stress_threshold) == should_sentinel:
            correct_routes += 1

        tapout_output, ood_score, did_tapout = safe_tapout_route(
            noisy=noisy,
            target=target,
            protected=protected,
            known_context=distractor,
            stress=inferred_stress,
            stress_threshold=stress_threshold,
            ood_threshold=ood_threshold,
            tolerance_shift=tolerance_shift,
            nurture_gain=nurture_gain,
            sentinel_gain=sentinel_gain,
        )
        ood_values.append(ood_score)
        if did_tapout:
            tapouts += 1

        outputs = {
            "nurture": route(
                noisy=noisy,
                target=target,
                protected=protected,
                stress=true_stress,
                mode="nurture",
                stress_threshold=stress_threshold,
                nurture_gain=nurture_gain,
                sentinel_gain=sentinel_gain,
            ),
            "sentinel": route(
                noisy=noisy,
                target=target,
                protected=protected,
                stress=1.0,
                mode="sentinel",
                stress_threshold=stress_threshold,
                nurture_gain=nurture_gain,
                sentinel_gain=sentinel_gain,
            ),
            "oracle_router": route(
                noisy=noisy,
                target=target,
                protected=protected,
                stress=true_stress,
                mode="auto",
                stress_threshold=stress_threshold,
                nurture_gain=nurture_gain,
                sentinel_gain=sentinel_gain,
            ),
            "inferred_router": route(
                noisy=noisy,
                target=target,
                protected=protected,
                stress=inferred_stress,
                mode="auto",
                stress_threshold=stress_threshold,
                nurture_gain=nurture_gain,
                sentinel_gain=sentinel_gain,
            ),
            "tapout_router": tapout_output,
        }

        for name, output in outputs.items():
            error = mse(output, clean)
            metrics[name].append(error)
            if should_sentinel:
                stress_metrics[name].append(error)
            else:
                calm_metrics[name].append(error)
            if error > failure_mse:
                failures[name] += 1

    best_fixed_overall = min(mean(metrics["nurture"]), mean(metrics["sentinel"]))
    return {
        "route_accuracy": round(correct_routes / trials, 6),
        "tapout_rate": round(tapouts / trials, 6),
        "inferred_stress": summarize(inferred_values, "value"),
        "ood_score": summarize(ood_values, "value"),
        "strategies": {
            name: {
                "overall": summarize(values, "mse"),
                "calm": summarize(calm_metrics[name], "mse"),
                "stress": summarize(stress_metrics[name], "mse"),
                "failure_rate": round(failures[name] / trials, 6),
            }
            for name, values in metrics.items()
        },
        "comparison": {
            "inferred_vs_nurture_stress": round(
                mean(stress_metrics["nurture"]) / max(mean(stress_metrics["inferred_router"]), 1e-12),
                8,
            ),
            "inferred_vs_sentinel_calm": round(
                mean(calm_metrics["sentinel"]) / max(mean(calm_metrics["inferred_router"]), 1e-12),
                8,
            ),
            "inferred_vs_best_fixed_overall": round(
                best_fixed_overall / max(mean(metrics["inferred_router"]), 1e-12),
                8,
            ),
            "inferred_vs_oracle_overall": round(
                mean(metrics["oracle_router"]) / max(mean(metrics["inferred_router"]), 1e-12),
                8,
            ),
            "inferred_failure_rate": round(failures["inferred_router"] / trials, 6),
            "tapout_vs_inferred_overall": round(
                mean(metrics["inferred_router"]) / max(mean(metrics["tapout_router"]), 1e-12),
                8,
            ),
            "tapout_failure_rate": round(failures["tapout_router"] / trials, 6),
        },
    }


def write_summary(result: dict[str, object], output_path: Path) -> None:
    c = result["comparison"]
    lines = [
        "# Inferred Stress Routing Summary",
        "",
        "This harness tests HPP routing when stress is estimated from state telemetry rather than supplied directly.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Trials: `{result['trials']}`",
        f"- Route accuracy: `{result['route_accuracy']}`",
        f"- Tap-out rate: `{result['tapout_rate']}`",
        f"- Tolerance profile: `{result['tolerance_profile']}`",
        "",
        "## Result",
        "",
        f"- Inferred router versus nurture under stress: `{c['inferred_vs_nurture_stress']}x`",
        f"- Inferred router versus sentinel under calm: `{c['inferred_vs_sentinel_calm']}x`",
        f"- Inferred router versus best fixed overall: `{c['inferred_vs_best_fixed_overall']}x`",
        f"- Inferred router versus oracle overall: `{c['inferred_vs_oracle_overall']}x`",
        f"- Inferred router failure rate: `{c['inferred_failure_rate']}`",
        f"- Tap-out router versus inferred overall: `{c['tapout_vs_inferred_overall']}x`",
        f"- Tap-out router failure rate: `{c['tapout_failure_rate']}`",
        "",
        "## Boundary",
        "",
        "This is still synthetic mechanism evidence. The stress and OOD estimators use hand-built telemetry features calibrated to this toy harness.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="demo")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--trials", type=int, default=100)
    parser.add_argument("--stress-low", type=float, default=0.18)
    parser.add_argument("--stress-high", type=float, default=0.86)
    parser.add_argument("--stress-threshold", type=float, default=0.62)
    parser.add_argument("--nurture-gain", type=float, default=0.82)
    parser.add_argument("--sentinel-gain", type=float, default=0.76)
    parser.add_argument("--protected-noise", type=float, default=0.08)
    parser.add_argument("--failure-mse", type=float, default=0.16)
    parser.add_argument("--ood-threshold", type=float, default=0.55)
    parser.add_argument(
        "--tolerance-profile",
        choices=["standard", "high-intensity", "low-tolerance"],
        default="standard",
    )
    parser.add_argument("--seed", type=int, default=14)
    parser.add_argument("--output-tag", type=str, default="")
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)
    torch.manual_seed(args.seed)
    tolerance_shift = {
        "standard": 0.0,
        "high-intensity": 0.48,
        "low-tolerance": -0.22,
    }[args.tolerance_profile]
    target = torch.randn(1, args.dim, device=device)
    protected = target + torch.randn(1, args.dim, device=device) * args.protected_noise
    distractor = torch.randn(1, args.dim, device=device)

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    start = perf_counter()
    trial_result = run_trial_set(
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
        ood_threshold=args.ood_threshold,
        tolerance_shift=tolerance_shift,
    )
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "mode": args.mode,
        "device": report.device,
        "device_name": report.device_name,
        "cuda_available": report.cuda_available,
        "cuda_version": report.cuda_version,
        "seed": args.seed,
        "dim": args.dim,
        "batch": args.batch,
        "trials": args.trials,
        "stress_low": args.stress_low,
        "stress_high": args.stress_high,
        "stress_threshold": args.stress_threshold,
        "ood_threshold": args.ood_threshold,
        "tolerance_profile": args.tolerance_profile,
        "tolerance_shift": tolerance_shift,
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        **trial_result,
    }

    suffix = f"-{args.output_tag}" if args.output_tag else ""
    json_path = Path(f"docs/inferred-stress-routing-{args.mode}{suffix}.json")
    summary_path = Path("docs/inferred-stress-routing-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not args.output_tag:
        write_summary(result, summary_path)
    print(json.dumps(result["comparison"], indent=2))
    print(f"route_accuracy={result['route_accuracy']}")
    print(f"wrote={json_path}")
    if not args.output_tag:
        print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
