from __future__ import annotations

from datetime import date, datetime, timedelta


def _generate_bts_fixture() -> list[dict[str, object]]:
    start_date = date(2024, 1, 5)
    route_templates = [
        {"carrier": "AA", "flight_number": 100, "origin": "JFK", "destination": "LAX"},
        {"carrier": "DL", "flight_number": 205, "origin": "LGA", "destination": "ATL"},
        {"carrier": "UA", "flight_number": 330, "origin": "EWR", "destination": "ORD"},
        {"carrier": "SW", "flight_number": 511, "origin": "BWI", "destination": "MDW"},
        {"carrier": "AA", "flight_number": 118, "origin": "JFK", "destination": "MIA"},
    ]

    rows: list[dict[str, object]] = []
    for day_offset in range(25):
        flight_date = start_date + timedelta(days=day_offset)
        for route_index, route in enumerate(route_templates):
            record_index = (day_offset * len(route_templates)) + route_index
            dep_delay = (
                -6
                + (day_offset % 5) * 4
                + route_index * 7
                + (day_offset // 4) * 2
                + ((record_index % 3) * 3)
            )
            arr_delay = dep_delay + 5 + ((day_offset + route_index) % 4) * 4
            cancelled = record_index % 17 == 0
            if cancelled:
                dep_delay = 0
                arr_delay = 0

            flight_number = int(route["flight_number"]) + (day_offset * 10)
            rows.append(
                {
                    "flight_id": (
                        f"{flight_date.isoformat()}-{route['carrier']}-{flight_number}-"
                        f"{route['origin']}-{route['destination']}"
                    ),
                    "flight_date": flight_date.isoformat(),
                    "carrier": route["carrier"],
                    "flight_number": flight_number,
                    "origin": route["origin"],
                    "destination": route["destination"],
                    "dep_delay_minutes": dep_delay,
                    "arr_delay_minutes": arr_delay,
                    "cancelled": cancelled,
                }
            )
    return rows


def _generate_weather_fixture() -> list[dict[str, object]]:
    start_date = date(2024, 1, 5)
    station_templates = [
        {
            "station_id": "KJFK",
            "temperature_c": 2.8,
            "wind_speed_kts": 14.0,
            "condition": "Cloudy",
        },
        {
            "station_id": "KLGA",
            "temperature_c": 2.1,
            "wind_speed_kts": 12.0,
            "condition": "Overcast",
        },
        {
            "station_id": "KEWR",
            "temperature_c": 1.9,
            "wind_speed_kts": 17.0,
            "condition": "Rain",
        },
        {
            "station_id": "KBWI",
            "temperature_c": 3.4,
            "wind_speed_kts": 10.0,
            "condition": "Clear",
        },
        {
            "station_id": "KATL",
            "temperature_c": 8.3,
            "wind_speed_kts": 15.0,
            "condition": "Rain",
        },
    ]

    rows: list[dict[str, object]] = []
    for day_offset in range(25):
        observed_date = start_date + timedelta(days=day_offset)
        for station_index, station in enumerate(station_templates):
            observed_at = datetime.combine(
                observed_date,
                datetime.min.time(),
            ) + timedelta(hours=10 + station_index)
            rows.append(
                {
                    "station_id": station["station_id"],
                    "observed_at": observed_at.isoformat(timespec="seconds") + "Z",
                    "temperature_c": round(
                        float(station["temperature_c"]) + ((day_offset % 6) - 2) * 1.1,
                        1,
                    ),
                    "wind_speed_kts": round(
                        float(station["wind_speed_kts"]) + ((day_offset + station_index) % 5) * 1.7,
                        1,
                    ),
                    "precip_mm": round(((day_offset + station_index) % 4) * 0.6, 1),
                    "condition": station["condition"],
                }
            )
    return rows


def _generate_comtrade_fixture() -> list[dict[str, object]]:
    periods = ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05", "2024-06"]
    trade_templates = [
        {
            "partner_iso": "HKG",
            "commodity_code": "8517",
            "trade_flow": "Import",
            "base_value": 1250000.0,
            "base_weight": 24000.0,
        },
        {
            "partner_iso": "CAN",
            "commodity_code": "8703",
            "trade_flow": "Export",
            "base_value": 980000.0,
            "base_weight": 15300.0,
        },
        {
            "partner_iso": "MEX",
            "commodity_code": "2710",
            "trade_flow": "Export",
            "base_value": 1560000.0,
            "base_weight": 51000.0,
        },
        {
            "partner_iso": "CHN",
            "commodity_code": "8471",
            "trade_flow": "Import",
            "base_value": 2140000.0,
            "base_weight": 28400.0,
        },
    ]

    rows: list[dict[str, object]] = []
    for period_index, period in enumerate(periods):
        for template_index, template in enumerate(trade_templates):
            multiplier = 1 + (period_index * 0.08) + (template_index * 0.03)
            rows.append(
                {
                    "trade_id": (
                        f"{period}-USA-{template['partner_iso']}-"
                        f"{template['commodity_code']}"
                    ),
                    "period": period,
                    "reporter_iso": "USA",
                    "partner_iso": template["partner_iso"],
                    "commodity_code": template["commodity_code"],
                    "trade_flow": template["trade_flow"],
                    "trade_value_usd": round(float(template["base_value"]) * multiplier, 2),
                    "net_weight_kg": round(float(template["base_weight"]) * multiplier, 2),
                }
            )
    return rows


BTS_FIXTURE = _generate_bts_fixture()
WEATHER_FIXTURE = _generate_weather_fixture()
COMTRADE_FIXTURE = _generate_comtrade_fixture()
