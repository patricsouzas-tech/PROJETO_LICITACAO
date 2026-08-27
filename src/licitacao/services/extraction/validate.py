"""Validação de conteúdo de documentos por assinatura, independente de extensão.

Todos os extratores confiam no conteúdo real, nunca apenas na extensão ou no
``Content-Type`` enviado pelo navegador.
"""
from __future__ import annotations

import io
import zipfile

from pypdf import PdfReader

VALID_EXTENSIONS = {"pdf", "docx", "xlsx", "txt"}


class FormatoInvalidoError(ValueError):
    """Conteúdo incompatível com o formato declarado pela extensão."""


def _eh_zip(dados: bytes) -> bool:
    return dados[:2] == b"PK"


def _zip_contem(dados: bytes, membro: str) -> bool:
    try:
        with zipfile.ZipFile(io.BytesIO(dados)) as zf:
            return membro in zf.namematches if hasattr(zf, "namematches") else membro in {
                n.lower() for n in zf.namelist()
            }
    except zipfile.BadZipFile:
        return False


def _tem_nulo(dados: bytes, amostra: int = 8192) -> bool:
    return b"\x00" in dados[: min(amostra, len(dados))]


def _magic_real(dados: bytes) -> str:
    if dados[:5].startswith(b"%PDF-"):
        return "PDF"
    if _eh_zip(dados) and _zip_contem(dados, "word/document.xml"):
        return "DOCX"
    if _eh_zip(dados) and _zip_contem(dados, "xl/workbook.xml"):
        return "XLSX"
    if _tem_nulo(dados):
        return "BINARIO"
    return "TXT"


def validar_pdf(dados: bytes) -> None:
    if not dados[:5].startswith(b"%PDF-"):
        raise FormatoInvalidoError("Conteudo nao corresponde a um PDF (sem assinatura %PDF).")
    try:
        PdfReader(io.BytesIO(dados))
    except Exception as exc:
        raise FormatoInvalidoError(f"pypdf nao conseguiu abrir o PDF: {exc}") from exc


def validar_docx(dados: bytes) -> None:
    if not _eh_zip(dados):
        raise FormatoInvalidoError("DOCX deve ser um arquivo ZIP (OpenXML).")
    if not _zip_contem(dados, "word/document.xml"):
        raise FormatoInvalidoError("DOCX invalido: ausente word/document.xml.")


def validar_xlsx(dados: bytes) -> None:
    if not _eh_zip(dados):
        raise FormatoInvalidoError("XLSX deve ser um arquivo ZIP (OpenXML).")
    if not _zip_contem(dados, "xl/workbook.xml"):
        raise FormatoInvalidoError("XLSX invalido: ausente xl/workbook.xml.")


def validar_txt(dados: bytes) -> None:
    if _tem_nulo(dados):
        raise FormatoInvalidoError("TXT contem bytes NUL: conteudo binario nao suportado.")
    real = _magic_real(dados)
    if real in {"PDF", "DOCX", "XLSX"}:
        raise FormatoInvalidoError(f"TXT renomeado: conteudo detectado como {real}.")


def validar_conteudo(extensao: str, dados: bytes) -> None:
    """Valida ``dados`` contra o formato declarado por ``extensao``.

    Levanta ``FormatoInvalidoError`` se o conteúdo não corresponder.
    """
    ext = (extensao or "").lower().lstrip(".")
    if ext not in VALID_EXTENSIONS:
        raise FormatoInvalidoError(f"Extensao nao suportada: .{ext or '(vazia)'}")
    if ext == "pdf":
        validar_pdf(dados)
    elif ext == "docx":
        validar_docx(dados)
    elif ext == "xlsx":
        validar_xlsx(dados)
    elif ext == "txt":
        validar_txt(dados)
