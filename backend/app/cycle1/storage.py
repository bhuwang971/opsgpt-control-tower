from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import duckdb

from app.cycle1.connectors import ConnectorResult


@dataclass(frozen=True)
class IngestSummary:
    source: str
    raw_rows: int
    bronze_rows: int
    artifact_path: Path


SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS raw.ingestion_runs (
    run_id VARCHAR,
    source VARCHAR,
    mode VARCHAR,
    extracted_at TIMESTAMP,
    record_count BIGINT,
    metadata_json VARCHAR
);

CREATE TABLE IF NOT EXISTS raw.bts_flights (
    flight_id VARCHAR PRIMARY KEY,
    extracted_at TIMESTAMP,
    payload_json VARCHAR
);

CREATE TABLE IF NOT EXISTS raw.weather_observations (
    station_id VARCHAR,
    observed_at TIMESTAMP,
    extracted_at TIMESTAMP,
    payload_json VARCHAR,
    PRIMARY KEY (station_id, observed_at)
);

CREATE TABLE IF NOT EXISTS raw.comtrade_monthly (
    trade_id VARCHAR PRIMARY KEY,
    extracted_at TIMESTAMP,
    payload_json VARCHAR
);

CREATE TABLE IF NOT EXISTS bronze.bts_flights (
    flight_id VARCHAR PRIMARY KEY,
    flight_date DATE,
    carrier VARCHAR,
    flight_number INTEGER,
    origin VARCHAR,
    destination VARCHAR,
    dep_delay_minutes INTEGER,
    arr_delay_minutes INTEGER,
    cancelled BOOLEAN,
    extracted_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bronze.weather_observations (
    station_id VARCHAR,
    observed_at TIMESTAMP,
    temperature_c DOUBLE,
    wind_speed_kts DOUBLE,
    precip_mm DOUBLE,
    condition VARCHAR,
    extracted_at TIMESTAMP,
    PRIMARY KEY (station_id, observed_at)
);

CREATE TABLE IF NOT EXISTS bronze.comtrade_monthly (
    trade_id VARCHAR PRIMARY KEY,
    period DATE,
    reporter_iso VARCHAR,
    partner_iso VARCHAR,
    commodity_code VARCHAR,
    trade_flow VARCHAR,
    trade_value_usd DOUBLE,
    net_weight_kg DOUBLE,
    extracted_at TIMESTAMP
);
"""


def connect(duckdb_path: Path) -> duckdb.DuckDBPyConnection:
    duckdb_path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(duckdb_path))
    conn.execute(SCHEMA_SQL)
    return conn


def ingest_result(
    conn: duckdb.DuckDBPyConnection, result: ConnectorResult, artifact_dir: Path
) -> IngestSummary:
    extracted_at = datetime.now(UTC).replace(tzinfo=None)
    artifact_path = _write_raw_artifact(artifact_dir, result, extracted_at.replace(tzinfo=UTC))
    run_id = f"{result.source}-{extracted_at.strftime('%Y%m%dT%H%M%S')}"
    conn.execute(
        """
        INSERT INTO raw.ingestion_runs (
            run_id, source, mode, extracted_at, record_count, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            run_id,
            result.source,
            str(result.metadata.get("mode", "unknown")),
            extracted_at,
            len(result.records),
            json.dumps(result.metadata, sort_keys=True),
        ],
    )

    if result.source == "bts":
        _ingest_bts(conn, result.records, extracted_at)
    elif result.source == "weather":
        _ingest_weather(conn, result.records, extracted_at)
    elif result.source == "comtrade":
        _ingest_comtrade(conn, result.records, extracted_at)
    else:
        raise ValueError(f"Unsupported source: {result.source}")

    bronze_rows = int(
        conn.execute(f"SELECT COUNT(*) FROM bronze.{_bronze_table(result.source)}").fetchone()[0]
    )
    return IngestSummary(result.source, len(result.records), bronze_rows, artifact_path)


def _write_raw_artifact(
    artifact_dir: Path, result: ConnectorResult, extracted_at: datetime
) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{result.source}_{extracted_at.strftime('%Y%m%dT%H%M%SZ')}.jsonl"
    lines = []
    for row in result.records:
        lines.append(
            json.dumps(
                {"source": result.source, "extracted_at": extracted_at.isoformat(), "payload": row},
                sort_keys=True,
            )
        )
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return path


def _bronze_table(source: str) -> str:
    return {
        "bts": "bts_flights",
        "weather": "weather_observations",
        "comtrade": "comtrade_monthly",
    }[source]


def _ingest_bts(
    conn: duckdb.DuckDBPyConnection, rows: list[dict[str, Any]], extracted_at: datetime
) -> None:
    for row in rows:
        conn.execute("DELETE FROM raw.bts_flights WHERE flight_id = ?", [row["flight_id"]])
        conn.execute(
            "INSERT INTO raw.bts_flights VALUES (?, ?, ?)",
            [row["flight_id"], extracted_at, json.dumps(row, sort_keys=True)],
        )
        conn.execute("DELETE FROM bronze.bts_flights WHERE flight_id = ?", [row["flight_id"]])
        conn.execute(
            """
            INSERT INTO bronze.bts_flights
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row["flight_id"],
                row["flight_date"],
                row["carrier"],
                row["flight_number"],
                row["origin"],
                row["destination"],
                row["dep_delay_minutes"],
                row["arr_delay_minutes"],
                row["cancelled"],
                extracted_at,
            ],
        )


def _ingest_weather(
    conn: duckdb.DuckDBPyConnection, rows: list[dict[str, Any]], extracted_at: datetime
) -> None:
    for row in rows:
        conn.execute(
            "DELETE FROM raw.weather_observations WHERE station_id = ? AND observed_at = ?",
            [row["station_id"], row["observed_at"]],
        )
        conn.execute(
            "INSERT INTO raw.weather_observations VALUES (?, ?, ?, ?)",
            [row["station_id"], row["observed_at"], extracted_at, json.dumps(row, sort_keys=True)],
        )
        conn.execute(
            "DELETE FROM bronze.weather_observations WHERE station_id = ? AND observed_at = ?",
            [row["station_id"], row["observed_at"]],
        )
        conn.execute(
            """
            INSERT INTO bronze.weather_observations
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row["station_id"],
                row["observed_at"],
                row["temperature_c"],
                row["wind_speed_kts"],
                row["precip_mm"],
                row["condition"],
                extracted_at,
            ],
        )


def _ingest_comtrade(
    conn: duckdb.DuckDBPyConnection, rows: list[dict[str, Any]], extracted_at: datetime
) -> None:
    for row in rows:
        conn.execute("DELETE FROM raw.comtrade_monthly WHERE trade_id = ?", [row["trade_id"]])
        conn.execute(
            "INSERT INTO raw.comtrade_monthly VALUES (?, ?, ?)",
            [row["trade_id"], extracted_at, json.dumps(row, sort_keys=True)],
        )
        conn.execute("DELETE FROM bronze.comtrade_monthly WHERE trade_id = ?", [row["trade_id"]])
        conn.execute(
            """
            INSERT INTO bronze.comtrade_monthly
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                row["trade_id"],
                f"{row['period']}-01",
                row["reporter_iso"],
                row["partner_iso"],
                row["commodity_code"],
                row["trade_flow"],
                row["trade_value_usd"],
                row["net_weight_kg"],
                extracted_at,
            ],
        )
