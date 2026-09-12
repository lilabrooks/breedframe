.PHONY: setup start check demo evaluate
setup:
	sh scripts/setup.sh
start:
	sh scripts/start.sh
check:
	uv sync --locked
	uv run --no-sync ruff check breedframe scripts tests
	uv run --no-sync ruff format --check breedframe scripts tests
	uv run --no-sync pytest -q
	node --check breedframe/static/app.js
	node --check breedframe/static/agent-flow.js
	node --test tests/test_agent_flow.cjs
demo:
	PYTHONPATH=. .venv/bin/python scripts/demo.py
evaluate:
	PYTHONPATH=. .venv/bin/python scripts/evaluate.py
