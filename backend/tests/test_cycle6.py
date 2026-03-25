from pathlib import Path

from fastapi.testclient import TestClient

from app import control_tower
from app.cycle6.cli import run_eval
from app.main import app

client = TestClient(app)


def _patch_runtime(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        control_tower,
        "default_duckdb_path",
        lambda: tmp_path / "cycle6.duckdb",
    )
    monkeypatch.setattr(control_tower, "runtime_artifact_root", lambda: tmp_path / "artifacts")


def test_cycle6_retrieval_returns_citations(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    response = client.post(
        "/api/assistant/query",
        json={"question": "What does the implementation cadence plan say about Cycle 6?"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "retrieval"
    assert payload["citations"]


def test_cycle6_sql_query_returns_rows_and_audit_id(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    response = client.post(
        "/api/assistant/query",
        json={"question": "Show the latest daily reliability and on-time trend"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "sql"
    assert payload["sql"]["rows"]
    assert payload["sql"]["audit_id"]


def test_cycle6_sql_guard_rejects_unknown_export_table(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    response = client.get("/api/control-tower/export/not_real")

    assert response.status_code == 404


def test_cycle6_eval_pack_writes_reports(tmp_path: Path, monkeypatch) -> None:
    _patch_runtime(tmp_path, monkeypatch)

    result = run_eval(tmp_path / "cycle6_eval")

    assert Path(result["artifacts"]["json_report"]).exists()
    assert Path(result["artifacts"]["markdown_report"]).exists()
    assert result["evaluation"]["summary"]["mode_accuracy"] >= 0.8
    assert result["evaluation"]["summary"]["red_team_pass_rate"] >= 0.75
