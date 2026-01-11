# Pain001 Copilot Instructions

## Project Overview

**Pain001** is a production-grade Python library for generating ISO 20022-compliant payment initiation files (pain.001) from CSV, SQLite, or direct Python data sources. Supports 9 versions of the ISO standard (v03 through v11) with 98.57% test coverage (341 tests).

## Architecture & Data Flow

### Core Orchestration (`pain001/core/core.py`)
- **Entry point**: `process_files()` function orchestrates the entire workflow
- Validates XML message type against `valid_xml_types` in constants
- Coordinates data loading, XML generation, and XSD validation
- Uses structured JSON logging with context-based logger instances
- **TODO**: Comments indicate intent to split orchestration into smaller helpers

### Data Pipeline (`pain001/data/loader.py`)
The library supports **three input methods** (backward compatible):
1. **File paths** (str): CSV `.csv` or SQLite `.db` files
2. **Python list**: List of payment dictionaries
3. **Python dict**: Single transaction (wrapped as list internally)

Each source route:
- CSV → `load_csv_data()` + `validate_csv_data()`
- DB → `load_db_data()` + `validate_db_data()`
- Python → Direct validation, no file I/O

### XML Generation (`pain001/xml/`)
Version-specific preparation functions (`_prepare_xml_data_v03()` through `_prepare_xml_data_v11()`):
- Extract header data from `data[0]` (common fields: id, date, initiator_name, etc.)
- Transform transaction data into `transactions` array for Jinja2 templating
- Each version has unique field sets and structures
- Jinja2 renders from `xml_template_file_path` → validates against XSD → writes output

**Key directories**:
- `create_xml_v*.py`: Version-specific XML element creation
- `validate_via_xsd()`: Validates generated XML against ISO 20022 schema
- `generate_xml()`: Orchestrates rendering and validation

## Development Workflow (PySentinel Standards)

### Strict Quality Gates (Non-Negotiable)
- **Poetry-only execution**: All commands must run via `poetry run`. No bare `python` or `pip` commands in CI/CD.
- **Coverage**: 100% branch coverage for modified code; total project coverage must not decrease (95% minimum enforced).
- **Typing**: Mandatory precise type hints; use `Protocol`, `TypeGuard`, `Generics` to avoid `Any`. `mypy` must pass without errors.
- **No gate weakening**: Never bypass linting, suppress type errors, or use bare `except:` blocks.

### Quick PR Gate (Recommended)
```bash
make pr  # Runs: ruff check, black check, isort check, mypy, pytest
```

### Local Development
```bash
make format    # Auto-format with ruff, isort, black
make lint      # Full linting (ruff, flake8, pylint)
make type      # mypy type checking (must exit 0)
make test      # pytest with 95% coverage requirement
make cov       # Coverage report (HTML/XML/terminal)
make sec       # Security checks (bandit + safety)
make check     # Full quality gate (lint + type + cov + sec)
```

### Test Structure
- **95% coverage required** (enforced via `pytest.ini_options` in `pyproject.toml`)
- Tests organized by module: `test_csv_loader.py`, `test_xml_generation.py`, `test_xsd_validator.py`, etc.
- Version-specific tests: `test_pain001_v03.py` through `test_pain001_v11.py` (9 total)
- Integration tests: `test_integration.py` for end-to-end workflows
- **pytest fixture pattern**: Tests use direct Python data structures, not file-based

## CLI Configuration & Security

### ConfigParser Usage (`pain001/cli/cli.py`)
CLI supports optional configuration file via `--config_file` parameter using Python's `configparser.ConfigParser`:
```ini
[Paths]
xml_template_file_path = /path/to/template.xml
xsd_schema_file_path = /path/to/schema.xsd
data_file_path = /path/to/data.csv
```

**Behavior**: CLI command-line arguments take precedence over config file values; config provides defaults only.

### Security Hardening (PySentinel-Grade)

**1. Interpolation Injection Prevention**
- **Current implementation uses `BasicConfigParser`** (no interpolation enabled) → prevents `${env:SECRET_KEY}` style attacks
- **Requirement**: Never enable `ExtendedInterpolation` or `BasicInterpolation` in ConfigParser without sanitizing untrusted config sources
- Risk: Attacker-controlled config could leak environment variables or reference sensitive configuration sections

**2. Denial of Service (DoS) via Circular References**
- While less critical than YAML/XML, avoid recursive config includes or deeply nested interpolation chains
- Keep config structure flat; validate config file size (e.g., max 1MB) before parsing
- **Mitigation**: ConfigParser's default behavior doesn't support includes, which prevents recursive loops

**3. Credential Exposure in Config Files**
- Configuration files may contain DB connection strings, API keys, or file paths to sensitive payment data
- **Enterprise Requirement**: Document and enforce `chmod 600` on production config files
- **Never commit** `.config`, `.env`, or `*.conf` files with real credentials to version control
- Use environment variables for secrets: `os.getenv("TEMPLATE_PATH")` rather than hardcoding in config
- **Code requirement**: When creating config files programmatically, set permissions explicitly:
  ```python
  os.chmod(config_path, 0o600)  # Owner read/write only
  ```

**4. File Permissions Audit**
Before reading config in automated pipelines:
```bash
# Validate permissions are restrictive (owner read/write only)
stat -c "%a %n" config.ini  # Should show "600"
```

**5. Validation-First Parsing**
- All CLI inputs and config values must be validated against schema or `pydantic`/`dataclass` equivalents
- Use `click.Choice()` for enums, `click.Path(exists=True)` for file validation
- Reject invalid config early with descriptive error messages

### Path Handling & Safety
- CLI expands `~` and `~user` via `os.path.expanduser()` for user-friendly paths
- All file paths validated with `os.path.isfile()` before processing
- Missing files exit gracefully with descriptive error messages (no silent failures)
- **Permission awareness**: When creating sensitive files (configs, keys), set `0o600` permissions immediately
- Always use absolute paths in production; document CWD assumptions

## Jinja2 Templates & XSD Schemas

### Template Structure (PySentinel Security)
Templates use **Jinja2 syntax** with ISO 20022 XML namespace definitions:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:pain.001.001.03">
    <CstmrCdtTrfInitn>
        <GrpHdr>
            <MsgId>{{id}}</MsgId>
            <CreDtTm>{{date}}</CreDtTm>
            <!-- ... -->
        </GrpHdr>
        <PmtInf>
            <!-- Header fields from data[0] -->
            {% for tx in transactions %}
                <CdtTrfTxInf>
                    <!-- Transaction fields from tx -->
                </CdtTrfTxInf>
            {% endfor %}
        </PmtInf>
    </CstmrCdtTrfInitn>
</Document>
```

**Key Points**:
- **No template inheritance** currently used; each version has standalone template
- **Line 1-2**: XML declaration and namespace URI matching version number (e.g., `pain.001.001.03`)
- **Loop variable**: `{% for tx in transactions %}` iterates prepared transaction data
- **Field mapping**: Template field names (e.g., `{{id}}`, `{{tx.payment_amount}}`) must match keys in `_prepare_xml_data_vXX()` output dict
- **Security requirement**: Always use `autoescape=True` in Jinja2 environment to prevent template injection:
  ```python
  env = Environment(loader=FileSystemLoader("."), autoescape=True)
  ```
- **Data sanitization**: Never pass untrusted user input directly to templates; validate and normalize in `_prepare_xml_data_vXX()` first

### XSD Schema Validation (XXE Prevention)
XSD files define ISO 20022 message structures with strict validation:
- **Type restrictions**: IBAN patterns, BIC codes (e.g., `[A-Z]{6,6}[A-Z2-9][A-NP-Z0-9]...`)
- **Numeric constraints**: Decimal fractions (e.g., `<fractionDigits value="2">` for currency amounts)
- **Enumeration values**: Restricted code sets (e.g., `ADDR`, `PBOX`, `HOME` for address types)

**Python-to-XSD Type Mapping**:
- Python `str` → XSD `Max35Text`, `Max128Text` (string length constraints)
- Python `Decimal` → XSD `ActiveOrHistoricCurrencyAndAmount_SimpleType` (2-5 decimal places)
- Python `date`/`datetime` → XSD `ISODate`/`ISODateTime` (ISO 8601 format required)
- Python `bool` → XSD `BatchBookingIndicator` (true/false only)

**XXE Prevention**: All XML parsing MUST use `defusedxml` to prevent entity expansion attacks:
```python
from defusedxml import ElementTree as DefusedET
tree = DefusedET.parse(xml_file)  # Not ElementTree.parse()
```
Never use `xml.etree.ElementTree` directly; it is vulnerable to XXE attacks.

**Critical**: Always validate data against XSD after XML generation via `validate_via_xsd()`. Schema mismatches (missing required fields, type violations) must be caught before sending to payment networks.

### Template Loading Nuance
```python
from jinja2 import Environment, FileSystemLoader
env = Environment(FileSystemLoader("."))
template = env.get_template("pain001/templates/pain.001.001.03/template.xml")
```

**Important**: `FileSystemLoader(".")` loads templates relative to **current working directory**. In production, ensure CWD is set correctly or use **absolute paths** with `FileSystemLoader("/absolute/path")`.

## Code Conventions & Patterns (PySentinel Grade)

### Logging
- Use `Context.get_instance().get_logger()` for application-level context (structured logging)
- Use module-level `logger = logging.getLogger(__name__)` for debug logs (allowed, not required)
- Log events as structured JSON: `logger.info(json.dumps({"event": "...", "data": ...}))`
- Log errors before raising exceptions for traceable audit trails
- **Never log secrets or sensitive payment data**; filter PII from all output

### Type Hints (Mandatory, No `Any`)
- **Strict requirement**: Full type hints on all function signatures
- Union types preferred over Optional: `Union[str, list[dict]]` not `Optional[List[Dict]]`
- Generic collections use Python 3.9+ syntax: `list[dict[str, Any]]` not `List[Dict[str, Any]]`
- Use `Protocol` for structural typing instead of loose duck-typing
- Use `TypeGuard` for type narrowing in validators
- **Avoid `Any` at all costs**: If you must, document why and use `# type: ignore[...]` with specific error codes
- mypy must pass: `poetry run mypy .` (exit 0, no errors or warnings)

### Resource Safety (Context Managers)
- **All I/O operations must use context managers** (`with` statements)
- Never rely on garbage collection for file/stream cleanup:
  ```python
  # GOOD
  with open(config_path, 'r', encoding='utf-8') as f:
      data = f.read()
  
  # BAD (implicit close on GC)
  f = open(config_path)
  data = f.read()
  ```
- All text I/O must specify `encoding="utf-8"` explicitly

### File Paths & Permissions
- Use `os.path.exists()` to validate paths before processing
- Raise `FileNotFoundError` with descriptive message including the path
- Support relative and absolute paths via `os.path.expanduser()`
- **Permission awareness**: When creating sensitive files (configs, keys), set `0o600` permissions immediately
- Always use absolute paths in production; document CWD assumptions

### Data Validation (Schema-Driven)
- CSV and DB data validated **before** XML generation via dedicated validators
- Validation functions return normalized list of dicts
- Invalid data raises `ValueError` with specific validation messages
- **No silent failures**: All exceptions must be caught, logged, and re-raised with context
- Avoid bare `except:` blocks; specify exception types (e.g., `except ValueError as e:`)
- Use schema validation (pydantic/dataclass equivalent) to enforce structure before processing

### Version Management
**Single source of truth**: `pain001/__init__.py` (`__version__ = "X.Y.Z"`)
- `setup.py` uses regex to extract version
- `setup.cfg` uses `attr: pain001.__version__` (setuptools dynamic attribute)
- `pyproject.toml` must be updated manually by Poetry (read-only by CI)
- Docs pull from `import pain001; release = pain001.__version__`

## Project-Specific Conventions

### XML Message Types
Valid types defined in `pain001/constants/constants.py`:
```python
valid_xml_types = ["pain.001.001.03", ..., "pain.001.001.11"]
```
Always validate user input against this list before processing.

### Payment Data Fields
**Header fields** (from `data[0]`): id, date, nb_of_txs, initiator_name, debtor_name, debtor_account_IBAN, etc.
**Transaction fields** (repeated per record): payment_id, payment_amount, creditor_name, creditor_account_IBAN, etc.
Field sets vary by version—check `_prepare_xml_data_vXX()` functions for version-specific requirements.

## GitHub Actions CI/CD Pipeline

### Workflow Files
- `ci.yml`: Runs on push/PR to main; pytest, flake8, version extraction, PyPI publish
- `security.yml`: Daily scheduled + on push; bandit, safety, license scanning
- `release.yml`: Triggered by `v*` tags; builds and publishes to PyPI
- `pr.yml`: Pre-submit checks on pull requests
- `quality.yml`: Code quality gates
- `docs.yml`: Documentation build and deployment
- `nightly.yml`: Extended testing (if exists)

### PyPI Publishing Security

**Current implementation** (`.github/workflows/release.yml`):
```yaml
- name: Publish to PyPI
  env:
    TWINE_USERNAME: __token__
    TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
  run: twine upload dist/*
```

**Security Status**: Using repository secret `PYPI_API_TOKEN` (hardcoded token approach).

**Recommended Upgrade to OIDC Trusted Publishing**:
Replace hardcoded token with OIDC trust relationship (no exposed API tokens):
```yaml
permissions:
  id-token: write
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@release/v1
```

**Benefits**:
- No API token in GitHub secrets (zero credential exposure)
- Token generated dynamically per publish with 5-minute lifetime
- Audit trail via OpenID Connect logs on PyPI
- Prevents token theft/rotation burden

### Action Pinning for Supply Chain Security
- **Current**: `actions/checkout@v4`, `actions/setup-python@v5` (floating tags)
- **Recommended**: Pin to commit SHA for immutability and protection against tag manipulation
  ```yaml
  - uses: actions/checkout@b4ff0907add4405f2b5017906e825022a20bd5f5  # v4.1.1
  - uses: actions/setup-python@61a6322f88396a6271a6ee3cb807b44d28e7f64c  # v5.0.0
  ```
- **Rationale**: Prevents `v4` tag from being reassigned to malicious commits after action updates
- **CI/CD Alignment Rule**: Do not modify `.github/workflows/` or XSD schemas without explicit approval; these are infrastructure gates

### Manual Approval Gates
- No manual approval gates currently configured
- **Future consideration**: For production release workflows, add `environment: production` with approval requirement:
  ```yaml
  - name: Publish to PyPI
    environment: production
    uses: pypa/gh-action-pypi-publish@release/v1
  ```

### Version Synchronization Rule
- **Enforce across CI/CD**: Any version bump in `pyproject.toml` must be synchronized with `setup.py`, `setup.cfg`, `README.md`, and `CHANGELOG.md`
- CI should verify version consistency; fail builds if mismatch detected
- Use single-source-of-truth pattern: `pain001/__init__.py` → auto-propagate to other files

## Prohibited Actions (Red Lines)
- **Gate Weakening**: Never bypass quality gates, suppress lint/type errors, or use `# type: ignore` without specific error codes
- **Insecure Defaults**: Never use `verify=False` in requests, disable XXE protection, or allow unvalidated input
- **Dependency Bloat**: No new dependencies without strong justification and security review
- **Global State**: No mutable module-level state or singletons beyond `Context`
- **Silent Failures**: No bare `except:` blocks; all I/O must use context managers

## Common Tasks for AI Agents

### Adding Support for New XML Version (PySentinel Process)
1. Create `pain001/xml/create_xml_vXX.py` with XML element creation + full type hints
2. Add `_prepare_xml_data_vXX()` function in `generate_xml.py` with schema validation
3. Add version string to `valid_xml_types` in constants
4. Create version-specific template in `pain001/templates/pain.001.001.XX/template.xml` (verify `autoescape=True` in generator)
5. Add version-specific XSD schema in `pain001/templates/pain.001.001.XX/pain.001.001.XX.xsd`
6. Create `tests/test_pain001_vXX.py` with **100% branch coverage of new code**
7. Run `poetry run make check` and verify all gates pass (exit 0)
8. Verify total project coverage does not decrease below 95%

### Implementing New Data Source (PySentinel Process)
1. Create loader in `pain001/[source]/load_[source]_data.py` with full type hints (no `Any`)
2. Create validator in `pain001/[source]/validate_[source]_data.py` with schema-driven validation
3. Add import + conditional branch in `load_payment_data()` with type guards
4. Update tests to cover new source type with **100% branch coverage**
5. Update docstrings with new example usage and type hints
6. Run `poetry run make check` and verify all gates pass (exit 0)
7. Verify new code handles exceptions explicitly (no silent failures)

### Debugging XML Generation Issues
1. Check `_prepare_xml_data_vXX()` for correct field mapping from data dict
2. Verify template file exists and has correct Jinja2 syntax (no unclosed tags)
3. Verify `autoescape=True` in Jinja2 environment to prevent injection
4. Check XSD validation output for specific field errors (type mismatches, missing required fields)
5. Inspect structured JSON logs for orchestration flow
6. Validate Jinja2 rendering separately: `env.get_template(path).render(context_dict)` (test with malicious input)
7. Confirm XXE protection: all XML parsing uses `defusedxml`, not `ElementTree`

---

**Updated**: January 2026  
**Coverage**: 95% (341 tests, 98.57% actual)  
**Python**: 3.9+  
**License**: Apache 2.0
