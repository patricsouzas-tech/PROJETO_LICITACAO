import hashlib
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.logging import get_logger
from ...db.models import DocumentoFonte, TrechoDocumento
from ...domain import enums
from ...domain.schemas import IngestResult
from ..extraction.extract import extrair

logger = get_logger(__name__)

_EXTENSOES_VALIDAS = {"pdf", "docx", "doc", "xlsx", "xlsm", "txt"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with caminho.open("rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def _armazenar_original(caminho: Path, sha256: str, extensao: str) -> str:
    base = Path(settings.data_dir)
    dest_dir = base / sha256[:2]
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{sha256}.{extensao}"
    if not dest.exists():
        shutil.copy2(caminho, dest)
    return str(dest)


def ingest_document(
    db: Session,
    licitacao_id: int,
    tipo_documento: enums.TipoDocumento,
    arquivo_path: str,
) -> IngestResult:
    caminho = Path(arquivo_path)
    if not caminho.exists():
        return IngestResult(
            documento_id=0,
            sha256="",
            duplicado=False,
            status=enums.StatusProcessamento.ERRO,
            trechos_criados=0,
            precisa_ocr=False,
            erro="Arquivo nao encontrado",
        )

    extensao = caminho.suffix.lstrip(".").lower()
    if extensao not in _EXTENSOES_VALIDAS:
        return IngestResult(
            documento_id=0,
            sha256="",
            duplicado=False,
            status=enums.StatusProcessamento.ERRO,
            trechos_criados=0,
            precisa_ocr=False,
            erro=f"Extensao nao suportada: {extensao}",
        )

    sha256 = _sha256_arquivo(caminho)
    existente = (
        db.query(DocumentoFonte).filter(DocumentoFonte.sha256 == sha256).first()
    )
    if existente is not None:
        return IngestResult(
            documento_id=existente.id,
            sha256=sha256,
            duplicado=True,
            status=existente.status_processamento,
            trechos_criados=len(existente.trechos),
            precisa_ocr=existente.precisa_ocr,
        )

    caminho_armazenado = _armazenar_original(caminho, sha256, extensao)
    doc = DocumentoFonte(
        licitacao_id=licitacao_id,
        tipo_documento=tipo_documento,
        nome_original=caminho.name,
        extensao=extensao,
        tamanho_bytes=caminho.stat().st_size,
        sha256=sha256,
        caminho_armazenado=caminho_armazenado,
        status_processamento=enums.StatusProcessamento.PROCESSANDO,
        precisa_ocr=False,
    )
    db.add(doc)
    db.flush()

    resultado = extrair(caminho, extensao)
    trechos_criados = 0
    if resultado.erro:
        doc.status_processamento = enums.StatusProcessamento.ERRO
        doc.erro_processamento = resultado.erro
    else:
        for i, trecho in enumerate(resultado.trechos, start=1):
            db.add(
                TrechoDocumento(
                    documento_id=doc.id,
                    ordem=i,
                    tipo_localizador=enums.TipoLocalizador(
                        trecho.tipo_localizador
                    ),
                    pagina=trecho.pagina,
                    planilha=trecho.planilha,
                    celula_inicio=trecho.celula_inicio,
                    celula_fim=trecho.celula_fim,
                    paragrafo=trecho.paragrafo,
                    texto_bruto=trecho.texto_bruto,
                    sha256_texto=hashlib.sha256(
                        trecho.texto_bruto.encode("utf-8")
                    ).hexdigest(),
                )
            )
            trechos_criados += 1
        if resultado.precisa_ocr:
            doc.status_processamento = enums.StatusProcessamento.OCR_REQUIRED
            doc.precisa_ocr = True
        else:
            doc.status_processamento = enums.StatusProcessamento.CONCLUIDO

    db.commit()
    db.refresh(doc)
    return IngestResult(
        documento_id=doc.id,
        sha256=sha256,
        duplicado=False,
        status=doc.status_processamento,
        trechos_criados=trechos_criados,
        precisa_ocr=doc.precisa_ocr,
        erro=doc.erro_processamento,
    )
