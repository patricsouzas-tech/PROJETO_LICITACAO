# PROJETO_LICITACAO

Sistema de apoio a licitações com ingestão documental rastreável.

## Status

- ETAPA 00: baseline real e auditoria de continuidade — concluída.
- ETAPA 01: fundação arquitetural + ingestão documental rastreável — **CONCLUÍDA** (corrigida em ETAPA 01B).
- Próximo: ETAPA 02 (parser de edital → lotes → itens → requisitos com evidência de origem), aguardando auditoria do ChatGPT.

## Stack

Python 3.13+ · FastAPI + Uvicorn · Pydantic v2 · SQLAlchemy 2.x · Alembic · pytest · httpx · Ruff · SQLite (dev).

## Instalação (Windows)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -U pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Requer Python 3.13+ (validado localmente em 3.14).

## Configuração

Copie `.env.example` para `.env` e ajuste:

```
APP_ENV=development
DATABASE_URL=sqlite:///./data/licitacao.db
DATA_DIR=./data/documentos
LOG_LEVEL=INFO
```

`.env` real é ignorado no Git.

## Migrations

```powershell
$env:DATABASE_URL="sqlite:///./data/licitacao.db"
$env:DATA_DIR="./data/documentos"
.\.venv\Scripts\python.exe -m alembic upgrade head
```

A migration inicial (`0001_initial`) é determinística (usa `op.create_table`, sem `Base.metadata.create_all`).

## Execução

```powershell
.\scripts\dev.ps1
# API em http://127.0.0.1:8000
```

Ou manualmente:

```powershell
.\.venv\Scripts\python.exe -m uvicorn licitacao.api.main:app --port 8000
```

## Testes e lint

```powershell
.\scripts\test.ps1
# roda pytest + ruff check
```

Ou:

```powershell
$env:DATABASE_URL="sqlite:///./data/test_licitacao.db"
$env:DATA_DIR="./data/test_documentos"
.\.venv\Scripts\python.exe -m pytest tests -v
.\.venv\Scripts\python.exe -m ruff check src tests
```

## Endpoints (/api/v1)

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | status (sem vazar config) |
| POST | `/licitacoes` | cria licitação |
| GET | `/licitacoes` | lista licitações |
| GET | `/licitacoes/{id}` | obtém licitação |
| POST | `/licitacoes/{id}/documentos` | ingere documento (UploadFile + `tipo_documento`) |
| GET | `/licitacoes/{id}/documentos` | lista documentos da licitação |
| GET | `/documentos/{id}` | obtém documento |
| GET | `/documentos/{id}/trechos` | lista trechos extraídos (rastreáveis) |

## Estrutura

```
src/licitacao/{api,core,db,domain,repositories,services}
alembic/versions/0001_initial.py
tests/{unit,integration,fixtures}
scripts/{dev,test}.ps1
docs/{architecture,audit}
```

## Formatos suportados (ingestão)

- PDF (texto nativo; sem texto → `OCR_REQUIRED`, sem OCR automático)
- DOCX (parágrafos + tabelas preservando ordem)
- XLSX (coordenadas de célula reais)
- TXT (detecção de encoding: utf-8-sig → utf-8 → cp1252 → latin-1)

`.doc` antigo **não** é suportado.

## Limitações / não implementado (ETAPA 01)

- Mercado Livre, OLX, Enjoei, scraping, Playwright
- Validação de produtos, cotação final
- IA/LLM, OCR, frontend completo
- Parser automático de edital (será ETAPA 02)
- PostgreSQL (arquitetura já neutra; SQLite em dev/testes)

## Princípios

Rastreabilidade de evidência (`TrechoDocumento` com localizador + `sha256_texto`),
imutabilidade do original (cópia por `sha256`), idempotência lógica por
`(licitacao_id, sha256)`, e dinheiro sempre `Numeric(18,6)`.
