from pathlib import Path

from fastapi.testclient import TestClient

from app import control_tower
from app.main import app

client = TestClient(app)


def test_interview_dashboard_endpoint(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "dashboard.duckdb",
    )
    monkeypatch.setattr(control_tower, "runtime_artifact_root", lambda: tmp_path / "artifacts")

    response = client.get("/api/interview/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ml"]["classification"]
    assert payload["rag"]["summary"]
    assert payload["responsible_ai"]["dataset_datasheet"]
    assert payload["platform"]["workflow_runtime"] == "LangGraph-inspired deterministic workflow"
