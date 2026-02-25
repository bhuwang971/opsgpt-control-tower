.PHONY: up down logs lint test

up:
	docker compose -f infra/docker-compose.yml --env-file .env up -d --build

down:
	docker compose -f infra/docker-compose.yml --env-file .env down

logs:
	docker compose -f infra/docker-compose.yml --env-file .env logs -f --tail=200

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

test:
	cd backend && pytest
	cd frontend && npm run build
