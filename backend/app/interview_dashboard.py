from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app import control_tower
from app.cycle6.eval import run_rag_evaluation
from app.cycle9.analysis import analyze_experiment
from app.cycle10.ope import analyze_policies
from app.peft_sandbox import peft_sandbox_summary
from app.responsible_ai import run_responsible_ai_review


def interview_dashboard(duckdb_path: Path | None = None) -> dict[str, Any]:
    runtime = control_tower.ensure_runtime_assets()
    dataset_path = duckdb_path or control_tower.default_duckdb_path()
    rag_eval = run_rag_evaluation()
    experiment = analyze_experiment(dataset_path, "adaptive_turnaround_buffers")
    ope = analyze_policies(dataset_path, "adaptive_turnaround_buffers")
    responsible = run_responsible_ai_review(dataset_path)
    training = runtime["training"]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "ml": {
            "classification": training["classification"]["baseline_segmented"]["metrics"],
            "regression": training["regression"]["baseline_segmented"]["metrics"],
            "forecasting": training["forecasting"]["baseline_moving_average"]["metrics"],
            "model_cards": training["artifacts"]["model_cards_markdown"],
        },
        "rag": {
            "summary": rag_eval["summary"],
            "benchmark_cases": rag_eval["cases"],
        },
        "experimentation": {
            "primary_metric": experiment["primary_metric_result"],
            "recommendation": experiment["recommendation"],
            "ope_champion": ope["champion_policy"],
        },
        "responsible_ai": responsible,
        "testing": {
            "fast_backend_suite": {"command": "cd backend && pytest", "test_count": 6},
            "pipeline_backend_suite": {
                "command": "cd backend && pytest -m pipeline",
                "test_count": 26,
            },
            "frontend_suite": {
                "commands": [
                    "cd frontend && npm run lint",
                    "cd frontend && npm run build",
                ]
            },
        },
        "platform": {
            "observability": ["Prometheus metrics", "Grafana dashboards", "Replay alerts"],
            "workflow_runtime": "LangGraph-inspired deterministic workflow",
            "peft_sandbox": peft_sandbox_summary(),
        },
    }
