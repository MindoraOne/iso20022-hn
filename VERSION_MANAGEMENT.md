# Version Management System

## Single Source of Truth ✅

This project uses a **single source of truth** for version management to prevent version mismatches across files.

### Version Definition

**Primary Source:** `pain001/__init__.py`

```python
__version__ = "0.0.35"
```

### Automatic Version Distribution

All other files **dynamically reference** the version from `pain001/__init__.py`:

#### 1. **setup.py** (Setuptools Configuration)
```python
# Dynamically reads version from pain001/__init__.py
import re
version_file = (this_directory / "pain001" / "__init__.py").read_text()
version_match = re.search(r'^__version__ = ["\']([^"\']*)["\']', version_file, re.MULTILINE)
version = version_match.group(1)

setup(
    name="pain001",
    version=version,  # Auto-updated from source
    ...
)
```

#### 2. **setup.cfg** (Alternative Configuration)
```ini
[metadata]
name = pain001
version = attr: pain001.__version__
```

Uses setuptools' `attr:` directive to automatically pull version from package attribute.

#### 3. **docs/conf.py** (Sphinx Documentation)
```python
import pain001

release = pain001.__version__  # Auto-updated from source
```

#### 4. **pyproject.toml** (Poetry Configuration)
```toml
[tool.poetry]
version = "0.0.35"
```

**Note:** pyproject.toml is read by Poetry during build. Can be kept as reference or updated via CI/CD.

### Updating Version

**To update to a new version, only change ONE file:**

```bash
# Edit pain001/__init__.py
# Change:
__version__ = "0.0.35"
# To:
__version__ = "0.0.36"
```

**That's it!** All downstream files will automatically reference the new version:
- ✅ `setup.py` will extract the new version
- ✅ `setup.cfg` will use the new version  
- ✅ `docs/conf.py` will import the new version
- ✅ Package imports will return the new version

### Verification

Test that version updates work correctly:

```bash
cd pain001
python3 -c "from pain001 import __version__; print(__version__)"
```

### Why This Approach?

| Approach | Problem | Solution |
|----------|---------|----------|
| **Hardcoded** | Version strings scattered across 5+ files | Single source via import |
| **Manual** | Easy to miss files during update | Automatic referencing |
| **Error-prone** | Mismatches cause version confusion | Dynamic resolution |
| **Unmaintainable** | Each file is an independent version source | Central definition |

### CI/CD Integration

The build system automatically handles version propagation:

1. **Local Development:** Import version from package
2. **Package Build:** Tools read from `pain001/__init__.py` or `pyproject.toml`
3. **Release:** Semantic release tools update `pain001/__init__.py`
4. **Documentation:** Sphinx builds with auto-imported version

### Checking for Version Consistency

Use this script to verify all files are in sync:

```bash
#!/bin/bash
EXPECTED=$(python3 -c "import pain001; print(pain001.__version__)")

echo "Expected version: $EXPECTED"
echo ""
echo "Checking files..."

# Check setup.py can extract it
grep -q "$EXPECTED" pyproject.toml && echo "✓ pyproject.toml"

# Check docs
grep -q "$EXPECTED" README.md && echo "✓ README.md (reference)"
```

### Files to Update for Release

**Release version updates:**
1. ✏️ `pain001/__init__.py` - Update `__version__`
2. ✏️ `pyproject.toml` - Update version (for semantic-release compatibility)
3. ✏️ `CHANGELOG.md` - Add release notes
4. ✏️ `releases/vX.X.X.md` - Create release notes file

**All other files automatically stay in sync:**
- ✅ setup.py
- ✅ setup.cfg
- ✅ docs/conf.py
- ✅ Sphinx builds
- ✅ Package imports

### Benefits

🎯 **Single point of maintenance** - Update version once, propagates everywhere
🎯 **No manual updates** - Eliminates human error in version management
🎯 **Automatic detection** - Any version mismatch is immediately obvious
🎯 **Clean git history** - Fewer files changed per release
🎯 **Standard practice** - Follows Python packaging best practices
