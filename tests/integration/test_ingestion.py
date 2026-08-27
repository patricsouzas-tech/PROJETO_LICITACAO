"""Testes de integracao da ingestaio documental (ETAPA 01B)."""
from pathlib import Path

import pytest

from licitacao.db.models import DocumentoFonte, Licitacao, TrechoDocumento
from licitacao.domain import enums
from licitacao.services.extraction.validate import FormatoInvalidoError
from licitacao.services.ingestion.ingest import ingest_document


def _criar_licitacao(db_session, titulo="Edital Teste"):
    obj = Licitacao(titulo=titulo, numero_processo="12345/2026")
    db_session.add(obj)
    db_session.commit()
    db_session.refresh(obj)
    return obj


def test_ingestao_txt_cria_documento_e_trechos(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "edital.txt"
    arquivo.write_text("Objeto: compra de cadeiras.\nQuantidade: 10.", encoding="utf-8")

    r = ingest_document(db_session, lic.id, enums.TipoDocumento.EDITAL, str(arquivo))

    assert r.status == enums.StatusProcessamento.CONCLUIDO
    assert r.duplicado is False
    assert r.trechos_criados >= 1

    doc = db_session.get(DocumentoFonte, r.documento_id)
    assert doc is not None
    assert doc.sha256 == r.sha256
    trechos = (
        db_session.query(TrechoDocumento)
        .filter(TrechoDocumento.documento_id == doc.id)
        .all()
    )
    assert len(trechos) == r.trechos_criados
    assert trechos[0].sha256_texto


def test_conteudo_pdf_invalido_levanta_erro_sem_criar_documento(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "TERMO DE REFERENCIA.pdf"
    arquivo.write_bytes(b"%PDF-1.4 fake")
    # conteudo incompativel com a extensao -> ERRO fatal, sem persistir documento
    with pytest.raises(FormatoInvalidoError):
        ingest_document(
            db_session,
            lic.id,
            enums.TipoDocumento.TERMO_REFERENCIA,
            str(arquivo),
            nome_original="TERMO DE REFERENCIA.pdf",
            mime_type="application/pdf",
        )
    assert db_session.query(DocumentoFonte).all() == []


def test_deduplicacao_mesma_licitacao(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "edital.txt"
    arquivo.write_text("Texto unico para duplicidade.", encoding="utf-8")

    r1 = ingest_document(db_session, lic.id, enums.TipoDocumento.EDITAL, str(arquivo))
    r2 = ingest_document(db_session, lic.id, enums.TipoDocumento.EDITAL, str(arquivo))

    assert r2.duplicado is True
    assert r2.documento_id == r1.documento_id
    assert r2.trechos_criados == r1.trechos_criados


def test_mesmo_sha_licitacoes_diferentes_documentos_distintos(db_session, tmp_path: Path):
    lic_a = _criar_licitacao(db_session, "A")
    lic_b = _criar_licitacao(db_session, "B")
    arquivo = tmp_path / "edital.txt"
    arquivo.write_text("Texto identico em duas licitacoes.", encoding="utf-8")

    r_a = ingest_document(db_session, lic_a.id, enums.TipoDocumento.EDITAL, str(arquivo))
    r_b = ingest_document(db_session, lic_b.id, enums.TipoDocumento.EDITAL, str(arquivo))

    assert r_a.documento_id != r_b.documento_id
    doc_a = db_session.get(DocumentoFonte, r_a.documento_id)
    doc_b = db_session.get(DocumentoFonte, r_b.documento_id)
    assert doc_a.licitacao_id == lic_a.id
    assert doc_b.licitacao_id == lic_b.id
    assert doc_a.sha256 == doc_b.sha256


def test_formato_invalido_retorna_erro(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "arquivo.xyz"
    arquivo.write_text("xyz", encoding="utf-8")

    r = ingest_document(db_session, lic.id, enums.TipoDocumento.OUTRO, str(arquivo))
    assert r.status == enums.StatusProcessamento.ERRO
    assert r.erro


def test_doc_antigo_nao_suportado(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "antigo.doc"
    arquivo.write_bytes(b"doc binario fake")

    r = ingest_document(db_session, lic.id, enums.TipoDocumento.OUTRO, str(arquivo))
    assert r.status == enums.StatusProcessamento.ERRO
    assert "nao suportada" in r.erro
