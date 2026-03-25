from pathlib import Path

from app.cycle1.cli import run_eda, run_full, run_ingest, run_quality
from app.cycle1.fixtures import BTS_FIXTURE, COMTRADE_FIXTURE, WEATHER_FIXTURE


def test_cycle1_full_run_creates_artifacts(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_root = tmp_path / "artifacts"

    result = run_full(mode="fixture", duckdb_path=duckdb_path, artifact_root=artifact_root)

    assert result["ingest"]["sources"]
    assert Path(result["quality"]["json_report"]).exists()
    assert Path(result["eda"]["json_report"]).exists()
    assert result["quality"]["failed_checks"] == []


def test_ingest_is_idempotent_for_fixture_data(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_dir = tmp_path / "artifacts" / "raw"

    first = run_ingest(
        source="all", mode="fixture", duckdb_path=duckdb_path, artifact_dir=artifact_dir
    )
    second = run_ingest(
        source="all", mode="fixture", duckdb_path=duckdb_path, artifact_dir=artifact_dir
    )

    first_counts = {item["source"]: item["bronze_rows"] for item in first["sources"]}
    second_counts = {item["source"]: item["bronze_rows"] for item in second["sources"]}
    expected_counts = {
        "bts": len(BTS_FIXTURE),
        "weather": len(WEATHER_FIXTURE),
        "comtrade": len(COMTRADE_FIXTURE),
    }
    assert first_counts == second_counts == expected_counts


def test_quality_and_eda_commands_work_after_ingest(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    run_ingest(source="all", mode="fixture", duckdb_path=duckdb_path, artifact_dir=tmp_path / "raw")

    quality = run_quality(duckdb_path, tmp_path / "quality")
    eda = run_eda(duckdb_path, tmp_path / "eda")

    assert quality["failed_checks"] == []
    assert Path(quality["markdown_report"]).exists()
    assert Path(eda["markdown_report"]).exists()
