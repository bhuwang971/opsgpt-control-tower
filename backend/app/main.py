import os
from importlib.metadata import version

import httpx
import psycopg
from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from pydantic import BaseModel
from starlette.responses import PlainTextResponse

from app import control_tower
from app.control_tower import control_tower_overview, export_dataset
from app.cycle6.assistant import answer_question
from app.cycle7.workflow import run_decision_workflow
from app.cycle8.replay import get_live_status, replay_events
from app.cycle9.analysis import analyze_experiment, available_toggles
from app.cycle10.ope import analyze_policies

app = FastAPI(title="OpsGPT Control Tower API", version="0.1.0")


class AssistantQuery(BaseModel):
    question: str


class DecisionMemoRequest(BaseModel):
    objective: str | None = None


class ReplayRequest(BaseModel):
    events: list[dict[str, object]] | None = None


class ExperimentRequest(BaseModel):
    toggle_name: str = "adaptive_turnaround_buffers"


class PortfolioRequest(BaseModel):
    toggle_name: str = "adaptive_turnaround_buffers"


def _pkg_version(pkg: str) -> str:
    try:
        return version(pkg)
    except Exception:
        return "unknown"


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "backend",
        "versions": {
            "python": os.sys.version.split()[0],
            "fastapi": _pkg_version("fastapi"),
        },
    }


def _postgres_dsn() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "opsgpt")
    password = os.getenv("POSTGRES_PASSWORD", "opsgpt")
    dbname = os.getenv("POSTGRES_DB", "opsgpt")
    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def _check_postgres() -> bool:
    try:
        with psycopg.connect(_postgres_dsn(), connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:
        return False


def _check_qdrant() -> bool:
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    try:
        r = httpx.get(f"{qdrant_url}/healthz", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


@app.get("/ready")
def ready() -> dict[str, object]:
    postgres_ok = _check_postgres()
    qdrant_ok = _check_qdrant()
    return {
        "status": "ok" if postgres_ok and qdrant_ok else "degraded",
        "checks": {
            "postgres": postgres_ok,
            "qdrant": qdrant_ok,
        },
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/control-tower/overview")
def control_tower_api() -> dict[str, object]:
    return control_tower_overview()


@app.get("/api/control-tower/export/{dataset}")
def control_tower_export(dataset: str) -> PlainTextResponse:
    try:
        csv_payload = export_dataset(dataset)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {dataset}") from exc
    return PlainTextResponse(
        content=csv_payload,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{dataset}.csv"'},
    )


@app.post("/api/assistant/query")
def assistant_query(payload: AssistantQuery) -> dict[str, object]:
    response = answer_question(payload.question)
    return {
        "mode": response.mode,
        "answer": response.answer,
        "citations": response.citations,
        "sql": response.sql,
    }


@app.post("/api/agent/decision-memo")
def decision_memo(payload: DecisionMemoRequest) -> dict[str, object]:
    return run_decision_workflow(payload.objective)


@app.get("/api/stream/status")
def stream_status() -> dict[str, object]:
    return get_live_status()


@app.post("/api/stream/replay")
def stream_replay(payload: ReplayRequest) -> dict[str, object]:
    return replay_events(payload.events)


@app.post("/api/experiments/analyze")
def experiment_analysis(payload: ExperimentRequest) -> dict[str, object]:
    if payload.toggle_name not in available_toggles():
        raise HTTPException(status_code=404, detail=f"Unknown toggle: {payload.toggle_name}")
    return analyze_experiment(control_tower.default_duckdb_path(), payload.toggle_name)


@app.post("/api/portfolio/ope")
def portfolio_ope(payload: PortfolioRequest) -> dict[str, object]:
    if payload.toggle_name not in available_toggles():
        raise HTTPException(status_code=404, detail=f"Unknown toggle: {payload.toggle_name}")
    return analyze_policies(control_tower.default_duckdb_path(), payload.toggle_name)
