.PHONY: test lint typecheck check build clean

test:
	PYTHONPATH=src pytest -q

coverage:
	PYTHONPATH=src pytest -q --cov=agentrail --cov-report=term-missing --cov-fail-under=80

lint:
	ruff check src tests scripts

typecheck:
	mypy src/agentrail --ignore-missing-imports

check: lint typecheck test

build:
	python -m build

clean:
	rm -rf build dist .pytest_cache .mypy_cache .ruff_cache
