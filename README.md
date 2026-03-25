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
- Fast backend checks: `cd backend && pytest`
- Full backend pipeline checks: `cd backend && pytest -m pipeline`

## Cycle 1
- Fixture-backed end-to-end run: `python -m app.cycle1.cli full-run`
- Ingest only: `python -m app.cycle1.cli ingest --source all`
- Data quality only: `python -m app.cycle1.cli quality`
- EDA only: `python -m app.cycle1.cli eda`
- Fixtures are now generated programmatically and currently produce `125` flight rows
- Live mode is supported through env-backed URLs: `BTS_DOWNLOAD_URL`, `WEATHER_BASE_URL`, `COMTRADE_BASE_URL`

## Cycle 2
- Build curated warehouse models: `python -m app.cycle2.cli build`
- Validate warehouse models: `python -m app.cycle2.cli validate`
- Fixture-backed end-to-end warehouse run: `python -m app.cycle2.cli full-run`
- Model SQL lives under `warehouse/models`, and KPI definitions live in `warehouse/glossary.md`

## Cycle 3
- Generate a statistical report from warehouse marts: `python -m app.cycle3.cli report`
- Fixture-backed end-to-end stats run: `python -m app.cycle3.cli full-run`
- Outputs include trend summaries, effect-size comparisons, and Poisson/Negative-Binomial count summaries

## Cycle 4
- Train and evaluate ML baselines: `python -m app.cycle4.cli train`
- Fixture-backed end-to-end ML run: `python -m app.cycle4.cli full-run`
- Outputs include evaluation dashboards, baseline comparisons, and model cards

## Cycle 5
- Launch the UI against the backend control-tower API: `make up`
- Backend now serves `GET /api/control-tower/overview`
- Backend exports are available under `GET /api/control-tower/export/{dataset}`
- Frontend dashboard includes KPI cards, trend boards, carrier drilldowns, alerts, forecast panels, saved views, and CSV exports

## Cycle 6
- Assistant endpoint: `POST /api/assistant/query`
- Retrieval mode returns grounded answers with citations from the local docs corpus
- SQL mode routes analytics questions through allowlisted, LIMIT-guarded DuckDB queries with audit logging
- RAG eval pack: `python -m app.cycle6.cli`
- Eval outputs include mode accuracy, citation coverage, refusal precision, and a hallucination-rate proxy
- Frontend assistant UI is available at `/assistant`

## Cycle 7
- Decision memo endpoint: `POST /api/agent/decision-memo`
- Deterministic workflow: diagnose -> gather evidence -> recommend -> memo
- Includes trace output, fallback tracking, and a memo rubric evaluation harness
- Frontend memo UI is available at `/memo`

## Cycle 8
- Live replay status: `GET /api/stream/status`
- Replay sample events: `POST /api/stream/replay`
- Prometheus metrics now include replay event count, active alerts, and live on-time rate
- Grafana dashboard and Prometheus alert rules are provisioned through the Cycle 8 assets
- Frontend live ops UI is available at `/live`

## Cycle 9
- Experiment analysis endpoint: `POST /api/experiments/analyze`
- Default toggle: `adaptive_turnaround_buffers`
- Outputs include primary lift, guardrail metrics, sequential checks, carrier slices, and rollout recommendation
- CLI flow: `python -m app.cycle9.cli analyze` or `python -m app.cycle9.cli full-run`
- Frontend experimentation UI is available at `/experiments`

## Cycle 10
- Portfolio OPE endpoint: `POST /api/portfolio/ope`
- Offline policy evaluation compares `always_control`, `always_treatment`, and `delay_aware_treatment`
- Outputs include IPS, DM, and DR estimates plus a champion policy summary
- CLI flow: `python -m app.cycle10.cli analyze` or `python -m app.cycle10.cli full-run`
- Frontend showcase UI is available at `/showcase`

## Architecture
See `docs/architecture.md` for the current system view and end-to-end data flow.

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
