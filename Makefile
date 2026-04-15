%PHONY: help build up down logs backend-logs frontend-logs shell-backend shell-postgres test clean lint format

help: ## Display this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

build: ## Build Docker images
	docker-compose build

up: ## Start all services
	docker-compose up -d
	@echo "Services starting... waiting for stabilization"
	@sleep 5
	@docker-compose ps
	@echo ""
	@echo "Frontend: http://localhost"
	@echo "Backend: http://localhost:8002"
	@echo "API Docs: http://localhost:8002/docs"

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## View all logs
	docker-compose logs -f

backend-logs: ## View backend logs
	docker-compose logs -f backend

frontend-logs: ## View frontend logs
	docker-compose logs -f frontend

postgres-logs: ## View PostgreSQL logs
	docker-compose logs -f postgres

shell-backend: ## Open shell in backend container
	docker-compose exec backend sh

shell-postgres: ## Open psql in postgres container
	docker-compose exec postgres psql -U simtek_user -d simtek_trader

backend-health: ## Check backend health
	curl -s http://localhost:8002/health | jq .

backend-tickers: ## Get available tickers
	curl -s http://localhost:8002/tickers | jq .

backend-signal: ## Get signal for NPN ticker
	curl -s http://localhost:8002/signal/NPN | jq '.current_signal'

test: ## Run tests (backend)
	docker-compose exec backend python -m pytest tests/ -v

clean: ## Remove Docker containers and volumes
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

lint: ## Lint Python code
	docker-compose exec backend python -m pylint src/

format: ## Format Python code
	docker-compose exec backend python -m black src/

production-build: ## Build for production
	docker-compose -f docker-compose.production.yml build

production-up: ## Start production services
	docker-compose -f docker-compose.production.yml up -d

production-down: ## Stop production services
	docker-compose -f docker-compose.production.yml down

production-logs: ## View production logs
	docker-compose -f docker-compose.production.yml logs -f

dev-setup: ## Setup development environment (local)
	python -m venv venv
	. venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev-backend: ## Run backend locally (dev)
	. venv/bin/activate && ENVIRONMENT=development BACKEND_PORT=8002 python src/main.py

dev-frontend: ## Run frontend locally (dev)
	cd frontend && npm run dev

dev-db: ## Start only PostgreSQL in Docker
	docker-compose up -d postgres
	@echo "PostgreSQL is running on localhost:5432"
	@echo "User: simtek_user"
	@echo "Password: simtek_password_dev"
	@echo "Database: simtek_trader"
