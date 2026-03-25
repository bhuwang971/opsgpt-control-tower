from pathlib import Path

from fastapi.testclient import TestClient

from app import control_tower
from app.cycle9.cli import run_analysis
from app.main import app

client = TestClient(app)


def _patch_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "cycle9.duckdb",
    )
    monkeypatch.setattr(control_tower, "runtime_artifact_root", lambda: tmp_path / "artifacts")


def test_cycle9_api_returns_experiment_summary(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    response = client.post("/api/experiments/analyze", json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["primary_metric_result"]["metric"] == "on_time_rate"
    assert payload["guardrails"]
    assert payload["sequential_checks"]
    assert payload["recommendation"]["decision"]


def test_cycle9_cli_writes_artifacts(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    result = run_analysis(
        duckdb_path=control_tower.default_duckdb_path(),
        artifact_dir=tmp_path / "cycle9_artifacts",
        toggle_name="adaptive_turnaround_buffers",
    )

    assert Path(result["artifacts"]["json_report"]).exists()
    assert Path(result["artifacts"]["markdown_report"]).exists()
    assert result["analysis"]["variant_counts"]["control"] > 0
    assert result["analysis"]["variant_counts"]["treatment"] > 0
