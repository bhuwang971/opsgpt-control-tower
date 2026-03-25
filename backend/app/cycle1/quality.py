from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import duckdb


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: str
    detail: str


def run_quality_checks(conn: duckdb.DuckDBPyConnection) -> list[CheckResult]:
    return [
        _check_non_empty(conn, "bronze.bts_flights"),
        _check_non_empty(conn, "bronze.weather_observations"),
        _check_non_empty(conn, "bronze.comtrade_monthly"),
        _check_null_threshold(conn, "bronze.bts_flights", "origin", 0.0),
        _check_null_threshold(conn, "bronze.weather_observations", "temperature_c", 0.0),
        _check_null_threshold(conn, "bronze.comtrade_monthly", "trade_value_usd", 0.0),
        _check_range(conn, "bronze.bts_flights", "arr_delay_minutes", -120, 1440),
        _check_range(conn, "bronze.weather_observations", "temperature_c", -80, 60),
        _check_range(conn, "bronze.comtrade_monthly", "trade_value_usd", 0, 1_000_000_000_000),
        _check_unique(conn, "bronze.bts_flights", "flight_id"),
        _check_unique(conn, "bronze.comtrade_monthly", "trade_id"),
        _check_freshness(conn, "raw.ingestion_runs", "extracted_at", max_age_days=30),
    ]


def write_quality_report(checks: list[CheckResult], artifact_dir: Path) -> tuple[Path, Path]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = artifact_dir / f"data_quality_{timestamp}.json"
    md_path = artifact_dir / f"data_quality_{timestamp}.md"
    payload = {"generated_at": timestamp, "checks": [check.__dict__ for check in checks]}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = ["# Cycle 1 Data Quality Report", "", f"Generated at: `{timestamp}`", ""]
    for check in checks:
        lines.append(f"- `{check.status}` {check.name}: {check.detail}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def _check_non_empty(conn: duckdb.DuckDBPyConnection, table: str) -> CheckResult:
    count = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    return CheckResult(f"{table} non_empty", "pass" if count > 0 else "fail", f"row_count={count}")


def _check_null_threshold(
    conn: duckdb.DuckDBPyConnection, table: str, column: str, max_null_ratio: float
) -> CheckResult:
    total, nulls = conn.execute(
        f"SELECT COUNT(*), SUM(CASE WHEN {column} IS NULL THEN 1 ELSE 0 END) FROM {table}"
    ).fetchone()
    null_count = 0 if nulls is None else int(nulls)
    ratio = 0.0 if total == 0 else float(null_count) / float(total)
    return CheckResult(
        f"{table}.{column} null_ratio",
        "pass" if ratio <= max_null_ratio else "fail",
        f"null_ratio={ratio:.3f} threshold={max_null_ratio:.3f}",
    )


def _check_range(
    conn: duckdb.DuckDBPyConnection, table: str, column: str, min_value: float, max_value: float
) -> CheckResult:
    violations = int(
        conn.execute(
            (
                f"SELECT COUNT(*) FROM {table} "
                f"WHERE {column} IS NOT NULL AND ({column} < ? OR {column} > ?)"
            ),
            [min_value, max_value],
        ).fetchone()[0]
    )
    return CheckResult(
        f"{table}.{column} range",
        "pass" if violations == 0 else "fail",
        f"violations={violations} expected_between=[{min_value}, {max_value}]",
    )


def _check_unique(conn: duckdb.DuckDBPyConnection, table: str, column: str) -> CheckResult:
    duplicates = int(
        conn.execute(
            f"""
            SELECT COUNT(*) FROM (
                SELECT {column}, COUNT(*) AS row_count
                FROM {table}
                GROUP BY 1
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]
    )
    return CheckResult(
        f"{table}.{column} unique",
        "pass" if duplicates == 0 else "fail",
        f"duplicate_keys={duplicates}",
    )


def _check_freshness(
    conn: duckdb.DuckDBPyConnection, table: str, column: str, max_age_days: int
) -> CheckResult:
    latest = conn.execute(f"SELECT MAX({column}) FROM {table}").fetchone()[0]
    if latest is None:
        return CheckResult(f"{table}.{column} freshness", "fail", "latest_timestamp=null")
    age_days = (datetime.now(UTC).replace(tzinfo=None) - latest).days
    return CheckResult(
        f"{table}.{column} freshness",
        "pass" if age_days <= max_age_days else "fail",
        f"age_days={age_days} threshold={max_age_days}",
    )
