#!/usr/bin/env bash
set -euo pipefail

echo "==> Scanning workspace for committed or exposed secrets..."

FOUND=0

EXCLUDE_DIRS="--exclude-dir=.git --exclude-dir=node_modules --exclude-dir=.aws-sam --exclude-dir=.pytest_cache --exclude-dir=.ruff_cache --exclude-dir=.mypy_cache --exclude-dir=dist"
EXCLUDE_FILES="--exclude=.env.example --exclude=package-lock.json --exclude=scan-secrets.sh"

check_pattern() {
  local desc="$1"
  local pattern="$2"
  
  local matches
  matches=$(grep -rInE $EXCLUDE_DIRS $EXCLUDE_FILES "$pattern" . 2>/dev/null || true)
  
  if [ -n "$matches" ]; then
    echo "ERROR: Potential secret detected ($desc):"
    echo "$matches" | cut -d: -f1,2
    FOUND=1
  fi
}

check_pattern "AWS Access Key ID" "AKIA[0-9A-Z]{16}"
check_pattern "AWS Secret Access Key" "(aws_secret_access_key|AWS_SECRET_ACCESS_KEY)[[:space:]]*=[[:space:]]*[A-Za-z0-9/+=]{30,}"
check_pattern "Private Key Header" "-----BEGIN (RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"
check_pattern "Hardcoded FIRMS Key / Hex Secret" "(FIRMS_MAP_KEY|map_key|MAP_KEY)[[:space:]]*=[[:space:]]*['\"][a-f0-9]{32}['\"]"
check_pattern "Generic Secret assignment" "(API_KEY|SECRET_KEY|BEARER_TOKEN)[[:space:]]*=[[:space:]]*['\"][A-Za-z0-9_=-]{24,}['\"]"

if [ $FOUND -eq 1 ]; then
  echo "==> Secrets scan FAILED! Remove or replace secrets before proceeding."
  exit 1
fi

echo "==> Secrets scan PASSED! No exposed secrets detected."
exit 0
