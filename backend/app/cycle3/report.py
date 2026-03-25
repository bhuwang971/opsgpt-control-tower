from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from app.cycle1.storage import connect
from app.cycle3.stats import (
    cohen_d,
    difference_in_proportions,
    negative_binomial_summary,
    poisson_rate_summary,
    rolling_z_scores,
    simple_linear_slope,
)


def build_statistical_report(*, duckdb_path: Path) -> dict[str, object]:
    conn = connect(duckdb_path)
    daily_rows = conn.execute(
        """
        SELECT
            flight_date,
            total_flights,
            on_time_rate,
            severe_delay_rate,
            cancellation_rate,
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
            severe_delay_rate
        FROM analytics.mart_kpi_carrier_performance
        ORDER BY on_time_rate DESC, avg_arr_delay_minutes ASC, carrier_code ASC
        """
    ).fetchall()
    severe_delay_counts = conn.execute(
        """
        SELECT flight_date, SUM(CASE WHEN is_severe_delay THEN 1 ELSE 0 END) AS severe_delay_count
        FROM analytics.fct_flight_operations
        GROUP BY 1
        ORDER BY 1
        """
    ).fetchall()
    conn.close()

    on_time_series = [float(row[2]) for row in daily_rows]
    reliability_series = [float(row[5]) for row in daily_rows]
    severe_counts = [int(row[1]) for row in severe_delay_counts]
    report = {
        "generated_at": datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "trend_summary": _trend_summary(daily_rows, on_time_series, reliability_series),
        "segment_comparison": _segment_comparison(duckdb_path, carrier_rows),
        "probability_models": _probability_models(severe_counts, daily_rows),
        "selected_kpi_segments": _selected_kpi_segments(daily_rows, carrier_rows),
    }
    return report


def write_statistical_report(report: dict[str, object], artifact_dir: Path) -> tuple[Path, Path]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = str(report["generated_at"])
    json_path = artifact_dir / f"cycle3_stats_{timestamp}.json"
    md_path = artifact_dir / f"cycle3_stats_{timestamp}.md"
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    trend = report["trend_summary"]
    segment = report["segment_comparison"]
    probability = report["probability_models"]
    lines = [
        "# Cycle 3 Statistical Report",
        "",
        f"Generated at: `{timestamp}`",
        "",
        "## Trend Summary",
        "",
        f"- On-time rate slope: {trend['on_time_rate_slope']}",
        f"- Reliability score slope: {trend['reliability_score_slope']}",
        f"- Latest on-time z-score: {trend['latest_on_time_rate_zscore']}",
        "",
        "## Segment Comparison",
        "",
        (
            f"- Compared carriers: {segment['best_carrier']['carrier_code']} vs "
            f"{segment['worst_carrier']['carrier_code']}"
        ),
        f"- On-time rate difference: {segment['on_time_rate_test']['difference']}",
        f"- Arrival delay mean difference: {segment['arrival_delay_effect']['mean_difference']}",
        "",
        "## Probability Models",
        "",
        f"- Poisson severe-delay rate: {probability['poisson_daily_severe_delay_rate']['rate']}",
        (
            f"- Negative Binomial overdispersed: "
            f"{probability['negative_binomial_daily_severe_delay']['overdispersed']}"
        ),
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def _trend_summary(
    daily_rows, on_time_series: list[float], reliability_series: list[float]
) -> dict[str, object]:
    on_time_z_scores = rolling_z_scores(on_time_series, window_size=1)
    return {
        "daily_points": [
            {
                "flight_date": str(row[0]),
                "total_flights": int(row[1]),
                "on_time_rate": float(row[2]),
                "severe_delay_rate": float(row[3]),
                "cancellation_rate": float(row[4]),
                "reliability_score": float(row[5]),
                "volatility_index": float(row[6]),
            }
            for row in daily_rows
        ],
        "on_time_rate_slope": simple_linear_slope(on_time_series),
        "reliability_score_slope": simple_linear_slope(reliability_series),
        "latest_on_time_rate_zscore": on_time_z_scores[-1] if on_time_z_scores else None,
    }


def _segment_comparison(duckdb_path: Path, carrier_rows) -> dict[str, object]:
    best_carrier = carrier_rows[0]
    worst_carrier = carrier_rows[-1]
    conn = connect(duckdb_path)
    best_delays = [
        float(row[0])
        for row in conn.execute(
            """
            SELECT arr_delay_minutes
            FROM analytics.fct_flight_operations
            WHERE carrier_code = ?
            ORDER BY flight_date, flight_id
            """,
            [best_carrier[0]],
        ).fetchall()
    ]
    worst_delays = [
        float(row[0])
        for row in conn.execute(
            """
            SELECT arr_delay_minutes
            FROM analytics.fct_flight_operations
            WHERE carrier_code = ?
            ORDER BY flight_date, flight_id
            """,
            [worst_carrier[0]],
        ).fetchall()
    ]
    conn.close()
    prop_test = difference_in_proportions(
        success_a=round(float(best_carrier[2]) * int(best_carrier[1])),
        total_a=int(best_carrier[1]),
        success_b=round(float(worst_carrier[2]) * int(worst_carrier[1])),
        total_b=int(worst_carrier[1]),
    )
    effect = cohen_d(best_delays, worst_delays)
    return {
        "best_carrier": {
            "carrier_code": best_carrier[0],
            "total_flights": int(best_carrier[1]),
            "on_time_rate": float(best_carrier[2]),
            "avg_arr_delay_minutes": float(best_carrier[3]),
        },
        "worst_carrier": {
            "carrier_code": worst_carrier[0],
            "total_flights": int(worst_carrier[1]),
            "on_time_rate": float(worst_carrier[2]),
            "avg_arr_delay_minutes": float(worst_carrier[3]),
        },
        "on_time_rate_test": {
            "proportion_a": prop_test.proportion_a,
            "proportion_b": prop_test.proportion_b,
            "difference": prop_test.difference,
            "z_score": prop_test.z_score,
            "p_value": prop_test.p_value,
        },
        "arrival_delay_effect": {
            "mean_a": effect.mean_a,
            "mean_b": effect.mean_b,
            "mean_difference": effect.mean_difference,
            "cohen_d": effect.cohen_d,
        },
    }


def _probability_models(severe_counts: list[int], daily_rows) -> dict[str, object]:
    total_flights = sum(int(row[1]) for row in daily_rows)
    total_severe = sum(severe_counts)
    poisson = poisson_rate_summary(count=total_severe, exposure=float(total_flights))
    neg_bin = negative_binomial_summary(severe_counts)
    return {
        "poisson_daily_severe_delay_rate": {
            "count": poisson.count,
            "exposure": poisson.exposure,
            "rate": poisson.rate,
            "lower_95": poisson.lower_95,
            "upper_95": poisson.upper_95,
        },
        "negative_binomial_daily_severe_delay": {
            "mean_count": neg_bin.mean_count,
            "variance_count": neg_bin.variance_count,
            "dispersion": neg_bin.dispersion,
            "overdispersed": neg_bin.overdispersed,
        },
    }


def _selected_kpi_segments(daily_rows, carrier_rows) -> dict[str, object]:
    return {
        "daily_operations": [
            {
                "flight_date": str(row[0]),
                "total_flights": int(row[1]),
                "on_time_rate": float(row[2]),
                "severe_delay_rate": float(row[3]),
            }
            for row in daily_rows
        ],
        "carrier_performance": [
            {
                "carrier_code": row[0],
                "total_flights": int(row[1]),
                "on_time_rate": float(row[2]),
                "avg_arr_delay_minutes": float(row[3]),
                "severe_delay_rate": float(row[4]),
            }
            for row in carrier_rows
        ],
    }
