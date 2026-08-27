"""parser rastreavel: rastreabilidade de lote/item, evidencias e execucao

Revision ID: 0002_parser_rastreabilidade
Revises: 0001_initial
Create Date: 2026-08-27 00:10:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002_parser_rastreabilidade"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ENTIDADE = ("LOTE", "ITEM", "REQUISITO")
_STATUS_PARSING = ("INICIADO", "CONCLUIDO", "PARCIAL", "ERRO")


def upgrade() -> None:
    op.add_column(
        "lote",
        sa.Column("sintetico", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "lote",
        sa.Column("documento_origem_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "lote",
        sa.Column("trecho_origem_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "lote",
        sa.Column("fingerprint", sa.String(64), nullable=True),
    )
    op.create_index("ix_lote_fingerprint", "lote", ["fingerprint"])

    op.add_column(
        "item",
        sa.Column("unidade_original", sa.String(32), nullable=True),
    )
    op.add_column(
        "item",
        sa.Column("unidade_normalizada", sa.String(32), nullable=True),
    )
    op.add_column(
        "item",
        sa.Column("documento_origem_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "item",
        sa.Column("trecho_origem_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "item",
        sa.Column("fingerprint", sa.String(64), nullable=True),
    )
    op.create_index("ix_item_fingerprint", "item", ["fingerprint"])

    op.add_column(
        "requisito_tecnico",
        sa.Column("fingerprint", sa.String(64), nullable=True),
    )
    op.create_index(
        "ix_requisito_tecnico_fingerprint", "requisito_tecnico", ["fingerprint"]
    )

    op.create_table(
        "evidencia_parsing",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "licitacao_id",
            sa.Integer(),
            sa.ForeignKey("licitacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "entidade_tipo",
            sa.Enum(*_ENTIDADE, native_enum=False),
            nullable=False,
        ),
        sa.Column("entidade_id", sa.Integer(), nullable=False),
        sa.Column("campo", sa.String(64), nullable=False),
        sa.Column(
            "documento_id",
            sa.Integer(),
            sa.ForeignKey("documento_fonte.id"),
            nullable=True,
        ),
        sa.Column(
            "trecho_id",
            sa.Integer(),
            sa.ForeignKey("trecho_documento.id"),
            nullable=True,
        ),
        sa.Column("ordem", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("texto_evidencia", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_evidencia_fingerprint"),
    )
    op.create_index(
        "ix_evidencia_parsing_fingerprint", "evidencia_parsing", ["fingerprint"]
    )

    op.create_table(
        "execucao_parsing",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "licitacao_id",
            sa.Integer(),
            sa.ForeignKey("licitacao.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("iniciado_em", sa.DateTime(timezone=True), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "status",
            sa.Enum(*_STATUS_PARSING, native_enum=False),
            nullable=False,
            server_default="INICIADO",
        ),
        sa.Column("documentos_processados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("lotes_criados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("itens_criados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("requisitos_criados", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("erros", sa.Text(), nullable=True),
        sa.Column("resumo", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("execucao_parsing")
    op.drop_index("ix_evidencia_parsing_fingerprint", table_name="evidencia_parsing")
    op.drop_table("evidencia_parsing")
    op.drop_index("ix_requisito_tecnico_fingerprint", table_name="requisito_tecnico")
    op.drop_column("requisito_tecnico", "fingerprint")
    op.drop_index("ix_item_fingerprint", table_name="item")
    op.drop_column("item", "trecho_origem_id")
    op.drop_column("item", "documento_origem_id")
    op.drop_column("item", "unidade_normalizada")
    op.drop_column("item", "unidade_original")
    op.drop_column("item", "fingerprint")
    op.drop_index("ix_lote_fingerprint", table_name="lote")
    op.drop_column("lote", "trecho_origem_id")
    op.drop_column("lote", "documento_origem_id")
    op.drop_column("lote", "sintetico")
    op.drop_column("lote", "fingerprint")
