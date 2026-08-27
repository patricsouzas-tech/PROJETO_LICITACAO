# ARCHITECTURE — PROJETO_LICITACAO

Fundação definida nas ETAPAS 01 e 01B. Monólito modular em Python.

## Stack

- Python 3.13+ (validado em 3.14 no ambiente local)
- FastAPI + Uvicorn
- Pydantic v2 (schemas)
- SQLAlchemy 2.x (ORM)
- Alembic (migrations determinísticas via `op.create_table`)
- pytest + httpx (TestClient) + Ruff
- SQLite para dev/testes; arquitetura neutra preparada para PostgreSQL

## Princípios

1. **Rastreabilidade de evidência**: cada texto extraído vira `TrechoDocumento`
   com localizador (página / parágrafo / célula / tabela+linha) e `sha256_texto`.
2. **Imutabilidade do original**: cópia do arquivo em `data/` (ignorado no Git)
   identificada por `sha256`.
3. **Idempotência lógica por `(licitacao_id, sha256)`**: o mesmo arquivo em
   licitações distintas gera DocumentosFonte distintos, reutilizando o blob físico.
4. **Dinheiro como `Numeric(18,6)`**, nunca `float`.

## Pipeline (ETAPA 01)

```
LICITAÇÃO → DOCUMENTOS → ARMAZENAMENTO → EXTRAÇÃO DE TEXTO → EVIDÊNCIA RASTREÁVEL
```

Fora de escopo: Mercado Livre, OLX, Enjoei, scraping, validação de produtos,
cotação final, IA/LLM, OCR, frontend completo.

## Estrutura

```
src/licitacao/
  api/        # FastAPI em /api/v1
  core/       # config, logging
  db/         # base, session, models
  domain/     # enums, schemas
  repositories/
  services/
    ingestion/  # ingest.py (orquestra)
    extraction/  # extract.py (pdf/docx/xlsx/txt)
tests/        # unit, integration, fixtures
alembic/      # migrations determinísticas
scripts/      # dev.ps1, test.ps1
```

## Contrato da API (/api/v1)

- `GET /health`
- `POST /licitacoes`
- `GET /licitacoes`
- `GET /licitacoes/{id}`
- `POST /licitacoes/{id}/documentos`
- `GET /licitacoes/{id}/documentos`
- `GET /documentos/{id}`
- `GET /documentos/{id}/trechos`

Veja `docs/architecture/DOMAIN_MODEL.md` para o modelo de domínio.
