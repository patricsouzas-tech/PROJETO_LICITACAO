$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $root
$venv = Join-Path $root ".venv"

if (-not (Test-Path $venv)) {
    python -m venv $venv
    & "$venv\Scripts\python.exe" -m pip install -q --upgrade pip
    & "$venv\Scripts\python.exe" -m pip install -q -e ".$root[dev]"
}

$env:DATABASE_URL = "sqlite:///$root/data/test_licitacao.db"
$env:DATA_DIR = "$root/data/test_documentos"

Write-Host "Executando testes"
& "$venv\Scripts\python.exe" -m pytest $root/tests -v
