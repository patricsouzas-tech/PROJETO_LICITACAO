$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $root
$venv = Join-Path $root ".venv"

if (-not (Test-Path $venv)) {
    python -m venv $venv
    & "$venv\Scripts\python.exe" -m pip install -q --upgrade pip
}

& "$venv\Scripts\python.exe" -m pip install -q -e "${root}[dev]"

$env:DATABASE_URL = "sqlite:///$root/data/test_licitacao.db"
$env:DATA_DIR = "$root/data/test_documentos"

& "$venv\Scripts\python.exe" -m pytest $root/tests -v
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& "$venv\Scripts\python.exe" -m ruff check "$root"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "TESTES E LINT OK"
