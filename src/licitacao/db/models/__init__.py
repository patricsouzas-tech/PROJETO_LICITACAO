from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship

from ...domain import enums
from ..base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Licitacao(Base):
    __tablename__ = "licitacao"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(512), nullable=False)
    numero_processo = Column(String(128), nullable=True)
    orgao = Column(String(512), nullable=True)
    descricao = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    documentos = relationship(
        "DocumentoFonte", back_populates="licitacao", cascade="all, delete-orphan"
    )


class DocumentoFonte(Base):
    __tablename__ = "documento_fonte"

    id = Column(Integer, primary_key=True, autoincrement=True)
    licitacao_id = Column(
        Integer, ForeignKey("licitacao.id", ondelete="CASCADE"), nullable=False
    )
    tipo_documento = Column(SQLEnum(enums.TipoDocumento), nullable=False)
    nome_original = Column(String(512), nullable=False)
    extensao = Column(String(32), nullable=False)
    mime_type = Column(String(128), nullable=True)
    tamanho_bytes = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False, index=True)
    caminho_armazenado = Column(String(1024), nullable=False)
    status_processamento = Column(
        SQLEnum(enums.StatusProcessamento),
        default=enums.StatusProcessamento.RECEBIDO,
        nullable=False,
    )
    precisa_ocr = Column(Boolean, default=False, nullable=False)
    erro_processamento = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    licitacao = relationship("Licitacao", back_populates="documentos")
    trechos = relationship(
        "TrechoDocumento",
        back_populates="documento",
        cascade="all, delete-orphan",
        order_by="TrechoDocumento.ordem",
    )


class TrechoDocumento(Base):
    __tablename__ = "trecho_documento"

    id = Column(Integer, primary_key=True, autoincrement=True)
    documento_id = Column(
        Integer, ForeignKey("documento_fonte.id", ondelete="CASCADE"), nullable=False
    )
    ordem = Column(Integer, nullable=False)
    tipo_localizador = Column(SQLEnum(enums.TipoLocalizador), nullable=False)
    pagina = Column(Integer, nullable=True)
    planilha = Column(String(128), nullable=True)
    celula_inicio = Column(String(16), nullable=True)
    celula_fim = Column(String(16), nullable=True)
    paragrafo = Column(Integer, nullable=True)
    texto_bruto = Column(Text, nullable=False)
    sha256_texto = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)

    documento = relationship("DocumentoFonte", back_populates="trechos")


class Lote(Base):
    __tablename__ = "lote"

    id = Column(Integer, primary_key=True, autoincrement=True)
    licitacao_id = Column(
        Integer, ForeignKey("licitacao.id", ondelete="CASCADE"), nullable=False
    )
    numero = Column(String(32), nullable=False)
    titulo = Column(String(512), nullable=True)
    descricao = Column(Text, nullable=True)

    itens = relationship(
        "Item", back_populates="lote", cascade="all, delete-orphan"
    )


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lote_id = Column(
        Integer, ForeignKey("lote.id", ondelete="CASCADE"), nullable=False
    )
    numero = Column(String(32), nullable=False)
    descricao_original = Column(Text, nullable=True)
    quantidade = Column(Numeric(18, 6), nullable=True)
    unidade = Column(String(16), nullable=True)

    lote = relationship("Lote", back_populates="itens")
    requisitos = relationship(
        "RequisitoTecnico", back_populates="item", cascade="all, delete-orphan"
    )


class RequisitoTecnico(Base):
    __tablename__ = "requisito_tecnico"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(
        Integer, ForeignKey("item.id", ondelete="CASCADE"), nullable=False
    )
    texto_original = Column(Text, nullable=False)
    texto_normalizado = Column(Text, nullable=True)
    obrigatorio = Column(Boolean, default=True, nullable=False)
    documento_origem_id = Column(
        Integer, ForeignKey("documento_fonte.id"), nullable=True
    )
    trecho_origem_id = Column(
        Integer, ForeignKey("trecho_documento.id"), nullable=True
    )

    item = relationship("Item", back_populates="requisitos")
    validacoes = relationship(
        "ValidacaoRequisito", back_populates="requisito", cascade="all, delete-orphan"
    )


class ProdutoCandidato(Base):
    __tablename__ = "produto_candidato"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requisito_id = Column(
        Integer, ForeignKey("requisito_tecnico.id", ondelete="CASCADE"), nullable=False
    )
    descricao = Column(Text, nullable=True)


class Oferta(Base):
    __tablename__ = "oferta"

    id = Column(Integer, primary_key=True, autoincrement=True)
    produto_candidato_id = Column(
        Integer, ForeignKey("produto_candidato.id", ondelete="CASCADE"), nullable=False
    )
    marketplace = Column(SQLEnum(enums.Marketplace), nullable=False)
    url = Column(String(2048), nullable=True)
    vendedor = Column(String(256), nullable=True)
    preco_unitario = Column(Numeric(18, 6), nullable=True)
    frete = Column(Numeric(18, 6), nullable=True)
    outros_custos = Column(Numeric(18, 6), nullable=True)
    valor_unitario_final = Column(Numeric(18, 6), nullable=True)
    quantidade_disponivel = Column(Integer, nullable=True)
    data_coleta = Column(DateTime(timezone=True), nullable=True)
    condicao = Column(SQLEnum(enums.CondicaoProduto), nullable=True)
    lacrado = Column(SQLEnum(enums.SimNaoConfirmado), nullable=True)
    caixa_original = Column(SQLEnum(enums.SimNaoConfirmado), nullable=True)
    nota_fiscal = Column(SQLEnum(enums.NotaFiscal), nullable=True)


class ValidacaoRequisito(Base):
    __tablename__ = "validacao_requisito"

    id = Column(Integer, primary_key=True, autoincrement=True)
    requisito_id = Column(
        Integer, ForeignKey("requisito_tecnico.id", ondelete="CASCADE"), nullable=False
    )
    oferta_id = Column(Integer, ForeignKey("oferta.id"), nullable=True)
    resultado = Column(SQLEnum(enums.ValidacaoResultado), nullable=False)
    observacao = Column(Text, nullable=True)

    requisito = relationship("RequisitoTecnico", back_populates="validacoes")
