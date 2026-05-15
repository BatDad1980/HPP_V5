"""Compare noisy recall before and after a Habit-14 style memory lock.

This is a toy mechanism harness, not a learned intelligence benchmark. It tests
one narrow HPP claim: repeated safe exposure can create a protected pathway that
resists later noise better than an unprotected pass-through state.
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

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch

from src.hpp_kernel.device import select_device


@dataclass
class HabitMemory:
    prototype: torch.Tensor
    exposures: int = 0
    threshold: int = 14
    learning_rate: float = 0.35

    def observe(self, sample: torch.Tensor) -> None:
        batch_mean = sample.mean(dim=0, keepdim=True)
        if self.exposures == 0:
            self.prototype = batch_mean.detach().clone()
        else:
            self.prototype = (
                (1.0 - self.learning_rate) * self.prototype
                + self.learning_rate * batch_mean.detach()
            )
        self.exposures += 1

    @property
    def is_locked(self) -> bool:
        return self.exposures >= self.threshold

    @property
    def protection(self) -> float:
        if not self.is_locked:
            return 0.0
        over_threshold = self.exposures - self.threshold
        return min(0.92, 0.72 + over_threshold * 0.025)

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


def run_condition(
    *,
    clean: torch.Tensor,
    exposures: int,
    threshold: int,
    exposure_noise: float,
    recall_noise: float,
    learning_rate: float,
    trials: int,
) -> dict[str, object]:
    memory = HabitMemory(
        prototype=torch.zeros_like(clean[:1]),
        threshold=threshold,
        learning_rate=learning_rate,
    )

    for _ in range(exposures):
        sample = clean + torch.randn_like(clean) * exposure_noise
        memory.observe(sample)

    baseline_errors = []
    protected_errors = []
    improvement_ratios = []

    for _ in range(trials):
        noisy = clean + torch.randn_like(clean) * recall_noise
        baseline_error = mse(noisy, clean)
        protected_error = mse(memory.recall(noisy), clean)
        baseline_errors.append(baseline_error)
        protected_errors.append(protected_error)
        improvement_ratios.append(baseline_error / max(protected_error, 1e-12))

    return {
        "exposures": exposures,
        "threshold": threshold,
        "locked": memory.is_locked,
        "protection": round(memory.protection, 4),
        "prototype_mse": round(mse(memory.prototype.expand_as(clean), clean), 8),
        "baseline": summarize(baseline_errors, "mse"),
        "protected": summarize(protected_errors, "mse"),
        "improvement": summarize(improvement_ratios, "ratio"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="plugged")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--threshold", type=int, default=14)
    parser.add_argument("--exposures", type=str, default="1,7,14,21")
    parser.add_argument("--exposure-noise", type=float, default=0.22)
    parser.add_argument("--recall-noise", type=float, default=0.95)
    parser.add_argument("--learning-rate", type=float, default=0.35)
    parser.add_argument("--trials", type=int, default=25)
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)

    torch.manual_seed(14)
    target = torch.randn(1, args.dim, device=device)
    clean = target.expand(args.batch, -1)
    exposure_counts = [int(value.strip()) for value in args.exposures.split(",") if value.strip()]

    conditions = [
        run_condition(
            clean=clean,
            exposures=count,
            threshold=args.threshold,
            exposure_noise=args.exposure_noise,
            recall_noise=args.recall_noise,
            learning_rate=args.learning_rate,
            trials=args.trials,
        )
        for count in exposure_counts
    ]

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "mode": args.mode,
        "device": report.device,
        "device_name": report.device_name,
        "cuda_available": report.cuda_available,
        "dim": args.dim,
        "batch": args.batch,
        "threshold": args.threshold,
        "exposure_noise": args.exposure_noise,
        "recall_noise": args.recall_noise,
        "learning_rate": args.learning_rate,
        "trials": args.trials,
        "conditions": conditions,
    }

    output_path = Path(f"docs/habit-memory-{args.mode}.json")
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    compact = {
        str(condition["exposures"]): {
            "locked": condition["locked"],
            "protection": condition["protection"],
            "protected_mse_mean": condition["protected"]["mse_mean"],
            "improvement_mean": condition["improvement"]["ratio_mean"],
        }
        for condition in conditions
    }
    print(json.dumps(compact, indent=2))
    print(f"wrote={output_path}")


if __name__ == "__main__":
    main()
