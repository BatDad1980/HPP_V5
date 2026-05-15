"""Inventory protected previous-HPP assets without modifying them.

This script reads file metadata only. It does not load checkpoints into CPU/GPU
memory and does not write outside HPP_V5.
"""

from __future__ import annotations

import json
from pathlib import Path


PREVIOUS_HPP_ROOT = Path(
    r"X:\Aural-Nexus-Workforce\Aural_IP_Data_Room\08_Hyperplasticity_Protocol"
)
OUTPUT_PATH = Path("docs/previous-hpp-asset-inventory.json")


def mib(size: int) -> float:
    return round(size / 1024 / 1024, 2)


def file_info(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "name": path.name,
        "relative_path": str(path.relative_to(PREVIOUS_HPP_ROOT)),
        "size_bytes": stat.st_size,
        "size_mib": mib(stat.st_size),
    }


def main() -> None:
    checkpoints = sorted((PREVIOUS_HPP_ROOT / "checkpoints").glob("*.pth"))
    core_files = sorted((PREVIOUS_HPP_ROOT / "core").glob("*.py"))
    training_files = sorted((PREVIOUS_HPP_ROOT / "training").glob("*.py"))
    utility_files = sorted((PREVIOUS_HPP_ROOT / "utils").glob("*.py"))
    reports = sorted((PREVIOUS_HPP_ROOT / "reports").glob("*.md"))

    inventory = {
        "source_root": str(PREVIOUS_HPP_ROOT),
        "note": "Read-only inventory generated from protected previous HPP source.",
        "checkpoints": [file_info(path) for path in checkpoints],
        "core_modules": [file_info(path) for path in core_files],
        "training_scripts": [file_info(path) for path in training_files],
        "utility_scripts": [file_info(path) for path in utility_files],
        "reports": [file_info(path) for path in reports],
    }

    OUTPUT_PATH.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    print(f"wrote={OUTPUT_PATH}")
    print(f"checkpoints={len(checkpoints)}")
    print(f"total_checkpoint_mib={mib(sum(path.stat().st_size for path in checkpoints))}")


if __name__ == "__main__":
    main()
