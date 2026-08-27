import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.models import DocumentoFonte, Licitacao, TrechoDocumento
from ..db.session import get_db
from ..domain import enums
from ..domain.schemas import (
    IngestResult,
    LicitacaoCreate,
    LicitacaoRead,
)
from ..services.ingestion.ingest import ingest_document

router = APIRouter()


@router.post("/licitacoes", response_model=LicitacaoRead, status_code=201)
def criar_licitacao(payload: LicitacaoCreate, db: Session = Depends(get_db)):
    obj = Licitacao(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/licitacoes/{licitacao_id}", response_model=LicitacaoRead)
def obter_licitacao(licitacao_id: int, db: Session = Depends(get_db)):
    obj = db.get(Licitacao, licitacao_id)
    if obj is None:
        raise HTTPException(status_code=404, detail="Licitacao nao encontrada")
    return obj


@router.post("/licitacoes/{licitacao_id}/documentos/ingest", response_model=IngestResult)
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
            db, licitacao_id, tipo_documento, tmp_path
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if resultado.status == enums.StatusProcessamento.ERRO:
        raise HTTPException(status_code=400, detail=resultado.erro)
    return resultado


@router.get("/documentos/{documento_id}/trechos")
def listar_trechos(documento_id: int, db: Session = Depends(get_db)):
    doc = db.get(DocumentoFonte, documento_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento nao encontrado")
    trechos = (
        db.query(TrechoDocumento)
        .filter(TrechoDocumento.documento_id == documento_id)
        .order_by(TrechoDocumento.ordem)
        .all()
    )
    return [
        {
            "id": t.id,
            "ordem": t.ordem,
            "tipo_localizador": t.tipo_localizador.value,
            "pagina": t.pagina,
            "planilha": t.planilha,
            "celula_inicio": t.celula_inicio,
            "celula_fim": t.celula_fim,
            "paragrafo": t.paragrafo,
            "texto_bruto": t.texto_bruto,
            "sha256_texto": t.sha256_texto,
        }
        for t in trechos
    ]


app = FastAPI(title="PROJETO_LICITACAO", version="0.1.0")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "database_url": settings.database_url}
