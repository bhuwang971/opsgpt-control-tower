from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.cycle2.build import default_repo_root
from app.cycle2.cli import run_full as run_cycle2_full
from app.cycle3.report import build_statistical_report, write_statistical_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 3 statistical layer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    report = subparsers.add_parser(
        "report", help="Generate a statistical report from warehouse marts"
    )
    report.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    report.add_argument("--artifact-dir", default="artifacts/cycle3/report")

    full_run = subparsers.add_parser(
        "full-run",
        help="Run fixture Cycle 2 warehouse flow and then generate the Cycle 3 report",
    )
    full_run.add_argument(
        "--duckdb-path",
        default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb"),
    )
    full_run.add_argument("--repo-root", default=str(default_repo_root()))
    full_run.add_argument("--artifact-root", default="artifacts/cycle3")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "report":
        result = run_report(Path(args.duckdb_path), Path(args.artifact_dir))
    else:
        result = run_full(
            repo_root=Path(args.repo_root),
            duckdb_path=Path(args.duckdb_path),
            artifact_root=Path(args.artifact_root),
        )
    print(json.dumps(result, indent=2))


def run_report(duckdb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    report = build_statistical_report(duckdb_path=duckdb_path)
    json_path, md_path = write_statistical_report(report, artifact_dir)
    return {
        "command": "report",
        "json_report": str(json_path),
        "markdown_report": str(md_path),
        "trend_summary": report["trend_summary"],
    }


def run_full(*, repo_root: Path, duckdb_path: Path, artifact_root: Path) -> dict[str, Any]:
    cycle2 = run_cycle2_full(
        repo_root=repo_root,
        duckdb_path=duckdb_path,
        artifact_root=artifact_root / "cycle2",
    )
    report = run_report(duckdb_path, artifact_root / "report")
    return {"command": "full-run", "cycle2": cycle2, "report": report}


if __name__ == "__main__":
    main()
