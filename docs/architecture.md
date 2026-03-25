# Architecture

## System View

```text
[React/Vite UI]
    |-- dashboard, assistant, memo, live ops, experiments, showcase
    v
[FastAPI backend]
    |-- health/readiness/metrics
    |-- control tower analytics API
    |-- grounded assistant + guarded SQL
    |-- decision memo workflow
    |-- replay + observability endpoints
    |-- experimentation + offline policy evaluation
    |
    +--> [DuckDB]
    |      raw -> bronze -> analytics marts
    |
    +--> [Postgres]
    |      app state, future run metadata, audit expansion point
    |
    +--> [Qdrant]
    |      local retrieval index
    |
    +--> [Prometheus -> Grafana]
    |      service and replay metrics
    |
    +--> [Redpanda]
           local streaming and replay posture
```

## Data Flow

1. Cycle 1 ingests BTS, weather, and Comtrade fixtures or live URLs into raw and bronze tables.
2. Cycle 2 builds curated facts and KPI marts in DuckDB.
3. Cycle 3 computes statistical summaries and probability-oriented readouts.
4. Cycle 4 trains local baseline models with time-safe evaluation.
5. Cycle 5 serves the control tower dashboard and exports.
6. Cycle 6 adds cited retrieval and guarded NL-to-SQL.
7. Cycle 7 assembles evidence-backed decision memos.
8. Cycle 8 replays event streams and emits observability metrics.
9. Cycle 9 evaluates config toggles through an experimentation layer.
10. Cycle 10 compares rollout policies with offline policy evaluation and packages the system for demo use.

## Design Choices

- DuckDB for local OLAP speed and reproducibility.
- FastAPI for typed contracts and lightweight service composition.
- React/Vite for quick iteration on multiple operator-facing views.
- Prometheus/Grafana and Redpanda included early to keep the system explainable and observable, not just functional.

## Risk and Tradeoff Notes

- The local fixture corpus is intentionally tiny, so advanced analytics and OPE outputs demonstrate engineering shape more than production statistical confidence.
- Postgres and Qdrant are present as production-like boundaries even though the current local flows lean heavily on DuckDB.
- The OPE layer is useful as a differentiator and portfolio talking point, but it should not be treated as shipment authority without richer logged data and stronger propensity controls.
