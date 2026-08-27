# ETAPA_01_RESULTADO

Auditoria de correção da fundação (ETAPA 01B) — ChatGPT exigiu antes da ETAPA 02.

## Identificação

- Caminho local: `D:\LICITAÇÃO_PROJETO`
- Repositório: `https://github.com/patricsouzas-tech/PROJETO_LICITACAO.git`
- Branch: `main`
- Commit inicial (auditado pelo ChatGPT): `6ad78d40c9d26cb9e47ee80faafa0a8c431747cc`
- Commit final: `ebe13cad2512bbfa19d508e951a23c7f184c2fd4`

## O que foi corrigido (ETAPA 01B)

### A. Migration determinística
`alembic/versions/0001_initial.py` reescrito com `op.create_table` explícitos
(tabelas, colunas, FKs, UniqueConstraint, índice). `alembic/script.py.mako`
voltou ao padrão Alembic (sem `Base.metadata.create_all`). Validação:
upgrade → downgrade → upgrade em banco temporário (teste automatizado).

### B. Modelo ProdutoCandidato
`ProdutoCandidato` agora pertence ao `Item` (`item_id`), não a um único requisito.
`ValidacaoRequisito` passou a ter `produto_candidato_id` obrigatório, ligando
requisito ↔ produto candidato.

### C. Deduplicação
Idempotência lógica por `UNIQUE(licitacao_id, sha256)`. Mesmo SHA em licitações
diferentes gera DocumentosFonte distintos (cada um aponta para sua licitação),
reutilizando o blob físico. Tratado `IntegrityError` por concorrência.

### D/E. Metadados e segurança
`ingest_document` recebe `nome_original` e `mime_type` explícitos; o nome do
arquivo temporário não é mais persisitido como `nome_original`. Sanitização de
nome neutraliza `../`, absolutos e separadores (path traversal). Caminho físico
continua baseado em `sha256`.

### F. Formatos
Removido `.doc` da lista de aceitos. Válidos: `pdf`, `docx`, `xlsx`, `txt`.
Arquivo corrompido/incompatível resulta em `ERRO`, nunca `PROCESSADO`.

### G. API
Todos os endpoints sob prefixo `/api/v1`. Health retorna apenas `{"status":"ok"}`
(sem `database_url`). Criados response models e endpoints de listagem/obtenção.

### H/I. DOCX e XLSX
DOCX itera blocos do corpo preservando ordem Paragraph↔Table (adicionado
`TipoLocalizador.TABELA` + campos `tabela`/`linha_tabela`). XLSX usa primeira e
última célula **não vazia** como `celula_inicio`/`celula_fim`.

### J/K. PDF/TXT
PDF textual (página), multipágina e sem texto → `OCR_REQUIRED` (sem OCR silencioso).
TXT com prioridade de encoding utf-8-sig → utf-8 → cp1252 → latin-1.

### L/M. Dependências e scripts
Adicionados `uvicorn` (runtime) e `httpx` (dev). `dev.ps1`/`test.ps1` corrigidos
(`${root}[dev]`), executam `alembic upgrade head`, `pytest` e `ruff`, falhando se
algum falhar.

### O/P. Schemas e .env.example
`ValidacaoRequisitoRead` corrigido para `requisito_id` + `produto_candidato_id`.
`.env.example` com `APP_ENV`, `DATABASE_URL`, `DATA_DIR`, `LOG_LEVEL`.

### Q/R. Testes
Cobertura ampliada (enums, Decimal, SHA, deduplicação nas duas variações,
PDF textual/multipágina/OCR, DOCX parágrafo/tabela/ordem, XLSX coordenadas,
TXT encoding, formato inválido, corrompido, nome original, mime, path traversal,
health, CRUD de licitação/documento/trechos, 404s, e teste isolado de Alembic).

## Resultado (formato ChatGPT)

```
Commit inicial: 6ad78d40c9d26cb9e47ee80faafa0a8c431747cc
Commit final: ebe13cad2512bbfa19d508e951a23c7f184c2fd4
Push: SUCESSO
Python 3.13: NAO VALIDADO (ambiente local 3.14.7)
Migration determinística: PASS
Upgrade -> downgrade -> upgrade: PASS
ProdutoCandidato -> Item: PASS
Deduplicação mesma licitação: PASS
Mesmo SHA em licitações distintas: PASS
Nome original: PASS
MIME type: PASS
API /api/v1: PASS
Health seguro: PASS
PDF: PASS
DOCX: PASS
Ordem DOCX: PASS
XLSX: PASS
TXT: PASS
OCR_REQUIRED: PASS
Path traversal: PASS
.env.example: PASS
PowerShell dev.ps1: PASS
PowerShell test.ps1: PASS
Testes: 36 PASS / 0 FAIL / 0 SKIP
Ruff: PASS
Segredos: NENHUM
Documentação: PASS
Fundação pronta para ETAPA 02? SIM
```

## Opinião técnica do OpenCode

- A correção `ProdutoCandidato → Item` faz sentido: o produto candida a atender o
  Item inteiro e é validado contra todos os seus requisitos.
- A estratégia de deduplicação por `licitacao_id + sha256` está adequada para esta
  fase. Separar blob físico (`ArquivoFisico`) de documento lógico (`DocumentoFonte`)
  seria uma evolução futura útil se o volume de documentos compartilhados crescer,
  mas não é necessária agora.
- Discordo de um único ponto menor: manter `oferta_id` opcional em `ValidacaoRequisito`
  pode gerar validações órfãs de oferta; recomendo que a validação referencie a
  oferta quando ela for a evidência, mas isso não bloqueia a ETAPA 02.
- Risco restante antes do parser: extração de PDFs apenas por texto nativo; escaneados
  ficam como `OCR_REQUIRED` até implementarmos OCR (fora de escopo). Isso está documentado.
- Considero a fundação pronta para ETAPA 02.
