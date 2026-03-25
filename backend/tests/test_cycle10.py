from pathlib import Path

from fastapi.testclient import TestClient

from app import control_tower
from app.cycle10.cli import run_analysis
from app.main import app

client = TestClient(app)


def _patch_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "cycle10.duckdb",
    )
    monkeypatch.setattr(control_tower, "runtime_artifact_root", lambda: tmp_path / "artifacts")


def test_cycle10_api_returns_policy_rankings(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    response = client.post("/api/portfolio/ope", json={})

    assert response.status_code == 200
    payload = response.json()
    assert payload["policies"]
    assert payload["champion_policy"]["policy_name"]
    assert payload["showcase_notes"]


def test_cycle10_cli_writes_portfolio_artifacts(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    result = run_analysis(
        repo_root=Path(__file__).resolve().parents[2],
        duckdb_path=control_tower.default_duckdb_path(),
        artifact_dir=tmp_path / "cycle10_artifacts",
        toggle_name="adaptive_turnaround_buffers",
    )

    assert Path(result["artifacts"]["json_report"]).exists()
    assert Path(result["artifacts"]["markdown_report"]).exists()
    assert result["ope"]["champion_policy"]["estimated_reward_dr"] >= 0.0
