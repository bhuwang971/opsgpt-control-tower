from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from app.cycle1.connectors import fetch_bts, fetch_comtrade, fetch_weather
from app.cycle1.eda import build_eda_payload, write_eda_report
from app.cycle1.quality import run_quality_checks, write_quality_report
from app.cycle1.storage import connect, ingest_result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="OpsGPT Cycle 1 data pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest = subparsers.add_parser("ingest", help="Load raw and bronze data")
    ingest.add_argument("--source", choices=["all", "bts", "weather", "comtrade"], default="all")
    ingest.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    ingest.add_argument(
        "--duckdb-path", default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb")
    )
    ingest.add_argument("--artifact-dir", default="artifacts/cycle1/raw")

    quality = subparsers.add_parser("quality", help="Run data quality checks")
    quality.add_argument(
        "--duckdb-path", default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb")
    )
    quality.add_argument("--artifact-dir", default="artifacts/cycle1/quality")

    eda = subparsers.add_parser("eda", help="Generate EDA artifacts")
    eda.add_argument(
        "--duckdb-path", default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb")
    )
    eda.add_argument("--artifact-dir", default="artifacts/cycle1/eda")

    full_run = subparsers.add_parser("full-run", help="Run ingest, quality, and EDA")
    full_run.add_argument("--mode", choices=["fixture", "live"], default="fixture")
    full_run.add_argument(
        "--duckdb-path", default=os.getenv("DUCKDB_PATH", "data/warehouse/opsgpt.duckdb")
    )
    full_run.add_argument("--artifact-root", default="artifacts/cycle1")

    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.command == "ingest":
        result = run_ingest(
            source=args.source,
            mode=args.mode,
            duckdb_path=Path(args.duckdb_path),
            artifact_dir=Path(args.artifact_dir),
        )
    elif args.command == "quality":
        result = run_quality(Path(args.duckdb_path), Path(args.artifact_dir))
    elif args.command == "eda":
        result = run_eda(Path(args.duckdb_path), Path(args.artifact_dir))
    else:
        result = run_full(
            mode=args.mode,
            duckdb_path=Path(args.duckdb_path),
            artifact_root=Path(args.artifact_root),
        )
    print(json.dumps(result, indent=2))


def run_ingest(*, source: str, mode: str, duckdb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    conn = connect(duckdb_path)
    summaries = []
    for connector_result in _select_results(source=source, mode=mode):
        summary = ingest_result(conn, connector_result, artifact_dir)
        summaries.append(
            {
                "source": summary.source,
                "raw_rows": summary.raw_rows,
                "bronze_rows": summary.bronze_rows,
                "artifact_path": str(summary.artifact_path),
            }
        )
    conn.close()
    return {"command": "ingest", "mode": mode, "sources": summaries}


def run_quality(duckdb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    conn = connect(duckdb_path)
    checks = run_quality_checks(conn)
    conn.close()
    json_path, md_path = write_quality_report(checks, artifact_dir)
    return {
        "command": "quality",
        "json_report": str(json_path),
        "markdown_report": str(md_path),
        "failed_checks": [check.name for check in checks if check.status == "fail"],
    }


def run_eda(duckdb_path: Path, artifact_dir: Path) -> dict[str, Any]:
    conn = connect(duckdb_path)
    payload = build_eda_payload(conn)
    conn.close()
    json_path, md_path = write_eda_report(payload, artifact_dir)
    return {
        "command": "eda",
        "json_report": str(json_path),
        "markdown_report": str(md_path),
    }


def run_full(*, mode: str, duckdb_path: Path, artifact_root: Path) -> dict[str, Any]:
    ingest = run_ingest(
        source="all",
        mode=mode,
        duckdb_path=duckdb_path,
        artifact_dir=artifact_root / "raw",
    )
    quality = run_quality(duckdb_path, artifact_root / "quality")
    eda = run_eda(duckdb_path, artifact_root / "eda")
    return {"command": "full-run", "ingest": ingest, "quality": quality, "eda": eda}


def _select_results(*, source: str, mode: str) -> list[Any]:
    if source == "all":
        return [
            fetch_bts(mode=mode, url=os.getenv("BTS_DOWNLOAD_URL")),
            fetch_weather(mode=mode, base_url=os.getenv("WEATHER_BASE_URL")),
            fetch_comtrade(mode=mode, base_url=os.getenv("COMTRADE_BASE_URL")),
        ]
    if source == "bts":
        return [fetch_bts(mode=mode, url=os.getenv("BTS_DOWNLOAD_URL"))]
    if source == "weather":
        return [fetch_weather(mode=mode, base_url=os.getenv("WEATHER_BASE_URL"))]
    return [fetch_comtrade(mode=mode, base_url=os.getenv("COMTRADE_BASE_URL"))]


if __name__ == "__main__":
    main()
