"""Testes unitarios do parser (ETAPA 02): normalizadores e detectores."""
from decimal import Decimal

from licitacao.services.parsing.detectors import (
    detectar_cabecalho_tabela,
    detectar_item_forte,
    detectar_lote,
    extrair_quantidade_unidade,
)
from licitacao.services.parsing.normalizers import normalizar_numero_br
from licitacao.services.parsing.units import normalizar_unidade


def test_normalizar_numero_br_inteiro():
    assert normalizar_numero_br("10") == Decimal("10")


def test_normalizar_numero_br_virgula_decimal():
    assert normalizar_numero_br("10,00") == Decimal("10.00")
    assert normalizar_numero_br("2,5") == Decimal("2.5")


def test_normalizar_numero_br_milhar_ponto():
    assert normalizar_numero_br("1.500") == Decimal("1500")
    assert normalizar_numero_br("1.500,00") == Decimal("1500.00")


def test_normalizar_numero_br_ponto_decimal_curto():
    assert normalizar_numero_br("1.5") == Decimal("1.5")


def test_normalizar_numero_br_invalido():
    assert normalizar_numero_br("abc") is None


def test_normalizar_unidade():
    assert normalizar_unidade("UN") == ("UN", "UNIDADE")
    assert normalizar_unidade("UND") == ("UND", "UNIDADE")
    assert normalizar_unidade("CX") == ("CX", "CAIXA")
    assert normalizar_unidade("M2") == ("M2", "METRO_QUADRADO")
    assert normalizar_unidade("ZZZ") == ("ZZZ", None)


def test_detectar_lote_variacoes():
    for txt in ["LOTE 1", "LOTE 01", "LOTE Nº 1", "LOTE N° 1", "GRUPO 1", "LOTE I"]:
        ok, num, _ = detectar_lote(txt)
        assert ok is True, txt


def test_detectar_lote_unico():
    ok, num, _ = detectar_lote("LOTE ÚNICO")
    assert ok and num == "UNICO"


def test_detectar_lote_nao_eh_cabecalho():
    ok, _, _ = detectar_lote("o lote deverá ser entregue em 10 dias")
    assert ok is False


def test_detectar_item_forte():
    ok, num = detectar_item_forte("ITEM 3 — Notebook")
    assert ok and num == "3"


def test_extrair_quantidade_unidade():
    val, un = extrair_quantidade_unidade("Quantidade: 10 UN")
    assert val == "10" and un == "UN"


def test_detectar_cabecalho_tabela():
    celulas = ["ITEM", "DESCRIÇÃO", "QTD", "UN"]
    m = detectar_cabecalho_tabela(celulas)
    assert m is not None
    assert m["ITEM"] == 0
    assert m["DESCRICAO"] == 1
    assert m["QUANTIDADE"] == 2
