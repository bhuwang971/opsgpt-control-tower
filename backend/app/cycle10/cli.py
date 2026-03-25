from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.cycle2.build import default_repo_root
from app.cycle9.cli import run_full as run_cycle9_full
from app.cycle10.ope import analyze_policies
from app.cycle10.report import write_cycle10_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 10 portfolio differentiators")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Run Cycle 10 offline policy evaluation")
    analyze.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    analyze.add_argument("--artifact-dir", default="artifacts/cycle10")
    analyze.add_argument("--toggle-name", default="adaptive_turnaround_buffers")
    analyze.add_argument("--repo-root", default=str(default_repo_root()))

    full_run = subparsers.add_parser(
        "full-run",
        help="Run the Cycle 9 chain and then generate Cycle 10 portfolio assets",
    )
    full_run.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    full_run.add_argument("--artifact-root", default="artifacts/cycle10")
    full_run.add_argument("--repo-root", default=str(default_repo_root()))
    full_run.add_argument("--toggle-name", default="adaptive_turnaround_buffers")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "analyze":
        result = run_analysis(
            repo_root=Path(args.repo_root),
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
    repo_root: Path,
    duckdb_path: Path,
    artifact_dir: Path,
    toggle_name: str,
) -> dict[str, Any]:
    ope = analyze_policies(duckdb_path, toggle_name)
    artifacts = write_cycle10_report(
        {
            "ope": ope,
            "demo_assets": {
                "architecture_doc": str(repo_root / "docs" / "architecture.md"),
                "demo_script": str(repo_root / "docs" / "demo-script.md"),
            },
        },
        artifact_dir,
    )
    return {
        "command": "analyze",
        "ope": ope,
        "demo_assets": {
            "architecture_doc": str(repo_root / "docs" / "architecture.md"),
            "demo_script": str(repo_root / "docs" / "demo-script.md"),
        },
        "artifacts": artifacts,
    }


def run_full(
    *,
    repo_root: Path,
    duckdb_path: Path,
    artifact_root: Path,
    toggle_name: str,
) -> dict[str, Any]:
    cycle9 = run_cycle9_full(
        repo_root=repo_root,
        duckdb_path=duckdb_path,
        artifact_root=artifact_root / "cycle9",
        toggle_name=toggle_name,
    )
    cycle10 = run_analysis(
        repo_root=repo_root,
        duckdb_path=duckdb_path,
        artifact_dir=artifact_root / "portfolio",
        toggle_name=toggle_name,
    )
    return {"command": "full-run", "cycle9": cycle9, "cycle10": cycle10}


if __name__ == "__main__":
    main()
