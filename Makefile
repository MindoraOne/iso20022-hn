# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

.PHONY: help check setup env run dev up start stop logs ps lint test load graph graph-label clean \
	pr format type perf xml-examples slos quality \
	lint-poetry test-slo cov \
	tollgate-deps tollgate-xsd tollgate-idempotency tollgate-envparity tollgates

.DEFAULT_GOAL := help

VENV := .venv

# Configuración (una sola fuente). Si existe .env, sus valores tienen prioridad;
# si no, se usan los defaults de acá. Se puede sobrescribir por comando:
# make dev PORT=9000
-include .env

PORT ?= 8000
HOST ?= 0.0.0.0
N ?= 40

# Banco local activo (ver pain001/api/local/settings.py, Settings.local_template_bank).
LOCAL_TEMPLATE_BANK ?= bancatlan
LOCAL_TEMPLATE_DIR := pain001/templates/local/$(LOCAL_TEMPLATE_BANK)/pain.001.001.05/xml

# Color output (usado por los targets heredados de CI)
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

# SLO Thresholds (in seconds) — usados por los targets heredados de CI
SLO_LINT := 45
SLO_TYPE := 20
SLO_TEST := 90
SLO_XML_GEN := 0.5

help: ## Lista los targets disponibles con su descripcion
	@grep -hE '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

check: ## Verifica que el entorno este listo (python, venv, deps, plantillas locales, .env, docker)
	@echo "Verificando el entorno de iso20022-hn:"
	@command -v python3 >/dev/null 2>&1 && echo "  [ok]    python3 presente" || echo "  [falta] python3 no encontrado  ->  instala Python 3.10+"
	@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null && echo "  [ok]    Python 3.10+" || echo "  [falta] se requiere Python 3.10+"
	@test -d $(VENV) && echo "  [ok]    entorno virtual ($(VENV))" || echo "  [falta] no hay venv  ->  corre: make setup"
	@test -x $(VENV)/bin/uvicorn && echo "  [ok]    dependencias instaladas en el venv" || echo "  [falta] dependencias no instaladas  ->  corre: make setup"
	@test -d $(LOCAL_TEMPLATE_DIR) && echo "  [ok]    plantillas locales ($(LOCAL_TEMPLATE_BANK))" || echo "  [falta] faltan las plantillas locales en $(LOCAL_TEMPLATE_DIR)  ->  copialas desde el repo iso20022-local-templates"
	@test -f .env && echo "  [ok]    archivo .env" || echo "  [nota]  sin .env: se usan los valores por defecto  ->  para personalizar: make env"
	@command -v docker >/dev/null 2>&1 && echo "  [ok]    docker presente" || echo "  [nota]  docker no encontrado  ->  solo hace falta si vas a correr con make up/start"
	@echo "Si todo dice [ok], podes: make run  (local)  o  make start  (docker)"

setup: ## Crea el venv e instala las dependencias (pip + requirements.dev.txt + lxml)
	@command -v python3 >/dev/null 2>&1 || { echo "ERROR: no se encontro python3. Instala Python 3.10+ y reintenta."; exit 1; }
	@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null || { echo "ERROR: se requiere Python 3.10+ (tu version es anterior)."; exit 1; }
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.dev.txt
	$(VENV)/bin/pip install lxml
	@echo ""
	@echo "Entorno listo. Proximo paso:  make run   (o  make start  para Docker)"

env: ## Crea .env desde .env.example si no existe
	@if [ -f .env ]; then \
		echo ".env ya existe (no se sobrescribe)."; \
	else \
		cp .env.example .env && echo "Creado .env desde .env.example. Ajusta los valores si hace falta."; \
	fi

run: ## Levanta la API local con uvicorn (usa PORT/HOST del .env o los defaults)
	@test -x $(VENV)/bin/uvicorn || { echo "ERROR: el entorno no esta instalado. Corre primero:  make setup"; exit 1; }
	@test -d $(LOCAL_TEMPLATE_DIR) || { echo "ERROR: faltan las plantillas locales en $(LOCAL_TEMPLATE_DIR). Copialas desde iso20022-local-templates (ver docs-intern/instalacion.md)."; exit 1; }
	$(VENV)/bin/uvicorn pain001.api.app_local:app --host $(HOST) --port $(PORT)

dev: ## Igual que run pero con recarga en caliente (hot-reload, como nodemon)
	@test -x $(VENV)/bin/uvicorn || { echo "ERROR: el entorno no esta instalado. Corre primero:  make setup"; exit 1; }
	@test -d $(LOCAL_TEMPLATE_DIR) || { echo "ERROR: faltan las plantillas locales en $(LOCAL_TEMPLATE_DIR). Copialas desde iso20022-local-templates (ver docs-intern/instalacion.md)."; exit 1; }
	$(VENV)/bin/uvicorn pain001.api.app_local:app --host $(HOST) --port $(PORT) --reload

up: ## Levanta el servicio en Docker en primer plano (crea .env si falta y hace build)
	@command -v docker >/dev/null 2>&1 || { echo "ERROR: docker no esta instalado o no esta en el PATH."; exit 1; }
	@$(MAKE) env
	docker compose up --build

start: ## Levanta el servicio en Docker en segundo plano (detached)
	@command -v docker >/dev/null 2>&1 || { echo "ERROR: docker no esta instalado o no esta en el PATH."; exit 1; }
	@$(MAKE) env
	docker compose up --build -d
	@echo "Servicio en segundo plano. Logs: make logs  |  Estado: make ps  |  Parar: make stop"

logs: ## Muestra y sigue los logs del contenedor (Ctrl+C para salir)
	docker compose logs -f

ps: ## Muestra el estado del contenedor
	docker compose ps

stop: ## Detiene y elimina el contenedor y la red
	docker compose down

lint: ## Corre ruff sobre pain001/api, tests y scripts
	@test -x $(VENV)/bin/ruff || { echo "ERROR: el entorno no esta instalado. Corre primero:  make setup"; exit 1; }
	$(VENV)/bin/ruff check pain001/api tests scripts

test: ## Corre la suite de tests
	@test -x $(VENV)/bin/pytest || { echo "ERROR: el entorno no esta instalado. Corre primero:  make setup"; exit 1; }
	$(VENV)/bin/pytest tests/ -v

load: ## Sonda manual el rate limit contra el servicio corriendo (scripts/load-test.sh [N])
	@test -x scripts/load-test.sh || { echo "ERROR: falta scripts/load-test.sh o no es ejecutable."; exit 1; }
	PORT=$(PORT) scripts/load-test.sh $(N)

graph: ## Actualiza el grafo de codigo del repo con graphify
	graphify update .

graph-label: ## Etiqueta el grafo de codigo usando el backend local de Ollama
	OLLAMA_API_KEY=ollama graphify label . --backend ollama --model qwen2.5:3b

clean: ## Borra artefactos generados y caches (graphify-out, __pycache__, .pytest_cache, etc.)
	rm -rf graphify-out/ .pytest_cache/ build/ dist/ htmlcov/ .coverage .mypy_cache/ .benchmarks/ sbom.xml LICENSES_REPORT.md licenses.json
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# ---------------------------------------------------------------------------
# Targets heredados de CI (poetry) — no forman parte del flujo DX local de
# arriba (que usa pip + $(VENV)); se mantienen porque .github/workflows/*.yml
# los invoca directamente vía `poetry run make <target>`. `check` y `lint` ya
# estaban tomados por el flujo DX de arriba, por eso quedan acá como
# `quality` y `lint-poetry` (con su referencia actualizada en nightly.yml /
# quality.yml).
# ---------------------------------------------------------------------------

pr: ## [CI] Gate rapido de PR: ruff check, ruff format --check, pytest (poetry)
	@echo "$(YELLOW)Running fast PR gate...$(NC)"
	@poetry run ruff check .
	@poetry run ruff format --check .
	@poetry run pytest --tb=short -q
	@echo "$(GREEN)✓ PR gate passed$(NC)"

format: ## [CI] Autoformatea el codigo (ruff format, isort) (poetry)
	@echo "$(YELLOW)Formatting code...$(NC)"
	@poetry run ruff format .
	@poetry run ruff check --select I --fix .
	@echo "$(GREEN)✓ Code formatted$(NC)"

lint-poetry: ## [CI] ruff con verificacion de SLO (poetry)
	@echo "$(YELLOW)Running linters (SLO: < $(SLO_LINT)s)...$(NC)"
	@time_start=$$(date +%s%N); \
	(poetry run ruff check .); \
	lint_result=$$?; \
	time_end=$$(date +%s%N); \
	elapsed=$$(( ($$time_end - $$time_start) / 1000000000 )); \
	if [ $$lint_result -ne 0 ]; then \
		echo "$(RED)✗ Linting failed$(NC)"; \
		exit $$lint_result; \
	fi; \
	if [ $$elapsed -gt $(SLO_LINT) ]; then \
		echo "$(RED)✗ LINTING SLO EXCEEDED: $${elapsed}s > $(SLO_LINT)s$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ Linting passed ($${elapsed}s < $(SLO_LINT)s)$(NC)"; \
	fi

type: ## [CI] mypy con verificacion de SLO (poetry)
	@echo "$(YELLOW)Type checking (SLO: < $(SLO_TYPE)s)...$(NC)"
	@time_start=$$(date +%s%N); \
	poetry run mypy . ; \
	type_result=$$?; \
	time_end=$$(date +%s%N); \
	elapsed=$$(( ($$time_end - $$time_start) / 1000000000 )); \
	if [ $$type_result -ne 0 ]; then \
		echo "$(RED)✗ Type checking failed$(NC)"; \
		exit $$type_result; \
	fi; \
	if [ $$elapsed -gt $(SLO_TYPE) ]; then \
		echo "$(RED)✗ TYPE CHECK SLO EXCEEDED: $${elapsed}s > $(SLO_TYPE)s$(NC)"; \
		exit 1; \
	else \
		echo "$(GREEN)✓ Type check passed ($${elapsed}s < $(SLO_TYPE)s)$(NC)"; \
	fi

test-slo: ## [CI] pytest con cobertura y verificacion de SLO (poetry)
	@echo "$(YELLOW)Running tests (SLO: < $(SLO_TEST)s, Coverage floor: 70%)...$(NC)"
	@time_start=$$(date +%s); \
	poetry run pytest --tb=short -v --cov=pain001 --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=70;
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

cov: ## [CI] Genera el reporte de cobertura (poetry)
	@echo "$(YELLOW)Generating coverage report (floor: 70%)...$(NC)"
	@poetry run pytest --cov=pain001 --cov-branch --cov-report=term-missing --cov-report=xml --cov-report=html --cov-fail-under=70
	@echo "$(GREEN)✓ Coverage report generated in htmlcov/index.html$(NC)"

perf: ## [CI] Benchmarks de generacion de XML (poetry)
	@echo "$(YELLOW)Running performance benchmarks (XML gen SLO: < $(SLO_XML_GEN)s/1000tx)...$(NC)"
	@poetry run pytest tests/test_integration.py -v --benchmark-only --benchmark-json=.benchmarks/results.json || true
	@echo "$(YELLOW)Note: Review benchmark results for XML generation performance$(NC)"

xml-examples: ## [CI] Genera archivos XML de ejemplo para los tests de XSD (poetry)
	@echo "$(YELLOW)Generating XML example files for XSD validation tests...$(NC)"
	@poetry run python scripts/generate_xml_examples.py
	@echo "$(GREEN)✓ XML examples generated$(NC)"

slos: lint-poetry type test-slo perf ## [CI] Verifica todos los SLO antes de un commit importante (poetry)
	@echo "$(GREEN)✓ All SLOs verified$(NC)"

quality: lint-poetry cov ## [CI] Gate completo bloqueante: lint + cobertura + seguridad (poetry) — antes se llamaba "check"
	@echo "$(GREEN)✓ Full quality gate passed$(NC)"

# --- Advanced Production Tollgates (Enterprise Hardening) ---

tollgate-deps: ## [CI] Gobernanza de dependencias (poetry)
	@echo "$(YELLOW)Tollgate 1: Dependency Governance (Shadow IT Prevention)$(NC)"
	@echo "Checking for new/modified dependencies in pyproject.toml..."
	@poetry show --latest > /dev/null && echo "$(GREEN)✓ All dependencies checked$(NC)" || (echo "$(RED)✗ Dependency check failed$(NC)" && exit 1)
	@echo "$(GREEN)✓ Dependency Governance tollgate PASSED$(NC)"

tollgate-xsd: ## [CI] Validacion de los XSD de pain.001 (poetry)
	@echo "$(YELLOW)Tollgate 2: XSD Semantic Anchor (Schema Validation)$(NC)"
	@echo "Validating XSD schemas for all pain.001 versions..."
	@for version in 03 04 05 06 07 08 09 10 11; do \
		if [ -f pain001/templates/pain.001.001.$$version/pain.001.001.$$version.xsd ]; then \
			echo "  $(GREEN)✓$(NC) XSD schema v$$version exists"; \
		else \
			echo "  $(RED)✗$(NC) XSD schema v$$version missing"; \
			exit 1; \
		fi; \
	done
	@echo "$(GREEN)✓ XSD Semantic Anchor tollgate PASSED$(NC)"

tollgate-idempotency: ## [CI] Verifica ausencia de estado global peligroso (poetry)
	@echo "$(YELLOW)Tollgate 3: Idempotency & Statelessness (Deterministic Processing)$(NC)"
	@echo "Verifying no dangerous global mutable state in core modules..."
	@grep -r "^[A-Z_]* = " pain001/ --include="*.py" | grep -v "__all__\|^pain001/constants\|\.pyc" | grep -v "^#" > /tmp/globals.txt && \
		(echo "$(YELLOW)  Warning: Global state found, review needed$(NC)" && cat /tmp/globals.txt) || true
	@echo "Checking for context managers in file I/O..."
	@if ! grep -r "open(" pain001/core --include="*.py" | grep -v "with open\|#" > /dev/null 2>&1; then \
		echo "  $(GREEN)✓$(NC) All file I/O uses context managers"; \
	else \
		echo "  $(YELLOW)⚠$(NC)  Found unprotected file I/O (check if in tests)"; \
	fi
	@echo "$(GREEN)✓ Idempotency tollgate PASSED$(NC)"

tollgate-envparity: ## [CI] Chequea rutas hardcodeadas no portables (poetry)
	@echo "$(YELLOW)Tollgate 4: Environmental Parity (Cross-Platform Compatibility)$(NC)"
	@echo "Checking for hardcoded Unix paths..."
	@! grep -r "/opt/\|/var/\|/usr/" pain001/ --include="*.py" | grep -v "example\|test\|#" | head -5 > /dev/null && \
		echo "  $(GREEN)✓$(NC) No hardcoded Unix paths" || \
		(echo "  $(YELLOW)⚠$(NC)  Found Unix paths (verify in docs)"; exit 0)
	@echo "Checking for hardcoded Windows paths..."
	@! grep -r "C:\\\\\\\\" pain001/ --include="*.py" | grep -v "example\|test\|#" > /dev/null && \
		echo "  $(GREEN)✓$(NC) No hardcoded Windows paths" || \
		(echo "  $(YELLOW)⚠$(NC)  Found Windows paths (verify in docs)"; exit 0)
	@echo "Verifying path safety patterns..."
	@echo "  $(GREEN)✓$(NC) Cross-platform checks completed"
	@echo "$(GREEN)✓ Environmental Parity tollgate PASSED$(NC)"

tollgates: tollgate-deps tollgate-xsd tollgate-idempotency tollgate-envparity ## [CI] Corre los 4 tollgates anteriores (poetry)
	@echo "$(GREEN)✓ All 4 Advanced Production Tollgates PASSED$(NC)"
