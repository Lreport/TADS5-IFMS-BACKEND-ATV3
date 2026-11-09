"""Configura as migracoes com os metadados e a conexao da aplicacao."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from database import DATABASE_URL, Base
from models import activity, user  # Importa os modelos para registrar as tabelas.


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
database_url = config.get_main_option("sqlalchemy.url") or DATABASE_URL


def run_migrations_offline() -> None:
    """Gera o SQL das migracoes sem abrir uma conexao com o banco.
    """
    context.configure(
        url=database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Aplica as migracoes usando uma conexao com o banco.
    """
    connectable = create_engine(database_url, poolclass=pool.NullPool)
    try:
        with connectable.connect() as connection:
            context.configure(
                connection=connection,
                target_metadata=target_metadata,
                render_as_batch=True,
            )

            with context.begin_transaction():
                context.run_migrations()
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
