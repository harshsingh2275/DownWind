#!/usr/bin/env bash
set -euo pipefail

echo "=================================================="
echo " Running all checks for DownWind Project"
echo "=================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Detect Python executable with ruff/mypy/pytest installed
PY=""
for candidate in python python.exe python3 py; do
  if command -v "$candidate" &>/dev/null && "$candidate" -m ruff --version &>/dev/null; then
    PY="$candidate"
    break
  fi
done

if [ -z "$PY" ]; then
  echo "ERROR: Python 3.12 environment with ruff/mypy/pytest not found!"
  exit 1
fi

# Detect npm executable
NPM=""
for candidate in npm npm.cmd; do
  if command -v "$candidate" &>/dev/null; then
    NPM="$candidate"
    break
  fi
done

if [ -z "$NPM" ]; then
  echo "ERROR: npm executable not found!"
  exit 1
fi

echo ""
echo "--> 1. Running backend checks (ruff, mypy, pytest) with $PY..."
(
  cd backend
  echo "    [1/3] ruff check..."
  "$PY" -m ruff check .
  echo "    [2/3] mypy..."
  "$PY" -m mypy .
  echo "    [3/3] pytest..."
  "$PY" -m pytest -q
)
echo "    Backend checks PASSED!"

echo ""
echo "--> 2. Running frontend checks (lint, typecheck, test) with $NPM..."
(
  cd frontend
  echo "    [1/3] npm run lint..."
  "$NPM" run lint
  echo "    [2/3] npm run typecheck..."
  "$NPM" run typecheck
  echo "    [3/3] npm test..."
  "$NPM" test
)
echo "    Frontend checks PASSED!"

echo ""
echo "--> 3. Running secrets scan..."
bash "$ROOT_DIR/scripts/scan-secrets.sh"

echo ""
echo "=================================================="
echo " All checks PASSED successfully!"
echo "=================================================="
exit 0
