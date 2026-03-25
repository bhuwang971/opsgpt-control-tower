from pathlib import Path

from fastapi.testclient import TestClient

from app import control_tower
from app.cycle8.cli import run_cycle8
from app.main import app

client = TestClient(app)


def _patch_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "cycle8.duckdb",
    )
    monkeypatch.setattr(control_tower, "runtime_artifact_root", lambda: tmp_path / "artifacts")


def test_cycle8_replay_updates_live_status(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    baseline = client.get("/api/stream/status").json()
    replayed = client.post("/api/stream/replay", json={}).json()

    assert replayed["live_kpis"]["on_time_rate"] != baseline["live_kpis"]["on_time_rate"]
    assert replayed["active_alerts"]


def test_cycle8_cli_writes_observability_assets(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    result = run_cycle8(tmp_path / "cycle8_artifacts")

    assert Path(result["observability"]["grafana_dashboards_yml"]).exists()
    assert Path(result["observability"]["grafana_dashboard_json"]).exists()
    assert Path(result["observability"]["prometheus_alert_rules"]).exists()
    assert Path(result["status_json"]).exists()
