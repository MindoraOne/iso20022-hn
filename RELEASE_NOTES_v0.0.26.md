# Release Notes - Pain001 v0.0.26

**Release Date:** January 9, 2026

## 🎉 Overview

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

## 🚀 Migration Guide

No migration steps required. Simply update to v0.0.26:

```bash
pip install --upgrade pain001
```

or with Poetry:

```bash
poetry update pain001
```

## 🙏 Acknowledgements

Special thanks to the security tools and libraries that made this release possible:
- [defusedxml](https://github.com/tiran/defusedxml) for secure XML parsing
- [Bandit](https://github.com/PyCQA/bandit) for security analysis
- [Safety](https://github.com/pyupio/safety) for dependency scanning

## 📋 Full Changelog

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

---

**Full Diff**: [v0.0.25...v0.0.26](https://github.com/sebastienrousseau/pain001/compare/v0.0.25...v0.0.26)

For detailed information about Pain001, visit:
- **Website**: https://pain001.com
- **Documentation**: https://github.com/sebastienrousseau/pain001
- **Issue Tracker**: https://github.com/sebastienrousseau/pain001/issues
