from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.cycle2.build import default_repo_root
from app.cycle3.cli import run_full as run_cycle3_full
from app.cycle4.evaluate import run_baselines, write_evaluation_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 4 ML baselines")
    subparsers = parser.add_subparsers(dest="command", required=True)

    train = subparsers.add_parser("train", help="Train and evaluate Cycle 4 baselines")
    train.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    train.add_argument("--artifact-dir", default="artifacts/cycle4")

    full_run = subparsers.add_parser(
        "full-run",
        help="Run fixture Cycle 3 pipeline and then execute Cycle 4 baselines",
    )
    full_run.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    full_run.add_argument("--repo-root", default=str(default_repo_root()))
    full_run.add_argument("--artifact-root", default="artifacts/cycle4")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "train":
        result = run_train(Path(args.duckdb_path), Path(args.artifact_dir))
    else:
        result = run_full(
            repo_root=Path(args.repo_root),
            duckdb_path=Path(args.duckdb_path),
            artifact_root=Path(args.artifact_root),
        )
    print(json.dumps(result, indent=2))


def run_train(duckdb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    bundle = run_baselines(duckdb_path)
    artifacts = write_evaluation_artifacts(bundle, artifact_dir)
    return {
        "command": "train",
        "benchmark_row_count": bundle.benchmark_row_count,
        "train_row_count": bundle.train_row_count,
        "test_row_count": bundle.test_row_count,
        "classification": bundle.classification,
        "regression": bundle.regression,
        "forecasting": bundle.forecasting,
        "artifacts": artifacts,
    }


def run_full(*, repo_root: Path, duckdb_path: Path, artifact_root: Path) -> dict[str, Any]:
    cycle3 = run_cycle3_full(
        repo_root=repo_root,
        duckdb_path=duckdb_path,
        artifact_root=artifact_root / "cycle3",
    )
    training = run_train(duckdb_path, artifact_root / "models")
    return {"command": "full-run", "cycle3": cycle3, "training": training}


if __name__ == "__main__":
    main()
