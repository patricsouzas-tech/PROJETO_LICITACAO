# Arquitetura — PROJETO_LICITACAO

Fundação definida na ETAPA 01. Monólito modular em Python.

## Stack

- Python 3.13+ (desenvolvido/validado em 3.14)
- FastAPI (API HTTP)
- Pydantic (schemas)
- SQLAlchemy 2.x (ORM)
- Alembic (migrations)
- pytest (testes)
- SQLite para dev/testes; arquitetura neutra preparada para PostgreSQL

## Princípios

1. **Rastreabilidade de evidência**: todo texto extraído vira um `TrechoDocumento`
   com localizador (página / parágrafo / célula) e `sha256_texto`.
2. **Imutabilidade do original**: o arquivo recebido é copiado para `data/`
   (ignorado no Git) e identificado por `sha256`.
3. **Idempotência**: arquivos iguais não geram documentos duplicados.
4. **Dinheiro como Decimal**: nunca `float` para preço/quantidade.

## Pipeline (ETAPA 01)

```
LICITAÇÃO → DOCUMENTOS → ARMAZENAMENTO → EXTRAÇÃO DE TEXTO → EVIDÊNCIA RASTREÁVEL
```

Fora de escopo nesta etapa: Mercado Livre, OLX, Enjoei, scraping, validação de
produtos, cotação final, IA/LLM, OCR, frontend completo.

## Estrutura

```
src/licitacao/
  api/        # FastAPI (main.py + routes)
  core/       # config, logging
  db/         # base, session, models
  domain/     # enums, schemas
  repositories/
  services/
    ingestion/  # ingest.py (orquestra)
    extraction/  # extract.py (pdf/docx/xlsx/txt)
tests/        # unit, integration, fixtures
```

## Modelo de domínio (entidades)

`Licitacao`, `DocumentoFonte`, `TrechoDocumento` (usadas nesta etapa);
`Lote`, `Item`, `RequisitoTecnico`, `ProdutoCandidato`, `Oferta`,
`ValidacaoRequisito` (preparadas para etapas futuras).
