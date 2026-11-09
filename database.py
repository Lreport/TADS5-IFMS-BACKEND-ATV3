"""Configura a conexao com o SQLite e as sessoes do banco de dados."""

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_PATH = Path(__file__).resolve().parent / "activities.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Reune os metadados dos models usados nas migracoes."""


def get_session() -> Iterator[Session]:
    """Fornece uma sessao do banco para cada requisicao.

    Yields:
        Session: Sessao fechada automaticamente ao terminar a requisicao.
    """
    with SessionLocal() as session:
        yield session
