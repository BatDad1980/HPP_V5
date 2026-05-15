"""Compare recurrent depth to a one-pass baseline under a similar parameter budget."""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from src.hpp_kernel.device import select_device
from src.hpp_kernel.tiny_recurrent import TinyOnePassAdapter, TinyRecurrentWorkshop, count_parameters


def find_baseline_width(input_dim: int, target_params: int, max_width: int = 1024) -> tuple[int, int]:
    best_width = 1
    best_params = count_parameters(TinyOnePassAdapter(input_dim=input_dim, hidden_dim=best_width))
    best_delta = abs(best_params - target_params)

    for width in range(1, max_width + 1):
        params = count_parameters(TinyOnePassAdapter(input_dim=input_dim, hidden_dim=width))
        delta = abs(params - target_params)
        if delta < best_delta:
            best_width = width
            best_params = params
            best_delta = delta

    return best_width, best_params


def run_once(
    model: torch.nn.Module,
    x: torch.Tensor,
    target: torch.Tensor,
    device: torch.device,
    passes: int | None = None,
) -> dict[str, object]:
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    start = perf_counter()
    with torch.no_grad():
        output = model(x, passes=passes) if passes is not None else model(x)

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    mse = torch.mean((output - target) ** 2).detach().cpu().item()
    return {
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "output_norm": round(float(output.norm().detach().cpu()), 6),
        "target_mse": round(float(mse), 8),
    }


def summarize(runs: list[dict[str, object]], key: str) -> dict[str, float | int]:
    values = [float(run[key]) for run in runs]
    return {
        "runs": len(runs),
        f"{key}_min": round(min(values), 6),
        f"{key}_mean": round(mean(values), 6),
        f"{key}_median": round(median(values), 6),
        f"{key}_max": round(max(values), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="plugged")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--passes", type=int, default=14)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)

    recurrent_seed = 14
    torch.manual_seed(recurrent_seed)
    recurrent = TinyRecurrentWorkshop(dim=args.dim).to(device).eval()
    recurrent_params = count_parameters(recurrent)
    baseline_width, baseline_params = find_baseline_width(args.dim, recurrent_params)

    torch.manual_seed(recurrent_seed)
    baseline = TinyOnePassAdapter(input_dim=args.dim, hidden_dim=baseline_width).to(device).eval()

    torch.manual_seed(1400)
    x = torch.randn(args.batch, args.dim, device=device)
    target = torch.tanh(x * 0.7)

    for _ in range(args.warmups):
        run_once(recurrent, x, target, device, passes=args.passes)
        run_once(baseline, x, target, device)

    recurrent_runs = [run_once(recurrent, x, target, device, passes=args.passes) for _ in range(args.runs)]
    baseline_runs = [run_once(baseline, x, target, device) for _ in range(args.runs)]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "mode": args.mode,
        "device": report.device,
        "device_name": report.device_name,
        "cuda_available": report.cuda_available,
        "dim": args.dim,
        "batch": args.batch,
        "passes": args.passes,
        "warmups": args.warmups,
        "runs": args.runs,
        "recurrent": {
            "parameters": recurrent_params,
            "summary_latency": summarize(recurrent_runs, "elapsed_ms"),
            "summary_target_mse": summarize(recurrent_runs, "target_mse"),
            "runs": recurrent_runs,
        },
        "one_pass_baseline": {
            "hidden_width": baseline_width,
            "parameters": baseline_params,
            "summary_latency": summarize(baseline_runs, "elapsed_ms"),
            "summary_target_mse": summarize(baseline_runs, "target_mse"),
            "runs": baseline_runs,
        },
        "comparison": {
            "parameter_ratio_baseline_to_recurrent": round(baseline_params / recurrent_params, 3),
            "mean_latency_ratio_baseline_to_recurrent": round(
                summarize(baseline_runs, "elapsed_ms")["elapsed_ms_mean"]
                / summarize(recurrent_runs, "elapsed_ms")["elapsed_ms_mean"],
                3,
            ),
            "mean_mse_ratio_baseline_to_recurrent": round(
                summarize(baseline_runs, "target_mse")["target_mse_mean"]
                / summarize(recurrent_runs, "target_mse")["target_mse_mean"],
                3,
            ),
        },
    }

    output_path = Path(f"docs/fixed-budget-comparison-{args.mode}.json")
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["comparison"], indent=2))
    print(f"wrote={output_path}")


if __name__ == "__main__":
    main()
