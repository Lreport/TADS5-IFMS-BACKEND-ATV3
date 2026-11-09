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
    monkeypatch.setattr(create_user, "SessionLocal", sessionmaker(database_engine))
    emails = iter(("aluno@EXAMPLE.COM", "outro@example.com"))
    password = "senha de teste longa"
    monkeypatch.setattr("builtins.input", lambda prompt: next(emails))
    monkeypatch.setattr(create_user, "getpass", lambda prompt: password)

    assert create_user.main() == 0
    assert create_user.main() == 1

    with Session(database_engine) as session:
        user = session.scalars(select(User)).one()
        assert user.email == "aluno@example.com"
        assert user.password_hash.startswith("$argon2id$")
        assert argon2.verify(password, user.password_hash)


def test_create_user_rejects_different_passwords(
    database_engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(create_user, "SessionLocal", sessionmaker(database_engine))
    monkeypatch.setattr("builtins.input", lambda prompt: "aluno@example.com")
    passwords = iter(("senha de teste longa", "outra senha de teste"))
    monkeypatch.setattr(create_user, "getpass", lambda prompt: next(passwords))

    assert create_user.main() == 1

    with Session(database_engine) as session:
        assert session.scalar(select(User)) is None
