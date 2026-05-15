"""Tiny recurrent workshop experiment for HPP V5.

This is not the full HPP model. It is a measured seed kernel for validating the
core claim: shared weights can provide controllable recurrent depth on modest
hardware.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from time import perf_counter

import torch
from torch import nn

from .device import select_device


@dataclass(frozen=True)
class KernelRun:
    device: str
    device_name: str
    dim: int
    batch: int
    passes: int
    parameters: int
    elapsed_ms: float
    allocated_mb: float
    reserved_mb: float
    output_norm: float


class TinyRecurrentWorkshop(nn.Module):
    def __init__(self, dim: int = 128):
        super().__init__()
        self.workshop = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim * 2),
            nn.GELU(),
            nn.Linear(dim * 2, dim),
        )
        self.gate = nn.Linear(dim * 2, dim)

    def forward(self, x: torch.Tensor, passes: int) -> torch.Tensor:
        state = x
        for _ in range(passes):
            refined = self.workshop(state)
            gate = torch.sigmoid(self.gate(torch.cat([state, refined], dim=-1)))
            state = state + gate * refined
        return state


class TinyUniqueStack(nn.Module):
    """Conventional stack with a distinct workshop and gate for each pass."""

    def __init__(self, dim: int = 128, depth: int = 14):
        super().__init__()
        self.layers = nn.ModuleList(
            [
                nn.ModuleDict(
                    {
                        "workshop": nn.Sequential(
                            nn.LayerNorm(dim),
                            nn.Linear(dim, dim * 2),
                            nn.GELU(),
                            nn.Linear(dim * 2, dim),
                        ),
                        "gate": nn.Linear(dim * 2, dim),
                    }
                )
                for _ in range(depth)
            ]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        state = x
        for layer in self.layers:
            refined = layer["workshop"](state)
            gate = torch.sigmoid(layer["gate"](torch.cat([state, refined], dim=-1)))
            state = state + gate * refined
        return state


def run_probe(mode: str = "plugged", dim: int = 128, batch: int = 8, passes: int = 14) -> dict[str, object]:
    report = select_device(mode)
    device = torch.device(report.device)

    torch.manual_seed(14)
    model = TinyRecurrentWorkshop(dim=dim).to(device)
    model.eval()
    x = torch.randn(batch, dim, device=device)

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    start = perf_counter()
    with torch.no_grad():
        output = model(x, passes=passes)

    if device.type == "cuda":
        torch.cuda.synchronize(device)

    elapsed_ms = round((perf_counter() - start) * 1000, 3)
    parameters = sum(parameter.numel() for parameter in model.parameters())

    run = KernelRun(
        device=report.device,
        device_name=report.device_name,
        dim=dim,
        batch=batch,
        passes=passes,
        parameters=parameters,
        elapsed_ms=elapsed_ms,
        allocated_mb=round(torch.cuda.memory_allocated(device) / 1024 / 1024, 2) if device.type == "cuda" else 0.0,
        reserved_mb=round(torch.cuda.memory_reserved(device) / 1024 / 1024, 2) if device.type == "cuda" else 0.0,
        output_norm=round(float(output.norm().detach().cpu()), 6),
    )
    return asdict(run)


def count_parameters(model: nn.Module) -> int:
    return sum(parameter.numel() for parameter in model.parameters())


if __name__ == "__main__":
    print(run_probe())
