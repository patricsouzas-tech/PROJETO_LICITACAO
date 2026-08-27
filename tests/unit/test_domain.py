
from sqlalchemy import Numeric

from licitacao.db.models import Item, ProdutoCandidato, ValidacaoRequisito
from licitacao.domain.enums import ValidacaoResultado
from licitacao.domain.schemas import (
    LicitacaoRead,
    ValidacaoRequisitoRead,
)


def test_numeric_e_decimal_para_dinheiro():
    col = Item.__table__.c["quantidade"].type
    assert isinstance(col, Numeric)
    assert col.precision == 18
    assert col.scale == 6


def test_schema_licitacao_from_orm():
    obj = LicitacaoRead(
        id=1,
        titulo="Edital X",
        numero_processo="1/2026",
        orgao=None,
        descricao=None,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    assert obj.titulo == "Edital X"
    assert obj.id == 1


def test_schema_validacao_requisito_reflete_modelo():
    v = ValidacaoRequisito(
        id=1,
        requisito_id=10,
        produto_candidato_id=20,
        resultado=ValidacaoResultado.ATENDE,
    )
    schema = ValidacaoRequisitoRead.model_validate(v)
    assert schema.requisito_id == 10
    assert schema.produto_candidato_id == 20
    assert schema.resultado == ValidacaoResultado.ATENDE


def test_produto_candidato_pertence_ao_item():
    item = Item(id=5, lote_id=1, numero="1")
    prod = ProdutoCandidato(id=9, item_id=5, descricao="Martelo")
    item.produtos_candidatos.append(prod)
    assert prod.item is item
    assert prod in item.produtos_candidatos
