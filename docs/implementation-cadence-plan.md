# OpsGPT Control Tower Implementation Cadence Plan

## Working agreement
- Development is local-first; no push until local checks pass and you sign off.
- Commits are feature/update based, not calendar-labeled.
- Every implementation cycle ends with:
  - backend checks: `ruff check .` and `pytest`
  - frontend checks: `npm run lint` and `npm run build`
  - runtime checks: `docker compose ... up -d --build` and health endpoints

## Problem statement
Ops teams with SLA targets need one system to monitor reliability KPIs, explain trend shifts, predict delay risk, and generate evidence-backed actions. Dashboards alone lack depth; ungrounded chatbots are unsafe. OpsGPT combines governed analytics, ML, cited retrieval, and tool-using agents.

## Expected outputs
- UI: KPI dashboard, trend/anomaly views, segment drilldowns, alert feed, exportable views.
- ML: classification (breach risk), regression (delay minutes), forecasting (future delay rate), model cards.
- RAG/NL2SQL: cited answers with cite-or-drop policy, validated SQL with audit trail.
- Agent: evidence-backed decision memo with tool traces and recommendation trade-offs.

## Stack with rationale and switch points
- Frontend: React + Vite + TS + Tailwind (fast iteration).
- Backend: FastAPI + Pydantic (typed contracts).
- OLAP: DuckDB (+ dbt patterns) for local analytics speed.
- OLTP: Postgres for app state, runs, audit logs.
- Vector DB: Qdrant for local production-like retrieval.
- LLM/RAG: Ollama + Phi-3.5 Mini Instruct + sentence-transformers.
- Agents: LangGraph for deterministic tool workflows.
- Streaming: Redpanda for event replay and alerting.
- Observability: Prometheus + Grafana.
- Switch when needed:
  - DuckDB -> ClickHouse/BigQuery for larger multi-user scale.
  - Qdrant -> pgvector/FAISS depending on ops simplicity and integration.
  - LangGraph -> LlamaIndex workflows when retrieval-first orchestration is preferred.

## Architecture and end-to-end data flow
1. Ingest BTS + Weather.gov + Comtrade + docs corpus.
2. Persist raw partitions and run metadata.
3. Transform to curated marts in DuckDB.
4. Train/evaluate models using time-safe splits and backtesting.
5. Serve KPIs/predictions/RAG/agent endpoints from FastAPI.
6. Render control-tower UI in React.
7. Stream updates via Redpanda for near-real-time refresh/alerts.
8. Monitor system/data/model quality in Prometheus/Grafana.

## Guardrails, evaluation, and monitoring
- Data quality: schema/type/null/range/freshness/uniqueness checks with thresholds.
- Leakage prevention: feature availability rules and strictly time-based splits.
- ML evaluation: PR-AUC/Brier/MAE/RMSE + segmented error slices + backtesting.
- RAG evaluation: retrieval Recall@k/MRR, citation coverage, latency.
- NL2SQL safety: allowlisted schema, SQL parse/validate, mandatory LIMIT, timeout, audit logs.
- Agent reliability: tool-first evidence path, retry/fallback graph nodes, human approval option.
- Monitoring: data drift, prediction drift, retrieval hit-rate, API latency/error rate, job duration.

## KPI, trend, and experimentation layer
- KPI set: on-time rate, P50/P90 delay, cancellation rate, reliability score, volatility index.
- Trend analysis: decomposition, rolling z-score, changepoint detection, segment comparisons.
- Probability models: Poisson/Negative Binomial for count outcomes + uncertainty intervals.
- Experiments: A/B design templates with primary/guardrail metrics, power/MDE, sequential checks.

## Cadence (Cycle 0 -> Cycle 10)

### Cycle 0: Foundation and platform hygiene
- Goals: monorepo, local stack, CI, pre-commit, health/readiness endpoints.
- Deliverables: running compose stack + base UI + backend + docs/runbook.
- Exit checks: `make up`, `/health`, `/ready`, `make lint`, `make test`.

### Cycle 1: Data ingestion + EDA + data quality
- Goals: reliable loading for BTS/Weather/Comtrade and first analytical profiling.
- Deliverables:
  - connector jobs with pagination/retries/idempotency
  - raw and bronze tables in DuckDB
  - data quality framework with threshold checks
  - EDA report (profiles, missingness, distributions, key slices)
- Exit checks:
  - re-run ingestion without duplicates
  - quality report generated and pass/fail behavior confirmed
  - EDA artifact generated from local command

### Cycle 2: Warehouse modeling and KPI marts
- Goals: curated schema and reusable KPI views.
- Deliverables: dimension/fact models, KPI marts, glossary.
- Exit checks: model tests pass and KPI queries match expected slices.

### Cycle 3: Statistical and probability layer
- Goals: trend comparisons and uncertainty-aware KPI interpretation.
- Deliverables: hypothesis/effect-size utilities, Poisson/NegBin notebooks.
- Exit checks: reproducible statistical report for selected KPI segments.
  Current implementation path:
  - `backend/app/cycle3` contains the reusable stats utilities and report runner
  - `python -m app.cycle3.cli full-run` produces the reproducible report artifact

### Cycle 4: ML baselines and out-of-sample evaluation
- Goals: classification + regression + forecasting baselines.
- Deliverables: training pipeline, model artifacts, evaluation dashboards.
- Exit checks: time-based split metrics + baseline comparisons + model cards.
  Current implementation path:
  - `backend/app/cycle4` contains the benchmark dataset builder, baselines, and evaluation runner
  - `python -m app.cycle4.cli full-run` generates the evaluation dashboard and model card artifacts

### Cycle 5: Control Tower UI expansion
- Goals: production-style analytics experience.
- Deliverables: KPI cards, trends, drilldowns, saved filters/exports.
- Exit checks: UI/API integration validated with sample scenarios.
  Current implementation path:
  - `backend/app/control_tower.py` serves the control-tower overview and CSV export payloads
  - `frontend/src/App.tsx` renders the dashboard, carrier drilldowns, alerts, and forecast panels

### Cycle 6: RAG and safe NL-to-SQL
- Goals: grounded answers and auditable query generation.
- Deliverables: chunk/embed/index pipeline, citation UI, SQL guardrails.
- Exit checks: prompt regression pack, citation coverage, SQL safety tests.
  Current implementation path:
  - `backend/app/cycle6` contains retrieval, SQL guardrails, and assistant orchestration
  - `backend/app/cycle6/eval.py` contains the local RAG benchmark and hallucination/citation eval pack
  - retrieval now supports an optional cross-encoder reranker path with before/after eval tracking
  - `POST /api/assistant/query` serves the grounded response surface
  - `frontend/src/App.tsx` exposes the citation and SQL preview UI on `/assistant`

### Cycle 7: Agent workflows and eval harness
- Goals: evidence-backed decision automation.
- Deliverables: LangGraph flow (diagnose -> evidence -> recommend -> memo).
- Exit checks: stable agent traces, fallback behavior, memo quality rubric.
  Current implementation path:
  - `backend/app/cycle7` contains the deterministic workflow, trace model, and rubric harness
  - `POST /api/agent/decision-memo` serves the memo output
  - `frontend/src/App.tsx` exposes the memo workflow UI on `/memo`

### Cycle 8: Streaming and observability hardening
- Goals: near-real-time updates and robust ops visibility.
- Deliverables: Redpanda consumers, alert rules, Grafana dashboards, runbook.
- Exit checks: replayed events update KPIs; alerts and dashboards trigger as expected.
  Current implementation path:
  - `backend/app/cycle8` contains the local replay engine, metrics, and observability provisioning
  - `GET /api/stream/status` and `POST /api/stream/replay` expose the replay loop
  - `frontend/src/App.tsx` exposes the live replay view on `/live`

### Cycle 9: Experimentation module
- Goals: product and model experimentation support.
- Deliverables: A/B analysis templates, reporting views, guardrail metrics.
- Exit checks: end-to-end experiment analysis on a real config toggle.
  Current implementation path:
  - `backend/app/cycle9` contains the experiment frame builder, analysis runner, and report writer
  - `POST /api/experiments/analyze` serves the experiment summary payload
  - `frontend/src/App.tsx` exposes the experimentation UI on `/experiments`

### Cycle 10: Advanced differentiators and portfolio polish
- Goals: standout optional components and interview packaging.
- Deliverables: offline bandit/OPE, optional KG or MCP integration, final demo assets.
- Exit checks: complete demo script, architecture narrative, risk/tradeoff notes.
  Current implementation path:
  - `backend/app/cycle10` contains the offline policy evaluation runner and portfolio report writer
  - `POST /api/portfolio/ope` serves the OPE summary payload
  - `frontend/src/App.tsx` exposes the showcase UI on `/showcase`
  - `docs/architecture.md` and `docs/demo-script.md` hold the interview-facing narrative assets
  - `GET /api/interview/dashboard` and `/interview` expose an interviewer-facing evidence dashboard

## Implementation command contract for every cycle
When you ask for cycle execution, I will execute:
1. Scope lock for mapped cycle.
2. Small slices with conventional commits.
3. Full local checks after each slice.
4. A verification section for you with exact commands + expected outputs.
5. Wait for your sign-off before any push.

## Interview prep package
- 90-second talk track:
  OpsGPT is a local-first operations intelligence platform that combines real data ingestion, governed analytics, leak-safe ML forecasting, cited retrieval, and tool-based agent recommendations. It is designed to be reproducible, observable, and auditable on a laptop while preserving production engineering patterns.
- High-probability interview prompts to emphasize:
  - Why split DuckDB (OLAP) and Postgres (OLTP)?
  - How leakage is prevented in time-based ML tasks.
  - How RAG quality and safety are measured.
  - How NL-to-SQL is constrained and audited.
  - How model/data/retrieval drift is monitored and acted on.
