"""Prepara um banco temporario e uma sessao isolada para os testes."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from database import get_session
from main import app


@pytest.fixture
def migration_config(tmp_path: Path) -> Config:
    """Aponta as migracoes para um arquivo SQLite temporario.

    Args:
        tmp_path (Path): Diretorio temporario exclusivo do teste.

    Returns:
        Config: Configuracao do Alembic para o banco temporario.
    """
    project_path = Path(__file__).resolve().parents[1]
    config = Config(str(project_path / "alembic.ini"))
    database_path = tmp_path / "activities.db"
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    return config


@pytest.fixture
def database_engine(migration_config: Config) -> Iterator[Engine]:
    """Cria as tabelas pelas migracoes e libera as conexoes ao terminar.

    Args:
        migration_config (Config): Configuracao do Alembic para o banco temporario.

    Yields:
        Engine: Engine do banco temporario, liberado ao terminar o teste.
    """
    command.upgrade(migration_config, "head")
    engine = create_engine(
        migration_config.get_main_option("sqlalchemy.url"),
        connect_args={"check_same_thread": False},
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def client(database_engine: Engine) -> Iterator[TestClient]:
    """Fornece um cliente HTTP que usa somente o banco temporario.

    Args:
        database_engine (Engine): Engine do banco temporario usado nas requisicoes.

    Yields:
        TestClient: Cliente da API com a dependencia de sessao substituida.
    """
    def get_test_session() -> Iterator[Session]:
        """Fornece uma sessao isolada para cada requisicao de teste.

        Yields:
            Session: Sessao do banco temporario, fechada ao terminar a requisicao.
        """
        with Session(database_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_session, None)
