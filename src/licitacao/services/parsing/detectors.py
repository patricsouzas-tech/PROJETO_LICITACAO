"""Detectores determinísticos para lotes, itens e cabeçalhos de tabela (ETAPA 02)."""
from __future__ import annotations

import re

_LOTE = re.compile(
    r"^\s*(LOTE|GRUPO)\b[\s:.\-]*?(N[º°]\.?\s*)?"
    r"(?P<num>[0-9]+|[IVXLCDM]+|ÚNICO|UNICO)\b",
    re.IGNORECASE,
)
_ITEM_FORTE = re.compile(
    r"^\s*ITEM\b[\s:.\-]*?(N[º°]\.?\s*)?(?P<num>[0-9]+)\b",
    re.IGNORECASE,
)
_ITEM_FRACO = re.compile(r"^\s*(?P<num>[0-9]{1,3})[\.)\-]\s+\S")
_QTD_LABEL = re.compile(
    r"(?i)(quantidade|qtd|qtde|qt)\s*[:\-]?\s*(?P<val>[\d.,\s]+\d)\s*(?P<un>[A-Za-z.²°]+)?"
)
_UN_LABEL = re.compile(
    r"(?i)(unidade|und|un)\s*[:\-]?\s*(?P<un>[A-Za-z.²°]+)"
)

_CABECALHOS = {
    "ITEM": re.compile(r"(?i)^\s*ITEM\s*$"),
    "NUMERO": re.compile(r"(?i)(n[º°]|número|núm)"),
    "CODIGO": re.compile(r"(?i)(c[óo]d\.?|c[óo]digo)"),
    "DESCRICAO": re.compile(r"(?i)(descri[çc][ãa]o|especifica[çc][ãa]o)"),
    "QUANTIDADE": re.compile(r"(?i)(qtd|qtde|quantidade)"),
    "UNIDADE": re.compile(r"(?i)(und|unidade|un\b)"),
    "VALOR_UNITARIO": re.compile(r"(?i)(valor\s*unit)"),
    "VALOR_TOTAL": re.compile(r"(?i)(valor\s*total)"),
}


def detectar_lote(texto: str) -> tuple[bool, str | None, str | None]:
    m = _LOTE.match(texto or "")
    if not m:
        return False, None, None
    numero = m.group("num").upper()
    if numero in ("ÚNICO", "UNICO"):
        numero = "UNICO"
    return True, numero, (m.group(0) or "").strip()


def detectar_item_forte(texto: str) -> tuple[bool, str | None]:
    m = _ITEM_FORTE.match(texto or "")
    if not m:
        return False, None
    return True, m.group("num")


def detectar_item_fraco(texto: str) -> tuple[bool, str | None]:
    m = _ITEM_FRACO.match(texto or "")
    if not m:
        return False, None
    return True, m.group("num")


def extrair_quantidade_unidade(texto: str) -> tuple[str | None, str | None]:
    """Extrai (valor_bruto, unidade_bruta) apenas quando há rótulo explícito.

    Não confunde preço com quantidade: só atua após rótulos qtd/qtde/quantidade
    ou unidade/und.
    """
    val = None
    un = None
    q = _QTD_LABEL.search(texto or "")
    if q:
        val = q.group("val").strip()
        un = (q.group("un") or "").strip() or None
    if un is None:
        u = _UN_LABEL.search(texto or "")
        if u:
            un = u.group("un").strip()
    return val, un


def detectar_cabecalho_tabela(celulas: list[str]) -> dict[str, int] | None:
    """Mapeia colunas normalizadas -> índice. Retorna None se não for cabeçalho."""
    mapeamento: dict[str, int] = {}
    for idx, celula in enumerate(celulas):
        c = (celula or "").strip()
        for nome, pat in _CABECALHOS.items():
            if pat.search(c):
                mapeamento.setdefault(nome, idx)
    # cabeçalho mínimo: precisa de item/numero OU descrição
    if "ITEM" in mapeamento or "NUMERO" in mapeamento or "DESCRICAO" in mapeamento:
        return mapeamento
    return None
