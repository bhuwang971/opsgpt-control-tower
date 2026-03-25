from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

from app.cycle1.storage import connect


@dataclass(frozen=True)
class FlightExample:
    event_date: date
    carrier_code: str
    origin_airport_code: str
    destination_airport_code: str
    dep_delay_minutes: float
    weather_severity: float
    severe_delay_label: int
    arr_delay_minutes: float


def build_benchmark_dataset(duckdb_path: Path) -> list[FlightExample]:
    conn = connect(duckdb_path)
    rows = conn.execute(
        """
        WITH weather_daily AS (
            SELECT
                airport_code,
                observation_date,
                AVG(ABS(temperature_c)) AS avg_abs_temperature,
                AVG(wind_speed_kts) AS avg_wind_speed_kts,
                AVG(precip_mm) AS avg_precip_mm
            FROM analytics.fct_weather_observations
            GROUP BY 1, 2
        )
        SELECT
            f.flight_date,
            f.carrier_code,
            f.origin_airport_code,
            f.destination_airport_code,
            f.dep_delay_minutes,
            f.arr_delay_minutes,
            COALESCE(w.avg_abs_temperature, 0.0) AS avg_abs_temperature,
            COALESCE(w.avg_wind_speed_kts, 0.0) AS avg_wind_speed_kts,
            COALESCE(w.avg_precip_mm, 0.0) AS avg_precip_mm
        FROM analytics.fct_flight_operations AS f
        LEFT JOIN weather_daily AS w
            ON f.origin_airport_code = w.airport_code
           AND f.flight_date = w.observation_date
        ORDER BY f.flight_date, f.flight_id
        """
    ).fetchall()
    conn.close()

    benchmark_rows: list[FlightExample] = []
    for source_index, row in enumerate(rows):
        base_date = row[0]
        for offset in range(42):
            event_date = base_date + timedelta(days=offset)
            dep_delay = float(row[4]) + _dep_delay_adjustment(
                offset=offset, source_index=source_index
            )
            weather_severity = _weather_severity(
                avg_abs_temperature=float(row[6]),
                avg_wind_speed_kts=float(row[7]),
                avg_precip_mm=float(row[8]),
                offset=offset,
            )
            arr_delay = dep_delay + (weather_severity * 0.6) + _route_adjustment(source_index)
            severe_delay = 1 if arr_delay >= 60 else 0
            benchmark_rows.append(
                FlightExample(
                    event_date=event_date,
                    carrier_code=str(row[1]),
                    origin_airport_code=str(row[2]),
                    destination_airport_code=str(row[3]),
                    dep_delay_minutes=dep_delay,
                    weather_severity=weather_severity,
                    severe_delay_label=severe_delay,
                    arr_delay_minutes=arr_delay,
                )
            )
    return benchmark_rows


def time_split_rows(
    rows: list[FlightExample], test_fraction: float = 0.25
) -> tuple[list[FlightExample], list[FlightExample]]:
    unique_dates = sorted({row.event_date for row in rows})
    split_index = max(1, int(len(unique_dates) * (1 - test_fraction)))
    cutoff = unique_dates[split_index - 1]
    train = [row for row in rows if row.event_date <= cutoff]
    test = [row for row in rows if row.event_date > cutoff]
    if not test:
        test = [row for row in rows if row.event_date == cutoff]
        train = [row for row in rows if row.event_date < cutoff]
    return train, test


def build_daily_forecast_series(rows: list[FlightExample]) -> list[dict[str, float | str]]:
    daily: dict[date, list[FlightExample]] = {}
    for row in rows:
        daily.setdefault(row.event_date, []).append(row)
    output = []
    for event_date in sorted(daily):
        day_rows = daily[event_date]
        on_time_count = sum(1 for row in day_rows if row.arr_delay_minutes <= 15)
        output.append(
            {
                "event_date": event_date.isoformat(),
                "total_flights": float(len(day_rows)),
                "on_time_rate": on_time_count / len(day_rows),
                "avg_arr_delay_minutes": sum(row.arr_delay_minutes for row in day_rows)
                / len(day_rows),
            }
        )
    return output


def _dep_delay_adjustment(*, offset: int, source_index: int) -> float:
    wave = ((offset % 7) - 3) * 2.5
    trend = (offset // 7) * 1.5
    source_bias = (source_index - 1) * 4.0
    return wave + trend + source_bias


def _weather_severity(
    *,
    avg_abs_temperature: float,
    avg_wind_speed_kts: float,
    avg_precip_mm: float,
    offset: int,
) -> float:
    offset_pressure = 1.5 if offset % 5 == 0 else 0.0
    return (
        (avg_abs_temperature * 0.15)
        + (avg_wind_speed_kts * 0.4)
        + (avg_precip_mm * 4.0)
        + offset_pressure
    )


def _route_adjustment(source_index: int) -> float:
    return {0: 6.0, 1: -2.0, 2: 10.0}.get(source_index, 0.0)
