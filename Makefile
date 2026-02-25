.PHONY: up down logs lint test

up:
	docker compose -f infra/docker-compose.yml --env-file .env up -d --build

down:
	docker compose -f infra/docker-compose.yml --env-file .env down

logs:
	docker compose -f infra/docker-compose.yml --env-file .env logs -f --tail=200

lint:
	@echo "lint targets not wired yet"

test:
	@echo "test targets not wired yet"
