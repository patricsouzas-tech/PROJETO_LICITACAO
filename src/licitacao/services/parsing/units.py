"""Normalização de unidades para forma canônica (ETAPA 02)."""
from __future__ import annotations

_UNIDADES = {
    "UN": "UNIDADE",
    "UND": "UNIDADE",
    "UNID": "UNIDADE",
    "UNIDADE": "UNIDADE",
    "UNIDADES": "UNIDADE",
    "CX": "CAIXA",
    "CAIXA": "CAIXA",
    "CAIXAS": "CAIXA",
    "KIT": "KIT",
    "KITS": "KIT",
    "PCT": "PACOTE",
    "PACOTE": "PACOTE",
    "PACOTES": "PACOTE",
    "M": "METRO",
    "METRO": "METRO",
    "METROS": "METRO",
    "M2": "METRO_QUADRADO",
    "M²": "METRO_QUADRADO",
    "METRO QUADRADO": "METRO_QUADRADO",
    "METROS QUADRADOS": "METRO_QUADRADO",
    "L": "LITRO",
    "LT": "LITRO",
    "LITRO": "LITRO",
    "LITROS": "LITRO",
    "KG": "QUILOGRAMA",
    "QUILO": "QUILOGRAMA",
    "QUILOGRAMA": "QUILOGRAMA",
    "PC": "PECA",
    "PÇ": "PECA",
    "PECA": "PECA",
    "PEÇA": "PECA",
    "PECAS": "PECA",
    "PEÇAS": "PECA",
}


def normalizar_unidade(original: str | None) -> tuple[str | None, str | None]:
    """Retorna (unidade_original, unidade_normalizada).

    Preserva o texto original; gera a forma canônica quando reconhecida.
    Se não reconhecer, normalizada fica None (não inventa).
    """
    if not original:
        return None, None
    original = original.strip()
    normalizada = _UNIDADES.get(original.upper())
    return original, normalizada
