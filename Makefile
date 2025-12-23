.PHONY: up down restart logs test test-unit test-integration clean install migrate help

help:
	@echo "Kasparro Backend - Available Commands"
	@echo "======================================"
	@echo "make install          - Install dependencies"
	@echo "make up               - Start containers"
	@echo "make down             - Stop containers"
	@echo "make restart          - Restart containers"
	@echo "make logs             - View container logs"
	@echo "make test             - Run all tests"
	@echo "make test-unit        - Run unit tests"
	@echo "make test-integration - Run integration tests"
	@echo "make clean            - Clean up containers and volumes"
	@echo "make migrate          - Run database migrations"

install:
	pip install -r requirements.txt

up:
	docker-compose up -d
	@echo "Services starting. Wait 10 seconds for database initialization..."
	@sleep 10
	@echo "Backend available at http://localhost:8000"
	@echo "API documentation at http://localhost:8000/docs"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f backend

logs-db:
	docker-compose logs -f postgres

test:
	pytest tests/ -v --cov=src --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

migrate:
	docker-compose exec backend python -m alembic upgrade head

clean:
	docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov

shell:
	docker-compose exec backend bash

psql:
	docker-compose exec postgres psql -U postgres -d kasparro

lint:
	black src tests
	isort src tests
	flake8 src tests

format:
	black src tests --line-length 88
	isort src tests

type-check:
	mypy src --ignore-missing-imports
