# Architecture

## Diagram

```text
[React/Vite UI] <-> [FastAPI backend]
                      |--> [Postgres]
                      |--> [Qdrant]
                      |--> [DuckDB file]
                      |--> [/metrics -> Prometheus -> Grafana]
                      |--> [Redpanda]
```

## Notes

- Current scope focuses on local-first runnability and production hygiene.
- Domain ingestion and ML layers begin in later increments.
