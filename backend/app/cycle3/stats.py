from __future__ import annotations

from dataclasses import dataclass
from math import erf, sqrt


@dataclass(frozen=True)
class ProportionTestResult:
    proportion_a: float
    proportion_b: float
    difference: float
    z_score: float
    p_value: float


@dataclass(frozen=True)
class MeanEffectResult:
    mean_a: float
    mean_b: float
    mean_difference: float
    cohen_d: float


@dataclass(frozen=True)
class PoissonSummary:
    count: int
    exposure: float
    rate: float
    lower_95: float
    upper_95: float


@dataclass(frozen=True)
class NegativeBinomialSummary:
    mean_count: float
    variance_count: float
    dispersion: float | None
    overdispersed: bool


def difference_in_proportions(
    *,
    success_a: int,
    total_a: int,
    success_b: int,
    total_b: int,
) -> ProportionTestResult:
    proportion_a = 0.0 if total_a == 0 else success_a / total_a
    proportion_b = 0.0 if total_b == 0 else success_b / total_b
    pooled = 0.0 if total_a + total_b == 0 else (success_a + success_b) / (total_a + total_b)
    exposure_term = ((1 / total_a) if total_a else 0.0) + ((1 / total_b) if total_b else 0.0)
    standard_error = sqrt(pooled * (1 - pooled) * exposure_term)
    if standard_error == 0:
        z_score = 0.0
        p_value = 1.0
    else:
        z_score = (proportion_a - proportion_b) / standard_error
        p_value = 2 * (1 - _normal_cdf(abs(z_score)))
    return ProportionTestResult(
        proportion_a=proportion_a,
        proportion_b=proportion_b,
        difference=proportion_a - proportion_b,
        z_score=z_score,
        p_value=p_value,
    )


def cohen_d(sample_a: list[float], sample_b: list[float]) -> MeanEffectResult:
    mean_a = _mean(sample_a)
    mean_b = _mean(sample_b)
    variance_a = _sample_variance(sample_a)
    variance_b = _sample_variance(sample_b)
    pooled_denominator = len(sample_a) + len(sample_b) - 2
    pooled_variance = (
        0.0
        if pooled_denominator <= 0
        else (((len(sample_a) - 1) * variance_a) + ((len(sample_b) - 1) * variance_b))
        / pooled_denominator
    )
    pooled_std = sqrt(pooled_variance) if pooled_variance > 0 else 0.0
    effect = 0.0 if pooled_std == 0 else (mean_a - mean_b) / pooled_std
    return MeanEffectResult(
        mean_a=mean_a,
        mean_b=mean_b,
        mean_difference=mean_a - mean_b,
        cohen_d=effect,
    )


def poisson_rate_summary(*, count: int, exposure: float) -> PoissonSummary:
    rate = 0.0 if exposure <= 0 else count / exposure
    if exposure <= 0:
        return PoissonSummary(count=count, exposure=exposure, rate=0.0, lower_95=0.0, upper_95=0.0)
    standard_error = sqrt(count) / exposure if count > 0 else 1.96 / exposure
    return PoissonSummary(
        count=count,
        exposure=exposure,
        rate=rate,
        lower_95=max(0.0, rate - 1.96 * standard_error),
        upper_95=rate + 1.96 * standard_error,
    )


def negative_binomial_summary(counts: list[int]) -> NegativeBinomialSummary:
    mean_count = _mean([float(value) for value in counts])
    variance_count = _sample_variance([float(value) for value in counts])
    if mean_count <= 0 or variance_count <= mean_count:
        return NegativeBinomialSummary(
            mean_count=mean_count,
            variance_count=variance_count,
            dispersion=None,
            overdispersed=False,
        )
    dispersion = (mean_count**2) / (variance_count - mean_count)
    return NegativeBinomialSummary(
        mean_count=mean_count,
        variance_count=variance_count,
        dispersion=dispersion,
        overdispersed=True,
    )


def rolling_z_scores(values: list[float], window_size: int) -> list[float | None]:
    scores: list[float | None] = []
    for index, value in enumerate(values):
        if index < window_size:
            scores.append(None)
            continue
        window = values[index - window_size : index]
        std = sqrt(_sample_variance(window))
        if std == 0:
            scores.append(0.0)
        else:
            scores.append((value - _mean(window)) / std)
    return scores


def simple_linear_slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x_values = list(range(len(values)))
    mean_x = _mean([float(value) for value in x_values])
    mean_y = _mean(values)
    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, values))
    denominator = sum((x - mean_x) ** 2 for x in x_values)
    return 0.0 if denominator == 0 else numerator / denominator


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + erf(value / sqrt(2)))


def _mean(values: list[float]) -> float:
    return 0.0 if not values else sum(values) / len(values)


def _sample_variance(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean_value = _mean(values)
    return sum((value - mean_value) ** 2 for value in values) / (len(values) - 1)
