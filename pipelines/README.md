# Pipelines

Cycle 1 is implemented in the backend Python package under `app/cycle1`.

Commands:
- `python -m app.cycle1.cli ingest --source all`
- `python -m app.cycle1.cli quality`
- `python -m app.cycle1.cli eda`
- `python -m app.cycle1.cli full-run`

Behavior:
- Default mode is `fixture` for offline repeatability.
- Fixture data is generated programmatically and currently yields `125` BTS rows.
- `live` mode reads source URLs from environment variables.
- Raw records land as JSONL artifacts and are normalized into DuckDB raw/bronze tables.
