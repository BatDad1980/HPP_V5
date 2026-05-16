"""Compare HPP developmental memory against named baseline mechanisms.

This is a synthetic attractor-recovery harness. It does not test language,
agency, or broad reasoning. It asks a narrower question: after staged noisy
exposure, which mechanism best recovers the intended clean attractor under
held-out noise?
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median, stdev
from time import perf_counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import torch
from torch import nn
from torch.nn import functional as F

from src.hpp_kernel.device import select_device
from src.hpp_kernel.tiny_recurrent import count_parameters


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


def make_clean_patterns(classes: int, dim: int, device: torch.device) -> torch.Tensor:
    clean = F.normalize(torch.randn(classes, dim, device=device), dim=1)
    return clean * 2.5


def sample_batch(
    clean: torch.Tensor,
    *,
    batch: int,
    noise: float,
    distractor_scale: float,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    labels = torch.randint(0, clean.shape[0], (batch,), device=device)
    targets = clean[labels]
    distractors = clean[torch.randint(0, clean.shape[0], (batch,), device=device)]
    inputs = targets + torch.randn_like(targets) * noise + distractors * distractor_scale
    return inputs, targets, labels


@dataclass
class HPPDevelopmentalMemory:
    prototypes: torch.Tensor
    exposures: torch.Tensor
    threshold: int = 14
    learning_rate: float = 0.36
    distractor_learning_rate: float = 0.03

    def observe(self, x: torch.Tensor, labels: torch.Tensor, *, trusted: bool) -> None:
        rate = self.learning_rate if trusted else self.distractor_learning_rate
        for label in labels.unique():
            mask = labels == label
            batch_mean = x[mask].mean(dim=0)
            index = int(label.detach().cpu())
            self.prototypes[index] = (1.0 - rate) * self.prototypes[index] + rate * batch_mean.detach()
            if trusted:
                self.exposures[index] += int(mask.sum().detach().cpu())

    def recall(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        distances = torch.cdist(x, self.prototypes)
        labels = torch.argmin(distances, dim=1)
        selected = self.prototypes[labels]
        exposure = self.exposures[labels].float().to(x.device)
        maturity = torch.clamp((exposure - self.threshold) / max(self.threshold, 1), 0.0, 1.0)
        protection = (0.55 + 0.43 * maturity).unsqueeze(1)
        return x * (1.0 - protection) + selected * protection, labels


class NearestCentroidBaseline:
    def __init__(self, classes: int, dim: int, device: torch.device):
        self.prototypes = torch.zeros(classes, dim, device=device)
        self.counts = torch.zeros(classes, device=device)

    def observe(self, x: torch.Tensor, labels: torch.Tensor) -> None:
        for label in labels.unique():
            mask = labels == label
            index = int(label.detach().cpu())
            count = float(mask.sum().detach().cpu())
            batch_mean = x[mask].mean(dim=0)
            old_count = self.counts[index]
            total = old_count + count
            self.prototypes[index] = (self.prototypes[index] * old_count + batch_mean.detach() * count) / total
            self.counts[index] = total

    def recall(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        distances = torch.cdist(x, self.prototypes)
        labels = torch.argmin(distances, dim=1)
        return self.prototypes[labels], labels


class OnePassMLPDenoiser(nn.Module):
    def __init__(self, dim: int, hidden: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(dim, hidden),
            nn.GELU(),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Linear(hidden, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class GRURefiner(nn.Module):
    def __init__(self, dim: int, hidden: int):
        super().__init__()
        self.in_proj = nn.Linear(dim, hidden)
        self.gru = nn.GRUCell(dim, hidden)
        self.out = nn.Linear(hidden, dim)

    def forward(self, x: torch.Tensor, passes: int = 4) -> torch.Tensor:
        hidden = torch.tanh(self.in_proj(x))
        state = x
        for _ in range(passes):
            hidden = self.gru(state, hidden)
            state = self.out(hidden)
        return state


def train_model(
    model: nn.Module,
    clean: torch.Tensor,
    *,
    steps: int,
    batch: int,
    noise: float,
    distractor_scale: float,
    lr: float,
    device: torch.device,
) -> list[float]:
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    losses = []
    model.train()
    for _ in range(steps):
        x, target, _ = sample_batch(
            clean,
            batch=batch,
            noise=noise,
            distractor_scale=distractor_scale,
            device=device,
        )
        output = model(x)
        loss = F.mse_loss(output, target)
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        optimizer.step()
        losses.append(float(loss.detach().cpu()))
    model.eval()
    return losses


def train_memories(
    clean: torch.Tensor,
    *,
    classes: int,
    dim: int,
    exposures_per_class: int,
    batch: int,
    noise: float,
    distractor_scale: float,
    device: torch.device,
) -> tuple[HPPDevelopmentalMemory, NearestCentroidBaseline]:
    hpp = HPPDevelopmentalMemory(
        prototypes=torch.zeros(classes, dim, device=device),
        exposures=torch.zeros(classes, device=device, dtype=torch.long),
    )
    nearest = NearestCentroidBaseline(classes, dim, device)
    total_observations = classes * exposures_per_class
    steps = max(1, total_observations // batch)

    for index in range(steps):
        trusted = index >= max(1, steps // 4)
        current_noise = noise * (1.25 if not trusted else 0.85)
        current_distractor = distractor_scale * (1.35 if not trusted else 0.65)
        x, target, labels = sample_batch(
            clean,
            batch=batch,
            noise=current_noise,
            distractor_scale=current_distractor,
            device=device,
        )
        hpp_signal = target if trusted else x
        hpp.observe(hpp_signal, labels, trusted=trusted)
        nearest.observe(x, labels)

    return hpp, nearest


def evaluate(
    name: str,
    recall,
    clean: torch.Tensor,
    *,
    batches: int,
    batch: int,
    noise: float,
    distractor_scale: float,
    device: torch.device,
) -> dict[str, object]:
    errors = []
    accuracies = []
    latencies = []

    for _ in range(batches):
        x, target, labels = sample_batch(
            clean,
            batch=batch,
            noise=noise,
            distractor_scale=distractor_scale,
            device=device,
        )
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        start = perf_counter()
        with torch.no_grad():
            output, predicted = recall(x)
        if device.type == "cuda":
            torch.cuda.synchronize(device)
        latencies.append((perf_counter() - start) * 1000)
        errors.append(mse(output, target))
        accuracies.append(float((predicted == labels).float().mean().detach().cpu()))

    return {
        "name": name,
        "mse": summarize(errors, "mse"),
        "accuracy": summarize(accuracies, "accuracy"),
        "latency_ms": summarize(latencies, "latency_ms"),
    }


def write_summary(result: dict[str, object], output_path: Path) -> None:
    comparison = result["comparison"]
    lines = [
        "# Named Baseline Comparison Summary",
        "",
        "This synthetic harness compares HPP developmental memory against named baseline mechanisms on held-out noisy attractor recovery.",
        "",
        "## Run",
        "",
        f"- Mode: `{result['mode']}`",
        f"- Device: `{result['device_name']}`",
        f"- CUDA available: `{result['cuda_available']}`",
        f"- Classes: `{result['classes']}`",
        f"- Dimension: `{result['dim']}`",
        f"- Evaluation noise: `{result['eval_noise']}`",
        "",
        "## Baselines",
        "",
        "- Nearest-centroid prototype memory",
        "- One-pass MLP denoiser",
        "- GRU recurrent refiner",
        "",
        "## Result",
        "",
        f"- Best baseline by MSE: `{comparison['best_baseline']}`",
        f"- HPP MSE: `{comparison['hpp_mse_mean']}`",
        f"- Best baseline MSE: `{comparison['best_baseline_mse_mean']}`",
        f"- Best-baseline-to-HPP MSE ratio: `{comparison['hpp_vs_best_baseline_mse_ratio']}x`",
        f"- HPP accuracy: `{comparison['hpp_accuracy_mean']}`",
        f"- Best baseline accuracy: `{comparison['best_baseline_accuracy_mean']}`",
        f"- HPP mean latency: `{comparison['hpp_latency_ms_mean']} ms`",
        f"- HPP stored memory values: `{comparison['hpp_memory_values']}`",
        f"- MLP parameters: `{comparison['mlp_parameters']}`",
        f"- GRU parameters: `{comparison['gru_parameters']}`",
        "",
        "## Boundary",
        "",
        "This is mechanism evidence only. The HPP path receives trusted clean anchors after an early noisy period, while the MLP and GRU baselines receive supervised clean targets during gradient training. It compares toy attractor-recovery behavior under synthetic noise. It does not prove language ability, general intelligence, production safety, or a fixed efficiency multiple.",
        "",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["battery", "plugged", "demo", "auto"], default="plugged")
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
    parser.add_argument("--seed", type=int, default=14)
    args = parser.parse_args()

    report = select_device(args.mode)
    device = torch.device(report.device)
    torch.manual_seed(args.seed)

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

    hpp_result = results["hpp_developmental_memory"]
    baseline_keys = ["nearest_centroid", "one_pass_mlp", "gru_refiner"]
    best_baseline_key = min(
        baseline_keys,
        key=lambda key: results[key]["mse"]["mse_mean"],
    )
    best_baseline = results[best_baseline_key]
    comparison = {
        "best_baseline": best_baseline_key,
        "hpp_mse_mean": hpp_result["mse"]["mse_mean"],
        "best_baseline_mse_mean": best_baseline["mse"]["mse_mean"],
        "hpp_vs_best_baseline_mse_ratio": round(
            best_baseline["mse"]["mse_mean"] / max(hpp_result["mse"]["mse_mean"], 1e-12),
            8,
        ),
        "hpp_accuracy_mean": hpp_result["accuracy"]["accuracy_mean"],
        "best_baseline_accuracy_mean": best_baseline["accuracy"]["accuracy_mean"],
        "hpp_latency_ms_mean": hpp_result["latency_ms"]["latency_ms_mean"],
        "mlp_parameters": count_parameters(mlp),
        "gru_parameters": count_parameters(gru),
        "hpp_memory_values": int(hpp.prototypes.numel() + hpp.exposures.numel()),
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
        "allocated_mb_before": report.allocated_mb,
        "reserved_mb_before": report.reserved_mb,
        "peak_allocated_mb": peak_allocated_mb,
        "peak_reserved_mb": peak_reserved_mb,
        "seed": args.seed,
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
        "elapsed_ms": round((perf_counter() - start) * 1000, 3),
        "training": {
            "mlp_first_loss": round(mlp_losses[0], 8),
            "mlp_final_loss": round(mlp_losses[-1], 8),
            "gru_first_loss": round(gru_losses[0], 8),
            "gru_final_loss": round(gru_losses[-1], 8),
            "hpp_min_exposures": int(hpp.exposures.min().detach().cpu()),
            "hpp_max_exposures": int(hpp.exposures.max().detach().cpu()),
            "hpp_locked_classes": int((hpp.exposures >= hpp.threshold).sum().detach().cpu()),
        },
        "results": results,
        "comparison": comparison,
        "boundary": "Synthetic attractor-recovery mechanism evidence only; not a language, agency, or general intelligence benchmark.",
    }

    json_path = Path(f"docs/named-baseline-comparison-{args.mode}.json")
    summary_path = Path("docs/named-baseline-comparison-summary.md")
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    write_summary(result, summary_path)

    print(json.dumps(comparison, indent=2))
    print(f"wrote={json_path}")
    print(f"wrote={summary_path}")


if __name__ == "__main__":
    main()
