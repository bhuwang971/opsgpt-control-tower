from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.cycle2.build import default_repo_root
from app.cycle4.cli import run_full as run_cycle4_full
from app.cycle9.analysis import analyze_experiment, available_toggles
from app.cycle9.report import write_experiment_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 9 experimentation module")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Run Cycle 9 experiment analysis")
    analyze.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    analyze.add_argument("--artifact-dir", default="artifacts/cycle9")
    analyze.add_argument(
        "--toggle-name",
        default="adaptive_turnaround_buffers",
        choices=sorted(available_toggles()),
    )

    full_run = subparsers.add_parser(
        "full-run",
        help="Run the Cycle 4 asset chain and then execute Cycle 9 analysis",
    )
    full_run.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    full_run.add_argument("--repo-root", default=str(default_repo_root()))
    full_run.add_argument("--artifact-root", default="artifacts/cycle9")
    full_run.add_argument(
        "--toggle-name",
        default="adaptive_turnaround_buffers",
        choices=sorted(available_toggles()),
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "analyze":
        result = run_analysis(
            duckdb_path=Path(args.duckdb_path),
            artifact_dir=Path(args.artifact_dir),
            toggle_name=args.toggle_name,
        )
    else:
        result = run_full(
            repo_root=Path(args.repo_root),
            duckdb_path=Path(args.duckdb_path),
            artifact_root=Path(args.artifact_root),
            toggle_name=args.toggle_name,
        )
    print(json.dumps(result, indent=2))


def run_analysis(
    *,
    duckdb_path: Path,
    artifact_dir: Path,
    toggle_name: str,
) -> dict[str, Any]:
    analysis = analyze_experiment(duckdb_path, toggle_name)
    artifacts = write_experiment_report(analysis, artifact_dir)
    return {"command": "analyze", "analysis": analysis, "artifacts": artifacts}


def run_full(
    *,
    repo_root: Path,
    duckdb_path: Path,
    artifact_root: Path,
    toggle_name: str,
) -> dict[str, Any]:
    cycle4 = run_cycle4_full(
        repo_root=repo_root,
        duckdb_path=duckdb_path,
        artifact_root=artifact_root / "cycle4",
    )
    experiment = run_analysis(
        duckdb_path=duckdb_path,
        artifact_dir=artifact_root / "experiments",
        toggle_name=toggle_name,
    )
    return {"command": "full-run", "cycle4": cycle4, "experiment": experiment}


if __name__ == "__main__":
    main()
