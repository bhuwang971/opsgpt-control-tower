from app.cycle1.fixtures import BTS_FIXTURE, COMTRADE_FIXTURE, WEATHER_FIXTURE
from app.cycle3.stats import difference_in_proportions, rolling_z_scores
from app.cycle9.analysis import available_toggles


def test_generated_fixtures_are_large_and_unique() -> None:
    flight_ids = {str(row["flight_id"]) for row in BTS_FIXTURE}
    weather_keys = {
        (str(row["station_id"]), str(row["observed_at"]))
        for row in WEATHER_FIXTURE
    }
    trade_ids = {str(row["trade_id"]) for row in COMTRADE_FIXTURE}

    assert len(BTS_FIXTURE) >= 100
    assert len(flight_ids) == len(BTS_FIXTURE)
    assert len(weather_keys) == len(WEATHER_FIXTURE)
    assert len(COMTRADE_FIXTURE) >= 20
    assert len(trade_ids) == len(COMTRADE_FIXTURE)


def test_stats_utility_shapes_are_stable() -> None:
    result = difference_in_proportions(
        success_a=30,
        total_a=100,
        success_b=20,
        total_b=100,
    )

    scores = rolling_z_scores([1.0, 2.0, 3.0, 4.0, 5.0], window_size=2)

    assert result.difference > 0
    assert 0.0 <= result.p_value <= 1.0
    assert scores[:2] == [None, None]
    assert scores[-1] is not None


def test_experiment_toggle_registry_exposes_default_toggle() -> None:
    toggles = available_toggles()

    assert "adaptive_turnaround_buffers" in toggles
    assert toggles["adaptive_turnaround_buffers"].delay_reduction_minutes > 0
