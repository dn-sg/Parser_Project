.PHONY: help build up down restart logs test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build Docker images
	docker compose build

up: ## Start all services
	docker compose up -d

down: ## Stop all services
	docker compose down

restart: ## Restart all services
	docker compose restart

logs: ## Show logs from all services
	docker compose logs -f

logs-api: ## Show API logs
	docker compose logs -f web

logs-worker: ## Show Celery worker logs
	docker compose logs -f celery_worker

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=html --cov-report=term

clean: ## Clean up Docker volumes and images
	docker compose down -v
	docker system prune -f

install: ## Install Python dependencies
	pip install -r requirements.txt

lint: ## Run linters
	flake8 src/ tests/
	black --check src/ tests/

format: ## Format code
	black src/ tests/

