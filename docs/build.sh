#!/bin/bash
# Generate API documentation

cd "$(dirname "$0")"
sphinx-build -b html . _build/html
echo "Documentation built in _build/html/"
