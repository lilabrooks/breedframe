.PHONY: setup start check demo evaluate
PYTHON_VERSION := $(shell cat .python-version)

setup:
	sh scripts/setup.sh
start:
	sh scripts/start.sh
check:
	uv sync --locked --python "$(PYTHON_VERSION)"
	uv run --no-sync --python "$(PYTHON_VERSION)" ruff check breedframe scripts tests
	uv run --no-sync --python "$(PYTHON_VERSION)" ruff format --check breedframe scripts tests
	uv run --no-sync --python "$(PYTHON_VERSION)" pytest -q
	node --check breedframe/static/app.js
	node --check breedframe/static/agent-flow.js
	node --test tests/test_agent_flow.cjs
demo:
	PYTHONPATH=. .venv/bin/python scripts/demo.py
evaluate:
	PYTHONPATH=. .venv/bin/python scripts/evaluate.py
