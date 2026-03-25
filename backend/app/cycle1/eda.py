from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import duckdb


def build_eda_payload(conn: duckdb.DuckDBPyConnection) -> dict[str, object]:
    flights = conn.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            AVG(arr_delay_minutes) AS avg_arr_delay_minutes,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY arr_delay_minutes) AS p50_arr_delay_minutes,
            SUM(CASE WHEN cancelled THEN 1 ELSE 0 END) AS cancelled_flights
        FROM bronze.bts_flights
        """
    ).fetchone()
    weather = conn.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            AVG(temperature_c) AS avg_temperature_c,
            MAX(wind_speed_kts) AS max_wind_speed_kts,
            AVG(precip_mm) AS avg_precip_mm
        FROM bronze.weather_observations
        """
    ).fetchone()
    trade = conn.execute(
        """
        SELECT
            COUNT(*) AS row_count,
            SUM(trade_value_usd) AS total_trade_value_usd,
            AVG(net_weight_kg) AS avg_net_weight_kg
        FROM bronze.comtrade_monthly
        """
    ).fetchone()
    carriers = conn.execute(
        """
        SELECT carrier, COUNT(*) AS flight_count
        FROM bronze.bts_flights
        GROUP BY 1
        ORDER BY flight_count DESC, carrier ASC
        LIMIT 5
        """
    ).fetchall()
    conditions = conn.execute(
        """
        SELECT condition, COUNT(*) AS observation_count
        FROM bronze.weather_observations
        GROUP BY 1
        ORDER BY observation_count DESC, condition ASC
        LIMIT 5
        """
    ).fetchall()
    commodities = conn.execute(
        """
        SELECT commodity_code, SUM(trade_value_usd) AS trade_value_usd
        FROM bronze.comtrade_monthly
        GROUP BY 1
        ORDER BY trade_value_usd DESC, commodity_code ASC
        LIMIT 5
        """
    ).fetchall()
    return {
        "generated_at": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "tables": {
            "bts_flights": {
                "row_count": int(flights[0]),
                "avg_arr_delay_minutes": float(flights[1]) if flights[1] is not None else None,
                "p50_arr_delay_minutes": float(flights[2]) if flights[2] is not None else None,
                "cancelled_flights": int(flights[3]),
            },
            "weather_observations": {
                "row_count": int(weather[0]),
                "avg_temperature_c": float(weather[1]) if weather[1] is not None else None,
                "max_wind_speed_kts": float(weather[2]) if weather[2] is not None else None,
                "avg_precip_mm": float(weather[3]) if weather[3] is not None else None,
            },
            "comtrade_monthly": {
                "row_count": int(trade[0]),
                "total_trade_value_usd": float(trade[1]) if trade[1] is not None else None,
                "avg_net_weight_kg": float(trade[2]) if trade[2] is not None else None,
            },
        },
        "top_segments": {
            "carriers": [{"carrier": row[0], "flight_count": int(row[1])} for row in carriers],
            "weather_conditions": [
                {"condition": row[0], "observation_count": int(row[1])} for row in conditions
            ],
            "commodity_codes": [
                {"commodity_code": row[0], "trade_value_usd": float(row[1])} for row in commodities
            ],
        },
    }


def write_eda_report(payload: dict[str, object], artifact_dir: Path) -> tuple[Path, Path]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = str(payload["generated_at"])
    json_path = artifact_dir / f"eda_{timestamp}.json"
    md_path = artifact_dir / f"eda_{timestamp}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    tables = payload["tables"]
    top_segments = payload["top_segments"]
    lines = [
        "# Cycle 1 EDA Summary",
        "",
        f"Generated at: `{timestamp}`",
        "",
        "## Table Summary",
        "",
        (
            f"- BTS flights: {tables['bts_flights']['row_count']} rows, "
            f"avg arrival delay {tables['bts_flights']['avg_arr_delay_minutes']}"
        ),
        (
            f"- Weather observations: {tables['weather_observations']['row_count']} rows, "
            f"avg temp {tables['weather_observations']['avg_temperature_c']}"
        ),
        (
            f"- Comtrade monthly: {tables['comtrade_monthly']['row_count']} rows, "
            f"total trade value {tables['comtrade_monthly']['total_trade_value_usd']}"
        ),
        "",
        "## Top Segments",
        "",
        f"- Carriers: {top_segments['carriers']}",
        f"- Weather conditions: {top_segments['weather_conditions']}",
        f"- Commodity codes: {top_segments['commodity_codes']}",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path
