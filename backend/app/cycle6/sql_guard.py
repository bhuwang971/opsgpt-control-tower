from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app import control_tower
from app.cycle1.storage import connect

ALLOWED_TABLES = {
    "analytics.mart_kpi_daily_operations",
    "analytics.mart_kpi_carrier_performance",
    "analytics.mart_kpi_trade_monthly",
    "analytics.fct_flight_operations",
}
BLOCKED_PATTERNS = [
    r"\bINSERT\b",
    r"\bUPDATE\b",
    r"\bDELETE\b",
    r"\bDROP\b",
    r"\bALTER\b",
    r"\bTRUNCATE\b",
    r"\bATTACH\b",
    r"\bCOPY\b",
    r"\bPRAGMA\b",
]


@dataclass(frozen=True)
class SqlResult:
    statement: str
    columns: list[str]
    rows: list[list[Any]]
    audit_id: str


def question_to_sql(question: str) -> str | None:
    normalized = question.lower()
    if "carrier" in normalized:
        if "worst" in normalized or "delay" in normalized:
            return """
                SELECT carrier_code, total_flights, on_time_rate,
                       avg_arr_delay_minutes, severe_delay_rate
                FROM analytics.mart_kpi_carrier_performance
                ORDER BY avg_arr_delay_minutes DESC
                LIMIT 5
            """
        return """
            SELECT carrier_code, total_flights, on_time_rate,
                   avg_arr_delay_minutes, severe_delay_rate
            FROM analytics.mart_kpi_carrier_performance
            ORDER BY on_time_rate DESC, avg_arr_delay_minutes ASC
            LIMIT 5
        """
    if any(term in normalized for term in ["trade", "import", "export"]):
        return """
            SELECT period, trade_flow, shipment_count, total_trade_value_usd, avg_net_weight_kg
            FROM analytics.mart_kpi_trade_monthly
            ORDER BY period DESC, total_trade_value_usd DESC
            LIMIT 10
        """
    if any(term in normalized for term in ["on-time", "reliability", "daily", "trend", "delay"]):
        if "latest" in normalized:
            return """
                SELECT flight_date, total_flights, on_time_rate, p90_arr_delay_minutes,
                       severe_delay_rate, reliability_score
                FROM analytics.mart_kpi_daily_operations
                ORDER BY flight_date DESC
                LIMIT 1
            """
        return """
            SELECT flight_date, total_flights, on_time_rate, p90_arr_delay_minutes,
                   severe_delay_rate, reliability_score
            FROM analytics.mart_kpi_daily_operations
            ORDER BY flight_date
            LIMIT 30
        """
    return None


def validate_sql(statement: str) -> str:
    compact = " ".join(statement.strip().split())
    upper = compact.upper()
    if not (upper.startswith("SELECT") or upper.startswith("WITH")):
        raise ValueError("Only SELECT queries are allowed.")
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, upper):
            raise ValueError("The SQL statement contains a blocked operation.")
    for table in re.findall(r"analytics\.[a-z_]+", compact, flags=re.IGNORECASE):
        if table.lower() not in ALLOWED_TABLES:
            raise ValueError(f"Table not allowlisted: {table}")
    if "LIMIT" not in upper:
        compact += " LIMIT 50"
    limit_match = re.search(r"\bLIMIT\s+(\d+)\b", upper)
    if limit_match and int(limit_match.group(1)) > 200:
        raise ValueError("LIMIT cannot exceed 200 rows.")
    return compact


def execute_guarded_sql(question: str, statement: str) -> SqlResult:
    control_tower.ensure_runtime_assets()
    safe_sql = validate_sql(statement)
    conn = connect(control_tower.default_duckdb_path())
    cursor = conn.execute(safe_sql)
    rows = [list(row) for row in cursor.fetchall()]
    columns = [item[0] for item in cursor.description]
    conn.close()
    audit_id = write_audit_log(question=question, statement=safe_sql, row_count=len(rows))
    return SqlResult(statement=safe_sql, columns=columns, rows=rows, audit_id=audit_id)


def write_audit_log(*, question: str, statement: str, row_count: int) -> str:
    audit_id = uuid.uuid4().hex
    audit_dir = control_tower.repo_root() / "backend" / "artifacts" / "cycle6"
    audit_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "audit_id": audit_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "question": question,
        "statement": statement,
        "row_count": row_count,
    }
    with (audit_dir / "sql_audit.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    return audit_id


def sql_summary(result: SqlResult) -> str:
    if not result.rows:
        return "The guarded SQL query executed successfully but returned no rows."
    first_row = result.rows[0]
    preview = ", ".join(f"{column}={value}" for column, value in zip(result.columns, first_row))
    return f"Returned {len(result.rows)} rows. First row: {preview}"
