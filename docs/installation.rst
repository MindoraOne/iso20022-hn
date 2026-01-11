============
Installation
============

Pain001 is available on PyPI and can be installed using various package managers.

Quick Installation
==================

The easiest way to install Pain001 is via pip:

.. code-block:: bash

    pip install pain001

This will install Pain001 and all its required dependencies.

Installation Methods
====================

Using pip (Recommended)
-----------------------

.. code-block:: bash

    pip install pain001

Using pip with extras
~~~~~~~~~~~~~~~~~~~~~~

Install with optional development dependencies:

.. code-block:: bash

    # Development tools (formatting, linting, type checking)
    pip install pain001[dev]

    # Documentation build tools
    pip install pain001[docs]

    # All extras
    pip install pain001[all]

Using Poetry
------------

If you're using Poetry for dependency management:

.. code-block:: bash

    poetry add pain001

For development:

.. code-block:: bash

    poetry add --group dev pain001

Using Conda
-----------

If you prefer Conda, Pain001 can be installed from the default channels:

.. code-block:: bash

    conda install pain001

Development Installation
=========================

For contributing to Pain001 or running tests locally:

1. **Clone the repository**

   .. code-block:: bash

      git clone https://github.com/sebastienrousseau/pain001.git
      cd pain001

2. **Install with development dependencies**

   Using Poetry (recommended):

   .. code-block:: bash

      poetry install

   Using pip:

   .. code-block:: bash

      pip install -e ".[dev]"

3. **Run tests**

   .. code-block:: bash

      poetry run pytest
      # or
      make test

4. **Run code quality checks**

   .. code-block:: bash

      make lint
      make format
      make type

System Requirements
===================

- **Python**: 3.9 or higher
- **Operating System**: Linux, macOS, or Windows
- **Dependencies**: Automatically installed with Pain001

Verifying Installation
======================

To verify that Pain001 is correctly installed:

.. code-block:: python

    import pain001
    print(pain001.__version__)

You should see the version number of the installed Pain001 package.

Troubleshooting
===============

**Issue: "ModuleNotFoundError: No module named 'pain001'"**

Ensure you've activated the correct Python environment and installed Pain001:

.. code-block:: bash

    python -m pip install --upgrade pain001

**Issue: "Permission denied" during installation**

On Unix-like systems, you may need to use `--user`:

.. code-block:: bash

    pip install --user pain001

**Issue: Dependency conflicts**

If you encounter dependency conflicts, try creating a fresh virtual environment:

.. code-block:: bash

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install pain001

**Issue: XML schema validation errors**

Ensure you have the correct XSD schema files. Pain001 supports schemas from pain.001.001.03 to pain.001.001.11. Download official schemas from:
- `ISO 20022 UNIFI Schemas <https://www.iso20022.org>`_

Getting Help
============

If you encounter installation issues:

1. Check the `FAQ <faq.html>`_
2. Search existing `GitHub Issues <https://github.com/sebastienrousseau/pain001/issues>`_
3. Create a new GitHub issue with:
   - Python version (`python --version`)
   - OS information
   - Full error message and traceback
   - Steps to reproduce

Next Steps
==========

After installation, check out the `Getting Started Guide <usage.html>`_ to start using Pain001.
