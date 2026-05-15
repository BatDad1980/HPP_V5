"""Compare iterative stabilization against a one-pass stabilizer.

This harness tests the mechanism HPP cares about: repeated safe loops moving a
noisy state toward a stable attractor. It is not a learned quality benchmark.
The attractor is explicit so the measurement is easy to inspect.
"""

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
from torch import nn

from src.hpp_kernel.device import select_device
from src.hpp_kernel.tiny_recurrent import count_parameters


class TinyAttractorStabilizer(nn.Module):
    """Shared update rule that moves state toward a stored attractor."""

    def __init__(self, attractor: torch.Tensor, step_size: float = 0.18):
        super().__init__()
        self.attractor = nn.Parameter(attractor.detach().clone())
        # Keep the actual step bounded and inspectable.
        step_size = max(1e-4, min(step_size, 0.9999))
        self.step_logit = nn.Parameter(torch.logit(torch.tensor(step_size)))

    def forward(self, x: torch.Tensor, passes: int) -> tuple[torch.Tensor, list[float]]:
        state = x
        trajectory = []
        alpha = torch.sigmoid(self.step_logit)
        for _ in range(passes):
            state = state + alpha * (self.attractor - state)
            trajectory.append(float(torch.mean((state - self.attractor) ** 2).detach().cpu()))
        return state, trajectory


def run_once(
    stabilizer: TinyAttractorStabilizer,
    noisy: torch.Tensor,
    device: torch.device,
    passes: int,
) -> dict[str, object]:
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    start = perf_counter()
    with torch.no_grad():
        output, trajectory = stabilizer(noisy, passes=passes)

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    initial_mse = float(torch.mean((noisy - stabilizer.attractor) ** 2).detach().cpu())
    final_mse = float(torch.mean((output - stabilizer.attractor) ** 2).detach().cpu())
    improvement = initial_mse / max(final_mse, 1e-12)

    return {
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "initial_mse": round(initial_mse, 8),
        "final_mse": round(final_mse, 8),
        "improvement_ratio": round(improvement, 6),
        "trajectory_mse": [round(value, 8) for value in trajectory],
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
    parser.add_argument("--noise", type=float, default=0.75)
    parser.add_argument("--step-size", type=float, default=0.18)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--runs", type=int, default=10)
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)

    torch.manual_seed(14)
    attractor = torch.randn(1, args.dim, device=device)
    clean = attractor.expand(args.batch, -1)
    noisy = clean + torch.randn(args.batch, args.dim, device=device) * args.noise

    recurrent = TinyAttractorStabilizer(attractor=attractor, step_size=args.step_size).to(device).eval()
    one_pass = TinyAttractorStabilizer(attractor=attractor, step_size=args.step_size).to(device).eval()

    for _ in range(args.warmups):
        run_once(recurrent, noisy, device, passes=args.passes)
        run_once(one_pass, noisy, device, passes=1)

    recurrent_runs = [run_once(recurrent, noisy, device, passes=args.passes) for _ in range(args.runs)]
    one_pass_runs = [run_once(one_pass, noisy, device, passes=1) for _ in range(args.runs)]

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
        "noise": args.noise,
        "step_size": args.step_size,
        "warmups": args.warmups,
        "runs": args.runs,
        "recurrent": {
            "parameters": count_parameters(recurrent),
            "summary_latency": summarize(recurrent_runs, "elapsed_ms"),
            "summary_final_mse": summarize(recurrent_runs, "final_mse"),
            "summary_improvement": summarize(recurrent_runs, "improvement_ratio"),
            "example_trajectory_mse": recurrent_runs[-1]["trajectory_mse"],
            "runs": recurrent_runs,
        },
        "one_pass": {
            "parameters": count_parameters(one_pass),
            "summary_latency": summarize(one_pass_runs, "elapsed_ms"),
            "summary_final_mse": summarize(one_pass_runs, "final_mse"),
            "summary_improvement": summarize(one_pass_runs, "improvement_ratio"),
            "runs": one_pass_runs,
        },
        "comparison": {
            "parameter_ratio_one_pass_to_recurrent": round(count_parameters(one_pass) / count_parameters(recurrent), 3),
            "final_mse_ratio_one_pass_to_recurrent": round(
                summarize(one_pass_runs, "final_mse")["final_mse_mean"]
                / summarize(recurrent_runs, "final_mse")["final_mse_mean"],
                3,
            ),
            "improvement_ratio_recurrent_to_one_pass": round(
                summarize(recurrent_runs, "improvement_ratio")["improvement_ratio_mean"]
                / summarize(one_pass_runs, "improvement_ratio")["improvement_ratio_mean"],
                3,
            ),
            "mean_latency_ratio_recurrent_to_one_pass": round(
                summarize(recurrent_runs, "elapsed_ms")["elapsed_ms_mean"]
                / summarize(one_pass_runs, "elapsed_ms")["elapsed_ms_mean"],
                3,
            ),
        },
    }

    output_path = Path(f"docs/iterative-stability-{args.mode}.json")
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["comparison"], indent=2))
    print(f"wrote={output_path}")


if __name__ == "__main__":
    main()
