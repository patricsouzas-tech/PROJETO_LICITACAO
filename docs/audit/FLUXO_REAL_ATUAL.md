# FLUXO_REAL_ATUAL.md

Documentação do funcionamento atual do sistema de licitações (ETAPA 00 — baseline).

O sistema ainda não possui código. Abaixo descreve-se o fluxo **esperado** e o estado de cada etapa.

## Fluxo esperado

```
Arquivo recebido (edital / termo de referência / anexos)
  → extração de lotes e itens
  → especificações por item
  → produtos candidatos
  → validação de aderência técnica
  → pesquisa de preço (Mercado Livre principal; OLX/Enjoei alternativos)
  → condição do produto (novo/lacrado/na caixa)
  → nota fiscal (SIM / NÃO / NÃO CONFIRMADO)
  → valor final consolidado (sem aprovação intermediária)
  → planilha final de cotação
```

## Estado de cada etapa

- **Arquivo recebido**: NÃO IMPLEMENTADO
- **Extração**: NÃO IMPLEMENTADO
- **Lotes**: NÃO IMPLEMENTADO
- **Itens**: NÃO IMPLEMENTADO
- **Pesquisa**: NÃO IMPLEMENTADO
- **Validação**: NÃO IMPLEMENTADO
- **Preço**: NÃO IMPLEMENTADO
- **Consolidação**: NÃO IMPLEMENTADO
- **Saída (planilha)**: NÃO IMPLEMENTADO

## Resumo

Não há funcionalidade executável hoje. O próximo passo de desenvolvimento é criar o esqueleto do projeto e a entrada/parsing do edital, conforme definido em `ESTADO_REAL_CONTINUIDADE.md`.
