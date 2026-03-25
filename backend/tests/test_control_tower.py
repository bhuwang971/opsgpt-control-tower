from pathlib import Path

from fastapi.testclient import TestClient

from app import control_tower
from app.main import app

client = TestClient(app)


def test_control_tower_overview_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "control_tower.duckdb",
    )
    monkeypatch.setattr(
        control_tower,
        "runtime_artifact_root",
        lambda: tmp_path / "artifacts",
    )

    response = client.get("/api/control-tower/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["kpis"]
    assert payload["daily_trend"]
    assert payload["carrier_drilldown"]
    assert payload["forecast"]["projected_on_time_rate"]


def test_control_tower_export_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "control_tower.duckdb",
    )
    monkeypatch.setattr(
        control_tower,
        "runtime_artifact_root",
        lambda: tmp_path / "artifacts",
    )

    response = client.get("/api/control-tower/export/daily_kpis")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "flight_date" in response.text
