from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.cycle1.cli import run_ingest
from app.cycle2.build import build_models, default_repo_root
from app.cycle2.validate import run_validations, write_validation_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 2 warehouse models")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Materialize curated warehouse models")
    build.add_argument(
        "--duckdb-path", default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb")
    )
    build.add_argument("--repo-root", default=str(default_repo_root()))

    validate = subparsers.add_parser("validate", help="Run warehouse model validations")
    validate.add_argument(
        "--duckdb-path", default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb")
    )
    validate.add_argument("--artifact-dir", default="artifacts/cycle2/validation")
    validate.add_argument("--expect-fixture-slices", action="store_true")

    full_run = subparsers.add_parser(
        "full-run", help="Run fixture Cycle 1 ingest, Cycle 2 build, and validation"
    )
    full_run.add_argument(
        "--duckdb-path", default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb")
    )
    full_run.add_argument("--repo-root", default=str(default_repo_root()))
    full_run.add_argument("--artifact-root", default="artifacts/cycle2")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "build":
        result = run_build(repo_root=Path(args.repo_root), duckdb_path=Path(args.duckdb_path))
    elif args.command == "validate":
        result = run_validate(
            duckdb_path=Path(args.duckdb_path),
            artifact_dir=Path(args.artifact_dir),
            expect_fixture_slices=args.expect_fixture_slices,
        )
    else:
        result = run_full(
            repo_root=Path(args.repo_root),
            duckdb_path=Path(args.duckdb_path),
            artifact_root=Path(args.artifact_root),
        )
    print(json.dumps(result, indent=2))


def run_build(*, repo_root: Path, duckdb_path: Path) -> dict[str, Any]:
    results = build_models(repo_root=repo_root, duckdb_path=duckdb_path)
    return {
        "command": "build",
        "models": [
            {"model_name": result.model_name, "row_count": result.row_count} for result in results
        ],
    }


def run_validate(
    *, duckdb_path: Path, artifact_dir: Path, expect_fixture_slices: bool
) -> dict[str, Any]:
    results = run_validations(duckdb_path=duckdb_path, expect_fixture_slices=expect_fixture_slices)
    json_path, md_path = write_validation_report(results, artifact_dir)
    return {
        "command": "validate",
        "json_report": str(json_path),
        "markdown_report": str(md_path),
        "failed_checks": [result.name for result in results if result.status == "fail"],
    }


def run_full(*, repo_root: Path, duckdb_path: Path, artifact_root: Path) -> dict[str, Any]:
    cycle1 = run_ingest(
        source="all",
        mode="fixture",
        duckdb_path=duckdb_path,
        artifact_dir=artifact_root / "cycle1_raw",
    )
    build = run_build(repo_root=repo_root, duckdb_path=duckdb_path)
    validate = run_validate(
        duckdb_path=duckdb_path,
        artifact_dir=artifact_root / "validation",
        expect_fixture_slices=True,
    )
    return {"command": "full-run", "cycle1_ingest": cycle1, "build": build, "validate": validate}


if __name__ == "__main__":
    main()
