# Warehouse

DuckDB + dbt-style scaffolding for analytics models.

Cycle 2 adds:
- curated dimensions in `warehouse/models/curated`
- KPI marts in `warehouse/models/marts`
- warehouse glossary in `warehouse/glossary.md`

Run:
- `python -m app.cycle2.cli build`
- `python -m app.cycle2.cli validate`
- `python -m app.cycle2.cli full-run`

Notes:
- Fixture-backed warehouse runs now build over a generated `125`-row BTS corpus.
- Use `cd backend && pytest` for fast checks and `cd backend && pytest -m pipeline` for full pipeline validation.
