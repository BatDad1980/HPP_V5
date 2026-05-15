"""Inventory protected previous-HPP assets without modifying them.

This script reads file metadata only. It does not load checkpoints into CPU/GPU
memory and does not write outside HPP_V5.
"""

from __future__ import annotations

import json
from pathlib import Path


def mib(size: int) -> float:
    return round(size / 1024 / 1024, 2)


def file_info(path: Path, root: Path) -> dict[str, object]:
    stat = path.stat()
    return {
        "name": path.name,
        "relative_path": str(path.relative_to(root)),
        "size_bytes": stat.st_size,
        "size_mib": mib(stat.st_size),
    }


def build_inventory(root: Path) -> dict[str, object]:
    checkpoints = sorted((root / "checkpoints").glob("*.pth"))
    core_files = sorted((root / "core").glob("*.py"))
    training_files = sorted((root / "training").glob("*.py"))
    utility_files = sorted((root / "utils").glob("*.py"))
    reports = sorted((root / "reports").glob("*.md"))

    return {
        "source_root": str(root),
        "note": "Read-only inventory generated from protected previous HPP source.",
        "checkpoints": [file_info(path, root) for path in checkpoints],
        "core_modules": [file_info(path, root) for path in core_files],
        "training_scripts": [file_info(path, root) for path in training_files],
        "utility_scripts": [file_info(path, root) for path in utility_files],
        "reports": [file_info(path, root) for path in reports],
    }


def main() -> None:
    sources = [
        (
            Path(r"X:\Aural-Nexus-Workforce\Aural_IP_Data_Room\08_Hyperplasticity_Protocol"),
            Path("docs/previous-hpp-asset-inventory.json"),
        ),
        (
            Path(r"C:\Users\Aural\Desktop\Codename HYPERPLASTICITY PROTOCOL\Project_HPP"),
            Path("docs/desktop-hpp-asset-inventory.json"),
        ),
    ]

    for root, output_path in sources:
        if not root.exists():
            print(f"missing={root}")
            continue
        inventory = build_inventory(root)
        checkpoints = list((root / "checkpoints").glob("*.pth"))
        output_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
        print(f"wrote={output_path}")
        print(f"source={root}")
        print(f"checkpoints={len(checkpoints)}")
        print(f"total_checkpoint_mib={mib(sum(path.stat().st_size for path in checkpoints))}")
        print()


if __name__ == "__main__":
    main()
