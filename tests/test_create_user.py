"""Verifica a criacao da conta pelo comando local."""

import pytest
from passlib.hash import argon2
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

import create_user
from models.user import User


def test_create_user_stores_hash_and_rejects_second_account(
    database_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica se o cadastro grava o hash e recusa uma segunda conta.

    Args:
        database_engine (Engine): Conexão com o banco temporário dos testes.
        monkeypatch (pytest.MonkeyPatch): Substitui a sessão e as entradas do terminal.
    """
    monkeypatch.setattr(create_user, "SessionLocal", sessionmaker(database_engine))
    emails = iter(("aluno@EXAMPLE.COM", "outro@example.com"))
    password = "abcd"
    monkeypatch.setattr("builtins.input", lambda prompt: next(emails))
    monkeypatch.setattr(create_user, "getpass", lambda prompt: password)

    assert create_user.main() == 0
    assert create_user.main() == 1

    with Session(database_engine) as session:
        user = session.scalars(select(User)).one()
        assert user.email == "aluno@example.com"
        assert user.password_hash.startswith("$argon2id$")
        assert argon2.verify(password, user.password_hash)


@pytest.mark.parametrize(
    ("password", "confirmation"),
    [("abc", "abc"), ("abcd", "efgh")],
    ids=["senha-curta", "confirmacao-diferente"],
)
def test_create_user_rejects_invalid_password(
    database_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
    password: str,
    confirmation: str,
) -> None:
    """Verifica se senhas curtas ou sem confirmação impedem a criação da conta.

    Args:
        database_engine (Engine): Conexão com o banco temporário dos testes.
        monkeypatch (pytest.MonkeyPatch): Substitui a sessão e as entradas do terminal.
        password (str): Senha informada no cadastro.
        confirmation (str): Confirmação informada no cadastro.
    """
    monkeypatch.setattr(create_user, "SessionLocal", sessionmaker(database_engine))
    monkeypatch.setattr("builtins.input", lambda prompt: "aluno@example.com")
    passwords = iter((password, confirmation))
    monkeypatch.setattr(create_user, "getpass", lambda prompt: next(passwords))

    assert create_user.main() == 1

    with Session(database_engine) as session:
        assert session.scalar(select(User)) is None
