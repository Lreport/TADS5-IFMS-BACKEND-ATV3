"""Verifica a criacao, a reversao e as restricoes do banco pelas migracoes."""

from io import StringIO

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


def test_initial_migration_upgrade_and_downgrade(migration_config: Config) -> None:
    """Cria um banco vazio, confere os models e permite recriar a tabela.

    Args:
        migration_config (Config): Configuracao do Alembic para o banco temporario.
    """
    command.upgrade(migration_config, "head")
    engine = create_engine(migration_config.get_main_option("sqlalchemy.url"))
    try:
        assert "activities" in inspect(engine).get_table_names()
        command.check(migration_config)
        command.downgrade(migration_config, "base")
        assert "activities" not in inspect(engine).get_table_names()
        command.upgrade(migration_config, "head")
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO activities (title, subject) "
                    "VALUES (:title, :subject)"
                ),
                {"title": "Teste de migracao", "subject": "APIs e Microserviços"},
            )
            activity = connection.execute(
                text("SELECT description, done FROM activities")
            ).one()
            assert activity.description is None
            assert activity.done == 0
    finally:
        engine.dispose()


def test_database_rejects_unknown_subject(database_engine: Engine) -> None:
    """Aplica a lista de disciplinas permitidas tambem no banco.

    Args:
        database_engine (Engine): Engine do banco criado pelas migracoes.
    """
    with database_engine.begin() as connection:
        with pytest.raises(IntegrityError):
            connection.execute(
                text(
                    "INSERT INTO activities (title, subject) "
                    "VALUES (:title, :subject)"
                ),
                {"title": "Atividade", "subject": "Disciplina inexistente"},
            )


def test_user_migration_preserves_existing_activities(migration_config: Config) -> None:
    command.upgrade(migration_config, "50f0ee0bf44c")
    engine = create_engine(migration_config.get_main_option("sqlalchemy.url"))
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO activities (title, subject) VALUES (:title, :subject)"
                ),
                {"title": "Atividade existente", "subject": "Fundamentos de Estatística"},
            )

        command.upgrade(migration_config, "head")
        assert "users" in inspect(engine).get_table_names()
        command.check(migration_config)
        with engine.connect() as connection:
            title = connection.scalar(text("SELECT title FROM activities"))
            assert title == "Atividade existente"

        command.downgrade(migration_config, "50f0ee0bf44c")
        assert "users" not in inspect(engine).get_table_names()
        with engine.connect() as connection:
            title = connection.scalar(text("SELECT title FROM activities"))
            assert title == "Atividade existente"
    finally:
        engine.dispose()


def test_migration_can_generate_sql(migration_config: Config) -> None:
    """Permite gerar o SQL inicial sem conectar ao banco.

    Args:
        migration_config (Config): Configuracao do Alembic usada para gerar o SQL.
    """
    output = StringIO()
    migration_config.output_buffer = output
    command.upgrade(migration_config, "head", sql=True)
    assert "CREATE TABLE activities" in output.getvalue()
