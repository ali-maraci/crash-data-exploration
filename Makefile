.PHONY: install lint format test data train serve all

venv:
	python3 -m venv venv

install: venv
	venv/bin/pip install -e ".[dev]"

lint:
	venv/bin/ruff check src/ tests/ config/

format:
	venv/bin/ruff format src/ tests/ config/

test:
	venv/bin/pytest -v --tb=short

data:
	venv/bin/python -m src.pipeline data

train:
	venv/bin/python -m src.pipeline train

serve:
	venv/bin/uvicorn src.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

all: data train
