"""Test Habit-14 recall when the same core signal appears in changed contexts.

The earlier Habit-14 harness repeats an identical attractor. This one adds a
context term and compares a rigid full-pattern lock against a context-adaptive
lock that preserves the core while allowing the current context to vary.
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
class RigidHabitMemory:
    prototype: torch.Tensor
    exposures: int = 0
    threshold: int = 14
    learning_rate: float = 0.35

    def observe(self, sample: torch.Tensor, context: torch.Tensor) -> None:
        del context
        batch_mean = sample.mean(dim=0, keepdim=True)
        self.prototype = update_prototype(
            self.prototype,
            batch_mean,
            self.exposures,
            self.learning_rate,
        )
        self.exposures += 1

    @property
    def locked(self) -> bool:
        return self.exposures >= self.threshold

    @property
    def protection(self) -> float:
        if not self.locked:
            return 0.0
        return min(0.9, 0.68 + (self.exposures - self.threshold) * 0.025)

    def recall(self, noisy: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        del context
        return blend(noisy, self.prototype, self.protection)


@dataclass
class ContextAdaptiveHabitMemory:
    core_prototype: torch.Tensor
    exposures: int = 0
    threshold: int = 14
    learning_rate: float = 0.35

    def observe(self, sample: torch.Tensor, context: torch.Tensor) -> None:
        core_estimate = sample - context
        batch_mean = core_estimate.mean(dim=0, keepdim=True)
        self.core_prototype = update_prototype(
            self.core_prototype,
            batch_mean,
            self.exposures,
            self.learning_rate,
        )
        self.exposures += 1

    @property
    def locked(self) -> bool:
        return self.exposures >= self.threshold

    @property
    def protection(self) -> float:
        if not self.locked:
            return 0.0
        return min(0.9, 0.68 + (self.exposures - self.threshold) * 0.025)

    def recall(self, noisy: torch.Tensor, context: torch.Tensor) -> torch.Tensor:
        contextual_target = self.core_prototype + context
        return blend(noisy, contextual_target, self.protection)


def update_prototype(
    prototype: torch.Tensor,
    batch_mean: torch.Tensor,
    exposures: int,
    learning_rate: float,
) -> torch.Tensor:
    if exposures == 0:
        return batch_mean.detach().clone()
    return (1.0 - learning_rate) * prototype + learning_rate * batch_mean.detach()


def blend(noisy: torch.Tensor, prototype: torch.Tensor, protection: float) -> torch.Tensor:
    return noisy * (1.0 - protection) + prototype * protection


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
    core: torch.Tensor,
    familiar_context: torch.Tensor,
    shifted_context: torch.Tensor,
    exposures: int,
    threshold: int,
    batch: int,
    exposure_noise: float,
    recall_noise: float,
    learning_rate: float,
    trials: int,
) -> dict[str, object]:
    rigid = RigidHabitMemory(
        prototype=torch.zeros_like(core),
        threshold=threshold,
        learning_rate=learning_rate,
    )
    adaptive = ContextAdaptiveHabitMemory(
        core_prototype=torch.zeros_like(core),
        threshold=threshold,
        learning_rate=learning_rate,
    )

    for index in range(exposures):
        context_weight = 0.75 + 0.25 * torch.sin(torch.tensor(float(index), device=core.device))
        context = familiar_context * context_weight
        clean = core + context
        sample = clean.expand(batch, -1) + torch.randn(batch, core.shape[1], device=core.device) * exposure_noise
        rigid.observe(sample, context)
        adaptive.observe(sample, context)

    familiar = evaluate_context(
        core=core,
        context=familiar_context,
        batch=batch,
        recall_noise=recall_noise,
        rigid=rigid,
        adaptive=adaptive,
        trials=trials,
    )
    shifted = evaluate_context(
        core=core,
        context=shifted_context,
        batch=batch,
        recall_noise=recall_noise,
        rigid=rigid,
        adaptive=adaptive,
        trials=trials,
    )

    return {
        "exposures": exposures,
        "threshold": threshold,
        "locked": adaptive.locked,
        "protection": round(adaptive.protection, 4),
        "rigid_prototype_mse_familiar": round(mse(rigid.prototype, core + familiar_context), 8),
        "adaptive_core_mse": round(mse(adaptive.core_prototype, core), 8),
        "familiar_context": familiar,
        "shifted_context": shifted,
    }


def evaluate_context(
    *,
    core: torch.Tensor,
    context: torch.Tensor,
    batch: int,
    recall_noise: float,
    rigid: RigidHabitMemory,
    adaptive: ContextAdaptiveHabitMemory,
    trials: int,
) -> dict[str, object]:
    baseline_errors = []
    rigid_errors = []
    adaptive_errors = []
    adaptive_vs_baseline = []
    adaptive_vs_rigid = []

    clean = core + context
    target = clean.expand(batch, -1)

    for _ in range(trials):
        noisy = target + torch.randn(batch, core.shape[1], device=core.device) * recall_noise
        rigid_out = rigid.recall(noisy, context)
        adaptive_out = adaptive.recall(noisy, context)

        baseline_error = mse(noisy, target)
        rigid_error = mse(rigid_out, target)
        adaptive_error = mse(adaptive_out, target)

        baseline_errors.append(baseline_error)
        rigid_errors.append(rigid_error)
        adaptive_errors.append(adaptive_error)
        adaptive_vs_baseline.append(baseline_error / max(adaptive_error, 1e-12))
        adaptive_vs_rigid.append(rigid_error / max(adaptive_error, 1e-12))

    return {
        "baseline": summarize(baseline_errors, "mse"),
        "rigid": summarize(rigid_errors, "mse"),
        "adaptive": summarize(adaptive_errors, "mse"),
        "adaptive_vs_baseline": summarize(adaptive_vs_baseline, "ratio"),
        "adaptive_vs_rigid": summarize(adaptive_vs_rigid, "ratio"),
    }


def write_summary(result: dict[str, object], output_path: Path) -> None:
    final_condition = result["conditions"][-1]
    lines = [
        "# Changed-Context Habit Memory Summary",
        "",
        "This harness tests whether Habit-14 can protect a core pathway without becoming brittle when context changes.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Habit threshold: `{result['threshold']}`",
        f"- Final exposures: `{final_condition['exposures']}`",
        f"- Final protection: `{final_condition['protection']}`",
        "",
        "## Result At Final Exposure Count",
        "",
        f"- Familiar-context adaptive/baseline improvement: `{final_condition['familiar_context']['adaptive_vs_baseline']['ratio_mean']}x`",
        f"- Shifted-context adaptive/baseline improvement: `{final_condition['shifted_context']['adaptive_vs_baseline']['ratio_mean']}x`",
        f"- Shifted-context adaptive/rigid improvement: `{final_condition['shifted_context']['adaptive_vs_rigid']['ratio_mean']}x`",
        "",
        "## Boundary",
        "",
        "This is mechanism evidence only. The context vector is known to the adaptive memory, so the result should be read as a design test for context-aware protection, not as autonomous context discovery.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="demo")
    parser.add_argument("--dim", type=int, default=128)
    parser.add_argument("--batch", type=int, default=64)
    parser.add_argument("--threshold", type=int, default=14)
    parser.add_argument("--exposures", type=str, default="1,7,14,21")
    parser.add_argument("--exposure-noise", type=float, default=0.22)
    parser.add_argument("--recall-noise", type=float, default=0.86)
    parser.add_argument("--context-scale", type=float, default=0.42)
    parser.add_argument("--learning-rate", type=float, default=0.35)
    parser.add_argument("--trials", type=int, default=25)
    parser.add_argument("--seed", type=int, default=14)
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)
    torch.manual_seed(args.seed)

    core = torch.randn(1, args.dim, device=device)
    familiar_context = torch.randn(1, args.dim, device=device) * args.context_scale
    shifted_context = torch.randn(1, args.dim, device=device) * args.context_scale
    exposure_counts = [int(value.strip()) for value in args.exposures.split(",") if value.strip()]

    if device.type == "cuda":
        torch.cuda.synchronize(device)
    start = perf_counter()

    conditions = [
        run_condition(
            core=core,
            familiar_context=familiar_context,
            shifted_context=shifted_context,
            exposures=count,
            threshold=args.threshold,
            batch=args.batch,
            exposure_noise=args.exposure_noise,
            recall_noise=args.recall_noise,
            learning_rate=args.learning_rate,
            trials=args.trials,
        )
        for count in exposure_counts
    ]

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
        "allocated_mb": report.allocated_mb,
        "reserved_mb": report.reserved_mb,
        "seed": args.seed,
        "dim": args.dim,
        "batch": args.batch,
        "threshold": args.threshold,
        "exposure_noise": args.exposure_noise,
        "recall_noise": args.recall_noise,
        "context_scale": args.context_scale,
        "learning_rate": args.learning_rate,
        "trials": args.trials,
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "conditions": conditions,
    }

    json_path = Path(f"docs/changed-context-habit-memory-{args.mode}.json")
    summary_path = Path("docs/changed-context-habit-memory-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_summary(result, summary_path)

    compact = {
        str(condition["exposures"]): {
            "locked": condition["locked"],
            "protection": condition["protection"],
            "shifted_adaptive_vs_baseline": condition["shifted_context"]["adaptive_vs_baseline"]["ratio_mean"],
            "shifted_adaptive_vs_rigid": condition["shifted_context"]["adaptive_vs_rigid"]["ratio_mean"],
        }
        for condition in conditions
    }
    print(json.dumps(compact, indent=2))
    print(f"wrote={json_path}")
    print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
