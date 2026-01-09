## Release v0.0.26 - 2026-01-09
# Pain001: Automate ISO 20022-Compliant Payment File Creation

![Pain001 banner][banner]

## Overview

**Pain001** is an open-source Python Library that you can use to create
**ISO 20022-Compliant Payment Files** directly from your **CSV** or **SQLite**
Data Files.

- **Website:** <https://pain001.com>
- **Source code:** <https://github.com/sebastienrousseau/pain001>
- **Bug reports:** <https://github.com/sebastienrousseau/pain001/issues>

This release focuses on **security hardening**, **dependency updates**, and **code quality improvements**. All critical security vulnerabilities identified by Bandit have been resolved, and the codebase now follows enhanced security best practices.

## 🔒 Security Fixes

### Critical Security Improvements

1. **XML External Entity (XXE) Protection**
   - Replaced unsafe `xml.etree.ElementTree` parsing with `defusedxml.ElementTree`
   - Protects against XML bomb attacks, external entity expansion, and other XML-based vulnerabilities
   - Affected files:
     - `pain001/xml/create_xml_v3.py`
     - `pain001/xml/create_xml_v4.py`
     - `pain001/xml/create_xml_v5.py`
     - `pain001/xml/create_xml_v6.py`
     - `pain001/xml/create_xml_v7.py`
     - `pain001/xml/create_xml_v8.py`
     - `pain001/xml/create_xml_v9.py`
     - `pain001/xml/validate_via_xsd.py`

2. **SQL Injection Mitigation**
   - Enhanced SQL query safety in `pain001/db/load_db_data.py`
   - Added bracket notation for SQL identifiers
   - Documented security considerations with inline comments

3. **CVE-2024-35195 Resolution**
   - Updated `requests` from 2.32.0 (yanked version) to 2.32.5
   - Eliminates security vulnerability related to proxy authentication

## 📦 Dependency Updates

### Updated Dependencies

- **requests**: `2.32.0` → `2.32.5` (fixes CVE-2024-35195)

### New Development Dependencies

Added comprehensive development tools for code quality and security:

- **black** `^24.0.0` - Code formatter
- **flake8** `^7.0.0` - Style checker
- **isort** `^5.13.0` - Import sorter
- **mypy** `^1.11.0` - Static type checker
- **pylint** `^3.2.0` - Code quality analyzer
- **bandit** `^1.7.0` - Security vulnerability scanner
- **safety** `^3.0.0` - Dependency security checker

## ✨ Code Quality Improvements

### Import Organization
- Fixed import ordering in 23 files to comply with PEP 8 and Black standards
- Consistent import style across entire codebase

### Code Formatting
- All code now passes Black formatting checks
- Enhanced readability and maintainability

### Type Safety
- Improved type annotations support with mypy configuration

## 🧪 Testing

- ✅ All 71 tests passing
- ✅ 100% test coverage maintained
- ✅ No regression issues

## 🔍 Quality Metrics

### Security Scan Results
- **Bandit**: 0 medium/high severity issues (12 low-severity informational warnings only)
- **Safety**: Dependencies updated to eliminate known vulnerabilities

### Code Style
- **Black**: All files compliant
- **Flake8**: No violations
- **Isort**: All imports properly organized
- **Pylint**: Code quality score maintained

## 📝 Documentation

- Updated development dependencies in `pyproject.toml`
- Enhanced security documentation with inline comments
- Maintained backward compatibility

## 🔄 Breaking Changes

**None** - This release is fully backward compatible with v0.0.25.

## Requirements

**Pain001** works with macOS, Linux and Windows and requires Python 3.9.0 and
above.

## Installation

We recommend creating a virtual environment to install **Pain001**. This will ensure that the package is installed in an isolated environment and will not affect other projects. To install **Pain001** in a virtual environment, follow these steps:

### Install `virtualenv`

```sh
python -m pip install virtualenv
```

### Create a Virtual Environment

```sh
python -m venv venv
```

| Code | Explanation |
|---|---|
| `-m` | executes module `venv` |
| `env` | name of the virtual environment |

### Activate environment

```sh
source venv/bin/activate
```

### Getting Started

It takes just a few seconds to get up and running with **Pain001**. You can install Pain001 from PyPI with pip or your favourite package manager:

Open your terminal and run the following command to add the latest version:

```sh
python -m pip install pain001
```

Add the -U switch to update to the current version, if `pain001` is already installed.

```sh
python -m pip install -U pain001
```

## Changelog

### Security
- Fixed XML parsing vulnerabilities (XXE attacks) in all XML creation modules
- Enhanced SQL query safety with proper identifier handling
- Updated requests library to fix CVE-2024-35195

### Added
- Development tools: black, flake8, isort, mypy, pylint, bandit, safety
- Security annotations and documentation

### Changed
- Import organization across 23 files
- XML parsing to use defusedxml for security
- SQL query construction for better safety

### Fixed
- Import ordering inconsistencies
- Code formatting issues
- Yanked dependency (requests 2.32.0)

## Artifacts 🎁
* [pain001-0.0.26-py2.py3-none-any.whl](https://github.com/sebastienrousseau/pain001/releases/download/v0.0.26/pain001-0.0.26-py2.py3-none-any.whl)
* [pain001-0.0.26.tar.gz](https://github.com/sebastienrousseau/pain001/releases/download/v0.0.26/pain001-0.0.26.tar.gz)

[banner]: https://kura.pro/pain001/images/banners/banner-pain001.svg 'Pain001, A Python Library for Automating ISO 20022-Compliant Payment Files Using CSV Or SQLite Data Files.'
