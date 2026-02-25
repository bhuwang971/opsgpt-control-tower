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

## Local stop

- Run `make down`.
