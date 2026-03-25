# OpsGPT Control Tower

Local-first operations intelligence platform that combines data ingestion, warehouse modeling, statistical analysis, ML baselines, guarded RAG/NL-to-SQL, agent workflows, observability, experimentation, and offline policy evaluation.

The project is designed to be runnable on a laptop while still demonstrating production-style patterns that come up in data engineering, ML engineering, analytics engineering, and applied AI interviews.

## What This Project Covers

- Data ingestion from multiple sources with fixture and live modes
- Raw, bronze, curated, and mart-style DuckDB analytics layers
- Data quality checks and EDA artifacts
- Statistical trend and probability summaries
- Time-based ML evaluation for classification, regression, and forecasting
- Control-tower style frontend with KPI cards, alerts, trends, and drilldowns
- Grounded retrieval with citations and guarded NL-to-SQL
- Evidence-backed memo workflow for operational recommendations
- Replay-driven observability with Prometheus and Grafana
- Experiment analysis with guardrails and sequential checks
- Offline policy evaluation with IPS, DM, and DR estimates
- Responsible AI review artifacts and interview-facing dashboard summaries

## Tech Stack

### Frontend

- React
- Vite
- TypeScript
- CSS/Tailwind-era utility stack

### Backend

- Python 3.11+
- FastAPI
- Pydantic
- DuckDB
- Prometheus client

### Data and Platform

- DuckDB for local OLAP analytics
- Postgres as the OLTP boundary
- Qdrant as the retrieval boundary
- Redpanda for replay and streaming posture
- Prometheus and Grafana for observability
- Docker Compose for local orchestration

### Tooling

- Pytest
- Ruff
- GitHub Actions

## Repository Layout

```text
backend/        FastAPI app, cycle modules, tests, runtime artifacts
frontend/       React app
infra/          docker-compose, Prometheus, Grafana config
warehouse/      curated and mart SQL models, glossary
docs/           architecture, runbook, implementation plan, demo script
pipelines/      pipeline notes and entry-point documentation
```

## Setup

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js and npm

### Environment

1. Copy `.env.example` to `.env`.
2. Review the defaults:

```env
COMPOSE_PROJECT_NAME=opsgpt_control_tower
POSTGRES_USER=opsgpt
POSTGRES_PASSWORD=opsgpt
POSTGRES_DB=opsgpt
POSTGRES_PORT=5432
BACKEND_PORT=8000
FRONTEND_PORT=5173
GRAFANA_PORT=3000
PROMETHEUS_PORT=9090
QDRANT_PORT=6333
REDPANDA_BROKER_PORT=9092
DUCKDB_PATH=/data/warehouse/opsgpt.duckdb
```

### Full Local Startup

```powershell
make up
```

Open:

- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`
- Backend readiness: `http://localhost:8000/ready`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

### Backend Dev Setup

```powershell
cd backend
pip install -e .[dev]
```

### Frontend Dev Setup

```powershell
cd frontend
npm install
```

## Testing and Verification

### Fast Everyday Backend Checks

```powershell
cd backend
ruff check .
pytest
```

Current fast suite behavior:

- `6` fast tests
- excludes fixture-heavy pipeline tests by default

### Full Backend Pipeline Checks

```powershell
cd backend
pytest -m pipeline
```

Current pipeline suite behavior:

- `25` pipeline tests
- builds fixture-backed warehouse/runtime paths

### Frontend Checks

```powershell
cd frontend
npm run lint
npm run build
```

### CI

GitHub Actions runs:

- backend lint
- backend fast tests
- backend pipeline tests
- frontend lint
- frontend build

## Implemented Cycles

### Cycle 1: Data Ingestion, Quality, and EDA

Implemented in `backend/app/cycle1`.

Built:

- BTS, weather, and Comtrade connectors
- fixture mode and live mode
- raw and bronze DuckDB layers
- idempotent ingestion
- quality report generation
- EDA report generation

Commands:

```powershell
python -m app.cycle1.cli ingest --source all
python -m app.cycle1.cli quality
python -m app.cycle1.cli eda
python -m app.cycle1.cli full-run
```

### Cycle 2: Warehouse Modeling

Implemented in `backend/app/cycle2` and `warehouse/models`.

Built:

- curated dimensions
- curated fact tables
- KPI marts
- warehouse validations
- KPI glossary

Commands:

```powershell
python -m app.cycle2.cli build
python -m app.cycle2.cli validate
python -m app.cycle2.cli full-run
```

### Cycle 3: Statistical Layer

Implemented in `backend/app/cycle3`.

Built:

- difference-in-proportions utilities
- Cohen's d utilities
- rolling z-score summaries
- simple trend slopes
- Poisson and Negative Binomial summaries
- reproducible statistical report generation

Command:

```powershell
python -m app.cycle3.cli full-run
```

### Cycle 4: ML Baselines

Implemented in `backend/app/cycle4`.

Built:

- benchmark dataset builder from warehouse facts
- strict time-based train/test splitting
- classification baseline
- regression baseline
- forecasting baselines
- evaluation dashboard
- model cards

Commands:

```powershell
python -m app.cycle4.cli train
python -m app.cycle4.cli full-run
```

### Cycle 5: Control Tower UI

Built:

- KPI cards
- daily trend board
- carrier drilldown
- alert feed
- forecast section
- export links

API:

- `GET /api/control-tower/overview`
- `GET /api/control-tower/export/{dataset}`

### Cycle 6: Grounded Assistant and Safe SQL

Implemented in `backend/app/cycle6`.

Built:

- local document retrieval
- citation-backed retrieval answers
- guarded NL-to-SQL
- SQL allowlisting and LIMIT enforcement
- SQL audit log
- deterministic RAG evaluation pack

API:

- `POST /api/assistant/query`

Commands:

```powershell
python -m app.cycle6.cli
```

### Cycle 7: Decision Workflow

Implemented in `backend/app/cycle7`.

Built:

- deterministic workflow: diagnose -> gather evidence -> recommend -> memo
- stable trace output
- fallback tracking
- rubric-based memo scoring

API:

- `POST /api/agent/decision-memo`

### Cycle 8: Replay and Observability

Implemented in `backend/app/cycle8`.

Built:

- replay-driven live KPI simulation
- active alert generation
- Prometheus metrics
- Grafana dashboard provisioning
- Prometheus alert-rule provisioning

API:

- `GET /api/stream/status`
- `POST /api/stream/replay`

### Cycle 9: Experimentation

Implemented in `backend/app/cycle9`.

Built:

- A/B style analysis for an operations toggle
- primary metric analysis
- guardrail metric analysis
- sequential checkpoint analysis
- segment breakdowns
- rollout recommendation logic

API:

- `POST /api/experiments/analyze`

### Cycle 10: Portfolio Differentiator

Implemented in `backend/app/cycle10`.

Built:

- offline policy evaluation
- IPS estimates
- Direct Method estimates
- Doubly Robust estimates
- champion policy selection
- demo-ready portfolio report

API:

- `POST /api/portfolio/ope`

### Interview Dashboard

Built as a summary layer for interview/demo use.

API:

- `GET /api/interview/dashboard`

It aggregates:

- ML metrics
- RAG eval metrics
- experimentation and OPE outputs
- responsible AI review outputs
- testing posture
- PEFT sandbox metadata

## Current Fixture-Backed Dataset Size

The fixtures are generated programmatically in `backend/app/cycle1/fixtures.py`.

Current generated sizes:

- `125` BTS flight rows
- `125` weather rows
- `24` Comtrade rows

This is intentionally large enough to make later-cycle metrics more meaningful while still keeping the checked-in showcase assets under GitHub-friendly size limits.

Curated verification outputs now live in `backend/data/warehouse` and `backend/artifacts/` so the interviewer dashboard has reproducible local evidence to point at.

## Current Benchmark Metrics

These metrics come from the latest local fixture-backed verification run under `backend/artifacts/fixture_generator_verify`.

### Cycle 4 ML Metrics

- Benchmark rows: `5250`
- Train rows: `4485`
- Test rows: `765`
- Classification segmented PR-AUC proxy: `1.000`
- Regression segmented MAE: `50.18`
- Forecasting moving-average RMSE: `0.000`

Important note:

- These are fixture-backed benchmark metrics, so they validate pipeline behavior and evaluation design more than real-world predictive quality.

### Cycle 6 RAG Evaluation

- Total cases: `5`
- Mode accuracy: `1.000`
- Retrieval source hit rate: `1.000`
- Citation coverage: `0.667`
- Refusal precision: `1.000`
- Hallucination-rate proxy: `0.000`
- SQL success rate: `1.000`

### Cycle 9 Experiment Metrics

For the `adaptive_turnaround_buffers` toggle:

- Control on-time rate: `0.0484`
- Treatment on-time rate: `0.1587`
- Absolute lift: `0.1103`
- Relative lift: `2.2804`
- p-value: `0.0433`
- Recommendation: `hold_for_guardrail_review`

Guardrails:

- Cancellation rate: `watch`
- P90 arrival delay minutes: `pass`
- Severe delay rate: `pass`

### Cycle 10 OPE Metrics

Policy comparison:

- `always_control`: DR `0.0487`
- `always_treatment`: DR `0.1582`
- `delay_aware_treatment`: DR `0.1668`

Champion policy:

- `delay_aware_treatment`

## Responsible AI and Evaluation Coverage

Implemented:

- model cards
- dataset datasheet summary
- strict time-based leakage guard
- SQL audit logging
- citation-backed retrieval
- hallucination-rate proxy in Cycle 6 eval
- fairness slices by carrier segment
- privacy/governance checklist
- NIST AI RMF-style mapping in the responsible AI review module

Partially implemented:

- human review gate
- privacy review
- incident response process

Not production-complete:

- protected-class fairness analysis
- privacy engineering controls
- adversarial red-team harnesses at scale
- live model monitoring against real production traffic

## PEFT Sandbox Notes

The repo also exposes configuration-first PEFT sandbox metadata for interview discussion:

- LoRA experiment shape
- QLoRA experiment shape

These are intentionally not part of the main runtime path. They are present to support interview conversations around fine-tuning tradeoffs without forcing the product to depend on heavyweight local fine-tuning infrastructure.

## API Surface

### Platform

- `GET /health`
- `GET /ready`
- `GET /metrics`

### Product APIs

- `GET /api/control-tower/overview`
- `GET /api/control-tower/export/{dataset}`
- `POST /api/assistant/query`
- `POST /api/agent/decision-memo`
- `GET /api/stream/status`
- `POST /api/stream/replay`
- `POST /api/experiments/analyze`
- `POST /api/portfolio/ope`
- `GET /api/interview/dashboard`

## Frontend Routes

- `/` dashboard
- `/assistant`
- `/memo`
- `/live`
- `/experiments`
- `/showcase`
- `/interview`
- `/health`

## Interview-Relevant Concepts Demonstrated

- analytics engineering
- data quality and idempotent ingestion
- dimensional and mart-style modeling
- time-based ML evaluation
- leak prevention
- RAG grounding and SQL guardrails
- agent workflow design
- observability and replay simulation
- experimentation and guardrails
- offline policy evaluation
- responsible AI review artifacts
- local-first production-style architecture

## Limitations

- The project is fixture-backed and local-first, so benchmark metrics are not evidence of production-grade generalization.
- Retrieval is lexical and deterministic rather than embedding-based.
- Cycle 7 uses a graph-like workflow design but is not yet powered by the actual LangGraph runtime.
- The PEFT section is interview-oriented sandbox metadata, not a shipped training pipeline.

## Additional Docs

- `docs/architecture.md`
- `docs/runbook.md`
- `docs/implementation-cadence-plan.md`
- `docs/demo-script.md`
- `pipelines/README.md`
- `warehouse/README.md`
