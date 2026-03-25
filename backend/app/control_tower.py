from __future__ import annotations

import csv
import io
import json
import os
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import Any

from app.cycle1.storage import connect
from app.cycle4.cli import run_full as run_cycle4_full


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_duckdb_path() -> Path:
    configured = os.getenv("DUCKDB_PATH")
    if configured:
        return Path(configured)
    return repo_root() / "backend" / "data" / "warehouse" / "control_tower.duckdb"


def runtime_artifact_root() -> Path:
    return repo_root() / "backend" / "artifacts" / "runtime_control_tower"


def ensure_runtime_assets() -> dict[str, Any]:
    duckdb_path = default_duckdb_path()
    artifact_root = runtime_artifact_root()
    summary_path = artifact_root / "latest_cycle4_summary.json"
    if _warehouse_ready(duckdb_path) and summary_path.exists():
        return json.loads(summary_path.read_text(encoding="utf-8"))

    result = run_cycle4_full(
        repo_root=repo_root(),
        duckdb_path=duckdb_path,
        artifact_root=artifact_root,
    )
    artifact_root.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def control_tower_overview() -> dict[str, Any]:
    runtime = ensure_runtime_assets()
    duckdb_path = default_duckdb_path()
    conn = connect(duckdb_path)

    daily_rows = conn.execute(
        """
        SELECT
            flight_date,
            total_flights,
            on_time_rate,
            p50_arr_delay_minutes,
            p90_arr_delay_minutes,
            cancellation_rate,
            severe_delay_rate,
            reliability_score,
            volatility_index
        FROM analytics.mart_kpi_daily_operations
        ORDER BY flight_date
        """
    ).fetchall()
    carrier_rows = conn.execute(
        """
        SELECT
            carrier_code,
            total_flights,
            on_time_rate,
            avg_arr_delay_minutes,
            severe_delay_rate,
            cancellation_rate
        FROM analytics.mart_kpi_carrier_performance
        ORDER BY on_time_rate DESC, avg_arr_delay_minutes ASC
        """
    ).fetchall()
    trade_rows = conn.execute(
        """
        SELECT
            period,
            reporter_iso,
            trade_flow,
            shipment_count,
            total_trade_value_usd,
            avg_net_weight_kg
        FROM analytics.mart_kpi_trade_monthly
        ORDER BY period, trade_flow
        """
    ).fetchall()
    conn.close()

    latest = daily_rows[-1]
    previous = daily_rows[-2] if len(daily_rows) > 1 else latest
    trend = runtime["cycle3"]["report"]["trend_summary"]
    training = runtime["training"]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "kpis": _kpis(latest, previous),
        "daily_trend": [
            {
                "date": str(row[0]),
                "total_flights": int(row[1]),
                "on_time_rate": float(row[2]),
                "p50_arr_delay_minutes": float(row[3]),
                "p90_arr_delay_minutes": float(row[4]),
                "cancellation_rate": float(row[5]),
                "severe_delay_rate": float(row[6]),
                "reliability_score": float(row[7]),
                "volatility_index": float(row[8]),
            }
            for row in daily_rows
        ],
        "carrier_drilldown": [
            {
                "carrier_code": row[0],
                "total_flights": int(row[1]),
                "on_time_rate": float(row[2]),
                "avg_arr_delay_minutes": float(row[3]),
                "severe_delay_rate": float(row[4]),
                "cancellation_rate": float(row[5]),
            }
            for row in carrier_rows
        ],
        "trade_lens": [
            {
                "period": str(row[0]),
                "reporter_iso": row[1],
                "trade_flow": row[2],
                "shipment_count": int(row[3]),
                "total_trade_value_usd": float(row[4]),
                "avg_net_weight_kg": float(row[5]),
            }
            for row in trade_rows
        ],
        "alerts": _alerts(latest, previous, training),
        "forecast": {
            "horizon_days": 5,
            "projected_on_time_rate": _forecast_points(
                latest_date=latest[0],
                latest_on_time_rate=float(latest[2]),
                latest_reliability=float(latest[7]),
                slope=float(trend["on_time_rate_slope"]),
            ),
            "baseline_metrics": {
                "classification_pr_auc_proxy": float(
                    training["classification"]["baseline_segmented"]["metrics"]["pr_auc_proxy"]
                ),
                "regression_mae": float(
                    training["regression"]["baseline_segmented"]["metrics"]["mae"]
                ),
                "forecast_rmse": float(
                    training["forecasting"]["baseline_moving_average"]["metrics"]["rmse"]
                ),
            },
        },
        "saved_views": [
            {
                "id": "network_watch",
                "name": "Network Watch",
                "description": "Latest daily reliability, volatility, and severe-delay view.",
            },
            {
                "id": "carrier_benchmark",
                "name": "Carrier Benchmark",
                "description": "Carrier leaderboard by on-time performance and delay burden.",
            },
            {
                "id": "trade_context",
                "name": "Trade Context",
                "description": "Monthly import/export context to pair with ops narratives.",
            },
        ],
        "exports": [
            {"dataset": "daily_kpis", "path": "/api/control-tower/export/daily_kpis"},
            {
                "dataset": "carrier_performance",
                "path": "/api/control-tower/export/carrier_performance",
            },
            {"dataset": "trade_monthly", "path": "/api/control-tower/export/trade_monthly"},
        ],
    }


def export_dataset(dataset: str) -> str:
    ensure_runtime_assets()
    conn = connect(default_duckdb_path())
    queries = {
        "daily_kpis": """
            SELECT flight_date, total_flights, on_time_rate, p50_arr_delay_minutes,
                   p90_arr_delay_minutes, cancellation_rate, severe_delay_rate,
                   reliability_score, volatility_index
            FROM analytics.mart_kpi_daily_operations
            ORDER BY flight_date
        """,
        "carrier_performance": """
            SELECT carrier_code, total_flights, on_time_rate, avg_arr_delay_minutes,
                   severe_delay_rate, cancellation_rate
            FROM analytics.mart_kpi_carrier_performance
            ORDER BY on_time_rate DESC, avg_arr_delay_minutes ASC
        """,
        "trade_monthly": """
            SELECT period, reporter_iso, trade_flow, shipment_count,
                   total_trade_value_usd, avg_net_weight_kg
            FROM analytics.mart_kpi_trade_monthly
            ORDER BY period, trade_flow
        """,
    }
    if dataset not in queries:
        raise KeyError(dataset)
    cursor = conn.execute(queries[dataset])
    rows = cursor.fetchall()
    columns = [item[0] for item in cursor.description]
    conn.close()

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    writer.writerows(rows)
    return buffer.getvalue()


def _warehouse_ready(duckdb_path: Path) -> bool:
    if not duckdb_path.exists():
        return False
    try:
        conn = connect(duckdb_path)
        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_schema = 'analytics'
              AND table_name = 'mart_kpi_daily_operations'
            """
        ).fetchone()[0]
        conn.close()
        return bool(count)
    except Exception:
        return False


def _kpis(latest, previous) -> list[dict[str, Any]]:
    latest_on_time = float(latest[2])
    previous_on_time = float(previous[2])
    latest_reliability = float(latest[7])
    previous_reliability = float(previous[7])
    return [
        {
            "id": "on_time_rate",
            "label": "On-Time Rate",
            "value": latest_on_time,
            "display": f"{latest_on_time:.1%}",
            "delta": latest_on_time - previous_on_time,
            "status": "healthy" if latest_on_time >= 0.5 else "watch",
        },
        {
            "id": "reliability_score",
            "label": "Reliability Score",
            "value": latest_reliability,
            "display": f"{latest_reliability:.1f}",
            "delta": latest_reliability - previous_reliability,
            "status": "healthy" if latest_reliability >= 50 else "risk",
        },
        {
            "id": "p90_arr_delay_minutes",
            "label": "P90 Arrival Delay",
            "value": float(latest[4]),
            "display": f"{float(latest[4]):.1f} min",
            "delta": float(latest[4]) - float(previous[4]),
            "status": "risk" if float(latest[4]) >= 60 else "watch",
        },
        {
            "id": "volatility_index",
            "label": "Volatility Index",
            "value": float(latest[8]),
            "display": f"{float(latest[8]):.1f}",
            "delta": float(latest[8]) - float(previous[8]),
            "status": "watch" if float(latest[8]) > 5 else "healthy",
        },
    ]


def _alerts(latest, previous, training: dict[str, Any]) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    if float(latest[6]) > 0.5:
        alerts.append(
            {
                "severity": "high",
                "title": "Severe Delay Spike",
                "detail": (
                    "Latest daily severe-delay rate crossed 50%, indicating "
                    "concentrated disruption risk."
                ),
            }
        )
    if float(latest[7]) < float(previous[7]):
        alerts.append(
            {
                "severity": "medium",
                "title": "Reliability Sliding",
                "detail": (
                    "Reliability score fell versus the previous observed day "
                    "and should be monitored."
                ),
            }
        )
    regression_mae = float(training["regression"]["baseline_segmented"]["metrics"]["mae"])
    alerts.append(
        {
            "severity": "info",
            "title": "Baseline Model Check",
            "detail": (
                "Segmented regression baseline currently reports "
                f"MAE {regression_mae:.2f} on the time-based holdout."
            ),
        }
    )
    return alerts


def _forecast_points(
    *,
    latest_date: date,
    latest_on_time_rate: float,
    latest_reliability: float,
    slope: float,
) -> list[dict[str, Any]]:
    horizon = []
    for day_index in range(1, 6):
        projected_rate = max(0.0, min(1.0, latest_on_time_rate + (slope * day_index)))
        horizon.append(
            {
                "date": (latest_date + timedelta(days=day_index)).isoformat(),
                "projected_on_time_rate": projected_rate,
                "projected_reliability_score": max(
                    0.0,
                    min(100.0, latest_reliability + (slope * 100 * day_index)),
                ),
            }
        )
    return horizon
