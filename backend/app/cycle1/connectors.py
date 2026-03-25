from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

from app.cycle1.fixtures import BTS_FIXTURE, COMTRADE_FIXTURE, WEATHER_FIXTURE


@dataclass(frozen=True)
class ConnectorResult:
    source: str
    records: list[dict[str, Any]]
    metadata: dict[str, Any]


def _request_json_pages(
    *,
    base_url: str,
    params: dict[str, Any] | None = None,
    retries: int = 3,
    timeout_seconds: float = 10.0,
) -> list[dict[str, Any]]:
    merged_params = dict(params or {})
    page = 1
    rows: list[dict[str, Any]] = []
    while True:
        merged_params["page"] = page
        for attempt in range(1, retries + 1):
            try:
                response = httpx.get(base_url, params=merged_params, timeout=timeout_seconds)
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, dict):
                    page_rows = payload.get("data", [])
                    has_more = bool(payload.get("next_page"))
                else:
                    page_rows = payload
                    has_more = False
                if not isinstance(page_rows, list):
                    raise ValueError("Expected a list payload from JSON connector")
                rows.extend(page_rows)
                if not has_more or not page_rows:
                    return rows
                page += 1
                break
            except Exception:
                if attempt == retries:
                    raise
                time.sleep(attempt)
    return rows


def _request_csv(
    *,
    url: str,
    retries: int = 3,
    timeout_seconds: float = 15.0,
) -> list[dict[str, Any]]:
    for attempt in range(1, retries + 1):
        try:
            response = httpx.get(url, timeout=timeout_seconds)
            response.raise_for_status()
            return list(csv.DictReader(response.text.splitlines()))
        except Exception:
            if attempt == retries:
                raise
            time.sleep(attempt)
    return []


def _read_fixture_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_bts(
    *, mode: str, fixture_path: Path | None = None, url: str | None = None
) -> ConnectorResult:
    if mode == "fixture":
        rows = _read_fixture_json(fixture_path) if fixture_path else BTS_FIXTURE
        return ConnectorResult("bts", rows, {"mode": mode, "record_count": len(rows)})
    if not url:
        raise ValueError("BTS live mode requires a download URL")
    rows = _request_csv(url=url)
    normalized = [
        {
            "flight_id": row.get("flight_id")
            or (
                f"{row['flight_date']}-{row['carrier']}-{row['flight_number']}-"
                f"{row['origin']}-{row['destination']}"
            ),
            "flight_date": row["flight_date"],
            "carrier": row["carrier"],
            "flight_number": int(row["flight_number"]),
            "origin": row["origin"],
            "destination": row["destination"],
            "dep_delay_minutes": int(row["dep_delay_minutes"]),
            "arr_delay_minutes": int(row["arr_delay_minutes"]),
            "cancelled": str(row.get("cancelled", "false")).lower() == "true",
        }
        for row in rows
    ]
    return ConnectorResult(
        "bts", normalized, {"mode": mode, "record_count": len(normalized), "url": url}
    )


def fetch_weather(
    *,
    mode: str,
    fixture_path: Path | None = None,
    base_url: str | None = None,
    station: str = "KJFK",
) -> ConnectorResult:
    if mode == "fixture":
        rows = _read_fixture_json(fixture_path) if fixture_path else WEATHER_FIXTURE
        return ConnectorResult("weather", rows, {"mode": mode, "record_count": len(rows)})
    if not base_url:
        raise ValueError("Weather live mode requires a base URL")
    rows = _request_json_pages(base_url=base_url, params={"station": station})
    normalized = [
        {
            "station_id": row["station_id"],
            "observed_at": row["observed_at"],
            "temperature_c": float(row["temperature_c"]),
            "wind_speed_kts": float(row["wind_speed_kts"]),
            "precip_mm": float(row["precip_mm"]),
            "condition": row["condition"],
        }
        for row in rows
    ]
    return ConnectorResult(
        "weather",
        normalized,
        {"mode": mode, "record_count": len(normalized), "base_url": base_url, "station": station},
    )


def fetch_comtrade(
    *,
    mode: str,
    fixture_path: Path | None = None,
    base_url: str | None = None,
    reporter: str = "USA",
) -> ConnectorResult:
    if mode == "fixture":
        rows = _read_fixture_json(fixture_path) if fixture_path else COMTRADE_FIXTURE
        return ConnectorResult("comtrade", rows, {"mode": mode, "record_count": len(rows)})
    if not base_url:
        raise ValueError("Comtrade live mode requires a base URL")
    rows = _request_json_pages(base_url=base_url, params={"reporter": reporter})
    normalized = [
        {
            "trade_id": row["trade_id"],
            "period": row["period"],
            "reporter_iso": row["reporter_iso"],
            "partner_iso": row["partner_iso"],
            "commodity_code": row["commodity_code"],
            "trade_flow": row["trade_flow"],
            "trade_value_usd": float(row["trade_value_usd"]),
            "net_weight_kg": float(row["net_weight_kg"]),
        }
        for row in rows
    ]
    return ConnectorResult(
        "comtrade",
        normalized,
        {"mode": mode, "record_count": len(normalized), "base_url": base_url, "reporter": reporter},
    )
