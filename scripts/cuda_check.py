"""Lightweight CUDA diagnostic for HPP V5.

This script does not train, load checkpoints, or run heavy tensors. It only
prints the local PyTorch/CUDA device state so heavier HPP work can start from
known ground.
"""

from __future__ import annotations

import platform


def main() -> None:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"torch_import_error={exc!r}")
        return

    print(f"python={platform.python_version()}")
    print(f"torch={torch.__version__}")
    print(f"cuda_available={torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        print("device=cpu")
        return

    device = torch.device("cuda:0")
    print(f"device={torch.cuda.get_device_name(device)}")
    print(f"cuda_version={torch.version.cuda}")
    print(f"allocated_mb={torch.cuda.memory_allocated(device) / 1024 / 1024:.2f}")
    print(f"reserved_mb={torch.cuda.memory_reserved(device) / 1024 / 1024:.2f}")


if __name__ == "__main__":
    main()
