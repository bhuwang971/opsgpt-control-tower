from pathlib import Path

from fastapi.testclient import TestClient

from app import control_tower
from app.cycle7.cli import run_cycle7
from app.main import app

client = TestClient(app)


def _patch_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "cycle7.duckdb",
    )
    monkeypatch.setattr(control_tower, "runtime_artifact_root", lambda: tmp_path / "artifacts")


def test_cycle7_api_returns_trace_and_rubric(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    response = client.post(
        "/api/agent/decision-memo",
        json={"objective": "Stabilize reliability before the next reporting cycle"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace"]
    assert payload["evaluation"]["score"] >= 4
    assert "## Recommendations" in payload["memo_markdown"]


def test_cycle7_cli_writes_artifacts(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    result = run_cycle7(
        objective="Explain the current disruption pattern and produce an action memo",
        artifact_dir=tmp_path / "cycle7_artifacts",
    )

    assert Path(result["artifacts"]["json_report"]).exists()
    assert Path(result["artifacts"]["markdown_report"]).exists()
    assert result["evaluation"]["score"] >= 4


def test_cycle7_trace_is_stable(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    response = client.post("/api/agent/decision-memo", json={})
    payload = response.json()

    assert [step["step"] for step in payload["trace"]] == [
        "diagnose",
        "gather_evidence",
        "recommend",
        "memo",
    ]
    assert all(step["status"] == "completed" for step in payload["trace"])
