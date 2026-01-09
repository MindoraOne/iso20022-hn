# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.28] - 2026-01-09

### Security

- **Critical: Fixed urllib3 decompression bomb vulnerability** - Updated urllib3 from 2.6.0 to 2.6.3 to fix CVE-2026-21441 (CVSS 8.9 High) where decompression-bomb safeguards were bypassed when HTTP redirects were followed
- **Critical: Fixed Jinja2 sandbox escape vulnerabilities** - Updated jinja2 from 3.1.4 to 3.1.6 to fix multiple security issues:
  - GHSA-cpwx-vrp4-4pq7: The `|attr` filter no longer bypasses the environment's attribute lookup
  - GHSA-q2x7-8rv6-6q7h: Sandboxed environment properly handles indirect calls to `str.format`
  - GHSA-gmj6-6f8f-6699: Template names are properly escaped before formatting into error messages
- **Updated setuptools** - Updated from 70.0.0 to 78.1.1 with security fixes and stability improvements

### Changed

- **GitHub Actions workflow** - Updated pypa/gh-action-pypi-publish from 1.3.1 to 1.13.0 with security fixes (GHSA-vxmw-7h4f-hqxh)
- **CI/CD process** - Removed automatic PyPI publishing and GitHub release creation from CI to prevent conflicts with manual release processes
- **Project organization** - Moved release notes to `releases/` folder with simplified naming (v0.0.26.md, v0.0.27.md)

## [0.0.27] - 2026-01-09

### Fixed

- **Package installation issue** - Added missing `__init__.py` files to all package directories (Fixes #58, #56)
  - Added `__init__.py` to `pain001/xml/` - XML generation and validation module
  - Added `__init__.py` to `pain001/db/` - Database operations module
  - Added `__init__.py` to `pain001/csv/` - CSV operations module
  - Added `__init__.py` to `pain001/cli/` - Command-line interface module
  - Added `__init__.py` to `pain001/templates/` - ISO 20022 templates
  - Added `__init__.py` to all template subdirectories (pain.001.001.03 through pain.001.001.09)
- **Import errors resolved** - All submodules now correctly importable after pip installation
- **Distribution completeness** - Package installation via pip now includes all necessary modules

## [0.0.26] - 2026-01-09

### Security

- **Fixed XML parsing vulnerabilities (XXE attacks)** - Replaced unsafe `xml.etree.ElementTree` with `defusedxml.ElementTree` in all XML creation and validation modules to protect against XML External Entity attacks, XML bomb attacks, and other XML-based vulnerabilities
- **Enhanced SQL injection protection** - Improved SQL query safety in database operations with proper identifier handling and documentation
- **Updated requests library** - Updated from 2.32.0 (yanked) to 2.32.5 to fix CVE-2024-35195

### Added

- **Development tools** - Added comprehensive development dependencies for code quality and security:
  - `black` ^24.0.0 - Code formatter
  - `flake8` ^7.0.0 - Style checker
  - `isort` ^5.13.0 - Import sorter
  - `mypy` ^1.11.0 - Static type checker
  - `pylint` ^3.2.0 - Code quality analyzer
  - `bandit` ^1.7.0 - Security vulnerability scanner
  - `safety` ^3.0.0 - Dependency security checker
- **Security annotations** - Added inline security documentation and `# nosec` comments where appropriate
- **Development section in README** - Added comprehensive development setup and code quality tools documentation

### Changed

- **Import organization** - Fixed import ordering in 23 files to comply with PEP 8 and Black standards
- **XML parsing implementation** - All XML parsing now uses secure `defusedxml` library
- **SQL query construction** - Enhanced with bracket notation for safer SQL identifiers
- **README.md** - Enhanced Features section to highlight security measures and development tools

### Fixed

- **Import ordering inconsistencies** - All imports now follow consistent style across entire codebase
- **Code formatting issues** - All code now passes Black formatting checks
- **Yanked dependency** - Updated requests from yanked version 2.32.0 to stable 2.32.5

## [0.0.25] - Previous Release

*(Previous release notes not included in this changelog)*

---

For more detailed release notes, see individual release note files: `RELEASE_NOTES_v*.md`
