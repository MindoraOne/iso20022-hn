## Release v0.0.27 - 2026-01-09
# Pain001: Automate ISO 20022-Compliant Payment File Creation

![Pain001 banner][banner]

## Overview

**Pain001** is an open-source Python Library that you can use to create
**ISO 20022-Compliant Payment Files** directly from your **CSV** or **SQLite**
Data Files.

- **Website:** <https://pain001.com>
- **Source code:** <https://github.com/sebastienrousseau/pain001>
- **Bug reports:** <https://github.com/sebastienrousseau/pain001/issues>

This release fixes a critical packaging issue that prevented proper installation via pip. All submodules are now correctly recognized as Python packages.

## 🐛 Bug Fixes

### Package Installation Fix (Issues #58, #56)

**Problem:** When installing pain001 via pip, several subdirectories were not being installed, causing import errors. Users reported that modules like `csv`, `db`, `xml`, `cli`, and `templates` were missing from the installation.

**Root Cause:** Python's packaging tools (pip/setuptools) require `__init__.py` files in all directories to recognize them as packages and include them in the distribution.

**Solution:** Added `__init__.py` files to all package directories:
- `pain001/xml/__init__.py` - XML generation and validation module
- `pain001/db/__init__.py` - Database operations module
- `pain001/csv/__init__.py` - CSV operations module
- `pain001/cli/__init__.py` - Command-line interface module
- `pain001/templates/__init__.py` - ISO 20022 templates
- `pain001/templates/pain.001.001.03/__init__.py`
- `pain001/templates/pain.001.001.04/__init__.py`
- `pain001/templates/pain.001.001.05/__init__.py`
- `pain001/templates/pain.001.001.06/__init__.py`
- `pain001/templates/pain.001.001.07/__init__.py`
- `pain001/templates/pain.001.001.08/__init__.py`
- `pain001/templates/pain.001.001.09/__init__.py`

**Impact:** Users can now successfully install pain001 via pip and all modules will be available for import without manual intervention.

## 🧪 Testing

- ✅ All 71 tests passing
- ✅ 100% test coverage maintained
- ✅ No regression issues
- ✅ Verified package structure after pip installation

## 🔄 Breaking Changes

**None** - This release is fully backward compatible with v0.0.26.

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

### Fixed
- Added missing `__init__.py` files to all package directories (Fixes #58, #56)
- Package installation now correctly includes all submodules when installing via pip
- Resolved import errors for `pain001.csv`, `pain001.db`, `pain001.xml`, `pain001.cli`, and `pain001.templates`

## Related Issues

- Closes #58 - Not all files are installed when installing 0.0.25 with pip
- Closes #56 - Issues 36 and 44 still persist in 0.0.25
- Related to #46 - Previous packaging issue
- Related to #44 - Import errors in earlier versions
- Related to #36 - Missing directories in pip installation

## Artifacts 🎁
* [pain001-0.0.27-py2.py3-none-any.whl](https://github.com/sebastienrousseau/pain001/releases/download/v0.0.27/pain001-0.0.27-py2.py3-none-any.whl)
* [pain001-0.0.27.tar.gz](https://github.com/sebastienrousseau/pain001/releases/download/v0.0.27/pain001-0.0.27.tar.gz)

[banner]: https://kura.pro/pain001/images/banners/banner-pain001.svg 'Pain001, A Python Library for Automating ISO 20022-Compliant Payment Files Using CSV Or SQLite Data Files.'
