from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from math import sqrt
from pathlib import Path

from app.cycle4.data import (
    build_benchmark_dataset,
    build_daily_forecast_series,
    time_split_rows,
)
from app.cycle4.models import (
    forecast_moving_average,
    forecast_naive,
    predict_global_classifier,
    predict_mean_regressor,
    predict_segment_classifier,
    predict_segment_regressor,
    train_global_classifier,
    train_mean_regressor,
    train_segment_classifier,
    train_segment_regressor,
)


@dataclass(frozen=True)
class EvaluationBundle:
    benchmark_row_count: int
    train_row_count: int
    test_row_count: int
    classification: dict[str, object]
    regression: dict[str, object]
    forecasting: dict[str, object]


def run_baselines(duckdb_path: Path) -> EvaluationBundle:
    rows = build_benchmark_dataset(duckdb_path)
    train_rows, test_rows = time_split_rows(rows)

    global_classifier = train_global_classifier(train_rows)
    segment_classifier = train_segment_classifier(train_rows)
    global_classifier_pred = predict_global_classifier(global_classifier, test_rows)
    segment_classifier_pred = predict_segment_classifier(segment_classifier, test_rows)
    y_true_class = [row.severe_delay_label for row in test_rows]

    mean_regressor = train_mean_regressor(train_rows)
    segment_regressor = train_segment_regressor(train_rows)
    mean_regression_pred = predict_mean_regressor(mean_regressor, test_rows)
    segment_regression_pred = predict_segment_regressor(segment_regressor, test_rows)
    y_true_reg = [row.arr_delay_minutes for row in test_rows]

    daily_series = build_daily_forecast_series(rows)
    split_series_index = max(1, int(len(daily_series) * 0.75))
    train_series = daily_series[:split_series_index]
    test_series = daily_series[split_series_index:]
    naive_forecast = forecast_naive(train_series, len(test_series))
    moving_average_forecast = forecast_moving_average(train_series, len(test_series))
    y_true_forecast = [float(item["on_time_rate"]) for item in test_series]

    return EvaluationBundle(
        benchmark_row_count=len(rows),
        train_row_count=len(train_rows),
        test_row_count=len(test_rows),
        classification={
            "target": "severe_delay_label",
            "baseline_constant": {
                "model_type": "global_prevalence",
                "metrics": _classification_metrics(
                    y_true_class, global_classifier_pred.probabilities
                ),
                "artifact": global_classifier,
            },
            "baseline_segmented": {
                "model_type": "carrier_origin_rate_plus_delay",
                "metrics": _classification_metrics(
                    y_true_class, segment_classifier_pred.probabilities
                ),
                "artifact": segment_classifier,
            },
        },
        regression={
            "target": "arr_delay_minutes",
            "baseline_mean": {
                "model_type": "global_mean",
                "metrics": _regression_metrics(y_true_reg, mean_regression_pred.predictions),
                "artifact": mean_regressor,
            },
            "baseline_segmented": {
                "model_type": "segment_mean_plus_delay_weather",
                "metrics": _regression_metrics(y_true_reg, segment_regression_pred.predictions),
                "artifact": segment_regressor,
            },
        },
        forecasting={
            "target": "daily_on_time_rate",
            "baseline_naive": {
                "model_type": "last_value",
                "metrics": _forecast_metrics(y_true_forecast, naive_forecast.predictions),
                "artifact": {"history_points": len(train_series)},
            },
            "baseline_moving_average": {
                "model_type": "moving_average",
                "metrics": _forecast_metrics(y_true_forecast, moving_average_forecast.predictions),
                "artifact": {"history_points": len(train_series)},
            },
        },
    )


def write_evaluation_artifacts(bundle: EvaluationBundle, artifact_dir: Path) -> dict[str, str]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    dashboard_json = artifact_dir / f"cycle4_evaluation_{timestamp}.json"
    dashboard_md = artifact_dir / f"cycle4_evaluation_{timestamp}.md"
    model_cards_json = artifact_dir / f"cycle4_model_cards_{timestamp}.json"
    model_cards_md = artifact_dir / f"cycle4_model_cards_{timestamp}.md"

    dashboard_payload = asdict(bundle)
    dashboard_json.write_text(json.dumps(dashboard_payload, indent=2), encoding="utf-8")
    dashboard_md.write_text(_dashboard_markdown(timestamp, bundle), encoding="utf-8")

    model_cards_payload = _model_cards_payload(bundle)
    model_cards_json.write_text(json.dumps(model_cards_payload, indent=2), encoding="utf-8")
    model_cards_md.write_text(
        _model_cards_markdown(timestamp, model_cards_payload), encoding="utf-8"
    )

    return {
        "evaluation_json": str(dashboard_json),
        "evaluation_markdown": str(dashboard_md),
        "model_cards_json": str(model_cards_json),
        "model_cards_markdown": str(model_cards_md),
    }


def _classification_metrics(y_true: list[int], probabilities: list[float]) -> dict[str, float]:
    predicted = [1 if value >= 0.5 else 0 for value in probabilities]
    accuracy = sum(int(a == b) for a, b in zip(y_true, predicted)) / len(y_true)
    brier = sum((truth - prob) ** 2 for truth, prob in zip(y_true, probabilities)) / len(y_true)
    precision, recall = _precision_recall(y_true, predicted)
    pr_auc = precision * recall
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "pr_auc_proxy": pr_auc,
        "brier_score": brier,
    }


def _regression_metrics(y_true: list[float], predictions: list[float]) -> dict[str, float]:
    mae = sum(abs(actual - pred) for actual, pred in zip(y_true, predictions)) / len(y_true)
    rmse = sqrt(
        sum((actual - pred) ** 2 for actual, pred in zip(y_true, predictions)) / len(y_true)
    )
    return {"mae": mae, "rmse": rmse}


def _forecast_metrics(y_true: list[float], predictions: list[float]) -> dict[str, float]:
    mae = sum(abs(actual - pred) for actual, pred in zip(y_true, predictions)) / len(y_true)
    rmse = sqrt(
        sum((actual - pred) ** 2 for actual, pred in zip(y_true, predictions)) / len(y_true)
    )
    mape = (
        sum(
            abs((actual - pred) / actual)
            for actual, pred in zip(y_true, predictions)
            if actual != 0
        )
        / len(y_true)
        if y_true
        else 0.0
    )
    return {"mae": mae, "rmse": rmse, "mape": mape}


def _precision_recall(y_true: list[int], predicted: list[int]) -> tuple[float, float]:
    tp = sum(1 for truth, pred in zip(y_true, predicted) if truth == 1 and pred == 1)
    fp = sum(1 for truth, pred in zip(y_true, predicted) if truth == 0 and pred == 1)
    fn = sum(1 for truth, pred in zip(y_true, predicted) if truth == 1 and pred == 0)
    precision = 0.0 if tp + fp == 0 else tp / (tp + fp)
    recall = 0.0 if tp + fn == 0 else tp / (tp + fn)
    return precision, recall


def _dashboard_markdown(timestamp: str, bundle: EvaluationBundle) -> str:
    lines = [
        "# Cycle 4 Evaluation Dashboard",
        "",
        f"Generated at: `{timestamp}`",
        "",
        f"- Benchmark rows: {bundle.benchmark_row_count}",
        f"- Train rows: {bundle.train_row_count}",
        f"- Test rows: {bundle.test_row_count}",
        "",
        "## Classification",
        "",
        (
            f"- Constant baseline PR-AUC proxy: "
            f"{bundle.classification['baseline_constant']['metrics']['pr_auc_proxy']}"
        ),
        (
            f"- Segmented baseline PR-AUC proxy: "
            f"{bundle.classification['baseline_segmented']['metrics']['pr_auc_proxy']}"
        ),
        "",
        "## Regression",
        "",
        f"- Mean baseline MAE: {bundle.regression['baseline_mean']['metrics']['mae']}",
        f"- Segmented baseline MAE: {bundle.regression['baseline_segmented']['metrics']['mae']}",
        "",
        "## Forecasting",
        "",
        f"- Naive baseline RMSE: {bundle.forecasting['baseline_naive']['metrics']['rmse']}",
        (
            f"- Moving average baseline RMSE: "
            f"{bundle.forecasting['baseline_moving_average']['metrics']['rmse']}"
        ),
        "",
    ]
    return "\n".join(lines)


def _model_cards_payload(bundle: EvaluationBundle) -> dict[str, object]:
    return {
        "dataset": {
            "benchmark_row_count": bundle.benchmark_row_count,
            "train_row_count": bundle.train_row_count,
            "test_row_count": bundle.test_row_count,
            "split_strategy": "time-based holdout",
            "data_origin": "deterministic benchmark expansion from warehouse fixture facts",
        },
        "models": {
            "classification_constant": bundle.classification["baseline_constant"],
            "classification_segmented": bundle.classification["baseline_segmented"],
            "regression_mean": bundle.regression["baseline_mean"],
            "regression_segmented": bundle.regression["baseline_segmented"],
            "forecast_naive": bundle.forecasting["baseline_naive"],
            "forecast_moving_average": bundle.forecasting["baseline_moving_average"],
        },
        "limitations": [
            (
                "Current training corpus is a deterministic local benchmark derived "
                "from fixture warehouse data."
            ),
            (
                "Metrics validate pipeline behavior and leakage controls more than "
                "real-world predictive quality."
            ),
            (
                "Next cycle should replace benchmark expansion with real historical "
                "datasets and richer features."
            ),
        ],
    }


def _model_cards_markdown(timestamp: str, payload: dict[str, object]) -> str:
    lines = [
        "# Cycle 4 Model Cards",
        "",
        f"Generated at: `{timestamp}`",
        "",
        "## Dataset",
        "",
        f"- Rows: {payload['dataset']['benchmark_row_count']}",
        f"- Train rows: {payload['dataset']['train_row_count']}",
        f"- Test rows: {payload['dataset']['test_row_count']}",
        f"- Split strategy: {payload['dataset']['split_strategy']}",
        "",
        "## Limitations",
        "",
    ]
    for limitation in payload["limitations"]:
        lines.append(f"- {limitation}")
    return "\n".join(lines) + "\n"
