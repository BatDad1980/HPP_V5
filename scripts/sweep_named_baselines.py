"""Run the named-baseline comparison across multiple seeds."""

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

from scripts.compare_named_baselines import (
    GRURefiner,
    OnePassMLPDenoiser,
    evaluate,
    make_clean_patterns,
    train_memories,
    train_model,
)
from src.hpp_kernel.device import select_device
from src.hpp_kernel.tiny_recurrent import count_parameters


def summarize(values: list[float], prefix: str) -> dict[str, float | int]:
    return {
        "runs": len(values),
        f"{prefix}_min": round(min(values), 8),
        f"{prefix}_mean": round(mean(values), 8),
        f"{prefix}_median": round(median(values), 8),
        f"{prefix}_max": round(max(values), 8),
        f"{prefix}_stdev": round(stdev(values), 8) if len(values) > 1 else 0.0,
    }


def run_seed(args: argparse.Namespace, seed: int, device: torch.device) -> dict[str, object]:
    torch.manual_seed(seed)
    clean = make_clean_patterns(args.classes, args.dim, device)
    mlp = OnePassMLPDenoiser(args.dim, args.hidden).to(device)
    gru = GRURefiner(args.dim, args.hidden).to(device)

    if device.type == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)

    start = perf_counter()
    hpp, nearest = train_memories(
        clean,
        classes=args.classes,
        dim=args.dim,
        exposures_per_class=args.exposures_per_class,
        batch=args.batch,
        noise=args.train_noise,
        distractor_scale=args.distractor_scale,
        device=device,
    )
    mlp_losses = train_model(
        mlp,
        clean,
        steps=args.train_steps,
        batch=args.batch,
        noise=args.train_noise,
        distractor_scale=args.distractor_scale,
        lr=args.lr,
        device=device,
    )
    gru_losses = train_model(
        gru,
        clean,
        steps=args.train_steps,
        batch=args.batch,
        noise=args.train_noise,
        distractor_scale=args.distractor_scale,
        lr=args.lr,
        device=device,
    )

    def recall_mlp(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        output = mlp(x)
        predicted = torch.argmin(torch.cdist(output, clean), dim=1)
        return output, predicted

    def recall_gru(x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        output = gru(x)
        predicted = torch.argmin(torch.cdist(output, clean), dim=1)
        return output, predicted

    results = {
        "hpp_developmental_memory": evaluate(
            "hpp_developmental_memory",
            hpp.recall,
            clean,
            batches=args.eval_batches,
            batch=args.batch,
            noise=args.eval_noise,
            distractor_scale=args.distractor_scale,
            device=device,
        ),
        "nearest_centroid": evaluate(
            "nearest_centroid",
            nearest.recall,
            clean,
            batches=args.eval_batches,
            batch=args.batch,
            noise=args.eval_noise,
            distractor_scale=args.distractor_scale,
            device=device,
        ),
        "one_pass_mlp": evaluate(
            "one_pass_mlp",
            recall_mlp,
            clean,
            batches=args.eval_batches,
            batch=args.batch,
            noise=args.eval_noise,
            distractor_scale=args.distractor_scale,
            device=device,
        ),
        "gru_refiner": evaluate(
            "gru_refiner",
            recall_gru,
            clean,
            batches=args.eval_batches,
            batch=args.batch,
            noise=args.eval_noise,
            distractor_scale=args.distractor_scale,
            device=device,
        ),
    }

    if device.type == "cuda":
        torch.cuda.synchronize(device)
        peak_allocated_mb = round(torch.cuda.max_memory_allocated(device) / 1024 / 1024, 3)
        peak_reserved_mb = round(torch.cuda.max_memory_reserved(device) / 1024 / 1024, 3)
    else:
        peak_allocated_mb = 0.0
        peak_reserved_mb = 0.0

    baseline_keys = ["nearest_centroid", "one_pass_mlp", "gru_refiner"]
    best_baseline_key = min(
        baseline_keys,
        key=lambda key: results[key]["mse"]["mse_mean"],
    )
    best_baseline = results[best_baseline_key]
    hpp_result = results["hpp_developmental_memory"]
    best_accuracy_key = max(
        baseline_keys,
        key=lambda key: results[key]["accuracy"]["accuracy_mean"],
    )
    best_accuracy_baseline = results[best_accuracy_key]
    comparison = {
        "seed": seed,
        "best_mse_baseline": best_baseline_key,
        "best_accuracy_baseline": best_accuracy_key,
        "hpp_mse_mean": hpp_result["mse"]["mse_mean"],
        "best_baseline_mse_mean": best_baseline["mse"]["mse_mean"],
        "best_baseline_to_hpp_mse_ratio": round(
            best_baseline["mse"]["mse_mean"] / max(hpp_result["mse"]["mse_mean"], 1e-12),
            8,
        ),
        "hpp_accuracy_mean": hpp_result["accuracy"]["accuracy_mean"],
        "best_baseline_accuracy_mean": best_accuracy_baseline["accuracy"]["accuracy_mean"],
        "hpp_accuracy_minus_best_baseline": round(
            hpp_result["accuracy"]["accuracy_mean"]
            - best_accuracy_baseline["accuracy"]["accuracy_mean"],
            8,
        ),
        "hpp_won_mse": hpp_result["mse"]["mse_mean"] < best_baseline["mse"]["mse_mean"],
        "hpp_won_accuracy": hpp_result["accuracy"]["accuracy_mean"]
        > best_accuracy_baseline["accuracy"]["accuracy_mean"],
        "peak_allocated_mb": peak_allocated_mb,
        "peak_reserved_mb": peak_reserved_mb,
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "mlp_final_loss": round(mlp_losses[-1], 8),
        "gru_final_loss": round(gru_losses[-1], 8),
        "hpp_locked_classes": int((hpp.exposures >= hpp.threshold).sum().detach().cpu()),
        "mlp_parameters": count_parameters(mlp),
        "gru_parameters": count_parameters(gru),
        "hpp_memory_values": int(hpp.prototypes.numel() + hpp.exposures.numel()),
    }
    return {"comparison": comparison, "results": results}


def write_summary(result: dict[str, object], output_path: Path) -> None:
    aggregate = result["aggregate"]
    lines = [
        "# Named Baseline Sweep Summary",
        "",
        "This sweep repeats the named-baseline attractor-recovery comparison across multiple seeds.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Seeds: `{', '.join(str(seed) for seed in result['seeds'])}`",
        f"- Classes: `{result['classes']}`",
        f"- Dimension: `{result['dim']}`",
        f"- Evaluation noise: `{result['eval_noise']}`",
        "",
        "## Result",
        "",
        f"- HPP MSE win rate: `{aggregate['hpp_mse_win_rate']}`",
        f"- HPP accuracy win rate: `{aggregate['hpp_accuracy_win_rate']}`",
        f"- Best-baseline-to-HPP MSE ratio mean: `{aggregate['best_baseline_to_hpp_mse_ratio']['ratio_mean']}x`",
        f"- HPP accuracy minus best baseline mean: `{aggregate['hpp_accuracy_minus_best_baseline']['delta_mean']}`",
        f"- Peak allocated CUDA memory max: `{aggregate['peak_allocated_mb']['mb_max']} MB`",
        f"- HPP stored memory values: `{aggregate['hpp_memory_values']}`",
        f"- MLP parameters: `{aggregate['mlp_parameters']}`",
        f"- GRU parameters: `{aggregate['gru_parameters']}`",
        "",
        "## Boundary",
        "",
        "This is still a synthetic mechanism sweep. It strengthens repeatability for this task only; it does not prove broad model superiority, language ability, production safety, or a fixed efficiency multiple.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="plugged")
    parser.add_argument("--seeds", type=str, default="14,21,42,77,101")
    parser.add_argument("--classes", type=int, default=24)
    parser.add_argument("--dim", type=int, default=192)
    parser.add_argument("--hidden", type=int, default=384)
    parser.add_argument("--batch", type=int, default=96)
    parser.add_argument("--exposures-per-class", type=int, default=56)
    parser.add_argument("--train-steps", type=int, default=60)
    parser.add_argument("--eval-batches", type=int, default=24)
    parser.add_argument("--train-noise", type=float, default=0.42)
    parser.add_argument("--eval-noise", type=float, default=1.35)
    parser.add_argument("--distractor-scale", type=float, default=0.28)
    parser.add_argument("--lr", type=float, default=0.0016)
    args = parser.parse_args()

    seeds = [int(value.strip()) for value in args.seeds.split(",") if value.strip()]
    report = select_device(args.mode)
    device = torch.device(report.device)

    seed_reports = [run_seed(args, seed, device) for seed in seeds]
    comparisons = [seed_report["comparison"] for seed_report in seed_reports]
    ratio_values = [comparison["best_baseline_to_hpp_mse_ratio"] for comparison in comparisons]
    accuracy_deltas = [comparison["hpp_accuracy_minus_best_baseline"] for comparison in comparisons]
    peak_values = [comparison["peak_allocated_mb"] for comparison in comparisons]

    aggregate = {
        "hpp_mse_wins": sum(1 for comparison in comparisons if comparison["hpp_won_mse"]),
        "hpp_accuracy_wins": sum(1 for comparison in comparisons if comparison["hpp_won_accuracy"]),
        "hpp_mse_win_rate": round(
            sum(1 for comparison in comparisons if comparison["hpp_won_mse"]) / len(comparisons),
            6,
        ),
        "hpp_accuracy_win_rate": round(
            sum(1 for comparison in comparisons if comparison["hpp_won_accuracy"]) / len(comparisons),
            6,
        ),
        "best_baseline_to_hpp_mse_ratio": summarize(ratio_values, "ratio"),
        "hpp_accuracy_minus_best_baseline": summarize(accuracy_deltas, "delta"),
        "peak_allocated_mb": summarize(peak_values, "mb"),
        "mlp_parameters": comparisons[0]["mlp_parameters"],
        "gru_parameters": comparisons[0]["gru_parameters"],
        "hpp_memory_values": comparisons[0]["hpp_memory_values"],
    }

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "mode": args.mode,
        "device": report.device,
        "device_name": report.device_name,
        "cuda_available": report.cuda_available,
        "cuda_version": report.cuda_version,
        "seeds": seeds,
        "classes": args.classes,
        "dim": args.dim,
        "hidden": args.hidden,
        "batch": args.batch,
        "exposures_per_class": args.exposures_per_class,
        "train_steps": args.train_steps,
        "eval_batches": args.eval_batches,
        "train_noise": args.train_noise,
        "eval_noise": args.eval_noise,
        "distractor_scale": args.distractor_scale,
        "aggregate": aggregate,
        "seed_reports": seed_reports,
        "boundary": "Synthetic attractor-recovery mechanism sweep only.",
    }

    json_path = Path(f"docs/named-baseline-sweep-{args.mode}.json")
    summary_path = Path("docs/named-baseline-sweep-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_summary(result, summary_path)

    print(json.dumps(aggregate, indent=2))
    print(f"wrote={json_path}")
    print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
