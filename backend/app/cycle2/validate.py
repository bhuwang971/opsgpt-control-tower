from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from app.cycle1.storage import connect


@dataclass(frozen=True)
class ValidationResult:
    name: str
    status: str
    detail: str


def run_validations(
    *, duckdb_path: Path, expect_fixture_slices: bool = False
) -> list[ValidationResult]:
    conn = connect(duckdb_path)
    results = [
        _expect_positive_count(conn, "analytics.dim_airport"),
        _expect_positive_count(conn, "analytics.dim_carrier"),
        _expect_positive_count(conn, "analytics.fct_flight_operations"),
        _expect_positive_count(conn, "analytics.mart_kpi_daily_operations"),
        _expect_unique_not_null(conn, "analytics.dim_airport", "airport_code"),
        _expect_unique_not_null(conn, "analytics.dim_carrier", "carrier_code"),
        _expect_total_match(
            conn,
            """
            SELECT
                (SELECT COUNT(*) FROM analytics.fct_flight_operations),
                (SELECT COALESCE(SUM(total_flights), 0) FROM analytics.mart_kpi_daily_operations)
            """,
            "daily mart total flights reconcile to fact table",
        ),
        _expect_total_match(
            conn,
            """
            SELECT
                (SELECT COUNT(DISTINCT carrier_code) FROM analytics.fct_flight_operations),
                (SELECT COUNT(*) FROM analytics.mart_kpi_carrier_performance)
            """,
            "carrier mart row count matches carrier grain",
        ),
    ]
    if expect_fixture_slices:
        results.extend(_fixture_expectations(conn))
    conn.close()
    return results


def write_validation_report(
    results: list[ValidationResult], artifact_dir: Path
) -> tuple[Path, Path]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    json_path = artifact_dir / f"warehouse_validation_{timestamp}.json"
    md_path = artifact_dir / f"warehouse_validation_{timestamp}.md"
    payload = {"generated_at": timestamp, "results": [result.__dict__ for result in results]}
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Cycle 2 Warehouse Validation", "", f"Generated at: `{timestamp}`", ""]
    for result in results:
        lines.append(f"- `{result.status}` {result.name}: {result.detail}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def _expect_positive_count(conn, table_name: str) -> ValidationResult:
    count = int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    return ValidationResult(
        table_name + " row_count", "pass" if count > 0 else "fail", f"row_count={count}"
    )


def _expect_unique_not_null(conn, table_name: str, column_name: str) -> ValidationResult:
    null_count, duplicate_count = conn.execute(
        f"""
        SELECT
            SUM(CASE WHEN {column_name} IS NULL THEN 1 ELSE 0 END) AS null_count,
            COUNT(*) - COUNT(DISTINCT {column_name}) AS duplicate_count
        FROM {table_name}
        """
    ).fetchone()
    null_count = 0 if null_count is None else int(null_count)
    duplicate_count = 0 if duplicate_count is None else int(duplicate_count)
    status = "pass" if null_count == 0 and duplicate_count == 0 else "fail"
    return ValidationResult(
        f"{table_name}.{column_name} unique_not_null",
        status,
        f"null_count={null_count} duplicate_count={duplicate_count}",
    )


def _expect_total_match(conn, sql: str, name: str) -> ValidationResult:
    left_value, right_value = conn.execute(sql).fetchone()
    status = "pass" if left_value == right_value else "fail"
    return ValidationResult(name, status, f"left={left_value} right={right_value}")


def _fixture_expectations(conn) -> list[ValidationResult]:
    jan5 = conn.execute(
        """
        SELECT total_flights, on_time_rate, severe_delay_rate
        FROM analytics.mart_kpi_daily_operations
        WHERE flight_date = DATE '2024-01-05'
        """
    ).fetchone()
    jan6 = conn.execute(
        """
        SELECT total_flights, on_time_rate, severe_delay_rate
        FROM analytics.mart_kpi_daily_operations
        WHERE flight_date = DATE '2024-01-06'
        """
    ).fetchone()
    dl_row = conn.execute(
        """
        SELECT total_flights, on_time_rate
        FROM analytics.mart_kpi_carrier_performance
        WHERE carrier_code = 'DL'
        """
    ).fetchone()
    return [
        ValidationResult(
            "fixture daily KPI 2024-01-05",
            "pass" if jan5 and int(jan5[0]) >= 5 and 0.0 <= float(jan5[1]) <= 1.0 else "fail",
            f"actual={jan5}",
        ),
        ValidationResult(
            "fixture daily KPI 2024-01-06",
            "pass" if jan6 and int(jan6[0]) >= 5 and 0.0 <= float(jan6[1]) <= 1.0 else "fail",
            f"actual={jan6}",
        ),
        ValidationResult(
            "fixture carrier KPI DL",
            (
                "pass"
                if dl_row and int(dl_row[0]) >= 20 and 0.0 <= float(dl_row[1]) <= 1.0
                else "fail"
            ),
            f"actual={dl_row}",
        ),
    ]
