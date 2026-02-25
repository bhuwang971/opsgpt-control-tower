import os
from importlib.metadata import version

import httpx
import psycopg
from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

app = FastAPI(title="OpsGPT Control Tower API", version="0.1.0")


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
