from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app import control_tower
from app.cycle1.storage import connect
from app.cycle9.analysis import available_toggles


@dataclass(frozen=True)
class PolicySpec:
    policy_name: str
    description: str
    chooser: Callable[[dict[str, Any]], str]


def analyze_policies(
    duckdb_path: Path,
    toggle_name: str = "adaptive_turnaround_buffers",
) -> dict[str, Any]:
    toggle = available_toggles().get(toggle_name)
    if toggle is None:
        raise KeyError(toggle_name)

    control_tower.ensure_runtime_assets()
    rows = _load_logged_bandit_rows(duckdb_path, float(toggle.delay_reduction_minutes))
    reward_model = _fit_reward_model(rows)
    policy_summaries = [_evaluate_policy(spec, rows, reward_model) for spec in _policies()]
    champion = max(policy_summaries, key=lambda item: item["estimated_reward_dr"])
    return {
        "toggle_name": toggle_name,
        "reward_metric": "on_time_reward",
        "logged_rows": len(rows),
        "policies": policy_summaries,
        "champion_policy": champion,
        "showcase_notes": [
            "Offline policy evaluation is layered on top of the experimentation frame.",
            (
                "DR estimates are preferred for ranking because they combine"
                " model-based and IPS correction."
            ),
            (
                "The current fixture corpus is tiny, so the estimates are"
                " portfolio-quality demonstrations rather than production-ready"
                " decisions."
            ),
        ],
    }


def _load_logged_bandit_rows(
    duckdb_path: Path,
    delay_reduction_minutes: float,
) -> list[dict[str, Any]]:
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

    bandit_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        flight_id, flight_date, carrier_code, arr_delay_minutes, cancelled = row
        control_reward = _reward(float(arr_delay_minutes), bool(cancelled), 0.0)
        treatment_reward = _reward(
            float(arr_delay_minutes),
            bool(cancelled),
            delay_reduction_minutes,
        )
        logged_action = "treatment" if index % 2 == 0 else "control"
        bandit_rows.append(
            {
                "flight_id": flight_id,
                "flight_date": str(flight_date),
                "carrier_code": carrier_code,
                "arr_delay_minutes": float(arr_delay_minutes),
                "cancelled": bool(cancelled),
                "logged_action": logged_action,
                "logged_reward": (
                    treatment_reward if logged_action == "treatment" else control_reward
                ),
                "propensity": 0.5,
                "reward_by_action": {
                    "control": control_reward,
                    "treatment": treatment_reward,
                },
            }
        )
    if not bandit_rows:
        raise ValueError("No logged rows available for Cycle 10 policy analysis")
    return bandit_rows


def _policies() -> list[PolicySpec]:
    return [
        PolicySpec(
            policy_name="always_control",
            description="Keep the baseline operating mode for every eligible flight.",
            chooser=lambda row: "control",
        ),
        PolicySpec(
            policy_name="always_treatment",
            description="Apply the recovery toggle uniformly.",
            chooser=lambda row: "treatment",
        ),
        PolicySpec(
            policy_name="delay_aware_treatment",
            description=(
                "Use treatment for flights with moderate delay burden and fall"
                " back otherwise."
            ),
            chooser=lambda row: "treatment" if row["arr_delay_minutes"] <= 45 else "control",
        ),
    ]


def _fit_reward_model(rows: list[dict[str, Any]]) -> dict[tuple[str, str], float]:
    grouped: dict[tuple[str, str], list[float]] = {}
    for row in rows:
        key = (row["carrier_code"], row["logged_action"])
        grouped.setdefault(key, []).append(float(row["logged_reward"]))

    reward_model: dict[tuple[str, str], float] = {}
    global_means = {
        action: _mean(
            [float(row["logged_reward"]) for row in rows if row["logged_action"] == action]
        )
        for action in ("control", "treatment")
    }
    for carrier in {row["carrier_code"] for row in rows}:
        for action in ("control", "treatment"):
            key = (carrier, action)
            reward_model[key] = (
                _mean(grouped.get(key, [])) if grouped.get(key) else global_means[action]
            )
    return reward_model


def _evaluate_policy(
    spec: PolicySpec,
    rows: list[dict[str, Any]],
    reward_model: dict[tuple[str, str], float],
) -> dict[str, Any]:
    ips_terms: list[float] = []
    dm_terms: list[float] = []
    dr_terms: list[float] = []
    action_matches = 0

    for row in rows:
        chosen_action = spec.chooser(row)
        predicted_target = reward_model[(row["carrier_code"], chosen_action)]
        predicted_logged = reward_model[(row["carrier_code"], row["logged_action"])]
        dm_terms.append(predicted_target)
        if chosen_action == row["logged_action"]:
            action_matches += 1
            ips_correction = float(row["logged_reward"]) / float(row["propensity"])
            ips_terms.append(ips_correction)
            dr_terms.append(
                predicted_target
                + (
                    (float(row["logged_reward"]) - predicted_logged)
                    / float(row["propensity"])
                )
            )
        else:
            ips_terms.append(0.0)
            dr_terms.append(predicted_target)

    return {
        "policy_name": spec.policy_name,
        "description": spec.description,
        "match_rate": action_matches / len(rows),
        "estimated_reward_ips": _mean(ips_terms),
        "estimated_reward_dm": _mean(dm_terms),
        "estimated_reward_dr": _mean(dr_terms),
    }


def _reward(arr_delay_minutes: float, cancelled: bool, delay_reduction_minutes: float) -> float:
    if cancelled:
        return 0.0
    adjusted_delay = max(0.0, arr_delay_minutes - delay_reduction_minutes)
    return 1.0 if adjusted_delay <= 15 else 0.0


def _mean(values: list[float]) -> float:
    return 0.0 if not values else sum(values) / len(values)
