"""initial schema (deterministic)

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from licitacao.domain import enums


revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "licitacao",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("titulo", sa.String(512), nullable=False),
        sa.Column("numero_processo", sa.String(128), nullable=True),
        sa.Column("orgao", sa.String(512), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "documento_fonte",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "licitacao_id",
            sa.Integer(),
            sa.ForeignKey("licitacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tipo_documento",
            sa.Enum(enums.TipoDocumento, native_enum=False),
            nullable=False,
        ),
        sa.Column("nome_original", sa.String(512), nullable=False),
        sa.Column("extensao", sa.String(32), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=True),
        sa.Column("tamanho_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("caminho_armazenado", sa.String(1024), nullable=False),
        sa.Column(
            "status_processamento",
            sa.Enum(enums.StatusProcessamento, native_enum=False),
            nullable=False,
        ),
        sa.Column("precisa_ocr", sa.Boolean(), nullable=False),
        sa.Column("erro_processamento", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("licitacao_id", "sha256", name="uq_documento_licitacao_sha"),
    )
    op.create_index("ix_documento_fonte_sha256", "documento_fonte", ["sha256"])

    op.create_table(
        "trecho_documento",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "documento_id",
            sa.Integer(),
            sa.ForeignKey("documento_fonte.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("ordem", sa.Integer(), nullable=False),
        sa.Column(
            "tipo_localizador",
            sa.Enum(enums.TipoLocalizador, native_enum=False),
            nullable=False,
        ),
        sa.Column("pagina", sa.Integer(), nullable=True),
        sa.Column("planilha", sa.String(128), nullable=True),
        sa.Column("celula_inicio", sa.String(16), nullable=True),
        sa.Column("celula_fim", sa.String(16), nullable=True),
        sa.Column("paragrafo", sa.Integer(), nullable=True),
        sa.Column("tabela", sa.String(128), nullable=True),
        sa.Column("linha_tabela", sa.Integer(), nullable=True),
        sa.Column("texto_bruto", sa.Text(), nullable=False),
        sa.Column("sha256_texto", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "lote",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "licitacao_id",
            sa.Integer(),
            sa.ForeignKey("licitacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("numero", sa.String(32), nullable=False),
        sa.Column("titulo", sa.String(512), nullable=True),
        sa.Column("descricao", sa.Text(), nullable=True),
    )

    op.create_table(
        "item",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "lote_id",
            sa.Integer(),
            sa.ForeignKey("lote.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("numero", sa.String(32), nullable=False),
        sa.Column("descricao_original", sa.Text(), nullable=True),
        sa.Column("quantidade", sa.Numeric(18, 6), nullable=True),
        sa.Column("unidade", sa.String(16), nullable=True),
    )

    op.create_table(
        "requisito_tecnico",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("item.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("texto_original", sa.Text(), nullable=False),
        sa.Column("texto_normalizado", sa.Text(), nullable=True),
        sa.Column("obrigatorio", sa.Boolean(), nullable=False),
        sa.Column(
            "documento_origem_id",
            sa.Integer(),
            sa.ForeignKey("documento_fonte.id"),
            nullable=True,
        ),
        sa.Column(
            "trecho_origem_id",
            sa.Integer(),
            sa.ForeignKey("trecho_documento.id"),
            nullable=True,
        ),
    )

    op.create_table(
        "produto_candidato",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "item_id",
            sa.Integer(),
            sa.ForeignKey("item.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("descricao", sa.Text(), nullable=True),
    )

    op.create_table(
        "oferta",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "produto_candidato_id",
            sa.Integer(),
            sa.ForeignKey("produto_candidato.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "marketplace",
            sa.Enum(enums.Marketplace, native_enum=False),
            nullable=False,
        ),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("vendedor", sa.String(256), nullable=True),
        sa.Column("preco_unitario", sa.Numeric(18, 6), nullable=True),
        sa.Column("frete", sa.Numeric(18, 6), nullable=True),
        sa.Column("outros_custos", sa.Numeric(18, 6), nullable=True),
        sa.Column("valor_unitario_final", sa.Numeric(18, 6), nullable=True),
        sa.Column("quantidade_disponivel", sa.Integer(), nullable=True),
        sa.Column("data_coleta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("condicao", sa.Enum(enums.CondicaoProduto, native_enum=False), nullable=True),
        sa.Column("lacrado", sa.Enum(enums.SimNaoConfirmado, native_enum=False), nullable=True),
        sa.Column(
            "caixa_original", sa.Enum(enums.SimNaoConfirmado, native_enum=False), nullable=True
        ),
        sa.Column("nota_fiscal", sa.Enum(enums.NotaFiscal, native_enum=False), nullable=True),
    )

    op.create_table(
        "validacao_requisito",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "requisito_id",
            sa.Integer(),
            sa.ForeignKey("requisito_tecnico.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "produto_candidato_id",
            sa.Integer(),
            sa.ForeignKey("produto_candidato.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("oferta_id", sa.Integer(), sa.ForeignKey("oferta.id"), nullable=True),
        sa.Column(
            "resultado",
            sa.Enum(enums.ValidacaoResultado, native_enum=False),
            nullable=False,
        ),
        sa.Column("observacao", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("validacao_requisito")
    op.drop_table("oferta")
    op.drop_table("produto_candidato")
    op.drop_table("requisito_tecnico")
    op.drop_table("item")
    op.drop_table("lote")
    op.drop_table("trecho_documento")
    op.drop_index("ix_documento_fonte_sha256", table_name="documento_fonte")
    op.drop_table("documento_fonte")
    op.drop_table("licitacao")
