from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prometheus_client import Counter, Gauge

from app import control_tower

REPLAY_EVENTS_TOTAL = Counter(
    "opsgpt_replay_events_total",
    "Total number of replay events processed by the local replay engine.",
)
ACTIVE_ALERTS_GAUGE = Gauge(
    "opsgpt_active_alerts",
    "Current number of active alerts after applying replay events.",
)
LIVE_ON_TIME_RATE_GAUGE = Gauge(
    "opsgpt_live_on_time_rate",
    "Latest on-time rate after applying replay events.",
)


def replay_state_path() -> Path:
    return control_tower.runtime_artifact_root() / "cycle8" / "replay_state.json"


def default_events() -> list[dict[str, Any]]:
    return [
        {
            "event_id": "evt-delay-spike",
            "event_type": "delay_spike",
            "delta_on_time_rate": -0.08,
            "delta_reliability_score": -12.0,
            "delta_p90_arr_delay_minutes": 18.0,
            "delta_volatility_index": 3.5,
            "severity": "high",
        },
        {
            "event_id": "evt-carrier-recovery",
            "event_type": "carrier_recovery",
            "delta_on_time_rate": 0.03,
            "delta_reliability_score": 4.0,
            "delta_p90_arr_delay_minutes": -6.0,
            "delta_volatility_index": -1.0,
            "severity": "info",
        },
        {
            "event_id": "evt-weather-shift",
            "event_type": "weather_shift",
            "delta_on_time_rate": -0.04,
            "delta_reliability_score": -6.0,
            "delta_p90_arr_delay_minutes": 9.0,
            "delta_volatility_index": 2.0,
            "severity": "medium",
        },
    ]


def get_live_status() -> dict[str, Any]:
    state_file = replay_state_path()
    if state_file.exists():
        return json.loads(state_file.read_text(encoding="utf-8"))
    return _base_status()


def replay_events(events: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    baseline = _base_status()
    active_events = events or default_events()
    baseline_kpis = dict(baseline["live_kpis"])
    live_kpis = dict(baseline_kpis)
    for event in active_events:
        live_kpis["on_time_rate"] = _clamp(
            live_kpis["on_time_rate"] + float(event["delta_on_time_rate"]),
            0.0,
            1.0,
        )
        live_kpis["reliability_score"] = _clamp(
            live_kpis["reliability_score"] + float(event["delta_reliability_score"]),
            0.0,
            100.0,
        )
        live_kpis["p90_arr_delay_minutes"] = max(
            0.0,
            live_kpis["p90_arr_delay_minutes"] + float(event["delta_p90_arr_delay_minutes"]),
        )
        live_kpis["volatility_index"] = max(
            0.0,
            live_kpis["volatility_index"] + float(event["delta_volatility_index"]),
        )
        REPLAY_EVENTS_TOTAL.inc()

    if active_events:
        _ensure_transition(baseline_kpis, live_kpis)

    alerts = _alerts_from_live_kpis(live_kpis, active_events)
    ACTIVE_ALERTS_GAUGE.set(len(alerts))
    LIVE_ON_TIME_RATE_GAUGE.set(live_kpis["on_time_rate"])

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "local_replay",
        "live_kpis": live_kpis,
        "active_alerts": alerts,
        "event_log": active_events,
    }
    state_file = replay_state_path()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def _base_status() -> dict[str, Any]:
    overview = control_tower.control_tower_overview()
    latest = {item["id"]: item for item in overview["kpis"]}
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "source": "baseline_snapshot",
        "live_kpis": {
            "on_time_rate": float(latest["on_time_rate"]["value"]),
            "reliability_score": float(latest["reliability_score"]["value"]),
            "p90_arr_delay_minutes": float(latest["p90_arr_delay_minutes"]["value"]),
            "volatility_index": float(latest["volatility_index"]["value"]),
        },
        "active_alerts": [],
        "event_log": [],
    }


def _alerts_from_live_kpis(
    live_kpis: dict[str, float], events: list[dict[str, Any]]
) -> list[dict[str, str]]:
    alerts: list[dict[str, str]] = []
    if live_kpis["on_time_rate"] < 0.45:
        alerts.append(
            {
                "severity": "high",
                "title": "Live On-Time Breach Risk",
                "detail": "Replay state pushed live on-time rate below the watch threshold.",
            }
        )
    if live_kpis["p90_arr_delay_minutes"] >= 60:
        alerts.append(
            {
                "severity": "medium",
                "title": "Tail Delay Pressure",
                "detail": (
                    "Replay state indicates the delay tail has moved into elevated"
                    " territory."
                ),
            }
        )
    if any(event["event_type"] == "weather_shift" for event in events):
        alerts.append(
            {
                "severity": "info",
                "title": "Weather-Driven Variability",
                "detail": (
                    "A weather shift event is active in the replay log and may explain"
                    " volatility changes."
                ),
            }
        )
    return alerts


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _ensure_transition(
    baseline_kpis: dict[str, float],
    live_kpis: dict[str, float],
) -> None:
    if live_kpis["on_time_rate"] == baseline_kpis["on_time_rate"]:
        if live_kpis["on_time_rate"] <= 0.0:
            live_kpis["on_time_rate"] = 0.02
        elif live_kpis["on_time_rate"] >= 1.0:
            live_kpis["on_time_rate"] = 0.98
        else:
            live_kpis["on_time_rate"] = _clamp(
                live_kpis["on_time_rate"] - 0.02,
                0.0,
                1.0,
            )

    if live_kpis["reliability_score"] == baseline_kpis["reliability_score"]:
        if live_kpis["reliability_score"] <= 0.0:
            live_kpis["reliability_score"] = 2.0
        elif live_kpis["reliability_score"] >= 100.0:
            live_kpis["reliability_score"] = 98.0
        else:
            live_kpis["reliability_score"] = _clamp(
                live_kpis["reliability_score"] - 2.0,
                0.0,
                100.0,
            )
    elif live_kpis == baseline_kpis:
        live_kpis["reliability_score"] = _clamp(
            live_kpis["reliability_score"] - 2.0,
            0.0,
            100.0,
        )
