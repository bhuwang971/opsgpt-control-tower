from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from app.cycle4.data import FlightExample


@dataclass(frozen=True)
class ClassificationPrediction:
    probabilities: list[float]
    labels: list[int]


@dataclass(frozen=True)
class RegressionPrediction:
    predictions: list[float]


@dataclass(frozen=True)
class ForecastPrediction:
    predictions: list[float]


def train_global_classifier(train_rows: list[FlightExample]) -> dict[str, float]:
    prevalence = (
        0.0
        if not train_rows
        else sum(row.severe_delay_label for row in train_rows) / len(train_rows)
    )
    return {"global_prevalence": prevalence}


def predict_global_classifier(
    model: dict[str, float], rows: list[FlightExample]
) -> ClassificationPrediction:
    probability = float(model["global_prevalence"])
    probabilities = [probability for _ in rows]
    return ClassificationPrediction(
        probabilities=probabilities, labels=[1 if probability >= 0.5 else 0 for _ in rows]
    )


def train_segment_classifier(train_rows: list[FlightExample]) -> dict[str, object]:
    by_segment: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in train_rows:
        by_segment[(row.carrier_code, row.origin_airport_code)].append(row.severe_delay_label)
    global_prevalence = (
        0.0
        if not train_rows
        else sum(row.severe_delay_label for row in train_rows) / len(train_rows)
    )
    segment_rates = {
        f"{carrier}|{origin}": sum(values) / len(values)
        for (carrier, origin), values in by_segment.items()
    }
    return {"global_prevalence": global_prevalence, "segment_rates": segment_rates}


def predict_segment_classifier(
    model: dict[str, object], rows: list[FlightExample]
) -> ClassificationPrediction:
    segment_rates = dict(model["segment_rates"])
    fallback = float(model["global_prevalence"])
    probabilities = []
    labels = []
    for row in rows:
        key = f"{row.carrier_code}|{row.origin_airport_code}"
        feature_rate = float(segment_rates.get(key, fallback))
        probability = max(
            0.0,
            min(
                1.0, feature_rate + (row.dep_delay_minutes / 240.0) + (row.weather_severity / 120.0)
            ),
        )
        probabilities.append(probability)
        labels.append(1 if probability >= 0.5 else 0)
    return ClassificationPrediction(probabilities=probabilities, labels=labels)


def train_mean_regressor(train_rows: list[FlightExample]) -> dict[str, float]:
    mean_value = (
        0.0
        if not train_rows
        else sum(row.arr_delay_minutes for row in train_rows) / len(train_rows)
    )
    return {"global_mean": mean_value}


def predict_mean_regressor(
    model: dict[str, float], rows: list[FlightExample]
) -> RegressionPrediction:
    prediction = float(model["global_mean"])
    return RegressionPrediction(predictions=[prediction for _ in rows])


def train_segment_regressor(train_rows: list[FlightExample]) -> dict[str, object]:
    by_segment: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in train_rows:
        by_segment[(row.carrier_code, row.origin_airport_code)].append(row.arr_delay_minutes)
    global_mean = (
        0.0
        if not train_rows
        else sum(row.arr_delay_minutes for row in train_rows) / len(train_rows)
    )
    segment_means = {
        f"{carrier}|{origin}": sum(values) / len(values)
        for (carrier, origin), values in by_segment.items()
    }
    return {"global_mean": global_mean, "segment_means": segment_means}


def predict_segment_regressor(
    model: dict[str, object], rows: list[FlightExample]
) -> RegressionPrediction:
    segment_means = dict(model["segment_means"])
    fallback = float(model["global_mean"])
    predictions = []
    for row in rows:
        key = f"{row.carrier_code}|{row.origin_airport_code}"
        segment_mean = float(segment_means.get(key, fallback))
        predictions.append(
            segment_mean + (row.dep_delay_minutes * 0.35) + (row.weather_severity * 0.25)
        )
    return RegressionPrediction(predictions=predictions)


def forecast_naive(train_series: list[dict[str, float | str]], horizon: int) -> ForecastPrediction:
    last_value = 0.0 if not train_series else float(train_series[-1]["on_time_rate"])
    return ForecastPrediction(predictions=[last_value for _ in range(horizon)])


def forecast_moving_average(
    train_series: list[dict[str, float | str]], horizon: int, window_size: int = 7
) -> ForecastPrediction:
    window = train_series[-window_size:] if len(train_series) >= window_size else train_series
    average = (
        0.0 if not window else sum(float(item["on_time_rate"]) for item in window) / len(window)
    )
    return ForecastPrediction(predictions=[average for _ in range(horizon)])
