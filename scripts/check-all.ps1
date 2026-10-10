$ErrorActionPreference = "Stop"

Write-Host "=================================================="
Write-Host " Running all checks for DownWind Project (PowerShell)"
Write-Host "=================================================="

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

Write-Host "`n--> 1. Running backend checks (ruff, mypy, pytest)..."
Push-Location "backend"
try {
    Write-Host "    [1/3] ruff check..."
    python -m ruff check .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "    [2/3] mypy..."
    python -m mypy .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "    [3/3] pytest..."
    python -m pytest -q
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
Write-Host "    Backend checks PASSED!"

Write-Host "`n--> 2. Running frontend checks (lint, typecheck, test)..."
Push-Location "frontend"
try {
    Write-Host "    [1/3] npm run lint..."
    npm run lint
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "    [2/3] npm run typecheck..."
    npm run typecheck
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "    [3/3] npm test..."
    npm test
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
Write-Host "    Frontend checks PASSED!"

Write-Host "`n--> 3. Running secrets scan..."
bash "$RootDir/scripts/scan-secrets.sh"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n=================================================="
Write-Host " All checks PASSED successfully!"
Write-Host "=================================================="
exit 0
