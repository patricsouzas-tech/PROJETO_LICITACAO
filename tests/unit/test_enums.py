from licitacao.domain import enums


def test_enums_tristate():
    assert enums.SimNaoConfirmado.SIM.value == "SIM"
    assert enums.SimNaoConfirmado.NAO.value == "NAO"
    assert enums.SimNaoConfirmado.NAO_CONFIRMADO.value == "NAO_CONFIRMADO"


def test_nota_fiscal_tristate():
    valores = {e.value for e in enums.NotaFiscal}
    assert valores == {"SIM", "NAO", "NAO_CONFIRMADO"}


def test_validacao_resultado_regra():
    assert enums.ValidacaoResultado.ATENDE.value == "ATENDE"
    assert enums.ValidacaoResultado.NAO_ATENDE.value == "NAO_ATENDE"
    assert enums.ValidacaoResultado.NAO_COMPROVADO.value == "NAO_COMPROVADO"


def test_tipo_localizador_inclui_tabela():
    valores = {e.value for e in enums.TipoLocalizador}
    assert "TABELA" in valores
