$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $root
$venv = Join-Path $root ".venv"

if (-not (Test-Path $venv)) {
    python -m venv $venv
    & "$venv\Scripts\python.exe" -m pip install -q --upgrade pip
}

& "$venv\Scripts\python.exe" -m pip install -q -e "${root}[dev]"

$env:DATABASE_URL = "sqlite:///$root/data/licitacao.db"
$env:DATA_DIR = "$root/data/documentos"

& "$venv\Scripts\python.exe" -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Iniciando servidor em http://127.0.0.1:8000"
& "$venv\Scripts\python.exe" -m uvicorn licitacao.api.main:app --reload --port 8000
