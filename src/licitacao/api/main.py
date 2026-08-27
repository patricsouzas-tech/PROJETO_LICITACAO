import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..db.models import (
    DocumentoFonte,
    Licitacao,
    TrechoDocumento,
)
from ..db.session import get_db
from ..domain import enums
from ..domain.schemas import (
    DocumentoFonteRead,
    IngestResult,
    LicitacaoCreate,
    LicitacaoRead,
    TrechoDocumentoRead,
)
from ..services.extraction.validate import FormatoInvalidoError
from ..services.ingestion.ingest import ingest_document
from ..services.parsing import ParserService

router = APIRouter(prefix="/api/v1")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/licitacoes", response_model=LicitacaoRead, status_code=201)
def criar_licitacao(payload: LicitacaoCreate, db: Session = Depends(get_db)):
    obj = Licitacao(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/licitacoes", response_model=list[LicitacaoRead])
def listar_licitacoes(db: Session = Depends(get_db)):
    return db.query(Licitacao).order_by(Licitacao.id).all()


@router.get("/licitacoes/{licitacao_id}", response_model=LicitacaoRead)
def obter_licitacao(licitacao_id: int, db: Session = Depends(get_db)):
    obj = db.get(Licitacao, licitacao_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Licitacao nao encontrada")
    return obj


@router.post(
    "/licitacoes/{licitacao_id}/documentos",
    response_model=IngestResult,
)
async def ingerir_documento(
    licitacao_id: int,
    tipo_documento: enums.TipoDocumento = Form(...),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    licitacao = db.get(Licitacao, licitacao_id)
    if licitacao is None:
        raise HTTPException(status_code=404, detail="Licitacao nao encontrada")

    suffix = Path(arquivo.filename).suffix or ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        conteudo = await arquivo.read()
        tmp.write(conteudo)
        tmp_path = tmp.name

    try:
        resultado = ingest_document(
            db,
            licitacao_id,
            tipo_documento,
            tmp_path,
            nome_original=arquivo.filename,
            mime_type=arquivo.content_type,
        )
    except FormatoInvalidoError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if resultado.status == enums.StatusProcessamento.ERRO:
        raise HTTPException(status_code=400, detail=resultado.erro)
    return resultado


@router.get(
    "/licitacoes/{licitacao_id}/documentos",
    response_model=list[DocumentoFonteRead],
)
def listar_documentos(licitacao_id: int, db: Session = Depends(get_db)):
    licitacao = db.get(Licitacao, licitacao_id)
    if licitacao is None:
        raise HTTPException(status_code=404, detail="Licitacao nao encontrada")
    return (
        db.query(DocumentoFonte)
        .filter(DocumentoFonte.licitacao_id == licitacao_id)
        .order_by(DocumentoFonte.id)
        .all()
    )


@router.get("/documentos/{documento_id}", response_model=DocumentoFonteRead)
def obter_documento(documento_id: int, db: Session = Depends(get_db)):
    doc = db.get(DocumentoFonte, documento_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    return doc


@router.post("/licitacoes/{licitacao_id}/parser", status_code=200)
def executar_parser(licitacao_id: int, db: Session = Depends(get_db)):
    licitacao = db.get(Licitacao, licitacao_id)
    if licitacao is None:
        raise HTTPException(status_code=404, detail="Licitacao nao encontrada")
    execucao = ParserService(db).processar(licitacao_id)
    return {
        "execucao_id": execucao.id,
        "status": execucao.status.value,
        "documentos_processados": execucao.documentos_processados,
        "lotes_criados": execucao.lotes_criados,
        "itens_criados": execucao.itens_criados,
        "requisitos_criados": execucao.requisitos_criados,
        "erros": execucao.erros,
        "resumo": execucao.resumo,
    }


@router.get(
    "/documentos/{documento_id}/trechos",
    response_model=list[TrechoDocumentoRead],
)
def listar_trechos(documento_id: int, db: Session = Depends(get_db)):
    doc = db.get(DocumentoFonte, documento_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    return (
        db.query(TrechoDocumento)
        .filter(TrechoDocumento.documento_id == documento_id)
        .order_by(TrechoDocumento.ordem)
        .all()
    )


app = FastAPI(title="PROJETO_LICITACAO", version="0.1.0")
app.include_router(router)
