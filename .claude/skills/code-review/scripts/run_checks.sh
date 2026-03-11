#!/bin/bash
# Run all code quality checks for GenIE
set -e

echo "=== Ruff Format Check ==="
poetry run ruff format --check .

echo "=== Ruff Lint ==="
poetry run ruff check .

echo "=== MyPy Type Check ==="
poetry run mypy spec/

echo "=== All checks passed ==="
