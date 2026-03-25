from pathlib import Path

from app.cycle1.cli import run_ingest
from app.cycle2.build import default_repo_root
from app.cycle2.cli import run_build, run_full, run_validate


def test_cycle2_build_materializes_expected_models(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    run_ingest(source="all", mode="fixture", duckdb_path=duckdb_path, artifact_dir=tmp_path / "raw")

    result = run_build(repo_root=default_repo_root(), duckdb_path=duckdb_path)

    model_names = {item["model_name"] for item in result["models"]}
    assert "dim_airport" in model_names
    assert "fct_flight_operations" in model_names
    assert "mart_kpi_daily_operations" in model_names


def test_cycle2_validation_passes_for_fixture_slices(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    run_ingest(source="all", mode="fixture", duckdb_path=duckdb_path, artifact_dir=tmp_path / "raw")
    run_build(repo_root=default_repo_root(), duckdb_path=duckdb_path)

    result = run_validate(
        duckdb_path=duckdb_path,
        artifact_dir=tmp_path / "validation",
        expect_fixture_slices=True,
    )

    assert result["failed_checks"] == []


def test_cycle2_full_run_builds_and_validates(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_root = tmp_path / "artifacts"

    result = run_full(
        repo_root=default_repo_root(), duckdb_path=duckdb_path, artifact_root=artifact_root
    )

    assert result["validate"]["failed_checks"] == []
