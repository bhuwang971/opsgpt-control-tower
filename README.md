# OpsGPT Control Tower

Local-first, $0-cost, production-grade portfolio project.

## Run
1. Copy `.env.example` to `.env`
2. Run `make up`
3. Open frontend at `http://localhost:5173`

## Verify
- API health: `http://localhost:8000/health`
- API readiness: `http://localhost:8000/ready`
- Grafana: `http://localhost:3000`
- Prometheus: `http://localhost:9090`

## Dev checks
- `make lint`
- `make test`

## Architecture
Diagram placeholder: see `docs/architecture.md`.

## Roadmap
- Foundation: local-first setup, services, health, CI, pre-commit
- Data ingestion: BTS + NOAA + Comtrade connectors and raw loading
- Warehouse modeling: DuckDB analytics models and dbt structure
- Control Tower UI: KPIs, trends, drilldowns, and alert views
- ML baselines: delay classification and delay-minutes regression
- Forecasting: time-series modeling and backtesting pipeline
- RAG + SQL safety: retrieval with citations and guarded NL-to-SQL
- Agent workflows: tool-using orchestration and decision memo outputs
- Monitoring: drift checks, model/service metrics, observability dashboards
- Experimentation: A/B analysis module and reporting templates
- Hardening: performance tuning, docs expansion, and reliability polish
