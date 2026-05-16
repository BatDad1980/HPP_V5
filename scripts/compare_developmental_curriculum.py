"""Compare a flat learner against a staged HPP developmental learner.

This is a toy mechanism harness, not a general intelligence benchmark. It asks
one narrow question: does staged plasticity plus Habit-14 protection recover a
target attractor better than a flat all-at-once prototype under distractors?
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from src.hpp_kernel.device import select_device


@dataclass
class FlatPrototype:
    """Single-phase learner that averages everything it sees."""

    prototype: torch.Tensor
    observations: int = 0
    learning_rate: float = 0.18

    def observe(self, sample: torch.Tensor) -> None:
        batch_mean = sample.mean(dim=0, keepdim=True)
        if self.observations == 0:
            self.prototype = batch_mean.detach().clone()
        else:
            self.prototype = (
                (1.0 - self.learning_rate) * self.prototype
                + self.learning_rate * batch_mean.detach()
            )
        self.observations += 1

    def recall(self, noisy: torch.Tensor, blend: float) -> torch.Tensor:
        return noisy * (1.0 - blend) + self.prototype * blend


@dataclass
class DevelopmentalMemory:
    """HPP-style staged learner with maturity-dependent protection."""

    prototype: torch.Tensor
    exposures: int = 0
    threshold: int = 14
    learning_rate: float = 0.35
    distractor_learning_rate: float = 0.04

    def observe(self, sample: torch.Tensor, *, is_target_context: bool) -> None:
        batch_mean = sample.mean(dim=0, keepdim=True)
        rate = self.learning_rate if is_target_context else self.distractor_learning_rate

        if self.exposures == 0:
            self.prototype = batch_mean.detach().clone()
        else:
            self.prototype = (
                (1.0 - rate) * self.prototype
                + rate * batch_mean.detach()
            )

        if is_target_context:
            self.exposures += 1

    @property
    def locked(self) -> bool:
        return self.exposures >= self.threshold

    @property
    def protection(self) -> float:
        if not self.locked:
            return 0.0
        over_threshold = self.exposures - self.threshold
        return min(0.9, 0.68 + over_threshold * 0.025)

    def recall(self, noisy: torch.Tensor) -> torch.Tensor:
        protection = self.protection
        return noisy * (1.0 - protection) + self.prototype * protection


def mse(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.mean((a - b) ** 2).detach().cpu())


def summarize(values: list[float], prefix: str) -> dict[str, float | int]:
    return {
        "runs": len(values),
        f"{prefix}_min": round(min(values), 8),
        f"{prefix}_mean": round(mean(values), 8),
        f"{prefix}_median": round(median(values), 8),
        f"{prefix}_max": round(max(values), 8),
    }


def observe_stage(
    *,
    flat: FlatPrototype,
    hpp: DevelopmentalMemory,
    target: torch.Tensor,
    distractor: torch.Tensor,
    batch: int,
    noise: float,
    distractor_ratio: float,
) -> dict[str, object]:
    target_events = 0
    distractor_events = 0
    total_events = batch

    for index in range(total_events):
        is_distractor = index < int(total_events * distractor_ratio)
        base = distractor if is_distractor else target
        sample = base + torch.randn_like(base) * noise

        flat.observe(sample)
        hpp.observe(sample, is_target_context=not is_distractor)

        if is_distractor:
            distractor_events += 1
        else:
            target_events += 1

    return {
        "target_events": target_events,
        "distractor_events": distractor_events,
        "hpp_exposures": hpp.exposures,
        "hpp_locked": hpp.locked,
        "hpp_protection": round(hpp.protection, 4),
    }


def evaluate(
    *,
    flat: FlatPrototype,
    hpp: DevelopmentalMemory,
    target: torch.Tensor,
    distractor: torch.Tensor,
    batch: int,
    recall_noise: float,
    shifted_context: bool,
    flat_blend: float,
    trials: int,
) -> dict[str, object]:
    flat_errors = []
    hpp_errors = []
    noisy_errors = []
    improvement_ratios = []

    for trial in range(trials):
        shift = 0.12 * torch.sin(torch.tensor(float(trial), device=target.device))
        clean = target + shift if shifted_context else target
        distractor_pressure = 0.18 * distractor if shifted_context else 0.0
        noisy = clean.expand(batch, -1) + distractor_pressure + torch.randn(batch, target.shape[1], device=target.device) * recall_noise

        flat_out = flat.recall(noisy, blend=flat_blend)
        hpp_out = hpp.recall(noisy)

        noisy_error = mse(noisy, clean.expand(batch, -1))
        flat_error = mse(flat_out, clean.expand(batch, -1))
        hpp_error = mse(hpp_out, clean.expand(batch, -1))

        noisy_errors.append(noisy_error)
        flat_errors.append(flat_error)
        hpp_errors.append(hpp_error)
        improvement_ratios.append(flat_error / max(hpp_error, 1e-12))

    return {
        "shifted_context": shifted_context,
        "noisy": summarize(noisy_errors, "mse"),
        "flat": summarize(flat_errors, "mse"),
        "hpp": summarize(hpp_errors, "mse"),
        "hpp_vs_flat": summarize(improvement_ratios, "ratio"),
    }


def write_summary(result: dict[str, object], output_path: Path) -> None:
    comparison = result["comparison"]
    lines = [
        "# Developmental Curriculum Summary",
        "",
        "This toy harness compares a flat all-at-once prototype against staged HPP developmental memory.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Dimension: `{result['dim']}`",
        f"- Habit threshold: `{result['threshold']}`",
        "",
        "## Result",
        "",
        f"- Clean-context HPP/flat improvement: `{comparison['clean_context_hpp_vs_flat_mean']}x`",
        f"- Shifted-context HPP/flat improvement: `{comparison['shifted_context_hpp_vs_flat_mean']}x`",
        f"- HPP locked: `{comparison['hpp_locked']}`",
        f"- HPP protection: `{comparison['hpp_protection']}`",
        "",
        "## Boundary",
        "",
        "This is mechanism evidence only. It does not prove language ability, agency, or general intelligence.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="demo")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--threshold", type=int, default=14)
    parser.add_argument("--infant-events", type=int, default=4)
    parser.add_argument("--nurture-events", type=int, default=10)
    parser.add_argument("--scaffold-events", type=int, default=7)
    parser.add_argument("--noise", type=float, default=0.24)
    parser.add_argument("--recall-noise", type=float, default=0.78)
    parser.add_argument("--distractor-ratio", type=float, default=0.3)
    parser.add_argument("--flat-learning-rate", type=float, default=0.18)
    parser.add_argument("--flat-blend", type=float, default=0.68)
    parser.add_argument("--hpp-learning-rate", type=float, default=0.35)
    parser.add_argument("--hpp-distractor-learning-rate", type=float, default=0.04)
    parser.add_argument("--trials", type=int, default=25)
    parser.add_argument("--seed", type=int, default=14)
    parser.add_argument("--output-tag", type=str, default="")
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)
    torch.manual_seed(args.seed)

    target = torch.randn(1, args.dim, device=device)
    distractor = torch.randn(1, args.dim, device=device)

    flat = FlatPrototype(
        prototype=torch.zeros_like(target),
        learning_rate=args.flat_learning_rate,
    )
    hpp = DevelopmentalMemory(
        prototype=torch.zeros_like(target),
        threshold=args.threshold,
        learning_rate=args.hpp_learning_rate,
        distractor_learning_rate=args.hpp_distractor_learning_rate,
    )

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    start = perf_counter()

    stages = [
        {
            "name": "infant",
            "events": args.infant_events,
            "noise": args.noise * 1.35,
            "distractor_ratio": args.distractor_ratio,
        },
        {
            "name": "nurture",
            "events": args.nurture_events,
            "noise": args.noise,
            "distractor_ratio": args.distractor_ratio * 0.5,
        },
        {
            "name": "scaffold",
            "events": args.scaffold_events,
            "noise": args.noise * 0.85,
            "distractor_ratio": args.distractor_ratio * 0.25,
        },
    ]

    stage_reports = []
    for stage in stages:
        stage_reports.append(
            {
                "name": stage["name"],
                **observe_stage(
                    flat=flat,
                    hpp=hpp,
                    target=target,
                    distractor=distractor,
                    batch=stage["events"],
                    noise=stage["noise"],
                    distractor_ratio=stage["distractor_ratio"],
                ),
            }
        )

    clean_eval = evaluate(
        flat=flat,
        hpp=hpp,
        target=target,
        distractor=distractor,
        batch=args.batch,
        recall_noise=args.recall_noise,
        shifted_context=False,
        flat_blend=args.flat_blend,
        trials=args.trials,
    )
    shifted_eval = evaluate(
        flat=flat,
        hpp=hpp,
        target=target,
        distractor=distractor,
        batch=args.batch,
        recall_noise=args.recall_noise,
        shifted_context=True,
        flat_blend=args.flat_blend,
        trials=args.trials,
    )

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    elapsed_ms = (perf_counter() - start) * 1000

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
        "threshold": args.threshold,
        "noise": args.noise,
        "recall_noise": args.recall_noise,
        "distractor_ratio": args.distractor_ratio,
        "elapsed_ms": round(elapsed_ms, 3),
        "stage_reports": stage_reports,
        "clean_context": clean_eval,
        "shifted_context": shifted_eval,
        "comparison": {
            "flat_observations": flat.observations,
            "hpp_exposures": hpp.exposures,
            "hpp_locked": hpp.locked,
            "hpp_protection": round(hpp.protection, 4),
            "flat_prototype_mse": round(mse(flat.prototype, target), 8),
            "hpp_prototype_mse": round(mse(hpp.prototype, target), 8),
            "clean_context_hpp_vs_flat_mean": clean_eval["hpp_vs_flat"]["ratio_mean"],
            "shifted_context_hpp_vs_flat_mean": shifted_eval["hpp_vs_flat"]["ratio_mean"],
        },
    }

    suffix = f"-{args.output_tag}" if args.output_tag else ""
    json_path = Path(f"docs/developmental-curriculum-{args.mode}{suffix}.json")
    summary_path = Path("docs/developmental-curriculum-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if not args.output_tag:
        write_summary(result, summary_path)

    print(json.dumps(result["comparison"], indent=2))
    print(f"wrote={json_path}")
    if not args.output_tag:
        print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
