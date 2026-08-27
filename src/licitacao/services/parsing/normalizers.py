"""Normalizadores determinísticos (número BR e texto) — ETAPA 02."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_NUMERO = re.compile(r"[-+]?[\d.,\s]*\d")


def _limpar_numero(texto: str) -> str | None:
    s = texto.strip()
    # remove símbolos monetários e espaços internos
    s = re.sub(r"[R$\s]", "", s)
    s = s.replace("\u00a0", "")
    if not s:
        return None
    return s


def normalizar_numero_br(texto: str | None) -> Decimal | None:
    """Interpreta número no padrão brasileiro como Decimal (nunca float).

    Regras:
    - vírgula presente -> separador decimal; ponto é milhar.
    - apenas ponto: se o grupo após o ponto tem 3 dígitos -> milhar (ex.: 1.500=1500);
      caso contrário -> decimal (ex.: 1.5=1.5).
    - apenas vírgula: decimal (ex.: 2,5=2.5).
    """
    if texto is None:
        return None
    s = _limpar_numero(texto)
    if s is None:
        return None
    if not re.search(r"\d", s):
        return None

    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif "." in s:
        parte = s.split(".")
        fracao = parte[-1]
        if len(fracao) == 3 and len(parte) > 1:
            # grupo final de 3 dígitos -> separador de milhar (ex.: 1.500 = 1500)
            s = s.replace(".", "")
        # caso contrário mantém ponto como decimal (ex.: 1.5, 12.34)
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def normalizar_texto_requisito(texto: str) -> str:
    """Limpeza mínima de texto de requisito.

    Permite: colapsar espaços, unificar quebras de linha, caixa consistente.
    NÃO altera valor, marca, nem remove modificadores (mínimo, máximo, etc.).
    """
    if texto is None:
        return ""
    s = texto.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{2,}", "\n", s)
    s = s.strip()
    return s
