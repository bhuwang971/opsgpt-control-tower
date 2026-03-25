# Runbook

## Prereqs

- Docker Desktop with WSL integration
- Node.js (npm)
- Python 3.11+

## Local startup

1. Run `scripts/setup.ps1` (PowerShell) or `scripts/setup.sh` (WSL).
2. Run `make up`.
3. Verify:
   - API: `http://localhost:8000/health`
   - UI: `http://localhost:5173`
   - Grafana: `http://localhost:3000`

## Test modes

1. Fast backend checks for everyday work:
   - `cd backend`
   - `pytest`
2. Full pipeline-backed backend checks:
   - `cd backend`
   - `pytest -m pipeline`
3. Frontend checks:
   - `cd frontend && npm run lint`
   - `cd frontend && npm run build`

## Cycle 1 pipeline

1. Install backend deps: `pip install -e .\backend[dev]`
2. Run fixture-backed ingest + quality + EDA:
   - `python -m app.cycle1.cli full-run`
3. Output locations:
   - raw landing artifacts: `artifacts/cycle1/raw`
   - quality reports: `artifacts/cycle1/quality`
   - EDA reports: `artifacts/cycle1/eda`
4. Optional live-mode env vars:
   - `BTS_DOWNLOAD_URL`
   - `WEATHER_BASE_URL`
   - `COMTRADE_BASE_URL`

## Cycle 2 warehouse

1. Build curated dimensions, facts, and KPI marts:
   - `python -m app.cycle2.cli build`
2. Validate warehouse models:
   - `python -m app.cycle2.cli validate`
3. Run the fixture-backed Cycle 1 + Cycle 2 chain:
   - `python -m app.cycle2.cli full-run`
4. Key outputs:
   - SQL models: `warehouse/models/curated`, `warehouse/models/marts`
   - glossary: `warehouse/glossary.md`
   - validation reports: `artifacts/cycle2/validation`

## Cycle 3 statistical layer

1. Generate a report from existing warehouse marts:
   - `python -m app.cycle3.cli report`
2. Run the fixture-backed Cycle 2 + Cycle 3 chain:
   - `python -m app.cycle3.cli full-run`
3. Key outputs:
   - statistical reports: `artifacts/cycle3/report`
   - supporting warehouse artifacts: `artifacts/cycle3/cycle2`

## Cycle 4 ML baselines

1. Train and evaluate the baseline models:
   - `python -m app.cycle4.cli train`
2. Run the fixture-backed Cycle 3 + Cycle 4 chain:
   - `python -m app.cycle4.cli full-run`
3. Key outputs:
   - evaluation dashboards: `artifacts/cycle4/models`
   - upstream statistical artifacts: `artifacts/cycle4/cycle3`

## Cycle 5 control tower UI

1. Start the full stack:
   - `make up`
2. Open the dashboard:
   - `http://localhost:5173`
3. Backend analytics API:
   - `http://localhost:8000/api/control-tower/overview`
4. CSV exports:
   - `http://localhost:8000/api/control-tower/export/daily_kpis`
   - `http://localhost:8000/api/control-tower/export/carrier_performance`
   - `http://localhost:8000/api/control-tower/export/trade_monthly`

## Cycle 6 grounded assistant

1. Open the assistant UI:
   - `http://localhost:5173/assistant`
2. Backend query endpoint:
   - `POST http://localhost:8000/api/assistant/query`
3. Behavior:
   - documentation questions use local retrieval with citations
   - analytics questions use guarded NL-to-SQL with audit logging
4. Audit log:
   - `backend/artifacts/cycle6/sql_audit.jsonl`
5. RAG evaluation pack:
   - `python -m app.cycle6.cli`
6. Eval outputs:
   - markdown and JSON benchmark reports under `backend/artifacts/cycle6`
   - citation coverage, refusal precision, and hallucination-rate proxy metrics

## Cycle 7 decision workflow

1. Open the memo UI:
   - `http://localhost:5173/memo`
2. Backend memo endpoint:
   - `POST http://localhost:8000/api/agent/decision-memo`
3. Outputs:
   - markdown memo
   - workflow trace
   - rubric score
4. Artifact path when using the CLI:
   - `backend/artifacts/cycle7`

## Cycle 8 replay and observability

1. Open the live ops UI:
   - `http://localhost:5173/live`
2. Replay endpoints:
   - `GET http://localhost:8000/api/stream/status`
   - `POST http://localhost:8000/api/stream/replay`
3. Provision observability assets with the CLI:
   - `python -m app.cycle8.cli`
4. Generated assets:
   - Grafana dashboard JSON under `infra/grafana/provisioning/dashboards`
   - Prometheus alert rules at `infra/prometheus/alert_rules.yml`

## Cycle 9 experimentation module

1. Open the experiments UI:
   - `http://localhost:5173/experiments`
2. Backend experiment endpoint:
   - `POST http://localhost:8000/api/experiments/analyze`
3. CLI entry points:
   - `python -m app.cycle9.cli analyze`
   - `python -m app.cycle9.cli full-run`
4. Current local toggle:
   - `adaptive_turnaround_buffers`
5. Outputs:
   - primary lift and confidence interval
   - guardrail metrics
   - sequential checkpoint analysis
   - markdown and JSON artifacts under `backend/artifacts/cycle9`

## Cycle 10 portfolio showcase

1. Open the showcase UI:
   - `http://localhost:5173/showcase`
2. Backend OPE endpoint:
   - `POST http://localhost:8000/api/portfolio/ope`
3. CLI entry points:
   - `python -m app.cycle10.cli analyze`
   - `python -m app.cycle10.cli full-run`
4. Outputs:
   - IPS, DM, and DR estimates for candidate rollout policies
   - champion policy summary
   - portfolio report artifacts under `backend/artifacts/cycle10`
   - docs updates in `docs/architecture.md` and `docs/demo-script.md`

## Local stop

- Run `make down`.
