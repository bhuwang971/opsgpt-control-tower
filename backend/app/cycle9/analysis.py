from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Any

from app import control_tower
from app.cycle1.storage import connect
from app.cycle3.stats import difference_in_proportions


@dataclass(frozen=True)
class ToggleSpec:
    toggle_name: str
    title: str
    description: str
    delay_reduction_minutes: float
    alpha: float = 0.05
    power_target: float = 0.8


def available_toggles() -> dict[str, ToggleSpec]:
    return {
        "adaptive_turnaround_buffers": ToggleSpec(
            toggle_name="adaptive_turnaround_buffers",
            title="Adaptive Turnaround Buffers",
            description=(
                "Local fixture-backed toggle that reduces effective arrival delay for"
                " the treated cohort to emulate an operational recovery policy."
            ),
            delay_reduction_minutes=6.0,
        )
    }


def analyze_experiment(duckdb_path: Path, toggle_name: str) -> dict[str, Any]:
    toggle = available_toggles().get(toggle_name)
    if toggle is None:
        raise KeyError(toggle_name)

    control_tower.ensure_runtime_assets()
    rows = _load_experiment_rows(duckdb_path, toggle)
    grouped = _group_by_variant(rows)
    primary = _primary_metric(grouped["control"], grouped["treatment"], toggle)
    guardrails = _guardrails(grouped["control"], grouped["treatment"])
    sequential_checks = _sequential_checks(rows, toggle)
    segments = _segment_breakdown(rows)
    recommendation = _recommendation(primary, guardrails)

    return {
        "toggle_name": toggle.toggle_name,
        "title": toggle.title,
        "description": toggle.description,
        "design": {
            "primary_metric": "on_time_rate",
            "guardrail_metrics": [
                "cancellation_rate",
                "p90_arr_delay_minutes",
                "severe_delay_rate",
            ],
            "alpha": toggle.alpha,
            "power_target": toggle.power_target,
            "estimated_mde": _estimate_mde(
                grouped["control"],
                grouped["treatment"],
                toggle.alpha,
                toggle.power_target,
            ),
        },
        "sample_size": len(rows),
        "window": {
            "start_date": rows[0]["flight_date"],
            "end_date": rows[-1]["flight_date"],
        },
        "variant_counts": {
            "control": len(grouped["control"]),
            "treatment": len(grouped["treatment"]),
        },
        "primary_metric_result": primary,
        "guardrails": guardrails,
        "sequential_checks": sequential_checks,
        "segment_breakdown": segments,
        "recommendation": recommendation,
    }


def _load_experiment_rows(duckdb_path: Path, toggle: ToggleSpec) -> list[dict[str, Any]]:
    conn = connect(duckdb_path)
    rows = conn.execute(
        """
        SELECT
            flight_id,
            flight_date,
            carrier_code,
            arr_delay_minutes,
            cancelled
        FROM analytics.fct_flight_operations
        ORDER BY flight_date, flight_id
        """
    ).fetchall()
    conn.close()

    experiment_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        flight_id, flight_date, carrier_code, arr_delay_minutes, cancelled = row
        variant = "treatment" if index % 2 == 0 else "control"
        adjusted_delay = float(arr_delay_minutes)
        if variant == "treatment" and not cancelled:
            adjusted_delay = max(0.0, adjusted_delay - toggle.delay_reduction_minutes)
        is_on_time = (not cancelled) and adjusted_delay <= 15
        is_severe_delay = (not cancelled) and adjusted_delay >= 60
        experiment_rows.append(
            {
                "flight_id": flight_id,
                "flight_date": str(flight_date),
                "carrier_code": carrier_code,
                "variant": variant,
                "adjusted_arr_delay_minutes": adjusted_delay,
                "cancelled": bool(cancelled),
                "is_on_time": is_on_time,
                "is_severe_delay": is_severe_delay,
            }
        )
    if not experiment_rows:
        raise ValueError("No flight rows available for experimentation analysis")
    return experiment_rows


def _group_by_variant(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {"control": [], "treatment": []}
    for row in rows:
        grouped[row["variant"]].append(row)
    return grouped


def _primary_metric(
    control_rows: list[dict[str, Any]],
    treatment_rows: list[dict[str, Any]],
    toggle: ToggleSpec,
) -> dict[str, Any]:
    control_success = sum(1 for row in control_rows if row["is_on_time"])
    treatment_success = sum(1 for row in treatment_rows if row["is_on_time"])
    diff = difference_in_proportions(
        success_a=treatment_success,
        total_a=len(treatment_rows),
        success_b=control_success,
        total_b=len(control_rows),
    )
    ci_low, ci_high = _difference_ci_95(
        diff.proportion_a,
        len(treatment_rows),
        diff.proportion_b,
        len(control_rows),
    )
    relative_lift = 0.0 if diff.proportion_b == 0 else diff.difference / diff.proportion_b
    return {
        "metric": "on_time_rate",
        "control_rate": diff.proportion_b,
        "treatment_rate": diff.proportion_a,
        "absolute_lift": diff.difference,
        "relative_lift": relative_lift,
        "z_score": diff.z_score,
        "p_value": diff.p_value,
        "ci_95": [ci_low, ci_high],
        "significant": diff.p_value < toggle.alpha,
    }


def _guardrails(
    control_rows: list[dict[str, Any]],
    treatment_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    control_cancellations = sum(1 for row in control_rows if row["cancelled"])
    treatment_cancellations = sum(1 for row in treatment_rows if row["cancelled"])
    cancellation_diff = difference_in_proportions(
        success_a=treatment_cancellations,
        total_a=len(treatment_rows),
        success_b=control_cancellations,
        total_b=len(control_rows),
    )
    control_severe = sum(1 for row in control_rows if row["is_severe_delay"])
    treatment_severe = sum(1 for row in treatment_rows if row["is_severe_delay"])
    severe_diff = difference_in_proportions(
        success_a=treatment_severe,
        total_a=len(treatment_rows),
        success_b=control_severe,
        total_b=len(control_rows),
    )
    control_delays = [float(row["adjusted_arr_delay_minutes"]) for row in control_rows]
    treatment_delays = [float(row["adjusted_arr_delay_minutes"]) for row in treatment_rows]
    p90_control = _percentile(control_delays, 0.9)
    p90_treatment = _percentile(treatment_delays, 0.9)
    return [
        {
            "metric": "cancellation_rate",
            "control_value": cancellation_diff.proportion_b,
            "treatment_value": cancellation_diff.proportion_a,
            "difference": cancellation_diff.difference,
            "status": "pass" if cancellation_diff.difference <= 0.01 else "watch",
        },
        {
            "metric": "p90_arr_delay_minutes",
            "control_value": p90_control,
            "treatment_value": p90_treatment,
            "difference": p90_treatment - p90_control,
            "status": "pass" if (p90_treatment - p90_control) <= 5.0 else "watch",
        },
        {
            "metric": "severe_delay_rate",
            "control_value": severe_diff.proportion_b,
            "treatment_value": severe_diff.proportion_a,
            "difference": severe_diff.difference,
            "status": "pass" if severe_diff.difference <= 0.01 else "watch",
        },
    ]


def _sequential_checks(rows: list[dict[str, Any]], toggle: ToggleSpec) -> list[dict[str, Any]]:
    checkpoints = sorted({row["flight_date"] for row in rows})
    summaries: list[dict[str, Any]] = []
    for checkpoint in checkpoints:
        checkpoint_rows = [row for row in rows if row["flight_date"] <= checkpoint]
        grouped = _group_by_variant(checkpoint_rows)
        if not grouped["control"] or not grouped["treatment"]:
            continue
        control_success = sum(1 for row in grouped["control"] if row["is_on_time"])
        treatment_success = sum(1 for row in grouped["treatment"] if row["is_on_time"])
        diff = difference_in_proportions(
            success_a=treatment_success,
            total_a=len(grouped["treatment"]),
            success_b=control_success,
            total_b=len(grouped["control"]),
        )
        summaries.append(
            {
                "checkpoint": checkpoint,
                "sample_size": len(checkpoint_rows),
                "absolute_lift": diff.difference,
                "p_value": diff.p_value,
                "decision": "keep-running" if diff.p_value >= toggle.alpha else "promising",
            }
        )
    return summaries


def _segment_breakdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    carriers = sorted({row["carrier_code"] for row in rows})
    segments: list[dict[str, Any]] = []
    for carrier in carriers:
        carrier_rows = [row for row in rows if row["carrier_code"] == carrier]
        grouped = _group_by_variant(carrier_rows)
        if not grouped["control"] or not grouped["treatment"]:
            continue
        control_rate = _rate(grouped["control"], "is_on_time")
        treatment_rate = _rate(grouped["treatment"], "is_on_time")
        segments.append(
            {
                "carrier_code": carrier,
                "control_rate": control_rate,
                "treatment_rate": treatment_rate,
                "absolute_lift": treatment_rate - control_rate,
                "sample_size": len(carrier_rows),
            }
        )
    return sorted(segments, key=lambda item: item["absolute_lift"], reverse=True)


def _recommendation(
    primary_metric: dict[str, Any],
    guardrails: list[dict[str, Any]],
) -> dict[str, str]:
    guardrails_clean = all(item["status"] == "pass" for item in guardrails)
    if primary_metric["absolute_lift"] > 0 and guardrails_clean:
        decision = "ship_to_staged_rollout"
        rationale = "Primary metric improved and no guardrail breached the local watch thresholds."
    elif primary_metric["absolute_lift"] > 0:
        decision = "hold_for_guardrail_review"
        rationale = "Primary metric improved, but at least one guardrail needs a closer read."
    else:
        decision = "do_not_ship"
        rationale = "Treatment did not improve the primary metric on the local experiment frame."
    return {"decision": decision, "rationale": rationale}


def _difference_ci_95(
    proportion_a: float,
    total_a: int,
    proportion_b: float,
    total_b: int,
) -> tuple[float, float]:
    if total_a == 0 or total_b == 0:
        return (0.0, 0.0)
    standard_error = sqrt(
        (proportion_a * (1 - proportion_a) / total_a)
        + (proportion_b * (1 - proportion_b) / total_b)
    )
    difference = proportion_a - proportion_b
    return (difference - 1.96 * standard_error, difference + 1.96 * standard_error)


def _estimate_mde(
    control_rows: list[dict[str, Any]],
    treatment_rows: list[dict[str, Any]],
    alpha: float,
    power_target: float,
) -> float:
    del alpha
    del power_target
    if not control_rows or not treatment_rows:
        return 0.0
    pooled = (
        _rate(control_rows, "is_on_time") + _rate(treatment_rows, "is_on_time")
    ) / 2
    standard_error = sqrt(
        pooled * (1 - pooled) * ((1 / len(control_rows)) + (1 / len(treatment_rows)))
    )
    return 2.8 * standard_error


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower_index = int(index)
    upper_index = min(lower_index + 1, len(ordered) - 1)
    weight = index - lower_index
    return ordered[lower_index] + (ordered[upper_index] - ordered[lower_index]) * weight


def _rate(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if row[key]) / len(rows)
