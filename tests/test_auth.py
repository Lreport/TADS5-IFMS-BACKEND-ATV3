"""Verifica o login e o controle de acesso aos endpoints HTTP."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from passlib.hash import argon2
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from models.user import User


EMAIL = "aluno@example.com"
PASSWORD = "senha de teste longa"
TEST_SECRET = "chave-para-testes-do-jwt-sem-uso-real"


@pytest.fixture
def student(database_engine: Engine, monkeypatch: pytest.MonkeyPatch) -> int:
    """Cria o aluno de teste e configura uma chave de assinatura para o login.

    Args:
        database_engine (Engine): Conexão com o banco temporário dos testes.
        monkeypatch (pytest.MonkeyPatch): Configura a chave no ambiente do teste.

    Returns:
        int: Identificador do aluno cadastrado.
    """
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    with Session(database_engine) as session:
        user = User(email=EMAIL, password_hash=argon2.hash(PASSWORD))
        session.add(user)
        session.flush()
        user_id = user.id
        session.commit()
    return user_id


def test_login_returns_signed_token(client: TestClient, student: int) -> None:
    """Verifica assinatura, identificação do aluno e validade do token.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporário.
        student (int): Identificador esperado no campo sub do JWT.
    """
    response = client.post(
        "/token", data={"username": "aluno@EXAMPLE.COM", "password": PASSWORD}
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Pragma"] == "no-cache"
    body = response.json()
    assert body["token_type"] == "bearer"
    claims = jwt.decode(
        body["access_token"],
        TEST_SECRET,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp"]},
    )
    assert claims["sub"] == str(student)
    assert claims["exp"] - claims["iat"] == 30 * 60


def test_login_rejects_invalid_credentials(client: TestClient, student: int) -> None:
    """Verifica se as credenciais inválidas recebem a mesma resposta de erro.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporário.
        student (int): Identificador da conta criada para testar senhas incorretas.
    """
    for email, password in (
        (EMAIL, "senha incorreta"),
        ("outro@example.com", PASSWORD),
        (EMAIL, "a" * 5000),
    ):
        response = client.post("/token", data={"username": email, "password": password})

        assert response.status_code == 401
        assert response.headers["WWW-Authenticate"] == "Bearer"
        assert response.json() == {"detail": "E-mail ou senha inválidos."}


def test_login_requires_secret(
    client: TestClient, student: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verifica se o servidor recusa a emissão quando a chave está ausente.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporário.
        student (int): Identificador da conta criada para enviar credenciais válidas.
        monkeypatch (pytest.MonkeyPatch): Remove a chave do ambiente do teste.
    """
    monkeypatch.delenv("JWT_SECRET_KEY")

    response = client.post("/token", data={"username": EMAIL, "password": PASSWORD})

    assert response.status_code == 503
    assert "access_token" not in response.json()


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/activities"),
        ("GET", "/activities/1"),
        ("POST", "/activities"),
        ("PUT", "/activities/1"),
        ("DELETE", "/activities/1"),
    ],
)
def test_activity_routes_require_token(client: TestClient, method: str, path: str) -> None:
    """Verifica se cada rota de atividade recusa acesso sem token.

    Args:
        client (TestClient): Cliente HTTP sem autenticação.
        method (str): Método HTTP da operação.
        path (str): Caminho da rota testada.
    """
    response = client.request(method, path)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


@pytest.mark.parametrize("failure", ["signature", "expired", "unknown_user", "no_exp"])
def test_activity_rejects_invalid_token(
    client: TestClient, student: int, failure: str
) -> None:
    """Verifica se a API rejeita tokens que não atendem às regras de acesso.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporário.
        student (int): Identificador da conta usada como referência.
        failure (str): Condição que torna o token inválido.
    """
    now = datetime.now(timezone.utc)
    subject = str(student + 1 if failure == "unknown_user" else student)
    expires = now + timedelta(seconds=-1 if failure == "expired" else 300)
    claims = {"sub": subject, "iat": now - timedelta(minutes=1), "exp": expires}
    if failure == "no_exp":
        del claims["exp"]
    secret = TEST_SECRET + "-different" if failure == "signature" else TEST_SECRET
    token = jwt.encode(claims, secret, algorithm="HS256")

    response = client.get("/activities", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
