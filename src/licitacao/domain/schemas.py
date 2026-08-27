from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from .enums import (
    StatusProcessamento,
    TipoDocumento,
    TipoLocalizador,
    ValidacaoResultado,
)


class LicitacaoBase(BaseModel):
    titulo: str
    numero_processo: str | None = None
    orgao: str | None = None
    descricao: str | None = None


class LicitacaoCreate(LicitacaoBase):
    pass


class LicitacaoRead(LicitacaoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime


class DocumentoFonteBase(BaseModel):
    licitacao_id: int
    tipo_documento: TipoDocumento
    nome_original: str
    extensao: str
    mime_type: str | None = None
    tamanho_bytes: int
    sha256: str
    caminho_armazenado: str
    status_processamento: StatusProcessamento = StatusProcessamento.RECEBIDO
    precisa_ocr: bool = False
    erro_processamento: str | None = None


class DocumentoFonteRead(DocumentoFonteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class TrechoDocumentoBase(BaseModel):
    documento_id: int
    ordem: int
    tipo_localizador: TipoLocalizador
    pagina: int | None = None
    planilha: str | None = None
    celula_inicio: str | None = None
    celula_fim: str | None = None
    paragrafo: int | None = None
    texto_bruto: str
    sha256_texto: str


class TrechoDocumentoRead(TrechoDocumentoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class IngestResult(BaseModel):
    documento_id: int
    sha256: str
    duplicado: bool
    status: StatusProcessamento
    trechos_criados: int
    precisa_ocr: bool
    erro: str | None = None


class ItemBase(BaseModel):
    lote_id: int
    numero: str
    descricao_original: str | None = None
    quantidade: Decimal | None = None
    unidade: str | None = None


class ItemRead(ItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class ValidacaoRequisitoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    requisito_id: int
    produto_candidato_id: int
    resultado: ValidacaoResultado


class OfertaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    produto_candidato_id: int
    marketplace: str
    preco_unitario: Decimal | None = None
