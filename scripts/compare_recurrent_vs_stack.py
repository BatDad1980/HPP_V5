"""Compare shared recurrent depth against a unique-layer stack.

This is a diagnostic comparison for the HPP V5 efficiency thesis. It compares
parameter count and latency for the same number of effective refinement passes.
It does not train and keeps tensors intentionally small.
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

from src.hpp_kernel.device import select_device
from src.hpp_kernel.tiny_recurrent import TinyRecurrentWorkshop, TinyUniqueStack, count_parameters


def run_once(model: torch.nn.Module, x: torch.Tensor, device: torch.device, passes: int | None = None) -> dict[str, object]:
    if device.type == "cuda":
        torch.cuda.synchronize(device)

    start = perf_counter()
    with torch.no_grad():
        output = model(x, passes=passes) if passes is not None else model(x)

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    return {
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "output_norm": round(float(output.norm().detach().cpu()), 6),
    }


def summarize(runs: list[dict[str, object]]) -> dict[str, float | int]:
    timings = [float(run["elapsed_ms"]) for run in runs]
    return {
        "runs": len(runs),
        "elapsed_ms_min": round(min(timings), 3),
        "elapsed_ms_mean": round(mean(timings), 3),
        "elapsed_ms_median": round(median(timings), 3),
        "elapsed_ms_max": round(max(timings), 3),
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

    torch.manual_seed(14)
    x = torch.randn(args.batch, args.dim, device=device)
    recurrent = TinyRecurrentWorkshop(dim=args.dim).to(device).eval()
    stacked = TinyUniqueStack(dim=args.dim, depth=args.passes).to(device).eval()

    for _ in range(args.warmups):
        run_once(recurrent, x, device, passes=args.passes)
        run_once(stacked, x, device)

    recurrent_runs = [run_once(recurrent, x, device, passes=args.passes) for _ in range(args.runs)]
    stacked_runs = [run_once(stacked, x, device) for _ in range(args.runs)]

    recurrent_params = count_parameters(recurrent)
    stacked_params = count_parameters(stacked)

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
            "summary": summarize(recurrent_runs),
            "runs": recurrent_runs,
        },
        "unique_stack": {
            "parameters": stacked_params,
            "summary": summarize(stacked_runs),
            "runs": stacked_runs,
        },
        "comparison": {
            "parameter_ratio_unique_stack_to_recurrent": round(stacked_params / recurrent_params, 3),
            "mean_latency_ratio_unique_stack_to_recurrent": round(
                summarize(stacked_runs)["elapsed_ms_mean"] / summarize(recurrent_runs)["elapsed_ms_mean"], 3
            ),
        },
    }

    output_path = Path(f"docs/recurrent-vs-stack-{args.mode}.json")
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["comparison"], indent=2))
    print(f"wrote={output_path}")


if __name__ == "__main__":
    main()
