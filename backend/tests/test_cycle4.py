from pathlib import Path

from app.cycle2.build import default_repo_root
from app.cycle4.cli import run_full, run_train


def test_cycle4_full_run_creates_model_artifacts(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_root = tmp_path / "artifacts"

    result = run_full(
        repo_root=default_repo_root(),
        duckdb_path=duckdb_path,
        artifact_root=artifact_root,
    )

    assert result["cycle3"]["cycle2"]["validate"]["failed_checks"] == []
    assert result["training"]["benchmark_row_count"] > 100
    assert Path(result["training"]["artifacts"]["evaluation_json"]).exists()
    assert Path(result["training"]["artifacts"]["model_cards_json"]).exists()


def test_cycle4_segmented_baselines_beat_constant_or_mean(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_root = tmp_path / "artifacts"

    result = run_full(
        repo_root=default_repo_root(),
        duckdb_path=duckdb_path,
        artifact_root=artifact_root,
    )

    classification = result["training"]["classification"]
    regression = result["training"]["regression"]
    forecasting = result["training"]["forecasting"]

    assert (
        classification["baseline_segmented"]["metrics"]["pr_auc_proxy"]
        >= classification["baseline_constant"]["metrics"]["pr_auc_proxy"]
    )
    assert (
        regression["baseline_segmented"]["metrics"]["mae"]
        <= regression["baseline_mean"]["metrics"]["mae"]
    )
    assert forecasting["baseline_naive"]["metrics"]["rmse"] >= 0.0
    assert forecasting["baseline_moving_average"]["metrics"]["rmse"] >= 0.0


def test_cycle4_train_reuses_existing_warehouse(tmp_path: Path) -> None:
    duckdb_path = tmp_path / "warehouse" / "opsgpt.duckdb"
    artifact_root = tmp_path / "artifacts"

    initial = run_full(
        repo_root=default_repo_root(),
        duckdb_path=duckdb_path,
        artifact_root=artifact_root,
    )
    second = run_train(duckdb_path, artifact_root / "retrain")

    assert second["benchmark_row_count"] == initial["training"]["benchmark_row_count"]
    assert second["test_row_count"] > 0
