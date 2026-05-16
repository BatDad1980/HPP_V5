"""Run HPP V5 registered benchmarks."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from hpp_eval import BenchmarkConfig, list_benchmarks, run_benchmark, run_benchmarks


async def _run(args: argparse.Namespace) -> None:
    if args.list:
        print("\n".join(list_benchmarks()))
        return

    names = list_benchmarks() if args.benchmark == ["all"] else args.benchmark
    config = BenchmarkConfig(
        save_dir=args.save_dir,
        max_concurrency=args.max_concurrency,
        overwrite=not args.no_overwrite,
        include_trajectories=not args.no_trajectories,
        metadata={"invoked_by": "scripts/run_hpp_eval.py"},
    )

    if len(names) == 1:
        result = await run_benchmark(names[0], config)
        print(json.dumps(asdict(result), indent=2))
        return

    results = await run_benchmarks(names, config)
    compact = {name: asdict(result) for name, result in results.items()}
    print(json.dumps(compact, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "benchmark",
        nargs="*",
        default=["robotics_adapter_safety"],
        help="Benchmark names to run, or 'all'.",
    )
    parser.add_argument("--save-dir", default="docs/evals/latest")
    parser.add_argument("--max-concurrency", type=int, default=4)
    parser.add_argument("--no-overwrite", action="store_true")
    parser.add_argument("--no-trajectories", action="store_true")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    asyncio.run(_run(args))


if __name__ == "__main__":
    main()
