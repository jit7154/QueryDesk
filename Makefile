.PHONY: up down dev test lint eval setup

PYTHON := /opt/anaconda3/envs/querydesk/bin/python
PIP := /opt/anaconda3/envs/querydesk/bin/pip
UVICORN := /opt/anaconda3/envs/querydesk/bin/uvicorn
PYTEST := /opt/anaconda3/envs/querydesk/bin/pytest
RUFF := /opt/anaconda3/envs/querydesk/bin/ruff

up:
	docker compose up -d

down:
	docker compose down

dev-backend:
	cd backend && $(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

dev: up
	@echo "Starting backend and frontend services..."
	make -j 2 dev-backend dev-frontend

test:
	cd backend && $(PYTEST) tests/ -v -m "not integration"

test-integration:
	cd backend && $(PYTEST) tests/integration -v -m "integration"

test-all:
	cd backend && $(PYTEST) tests/ -v

lint:
	cd backend && $(RUFF) check .

eval:
	$(PYTHON) evals/run_retrieval_eval.py
	$(PYTHON) evals/run_sql_eval.py
	$(PYTHON) evals/run_e2e_eval.py

setup:
	$(PIP) install -e "backend[dev]"
	cd frontend && npm install
