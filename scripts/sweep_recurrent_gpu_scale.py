"""Run a controlled CUDA scaling sweep for the HPP recurrent workshop.

This is a plugged-in benchmark for finding the practical RTX 4050 envelope. It
does not train. It runs inference-only recurrent passes with increasing hidden
dimensions and records latency plus peak CUDA memory.
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
from src.hpp_kernel.tiny_recurrent import TinyRecurrentWorkshop, count_parameters


def summarize(values: list[float], prefix: str) -> dict[str, float | int]:
    return {
        "runs": len(values),
        f"{prefix}_min": round(min(values), 6),
        f"{prefix}_mean": round(mean(values), 6),
        f"{prefix}_median": round(median(values), 6),
        f"{prefix}_max": round(max(values), 6),
    }


def run_once(
    *,
    device: torch.device,
    dim: int,
    batch: int,
    passes: int,
    warmups: int,
    runs: int,
) -> dict[str, object]:
    torch.manual_seed(14 + dim + batch + passes)
    model = TinyRecurrentWorkshop(dim=dim).to(device).eval()
    x = torch.randn(batch, dim, device=device)

    if device.type == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)

    with torch.no_grad():
        for _ in range(warmups):
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
            output = model(x, passes=passes)
            if device.type == "cuda":
                torch.cuda.synchronize(device)
            elapsed_ms = (perf_counter() - start) * 1000
            timings.append(elapsed_ms)
            output_norm = float(output.norm().detach().cpu())

    parameters = count_parameters(model)
    peak_allocated_mb = (
        torch.cuda.max_memory_allocated(device) / 1024 / 1024
        if device.type == "cuda"
        else 0.0
    )
    peak_reserved_mb = (
        torch.cuda.max_memory_reserved(device) / 1024 / 1024
        if device.type == "cuda"
        else 0.0
    )
    current_allocated_mb = (
        torch.cuda.memory_allocated(device) / 1024 / 1024
        if device.type == "cuda"
        else 0.0
    )
    effective_token_steps = batch * passes
    mean_ms = mean(timings)

    del model
    del x
    if device.type == "cuda":
        torch.cuda.empty_cache()

    return {
        "dim": dim,
        "batch": batch,
        "passes": passes,
        "parameters": parameters,
        "parameter_mb_fp32": round(parameters * 4 / 1024 / 1024, 3),
        "timing": summarize(timings, "elapsed_ms"),
        "peak_allocated_mb": round(peak_allocated_mb, 3),
        "peak_reserved_mb": round(peak_reserved_mb, 3),
        "current_allocated_mb_before_cleanup": round(current_allocated_mb, 3),
        "effective_token_steps": effective_token_steps,
        "effective_token_steps_per_second": round(effective_token_steps / (mean_ms / 1000), 3),
        "output_norm": round(output_norm, 6),
        "status": "ok",
    }


def write_summary(result: dict[str, object], output_path: Path) -> None:
    successful = [row for row in result["results"] if row["status"] == "ok"]
    largest = successful[-1] if successful else None

    lines = [
        "# Recurrent GPU Scaling Summary",
        "",
        "This benchmark probes the HPP recurrent workshop envelope on the local plugged-in GPU.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Passes: `{result['passes']}`",
        f"- Runs per size: `{result['runs_per_size']}`",
        "",
        "## Results",
        "",
        "| Dim | Batch | Parameters | Mean ms | Peak MB | Steps/sec | Status |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | :--- |",
    ]

    for row in result["results"]:
        if row["status"] == "ok":
            lines.append(
                f"| {row['dim']} | {row['batch']} | {row['parameters']} | "
                f"{row['timing']['elapsed_ms_mean']} | {row['peak_allocated_mb']} | "
                f"{row['effective_token_steps_per_second']} | ok |"
            )
        else:
            lines.append(
                f"| {row['dim']} | {row['batch']} | - | - | - | - | {row['status']} |"
            )

    if largest:
        lines.extend(
            [
                "",
                "## Largest Successful Size",
                "",
                f"- Dimension: `{largest['dim']}`",
                f"- Batch: `{largest['batch']}`",
                f"- Parameters: `{largest['parameters']}`",
                f"- FP32 parameter footprint: `{largest['parameter_mb_fp32']} MB`",
                f"- Mean latency: `{largest['timing']['elapsed_ms_mean']} ms`",
                f"- Peak allocated CUDA memory: `{largest['peak_allocated_mb']} MB`",
                "",
            ]
        )

    lines.extend(
        [
            "## Boundary",
            "",
            "This is inference-only scaling evidence. It does not measure training, optimizer state, checkpoint loading, or model quality.",
            "",
        ]
    )
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["plugged", "auto"], default="plugged")
    parser.add_argument("--dims", type=str, default="256,512,1024,2048,3072,4096")
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--passes", type=int, default=14)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--stop-on-oom", action="store_true")
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)
    dims = [int(value.strip()) for value in args.dims.split(",") if value.strip()]

    results = []
    for dim in dims:
        try:
            row = run_once(
                device=device,
                dim=dim,
                batch=args.batch,
                passes=args.passes,
                warmups=args.warmups,
                runs=args.runs,
            )
        except RuntimeError as exc:
            message = str(exc)
            status = "cuda_oom" if "out of memory" in message.lower() else "runtime_error"
            row = {
                "dim": dim,
                "batch": args.batch,
                "passes": args.passes,
                "status": status,
                "error": message[:500],
            }
            if device.type == "cuda":
                torch.cuda.empty_cache()
            results.append(row)
            print(json.dumps(row, indent=2))
            if args.stop_on_oom and status == "cuda_oom":
                break
            continue

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

    json_path = Path("docs/recurrent-gpu-scaling-plugged.json")
    summary_path = Path("docs/recurrent-gpu-scaling-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_summary(result, summary_path)
    print(f"wrote={json_path}")
    print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
