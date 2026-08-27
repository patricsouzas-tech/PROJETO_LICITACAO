"""Testes de integracao do parser rastreavel (ETAPA 02)."""
from decimal import Decimal

from licitacao.db.models import (
    DocumentoFonte,
    EntidadeTipo,
    EvidenciaParsing,
    Item,
    Lote,
    RequisitoTecnico,
    TrechoDocumento,
)
from licitacao.domain import enums
from licitacao.services.parsing import ParserService


def _criar_licitacao(db, titulo="Edital Parser"):
    from licitacao.db.models import Licitacao

    lic = Licitacao(titulo=titulo, numero_processo="2026/1")
    db.add(lic)
    db.commit()
    db.refresh(lic)
    return lic


def _doc(db, lic, tipo, status=enums.StatusProcessamento.CONCLUIDO):
    doc = DocumentoFonte(
        licitacao_id=lic.id,
        tipo_documento=tipo,
        nome_original="doc.txt",
        extensao="txt",
        mime_type="text/plain",
        tamanho_bytes=10,
        sha256="x" * 64,
        caminho_armazenado="./data/x",
        status_processamento=status,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def _trecho(db, doc, ordem, texto):
    t = TrechoDocumento(
        documento_id=doc.id,
        ordem=ordem,
        tipo_localizador=enums.TipoLocalizador.PARAGRAFO,
        pagina=1,
        texto_bruto=texto,
        sha256_texto="y" * 64,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def test_parser_cria_lotes_itens_requisitos_e_evidencias(db_session):
    lic = _criar_licitacao(db_session)
    doc = _doc(db_session, lic, enums.TipoDocumento.TERMO_REFERENCIA)
    _trecho(db_session, doc, 1, "LOTE 1")
    _trecho(db_session, doc, 2, "ITEM 1 - Notebook")
    _trecho(db_session, doc, 3, "Quantidade: 10 UN")
    _trecho(db_session, doc, 4, "Processador Intel Core i5")
    _trecho(db_session, doc, 5, "16 GB de RAM")
    _trecho(db_session, doc, 6, "ITEM 2 - Cadeira")
    _trecho(db_session, doc, 7, "Quantidade: 2,5 CX")

    execucao = ParserService(db_session).processar(lic.id)

    assert execucao.status.value == "CONCLUIDO"
    lotes = db_session.query(Lote).filter(Lote.licitacao_id == lic.id).all()
    assert len(lotes) == 1
    assert lotes[0].numero == "1"
    assert lotes[0].sintetico is False

    itens = (
        db_session.query(Item).join(Lote).filter(Lote.licitacao_id == lic.id).all()
    )
    assert len(itens) == 2
    by_num = {i.numero: i for i in itens}
    assert by_num["1"].quantidade == Decimal("10")
    assert by_num["1"].unidade_normalizada == "UNIDADE"
    assert by_num["2"].quantidade == Decimal("2.5")
    assert by_num["2"].unidade_normalizada == "CAIXA"
    assert by_num["1"].descricao_original == "Notebook"

    reqs = (
        db_session.query(RequisitoTecnico)
        .join(Item)
        .join(Lote)
        .filter(Lote.licitacao_id == lic.id)
        .all()
    )
    # apenas os dois trechos de especificacao apos o item 1
    assert len(reqs) == 2

    evs = (
        db_session.query(EvidenciaParsing)
        .filter(EvidenciaParsing.licitacao_id == lic.id)
        .all()
    )
    assert len(evs) >= 4
    assert any(e.entidade_tipo == EntidadeTipo.LOTE for e in evs)
    assert any(e.entidade_tipo == EntidadeTipo.ITEM for e in evs)
    assert any(e.entidade_tipo == EntidadeTipo.REQUISITO for e in evs)


def test_parser_idempotente(db_session):
    lic = _criar_licitacao(db_session)
    doc = _doc(db_session, lic, enums.TipoDocumento.EDITAL)
    _trecho(db_session, doc, 1, "LOTE 1")
    _trecho(db_session, doc, 2, "ITEM 1 - Mesa")
    _trecho(db_session, doc, 3, "Quantidade: 5 UN")

    e1 = ParserService(db_session).processar(lic.id)
    lotes1 = db_session.query(Lote).filter(Lote.licitacao_id == lic.id).count()
    itens1 = (
        db_session.query(Item).join(Lote).filter(Lote.licitacao_id == lic.id).count()
    )
    ev1 = db_session.query(EvidenciaParsing).filter(
        EvidenciaParsing.licitacao_id == lic.id
    ).count()

    e2 = ParserService(db_session).processar(lic.id)
    lotes2 = db_session.query(Lote).filter(Lote.licitacao_id == lic.id).count()
    itens2 = (
        db_session.query(Item).join(Lote).filter(Lote.licitacao_id == lic.id).count()
    )
    ev2 = db_session.query(EvidenciaParsing).filter(
        EvidenciaParsing.licitacao_id == lic.id
    ).count()

    assert (lotes1, itens1, ev1) == (lotes2, itens2, ev2)
    assert e1.status.value == e2.status.value


def test_parser_lote_sintetico_sem_lote_explicito(db_session):
    lic = _criar_licitacao(db_session)
    doc = _doc(db_session, lic, enums.TipoDocumento.TERMO_REFERENCIA)
    _trecho(db_session, doc, 1, "ITEM 1 - Cadeira")
    _trecho(db_session, doc, 2, "Quantidade: 4 UN")

    ParserService(db_session).processar(lic.id)
    lote = db_session.query(Lote).filter(Lote.licitacao_id == lic.id).one()
    assert lote.sintetico is True
    assert lote.numero == "UNICO"
    assert lote.documento_origem_id is None


def test_parser_documento_ocr_requerido_nao_gera_estrutura(db_session):
    lic = _criar_licitacao(db_session)
    status_ocr = enums.StatusProcessamento.OCR_REQUIRED
    doc = _doc(db_session, lic, enums.TipoDocumento.EDITAL, status=status_ocr)
    _trecho(db_session, doc, 1, "ITEM 1 - Mesa")

    execucao = ParserService(db_session).processar(lic.id)
    assert execucao.status.value == "PARCIAL"
    assert execucao.itens_criados == 0
    assert "OCR" in (execucao.erros or "")
