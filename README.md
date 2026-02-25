# OpsGPT Control Tower

Local-first, $0-cost, production-grade portfolio project.

## Run (Week 0)
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
![Architecture diagram placeholder](docs/architecture-placeholder.png)

## Roadmap (Week 0-10)
- Week 0: foundations and production hygiene
- Week 1: ingest BTS + NOAA + Comtrade connectors
- Week 2: DuckDB models + dbt scaffolding
- Week 3: control tower KPI views + drilldowns
- Week 4: delay classification/regression baselines
- Week 5: time-series forecasting + backtesting
- Week 6: RAG + citations + safe NL-to-SQL guardrails
- Week 7: LangGraph agentic workflows + decision memos
- Week 8: drift checks + performance monitoring
- Week 9: experimentation module (A/B analysis)
- Week 10: hardening, docs, and polish
