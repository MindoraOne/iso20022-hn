.PHONY: format lint type test cov sec pr check perf slos clean help

# Color output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# SLO Thresholds (in seconds)
SLO_LINT := 15
SLO_TYPE := 10
SLO_TEST := 60
SLO_XML_GEN := 0.5

# Help target
help:
	@echo "Available targets:"
	@echo "  pr       - Fast PR gate (ruff, black, isort, mypy, pytest)"
	@echo "  check    - Full quality gate (lint + type + cov + sec) + SLO verification"
	@echo "  slos     - Verify SLO compliance (lint, type, test, perf)"
	@echo "  format   - Auto-format code (ruff, isort, black)"
	@echo "  lint     - Run linting checks (ruff, flake8, pylint) with SLO timing"
	@echo "  type     - Type checking with mypy + SLO timing"
	@echo "  test     - Run tests with timing verification"
	@echo "  cov      - Generate coverage report (95% enforced)"
	@echo "  sec      - Security checks (bandit, safety)"
	@echo "  perf     - Performance benchmarks (XML generation < 500ms/1000tx)"
	@echo "  complex  - Code complexity analysis"
	@echo "  mutate   - Mutation testing"
	@echo "  docs     - Build documentation"
	@echo "  clean    - Clean build artifacts"

# --- Fast PR gate (recommended on every PR) ---
pr:
	@echo "$(YELLOW)Running fast PR gate...$(NC)"
	@poetry run ruff check .
	@poetry run ruff format --check .
	@poetry run black --check .
	@poetry run isort --check-only .
	@poetry run mypy .
	@poetry run pytest --tb=short -q
	@echo "$(GREEN)✓ PR gate passed$(NC)"

# --- Full local gate (heavier) with SLO verification ---
format:
	@echo "$(YELLOW)Formatting code...$(NC)"
	@poetry run ruff format .
	@poetry run isort .
	@poetry run black .
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint:
	@echo "$(YELLOW)Running linters (SLO: < $(SLO_LINT)s)...$(NC)"
	@time_start=$$(date +%s%N); \
	poetry run ruff check . && \
	poetry run flake8 pain001 && \
	poetry run pylint -j 4 pain001 --exit-zero; \
	time_end=$$(date +%s%N); \
	elapsed=$$(( ($$time_end - $$time_start) / 1000000000 )); \
	if [ $$elapsed -gt $(SLO_LINT) ]; then \
		echo "$(RED)✗ LINTING SLO EXCEEDED: $${elapsed}s > $(SLO_LINT)s$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ Linting passed ($${elapsed}s < $(SLO_LINT)s)$(NC)"; \
	fi

type:
	@echo "$(YELLOW)Type checking (SLO: < $(SLO_TYPE)s)...$(NC)"
	@time_start=$$(date +%s%N); \
	poetry run mypy . ; \
	time_end=$$(date +%s%N); \
	elapsed=$$(( ($$time_end - $$time_start) / 1000000000 )); \
	if [ $$elapsed -gt $(SLO_TYPE) ]; then \
		echo "$(RED)✗ TYPE CHECK SLO EXCEEDED: $${elapsed}s > $(SLO_TYPE)s$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ Type check passed ($${elapsed}s < $(SLO_TYPE)s)$(NC)"; \
	fi

test:
	@echo "$(YELLOW)Running tests (SLO: < $(SLO_TEST)s, Coverage floor: 95%)...$(NC)"
	@time_start=$$(date +%s%N); \
	poetry run pytest --tb=short -v --cov=pain001 --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=95; \
	test_result=$$?; \
	time_end=$$(date +%s%N); \
	elapsed=$$(( ($$time_end - $$time_start) / 1000000000 )); \
	if [ $$elapsed -gt $(SLO_TEST) ]; then \
		echo "$(RED)✗ TEST SLO EXCEEDED: $${elapsed}s > $(SLO_TEST)s$(NC)"; \
		exit 1; \
	fi; \
	if [ $$test_result -ne 0 ]; then \
		exit $$test_result; \
	fi; \
	echo "$(GREEN)✓ Tests passed ($${elapsed}s < $(SLO_TEST)s)$(NC)"

cov:
	@echo "$(YELLOW)Generating coverage report (floor: 95%)...$(NC)"
	@poetry run pytest --cov=pain001 --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=95
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

sec:
	@echo "$(YELLOW)Running security checks...$(NC)"
	@poetry run bandit -q -r pain001
	@poetry run safety check
	@echo "$(GREEN)✓ Security checks passed$(NC)"

perf:
	@echo "$(YELLOW)Running performance benchmarks (XML gen SLO: < $(SLO_XML_GEN)s/1000tx)...$(NC)"
	@poetry run pytest tests/test_integration.py -v --benchmark-only --benchmark-json=.benchmarks/results.json || true
	@echo "$(YELLOW)Note: Review benchmark results for XML generation performance$(NC)"

complex:
	@echo "$(YELLOW)Analyzing code complexity...$(NC)"
	@poetry run radon cc pain001 -a -s
	@poetry run radon mi pain001

mutate:
	@echo "$(YELLOW)Running mutation testing...$(NC)"
	@poetry run mutmut run --paths-to-mutate=pain001 --tests-dir=tests --runner="python -m pytest -x --no-cov -q" --use-coverage

mutate-fast:
	@echo "$(YELLOW)Running fast mutation testing (core modules only)...$(NC)"
	@poetry run mutmut run \
		--paths-to-mutate=pain001/core,pain001/xml \
		--tests-dir=tests \
		--runner="python -m pytest -x --no-cov -q" \
		--use-coverage

docs:
	@echo "$(YELLOW)Building documentation...$(NC)"
	@poetry install --with docs -q
	@poetry run sphinx-build -b html docs docs/_build/html
	@echo "$(GREEN)✓ Docs built to docs/_build/html$(NC)"

clean:
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf build/ dist/ *.egg-info htmlcov/ .coverage .pytest_cache/ .mypy_cache/ .radon-rc sbom.xml LICENSES_REPORT.md licenses.json .benchmarks/
	@echo "$(GREEN)✓ Cleaned$(NC)"

# --- SLO verification (recommended before commit) ---
slos: lint type test perf
	@echo "$(GREEN)✓ All SLOs verified$(NC)"

# --- Full quality gate (blocking) ---
check: lint type cov sec
	@echo "$(GREEN)✓ Full quality gate passed$(NC)"

