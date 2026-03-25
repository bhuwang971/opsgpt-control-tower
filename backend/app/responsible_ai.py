from __future__ import annotations

from pathlib import Path
from typing import Any

from app import control_tower
from app.cycle4.data import build_benchmark_dataset, time_split_rows
from app.cycle4.models import (
    predict_mean_regressor,
    predict_segment_classifier,
    predict_segment_regressor,
    train_mean_regressor,
    train_segment_classifier,
    train_segment_regressor,
)


def run_responsible_ai_review(duckdb_path: Path | None = None) -> dict[str, Any]:
    control_tower.ensure_runtime_assets()
    dataset_path = duckdb_path or control_tower.default_duckdb_path()
    rows = build_benchmark_dataset(dataset_path)
    train_rows, test_rows = time_split_rows(rows)

    classifier = train_segment_classifier(train_rows)
    regressor = train_segment_regressor(train_rows)
    baseline_regressor = train_mean_regressor(train_rows)
    class_predictions = predict_segment_classifier(classifier, test_rows)
    regression_predictions = predict_segment_regressor(regressor, test_rows)
    baseline_predictions = predict_mean_regressor(baseline_regressor, test_rows)

    fairness_slices = _carrier_slices(
        test_rows=test_rows,
        class_predictions=class_predictions.probabilities,
        regression_predictions=regression_predictions.predictions,
        baseline_predictions=baseline_predictions.predictions,
    )
    return {
        "dataset_datasheet": {
            "sources": ["BTS flights", "weather observations", "Comtrade trade flows"],
            "record_count": len(rows),
            "train_count": len(train_rows),
            "test_count": len(test_rows),
            "time_split": "strict time-based holdout",
            "intended_use": "local-first operations analytics, forecasting, and retrieval demos",
            "limitations": [
                "Fixture-backed base data still limits real-world representativeness.",
                "Carrier slices are operational segments, not protected-class fairness groups.",
            ],
        },
        "fairness_slices": fairness_slices,
        "explainability_notes": [
            "Classification baseline is segment + delay + weather based and remains interpretable.",
            "Regression baseline is segment mean plus transparent delay/weather adjustments.",
            (
                "Forecasting remains baseline-only and should be explained as"
                " planning guidance, not shipment authority."
            ),
        ],
        "privacy_governance_checklist": [
            {"control": "model_cards", "status": "implemented"},
            {"control": "dataset_datasheet", "status": "implemented"},
            {"control": "time_split_leakage_guard", "status": "implemented"},
            {"control": "sql_audit_logging", "status": "implemented"},
            {"control": "fairness_slice_review", "status": "implemented"},
            {"control": "human_review_gate", "status": "partial"},
            {"control": "privacy_review", "status": "partial"},
            {"control": "incident_response_runbook", "status": "planned"},
            {"control": "nist_ai_rmf_mapping", "status": "implemented"},
        ],
        "nist_alignment": {
            "govern": "Model cards, datasheets, audit trails, and review checklist included.",
            "map": (
                "Risks documented for leakage, hallucination, retrieval"
                " grounding, and rollout decisions."
            ),
            "measure": (
                "Cycle 4, Cycle 6, Cycle 9, and Cycle 10 metrics provide"
                " measurable checks."
            ),
            "manage": (
                "Guardrails, refusal behavior, SQL controls, and staged"
                " rollout logic are present."
            ),
        },
    }


def _carrier_slices(
    *,
    test_rows,
    class_predictions: list[float],
    regression_predictions: list[float],
    baseline_predictions: list[float],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for row, class_prob, reg_pred, base_pred in zip(
        test_rows,
        class_predictions,
        regression_predictions,
        baseline_predictions,
    ):
        bucket = grouped.setdefault(
            row.carrier_code,
            {
                "count": 0,
                "actual_positive": 0,
                "pred_positive": 0,
                "reg_error_total": 0.0,
                "baseline_reg_error_total": 0.0,
            },
        )
        bucket["count"] += 1
        bucket["actual_positive"] += int(row.severe_delay_label)
        bucket["pred_positive"] += int(class_prob >= 0.5)
        bucket["reg_error_total"] += abs(row.arr_delay_minutes - reg_pred)
        bucket["baseline_reg_error_total"] += abs(row.arr_delay_minutes - base_pred)

    slices = []
    for carrier, metrics in grouped.items():
        count = metrics["count"]
        slices.append(
            {
                "carrier_code": carrier,
                "count": count,
                "actual_positive_rate": metrics["actual_positive"] / count,
                "predicted_positive_rate": metrics["pred_positive"] / count,
                "mae": metrics["reg_error_total"] / count,
                "baseline_mae": metrics["baseline_reg_error_total"] / count,
                "mae_delta_vs_baseline": (
                    metrics["baseline_reg_error_total"] - metrics["reg_error_total"]
                )
                / count,
            }
        )
    return sorted(slices, key=lambda item: item["carrier_code"])
