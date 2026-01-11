.PHONY: format lint type test cov sec pr check perf complex mutate mutate-fast docs clean help

# Help target
help:
	@echo "Available targets:"
	@echo "  pr       - Fast PR gate (ruff check, type check, tests)"
	@echo "  format   - Auto-format code"
	@echo "  lint     - Run linting checks"
	@echo "  type     - Type checking with mypy"
	@echo "  test     - Run tests"
	@echo "  cov      - Generate coverage report"
	@echo "  sec      - Security checks"
	@echo "  perf     - Performance benchmarks"
	@echo "  complex  - Code complexity analysis"
	@echo "  mutate   - Mutation testing"
	@echo "  check    - Full quality gate (lint + type + cov + sec)"
	@echo "  docs     - Build documentation"
	@echo "  clean    - Clean build artifacts"

# --- Fast PR gate (recommended on every PR) ---
pr:
	poetry run ruff check .
	poetry run ruff format --check .
	poetry run black --check .
	poetry run isort --check-only .
	poetry run mypy .
	poetry run pytest

# --- Full local gate (heavier) ---
format:
	poetry run ruff format .
	poetry run isort .
	poetry run black .

lint:
	poetry run ruff check .
	poetry run flake8 pain001
	poetry run pylint pain001

type:
	poetry run mypy .

test:
	poetry run pytest

cov:
	poetry run pytest --cov=pain001 --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html

sec:
	poetry run bandit -q -r pain001
	poetry run safety check

perf:
	poetry run pytest tests/perf_benchmarks.py -v --benchmark-only --no-cov

complex:
	poetry run radon cc pain001 -a -s
	poetry run radon mi pain001

mutate:
	poetry run mutmut run --paths-to-mutate=pain001 --tests-dir=tests --runner="python -m pytest -x --no-cov -q" --use-coverage

# Faster mutation testing limited to core modules for CI push events
mutate-fast:
	poetry run mutmut run \
		--paths-to-mutate=pain001/core.py,pain001/xml \
		--tests-dir=tests \
		--runner="python -m pytest -x --no-cov -q" \
		--use-coverage

docs:
	poetry install --with docs -q
	poetry run sphinx-build -b html docs docs/_build/html

clean:
	rm -rf build/ dist/ *.egg-info htmlcov/ .coverage .pytest_cache/ .mypy_cache/ .radon-rc sbom.xml LICENSES_REPORT.md licenses.json

check: lint type cov sec

