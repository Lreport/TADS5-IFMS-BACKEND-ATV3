"""Cria a tabela de usuarios.

Revision ID: 68e41228dfa0
Revises: 50f0ee0bf44c
"""

import sqlalchemy as sa
from alembic import op


revision = "68e41228dfa0"
down_revision = "50f0ee0bf44c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria a tabela de usuários com e-mail único e hash de senha obrigatório."""
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )


def downgrade() -> None:
    """Remove a tabela de usuários e os dados armazenados nela."""
    op.drop_table("users")
