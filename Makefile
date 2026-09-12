.PHONY: setup start check demo evaluate
setup:
	sh scripts/setup.sh
start:
	sh scripts/start.sh
check:
	.venv/bin/ruff check breedframe scripts tests
	.venv/bin/ruff format --check breedframe scripts tests
	.venv/bin/pytest -q
	node --check breedframe/static/app.js
demo:
	PYTHONPATH=. .venv/bin/python scripts/demo.py
evaluate:
	PYTHONPATH=. .venv/bin/python scripts/evaluate.py
