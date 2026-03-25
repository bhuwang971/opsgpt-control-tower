# Demo Script

## 90-Second Walkthrough

OpsGPT is a local-first operations intelligence platform that starts with governed ingestion, builds reproducible KPI marts in DuckDB, adds trend statistics and leak-safe ML baselines, then layers on cited retrieval, safe NL-to-SQL, tool-based decision memos, live replay monitoring, experimentation, and offline policy evaluation. The goal is to show not just dashboards, but an end-to-end operating system for analysis, decisions, and rollout safety.

## Demo Path

1. Open `/` and show KPI cards, trend board, carrier drilldown, and exports.
2. Open `/assistant` and ask a grounded analytics question.
3. Open `/memo` and generate a decision memo with trace and rubric.
4. Open `/live` and replay sample events to show alert behavior.
5. Open `/experiments` and explain the primary metric, guardrails, and sequential checks.
6. Open `/showcase` and compare IPS, DM, and DR estimates across candidate policies.

## Interview Talking Points

- Why DuckDB and Postgres are split even in a laptop project.
- How time-based evaluation and auditability were kept visible from early cycles.
- Why retrieval, SQL, and workflow steps each have separate safety boundaries.
- How experimentation and OPE help bridge analytics and rollout decisions.

## Known Limitations

- Fixture-backed data keeps the repo reproducible but limits statistical depth.
- OPE is a portfolio differentiator here, not a production launch gate.
- Current streaming is replay-oriented rather than a full live consumer service.
