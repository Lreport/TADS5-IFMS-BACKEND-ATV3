"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence

import sqlalchemy as sa
from alembic import op
${imports if imports else ""}

# Identificadores usados pelo Alembic para ordenar as migracoes.
revision: str = ${repr(up_revision)}
down_revision: str | Sequence[str] | None = ${repr(down_revision)}
branch_labels: str | Sequence[str] | None = ${repr(branch_labels)}
depends_on: str | Sequence[str] | None = ${repr(depends_on)}


def upgrade() -> None:
    """Aplica as alteracoes na estrutura do banco."""
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """Desfaz as alteracoes na estrutura do banco."""
    ${downgrades if downgrades else "pass"}
