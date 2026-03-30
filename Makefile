.PHONY: install lint format test data train serve all

install:
	pip install -e ".[dev]"

lint:
	ruff check src/ tests/ config/

format:
	ruff format src/ tests/ config/

test:
	pytest -v --tb=short

data:
	python -m src.pipeline data

train:
	python -m src.pipeline train

serve:
	uvicorn src.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000

all: data train
