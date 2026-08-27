"""Testes de extracao de texto (etapa 01)."""
from pathlib import Path

from licitacao.services.extraction.extract import (
    extrair,
    extrair_txt,
    extrair_xlsx,
)


def test_extrair_txt_preserva_ordem_e_paragrafo(tmp_path: Path):
    arquivo = tmp_path / "edital.txt"
    arquivo.write_text(
        "Linha um do edital.\n\nLinha tres com detalhe.", encoding="utf-8"
    )
    resultado = extrair_txt(arquivo)
    assert resultado.erro is None
    assert len(resultado.trechos) == 2
    assert resultado.trechos[0].paragrafo == 1
    assert "Linha um" in resultado.trechos[0].texto_bruto
    assert resultado.trechos[1].paragrafo == 3
    assert resultado.precisa_ocr is False


def test_extrair_xlsx_mantem_coordenadas(tmp_path: Path):
    try:
        from openpyxl import Workbook
    except ImportError:
        import pytest

        pytest.skip("openpyxl nao instalado")
    wb = Workbook()
    ws = wb.active
    ws.title = "LOTE 01"
    ws["A7"] = "Item"
    ws["B7"] = "Martelo"
    arquivo = tmp_path / "planilha.xlsx"
    wb.save(arquivo)

    resultado = extrair_xlsx(arquivo)
    assert resultado.erro is None
    assert len(resultado.trechos) == 1
    t = resultado.trechos[0]
    assert t.tipo_localizador == "CELULA"
    assert t.planilha == "LOTE 01"
    assert t.celula_inicio == "A7"
    assert t.celula_fim == "B7"
    assert "Martelo" in t.texto_bruto


def test_extrair_dispatch_por_extensao(tmp_path: Path):
    arquivo = tmp_path / "doc.txt"
    arquivo.write_text("conteudo simples", encoding="utf-8")
    resultado = extrair(arquivo, "txt")
    assert len(resultado.trechos) == 1
