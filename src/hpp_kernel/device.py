"""Device selection helpers for HPP V5."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DeviceReport:
    requested_mode: str
    device: str
    cuda_available: bool
    device_name: str
    cuda_version: str | None
    allocated_mb: float
    reserved_mb: float


def select_device(mode: str = "auto") -> DeviceReport:
    """Select a torch device with HPP power-mode rules.

    Modes:
    - battery: force CPU
    - plugged: prefer CUDA
    - demo: force CPU for deterministic buyer-safe demos
    - auto: prefer CUDA when available
    """

    import torch

    cuda_available = torch.cuda.is_available()
    use_cuda = cuda_available and mode in {"auto", "plugged"}
    device = "cuda:0" if use_cuda else "cpu"

    device_name = "CPU"
    cuda_version = None
    allocated_mb = 0.0
    reserved_mb = 0.0

    if use_cuda:
        torch_device = torch.device(device)
        device_name = torch.cuda.get_device_name(torch_device)
        cuda_version = torch.version.cuda
        allocated_mb = round(torch.cuda.memory_allocated(torch_device) / 1024 / 1024, 2)
        reserved_mb = round(torch.cuda.memory_reserved(torch_device) / 1024 / 1024, 2)

    return DeviceReport(
        requested_mode=mode,
        device=device,
        cuda_available=cuda_available,
        device_name=device_name,
        cuda_version=cuda_version,
        allocated_mb=allocated_mb,
        reserved_mb=reserved_mb,
    )
