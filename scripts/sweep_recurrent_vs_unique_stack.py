"""Scale shared recurrent depth against a unique-layer stack.

This benchmark compares two ways to get the same effective depth:

- shared recurrent workshop: one block reused for every pass
- unique stack: a distinct block for every pass

It is inference-only and catches CUDA OOM so the practical boundary can be
recorded instead of guessed.
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


def summarize(values: list[float], prefix: str) -> dict[str, float | int]:
    return {
        "runs": len(values),
        f"{prefix}_min": round(min(values), 6),
        f"{prefix}_mean": round(mean(values), 6),
        f"{prefix}_median": round(median(values), 6),
        f"{prefix}_max": round(max(values), 6),
    }


def benchmark_model(
    *,
    model: torch.nn.Module,
    x: torch.Tensor,
    device: torch.device,
    passes: int | None,
    warmups: int,
    runs: int,
) -> dict[str, object]:
    if device.type == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    with torch.no_grad():
        for _ in range(warmups):
            if passes is None:
                _ = model(x)
            else:
                _ = model(x, passes=passes)

    if device.type == "cuda":
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)

    timings = []
    output_norm = 0.0
    with torch.no_grad():
        for _ in range(runs):
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            start = perf_counter()
            if passes is None:
                output = model(x)
            else:
                output = model(x, passes=passes)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            timings.append((perf_counter() - start) * 1000)
            output_norm = float(output.norm().detach().cpu())

    return {
        "parameters": count_parameters(model),
        "parameter_mb_fp32": round(count_parameters(model) * 4 / 1024 / 1024, 3),
        "timing": summarize(timings, "elapsed_ms"),
        "peak_allocated_mb": round(
            torch.cuda.max_memory_allocated(device) / 1024 / 1024
            if device.type == "cuda"
            else 0.0,
            3,
        ),
        "peak_reserved_mb": round(
            torch.cuda.max_memory_reserved(device) / 1024 / 1024
            if device.type == "cuda"
            else 0.0,
            3,
        ),
        "output_norm": round(output_norm, 6),
        "status": "ok",
    }


def run_dim(
    *,
    device: torch.device,
    dim: int,
    batch: int,
    passes: int,
    warmups: int,
    runs: int,
) -> dict[str, object]:
    torch.manual_seed(1400 + dim)
    x = torch.randn(batch, dim, device=device)

    row: dict[str, object] = {
        "dim": dim,
        "batch": batch,
        "passes": passes,
    }

    try:
        recurrent = TinyRecurrentWorkshop(dim=dim).to(device).eval()
        row["recurrent"] = benchmark_model(
            model=recurrent,
            x=x,
            device=device,
            passes=passes,
            warmups=warmups,
            runs=runs,
        )
        del recurrent
        if device.type == "cuda":
            torch.cuda.empty_cache()
    except RuntimeError as exc:
        row["recurrent"] = {
            "status": "cuda_oom" if "out of memory" in str(exc).lower() else "runtime_error",
            "error": str(exc)[:500],
        }
        if device.type == "cuda":
            torch.cuda.empty_cache()

    try:
        unique_stack = TinyUniqueStack(dim=dim, depth=passes).to(device).eval()
        row["unique_stack"] = benchmark_model(
            model=unique_stack,
            x=x,
            device=device,
            passes=None,
            warmups=warmups,
            runs=runs,
        )
        del unique_stack
        if device.type == "cuda":
            torch.cuda.empty_cache()
    except RuntimeError as exc:
        row["unique_stack"] = {
            "status": "cuda_oom" if "out of memory" in str(exc).lower() else "runtime_error",
            "error": str(exc)[:500],
        }
        if device.type == "cuda":
            torch.cuda.empty_cache()

    if (
        row["recurrent"].get("status") == "ok"
        and row["unique_stack"].get("status") == "ok"
    ):
        row["comparison"] = {
            "parameter_ratio_unique_to_recurrent": round(
                row["unique_stack"]["parameters"] / row["recurrent"]["parameters"],
                6,
            ),
            "peak_memory_ratio_unique_to_recurrent": round(
                row["unique_stack"]["peak_allocated_mb"]
                / max(row["recurrent"]["peak_allocated_mb"], 1e-12),
                6,
            ),
            "latency_ratio_unique_to_recurrent": round(
                row["unique_stack"]["timing"]["elapsed_ms_mean"]
                / max(row["recurrent"]["timing"]["elapsed_ms_mean"], 1e-12),
                6,
            ),
        }

    del x
    if device.type == "cuda":
        torch.cuda.empty_cache()
    return row


def write_summary(result: dict[str, object], output_path: Path) -> None:
    lines = [
        "# Recurrent vs Unique Stack Scaling Summary",
        "",
        "This benchmark compares shared recurrent depth against a unique-layer stack at the same effective pass count.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Passes/depth: `{result['passes']}`",
        f"- Batch: `{result['batch']}`",
        "",
        "## Results",
        "",
        "| Dim | Recurrent params | Unique params | Param ratio | Recurrent peak MB | Unique peak MB | Latency ratio | Status |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]

    largest_both = None
    largest_recurrent = None
    for row in result["results"]:
        recurrent = row["recurrent"]
        unique = row["unique_stack"]
        recurrent_ok = recurrent.get("status") == "ok"
        unique_ok = unique.get("status") == "ok"
        if recurrent_ok:
            largest_recurrent = row
        if recurrent_ok and unique_ok:
            largest_both = row
            comparison = row["comparison"]
            lines.append(
                f"| {row['dim']} | {recurrent['parameters']} | {unique['parameters']} | "
                f"{comparison['parameter_ratio_unique_to_recurrent']} | "
                f"{recurrent['peak_allocated_mb']} | {unique['peak_allocated_mb']} | "
                f"{comparison['latency_ratio_unique_to_recurrent']} | both ok |"
            )
        else:
            lines.append(
                f"| {row['dim']} | "
                f"{recurrent.get('parameters', '-')} | {unique.get('parameters', '-')} | "
                f"- | {recurrent.get('peak_allocated_mb', '-')} | {unique.get('peak_allocated_mb', '-')} | "
                f"- | recurrent={recurrent.get('status')}, unique={unique.get('status')} |"
            )

    if largest_both:
        lines.extend(
            [
                "",
                "## Largest Size Where Both Ran",
                "",
                f"- Dimension: `{largest_both['dim']}`",
                f"- Shared recurrent parameters: `{largest_both['recurrent']['parameters']}`",
                f"- Unique stack parameters: `{largest_both['unique_stack']['parameters']}`",
                f"- Parameter ratio: `{largest_both['comparison']['parameter_ratio_unique_to_recurrent']}x`",
                f"- Peak memory ratio: `{largest_both['comparison']['peak_memory_ratio_unique_to_recurrent']}x`",
                "",
            ]
        )

    if largest_recurrent:
        lines.extend(
            [
                "## Largest Recurrent Size",
                "",
                f"- Dimension: `{largest_recurrent['dim']}`",
                f"- Shared recurrent parameters: `{largest_recurrent['recurrent']['parameters']}`",
                f"- Shared recurrent peak memory: `{largest_recurrent['recurrent']['peak_allocated_mb']} MB`",
                "",
            ]
        )

    lines.extend(
        [
            "## Boundary",
            "",
            "This is inference-only scaling evidence. It does not measure training, optimizer state, learned quality, or production deployment efficiency.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["plugged", "auto"], default="plugged")
    parser.add_argument("--dims", type=str, default="512,1024,2048,4096,8192")
    parser.add_argument("--batch", type=int, default=2)
    parser.add_argument("--passes", type=int, default=14)
    parser.add_argument("--warmups", type=int, default=0)
    parser.add_argument("--runs", type=int, default=1)
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)
    dims = [int(value.strip()) for value in args.dims.split(",") if value.strip()]

    results = []
    for dim in dims:
        row = run_dim(
            device=device,
            dim=dim,
            batch=args.batch,
            passes=args.passes,
            warmups=args.warmups,
            runs=args.runs,
        )
        results.append(row)
        print(json.dumps(row, indent=2))

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "torch": torch.__version__,
        "mode": args.mode,
        "device": report.device,
        "device_name": report.device_name,
        "cuda_available": report.cuda_available,
        "cuda_version": report.cuda_version,
        "batch": args.batch,
        "passes": args.passes,
        "warmups": args.warmups,
        "runs_per_size": args.runs,
        "results": results,
    }

    json_path = Path("docs/recurrent-vs-unique-stack-scaling-plugged.json")
    summary_path = Path("docs/recurrent-vs-unique-stack-scaling-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_summary(result, summary_path)
    print(f"wrote={json_path}")
    print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
