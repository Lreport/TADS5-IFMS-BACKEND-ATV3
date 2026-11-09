"""Define a conta do aluno no banco de dados."""

from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    """Armazena o e-mail e o hash da senha da conta."""

    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254))
    password_hash: Mapped[str] = mapped_column(Text)
