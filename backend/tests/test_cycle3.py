from pathlib import Path

from app.cycle1.fixtures import BTS_FIXTURE
from app.cycle2.build import default_repo_root
from app.cycle3.cli import run_full, run_report


def test_cycle3_full_run_creates_report(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_root = tmp_path / "artifacts"

    result = run_full(
        repo_root=default_repo_root(),
        duckdb_path=duckdb_path,
        artifact_root=artifact_root,
    )

    assert result["cycle2"]["validate"]["failed_checks"] == []
    assert Path(result["report"]["json_report"]).exists()
    assert Path(result["report"]["markdown_report"]).exists()


def test_cycle3_report_contains_expected_fixture_segments(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_root = tmp_path / "artifacts"

    run_full(
        repo_root=default_repo_root(),
        duckdb_path=duckdb_path,
        artifact_root=artifact_root,
    )
    report = run_report(duckdb_path, artifact_root / "report_only")

    daily_points = report["trend_summary"]["daily_points"]
    expected_dates = sorted({str(row["flight_date"]) for row in BTS_FIXTURE})
    assert len(daily_points) == len(expected_dates)
    assert daily_points[0]["flight_date"] == expected_dates[0]
    assert daily_points[-1]["flight_date"] == expected_dates[-1]
