from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.cycle1.storage import connect


@dataclass(frozen=True)
class ModelBuildResult:
    model_name: str
    row_count: int


MODEL_FILES = [
    "warehouse/models/curated/dim_date.sql",
    "warehouse/models/curated/dim_airport.sql",
    "warehouse/models/curated/dim_carrier.sql",
    "warehouse/models/curated/dim_trade_partner.sql",
    "warehouse/models/curated/dim_commodity.sql",
    "warehouse/models/curated/fct_flight_operations.sql",
    "warehouse/models/curated/fct_weather_observations.sql",
    "warehouse/models/curated/fct_trade_monthly.sql",
    "warehouse/models/marts/mart_kpi_daily_operations.sql",
    "warehouse/models/marts/mart_kpi_carrier_performance.sql",
    "warehouse/models/marts/mart_kpi_trade_monthly.sql",
]


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def build_models(*, repo_root: Path, duckdb_path: Path) -> list[ModelBuildResult]:
    conn = connect(duckdb_path)
    results: list[ModelBuildResult] = []
    for relative_path in MODEL_FILES:
        sql_path = repo_root / relative_path
        conn.execute(sql_path.read_text(encoding="utf-8"))
        table_name = _model_table_name(Path(relative_path).stem)
        row_count = int(conn.execute(f"SELECT COUNT(*) FROM analytics.{table_name}").fetchone()[0])
        results.append(ModelBuildResult(model_name=table_name, row_count=row_count))
    conn.close()
    return results


def _model_table_name(stem: str) -> str:
    return stem
