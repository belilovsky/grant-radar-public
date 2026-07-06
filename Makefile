PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
BOOTSTRAP_PYTHON ?= python3
PYTEST ?= $(PYTHON) -m pytest
PY_MODULES ?= api/ core/ sources/ tests/ scripts/ alembic/
MYPY_MODULES ?= api/ core/ sources/ scripts/
COMPOSE ?= $(shell if command -v docker-compose >/dev/null 2>&1; then echo docker-compose; elif command -v docker >/dev/null 2>&1; then echo "docker compose"; else echo docker-compose; fi)

.PHONY: help bootstrap bootstrap-reset playwright-install export-public-repo dev dev-logs dev-down lint format test test-cov db-shell redis-cli build build-prod install-hooks db-init db-reset test-db ci ci-fast ci-local smoke-prod content-audit db-upgrade db-downgrade db-revision db-migrate migrate translate-ru

help:
	@echo "Available commands:"
	@echo "  make bootstrap        - Create .venv and install project dependencies"
	@echo "  make bootstrap-reset  - Recreate .venv with the selected Python runtime"
	@echo "  make playwright-install - Install Playwright browser binaries"
	@echo "  make export-public-repo - Create a fresh public-safe repo snapshot"
	@echo "  make dev              - Start development environment"
	@echo "  make dev-logs         - View development logs"
	@echo "  make dev-down         - Stop development environment"
	@echo "  make lint             - Check code quality (Black, isort, Flake8, mypy)"
	@echo "  make format           - Auto-format code (Black, isort)"
	@echo "  make test             - Run tests with pytest"
	@echo "  make test-cov         - Run tests with coverage report"
	@echo "  make db-shell         - Access PostgreSQL shell"
	@echo "  make redis-cli        - Access Redis CLI"
	@echo "  make build            - Build Docker image (dev)"
	@echo "  make build-prod       - Build production Docker image"
	@echo "  make install-hooks    - Install pre-commit git hooks"
	@echo "  make migrate          - Run Alembic migrations to head"
	@echo "  make translate-ru     - Backfill Russian localized content into DB"
	@echo "  make smoke-prod       - Run live production smoke checks"
	@echo "  make content-audit    - Run live content coverage and quality checks"

bootstrap:
	$(BOOTSTRAP_PYTHON) scripts/check_python_version.py
	test -d .venv || $(BOOTSTRAP_PYTHON) -m venv .venv
	./.venv/bin/python scripts/check_python_version.py
	./.venv/bin/python -m pip install --upgrade pip
	./.venv/bin/python -m pip install -r requirements.txt

bootstrap-reset:
	rm -rf .venv
	$(BOOTSTRAP_PYTHON) scripts/check_python_version.py
	$(BOOTSTRAP_PYTHON) -m venv .venv
	./.venv/bin/python scripts/check_python_version.py
	./.venv/bin/python -m pip install --upgrade pip
	./.venv/bin/python -m pip install -r requirements.txt

playwright-install:
	./.venv/bin/python -m playwright install chromium

export-public-repo:
	bash scripts/export_public_repo.sh

dev:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml up -d
	@echo "✅ Development environment started"
	@echo "   API: http://localhost:8000"
	@echo "   PostgreSQL: localhost:5434 (user: grantradar)"
	@echo "   Redis: localhost:6380"

dev-logs:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml logs -f

dev-down:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml down
	@echo "✅ Development environment stopped"

lint:
	@echo "Running Black..."
	$(PYTHON) -m black --check $(PY_MODULES)
	@echo "Running isort..."
	$(PYTHON) -m isort --check-only $(PY_MODULES)
	@echo "Running Flake8..."
	$(PYTHON) -m flake8 $(PY_MODULES) --max-line-length=100
	@echo "Running mypy..."
	$(PYTHON) -m mypy $(MYPY_MODULES) --ignore-missing-imports

format:
	@echo "Running Black..."
	$(PYTHON) -m black $(PY_MODULES)
	@echo "Running isort..."
	$(PYTHON) -m isort $(PY_MODULES)

test:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api pytest tests/

test-cov:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api pytest tests/ --cov=api --cov=core --cov-report=term-missing

db-shell:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml exec db psql -U grantradar -d grantradar

redis-cli:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml exec redis redis-cli

build:
	$(COMPOSE) build api

build-prod:
	docker build -f Dockerfile.prod -t grant-radar:latest .

install-hooks:
	$(PYTHON) -m pip install pre-commit
	$(PYTHON) -m pre_commit install
	@echo "✅ Pre-commit hooks installed"

db-init:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api python -m scripts.init_db

db-reset:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api python -m scripts.init_db --reset

test-db:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api pytest tests/test_db_repository.py tests/test_runner_factory.py tests/test_init_db.py -v

ci-fast:
	$(PYTEST) tests/ -v

ci-local:
	$(PYTHON) -m pre_commit run --all-files
	$(PYTEST) tests/ -v

smoke-prod:
	$(PYTHON) -m scripts.production_smoke $(ARGS)

content-audit:
	$(PYTHON) -m scripts.content_audit $(ARGS)

ci:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api sh -c "black --check api/ core/ sources/ tests/ scripts/ alembic/ && isort --check-only api/ core/ sources/ tests/ scripts/ alembic/ && flake8 api/ core/ sources/ tests/ scripts/ alembic/ --max-line-length=100 && pytest tests/ -v"


db-upgrade:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api alembic upgrade head

db-downgrade:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api alembic downgrade -1

db-revision:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml run --rm api alembic revision --autogenerate -m "$(m)"

db-migrate: db-upgrade

migrate: db-upgrade

translate-ru:
	@if [ -z "$$GRANT_RADAR_DB_URL" ] && [ -z "$$DATABASE_URL" ]; then \
		echo "GRANT_RADAR_DB_URL/DATABASE_URL is not set; export it or pass ARGS='--url ...'" >&2; \
		exit 2; \
	fi
	$(PYTHON) -m scripts.backfill_russian_content $(ARGS)


.PHONY: show-runs
show-runs:
	@if [ -z "$$GRANT_RADAR_DB_URL" ]; then \
		echo "GRANT_RADAR_DB_URL is not set; export it or pass --url" >&2; \
		exit 2; \
	fi
	$(PYTHON) -m scripts.show_runs $(ARGS)
