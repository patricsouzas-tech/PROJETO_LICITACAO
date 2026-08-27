"""Testes de integracao da ingestaio documental (etapa 01)."""
from pathlib import Path

from licitacao.db.models import DocumentoFonte, Licitacao, TrechoDocumento
from licitacao.domain import enums
from licitacao.services.ingestion.ingest import ingest_document


def _criar_licitacao(db_session):
    obj = Licitacao(titulo="Edital Teste", numero_processo="12345/2026")
    db_session.add(obj)
    db_session.commit()
    db_session.refresh(obj)
    return obj


def test_ingestao_txt_cria_documento_e_trechos(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "edital.txt"
    arquivo.write_text("Objeto: compra de cadeiras.\nQuantidade: 10.", encoding="utf-8")

    resultado = ingest_document(
        db_session, lic.id, enums.TipoDocumento.EDITAL, str(arquivo)
    )

    assert resultado.status == enums.StatusProcessamento.CONCLUIDO
    assert resultado.duplicado is False
    assert resultado.trechos_criados >= 1

    doc = db_session.get(DocumentoFonte, resultado.documento_id)
    assert doc is not None
    assert doc.sha256 == resultado.sha256
    assert doc.tamanho_bytes > 0

    trechos = (
        db_session.query(TrechoDocumento)
        .filter(TrechoDocumento.documento_id == doc.id)
        .all()
    )
    assert len(trechos) == resultado.trechos_criados
    assert trechos[0].sha256_texto


def test_ingestao_idempotente_por_sha256(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "edital.txt"
    arquivo.write_text("Texto unico para duplicidade.", encoding="utf-8")

    r1 = ingest_document(db_session, lic.id, enums.TipoDocumento.EDITAL, str(arquivo))
    r2 = ingest_document(db_session, lic.id, enums.TipoDocumento.EDITAL, str(arquivo))

    assert r1.documento_id != r2.documento_id or r1.duplicado is False
    assert r2.duplicado is True
    assert r2.documento_id == r1.documento_id
    assert r2.trechos_criados == r1.trechos_criados


def test_ingestao_formato_invalido_retorna_erro(db_session, tmp_path: Path):
    lic = _criar_licitacao(db_session)
    arquivo = tmp_path / "arquivo.xyz"
    arquivo.write_text("xyz", encoding="utf-8")

    resultado = ingest_document(
        db_session, lic.id, enums.TipoDocumento.OUTRO, str(arquivo)
    )
    assert resultado.status == enums.StatusProcessamento.ERRO
    assert resultado.erro
