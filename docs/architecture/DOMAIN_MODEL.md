# DOMAIN_MODEL — PROJETO_LICITACAO

Modelo de domínio (SQLAlchemy 2.x). Preparado para ETAPA 02 (parser de edital).

## Hierarquia

```
LICITACAO
 ├── DOCUMENTOS (DocumentoFonte)
 │    └── TRECHOS (TrechoDocumento)  ← rastreabilidade de evidência
 └── LOTES (Lote)
      └── ITENS (Item)
           ├── REQUISITOS (RequisitoTecnico)
           │    └── VALIDACOES (ValidacaoRequisito)
           └── PRODUTOS_CANDIDATOS (ProdutoCandidato)
                └── OFERTAS (Oferta)
```

## Entidades e campos principais

- **Licitacao**: id, titulo, numero_processo, orgao, descricao, created_at, updated_at
- **DocumentoFonte**: id, licitacao_id, tipo_documento, nome_original, extensao,
  mime_type, tamanho_bytes, sha256, caminho_armazenado, status_processamento,
  precisa_ocr, erro_processamento, created_at
  - Restrição única: `UNIQUE(licitacao_id, sha256)`
- **TrechoDocumento**: id, documento_id, ordem, tipo_localizador
  (PAGINA/PARAGRAFO/CELULA/TABELA), pagina, planilha, celula_inicio, celula_fim,
  paragrafo, tabela, linha_tabela, texto_bruto, sha256_texto
- **Lote**: id, licitacao_id, numero, titulo, descricao
- **Item**: id, lote_id, numero, descricao_original, quantidade (Numeric), unidade
- **RequisitoTecnico**: id, item_id, texto_original, texto_normalizado, obrigatorio,
  documento_origem_id, trecho_origem_id
- **ProdutoCandidato**: id, item_id (NÃO mais por requisito), descricao
- **Oferta**: id, produto_candidato_id, marketplace, url, vendedor, preco_unitario,
  frete, outros_custos, valor_unitario_final (Numeric), quantidade_disponivel,
  data_coleta, condicao, lacrado, caixa_original, nota_fiscal
- **ValidacaoRequisito**: id, requisito_id, produto_candidato_id, oferta_id (opcional),
  resultado, observacao

## Validação técnica (regra futura)

`ValidacaoRequisito` conecta um `RequisitoTecnico` a um `ProdutoCandidato`
(avaliação do produto contra **todos** os requisitos do Item):

- se qualquer requisito obrigatório = NAO_ATENDE → produto rejeitado;
- se nenhum falhar, mas algum obrigatório = NAO_COMPROVADO → não aprovado tecnicamente;
- somente todos os requisitos obrigatórios ATENDE → tecnicamente aprovado.
- Não usar porcentagem para substituir essa regra.

## Enums importantes

- `CondicaoProduto`: NOVO / USADO / RECONDICIONADO / NAO_CONFIRMADO
- `SimNaoConfirmado` (Lacrado, CaixaOriginal): SIM / NAO / NAO_CONFIRMADO
- `NotaFiscal`: SIM / NAO / NAO_CONFIRMADO (nunca boolean)
- `ValidacaoResultado`: ATENDE / NAO_ATENDE / NAO_COMPROVADO
- `Marketplace`: MERCADO_LIVRE / OLX / ENJOEI / OUTRO
