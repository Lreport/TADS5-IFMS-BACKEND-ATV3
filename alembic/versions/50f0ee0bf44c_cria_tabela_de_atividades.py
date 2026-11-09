"""Cria a tabela de atividades.

Revision ID: 50f0ee0bf44c
Revises:
Create Date: 2026-11-02 19:19:49.168327

"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op


# Identificadores usados pelo Alembic para ordenar as migracoes.
revision: str = "50f0ee0bf44c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Aplica as alteracoes na estrutura do banco.
    """
    op.create_table(
        "activities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column(
            "subject",
            sa.Enum(
                "APIs e Microserviços",
                "Agentes Inteligentes",
                "Atividade de Extensão IV",
                "Comunicação Assíncrona e Observabilidade",
                "Frameworks Back-End",
                "Fundamentos de Estatística",
                "Gestão de Projetos",
                name="activity_subject",
                native_enum=False,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("done", sa.Boolean(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sqlite_autoincrement=True,
    )


def downgrade() -> None:
    """Desfaz as alteracoes na estrutura do banco.
    """
    op.drop_table("activities")
