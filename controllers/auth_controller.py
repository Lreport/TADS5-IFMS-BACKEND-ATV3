"""Emite e valida os tokens de acesso do aluno."""

from datetime import datetime, timedelta, timezone
from os import getenv
from secrets import token_urlsafe
from typing import Annotated, Literal

import jwt
from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.exc import PasswordSizeError
from passlib.hash import argon2
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_session
from models.user import User


router = APIRouter(tags=["Autenticação"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=30)

# Mantém o custo de verificar a senha mesmo quando o e-mail não está cadastrado.
_DUMMY_PASSWORD_HASH = argon2.hash(token_urlsafe(32))


class Token(BaseModel):
    """Representa o token Bearer retornado pelo login."""

    access_token: str
    token_type: Literal["bearer"] = "bearer"


def get_jwt_secret() -> str:
    """Lê a chave de assinatura configurada no ambiente do servidor.

    Raises:
        HTTPException: Retorna 503 se a chave estiver ausente ou tiver menos de 32 bytes.

    Returns:
        str: Chave usada para assinar o JWT.
    """
    secret = getenv("JWT_SECRET_KEY", "").strip()
    if len(secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autenticação indisponível. Configure JWT_SECRET_KEY no servidor.",
        )
    return secret


def require_authenticated_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    secret: Annotated[str, Depends(get_jwt_secret)],
    session: Annotated[Session, Depends(get_session)],
) -> None:
    """Exige um JWT válido associado a um aluno cadastrado.

    Args:
        token (str): JWT enviado no cabeçalho Authorization.
        secret (str): Chave usada para verificar a assinatura do token.
        session (Session): Sessão usada para consultar a conta do aluno.

    Raises:
        HTTPException: Retorna 401 se o token for inválido ou a conta não existir.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = jwt.decode(
            token,
            secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "iat", "exp"]},
        )
        user_id = int(claims["sub"])
    except (jwt.InvalidTokenError, ValueError) as error:
        raise credentials_error from error

    # O SQLite aceita apenas inteiros de 64 bits para o identificador.
    if not 0 < user_id <= 2**63 - 1 or session.get(User, user_id) is None:
        raise credentials_error


def _authenticate_user(email: str, password: str, session: Session) -> User | None:
    """Busca o aluno pelo e-mail e verifica a senha com o hash cadastrado.

    Args:
        email (str): E-mail informado no formulário.
        password (str): Senha informada no formulário.
        session (Session): Sessão usada para buscar o aluno.

    Returns:
        User | None: Aluno autenticado ou None se as credenciais forem inválidas.
    """
    try:
        email = validate_email(email.strip(), check_deliverability=False).normalized
    except EmailNotValidError:
        return None

    user = session.scalar(select(User).where(User.email == email))
    password_hash = user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
    try:
        password_matches = argon2.verify(password, password_hash)
    except PasswordSizeError:
        return None
    return user if password_matches else None


@router.post("/token", summary="Autenticar o aluno")
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
    secret: Annotated[str, Depends(get_jwt_secret)],
    response: Response,
) -> Token:
    """Autentica o aluno e devolve um token Bearer com validade de 30 minutos.

    Args:
        form (OAuth2PasswordRequestForm): E-mail no campo username e senha em password.
        session (Session): Sessão do banco usada para consultar a conta.
        secret (str): Chave de assinatura do JWT.
        response (Response): Resposta que recebe os cabeçalhos de controle de cache.

    Raises:
        HTTPException: Retorna 401 se as credenciais forem inválidas.

    Returns:
        Token: JWT assinado e tipo de autenticação Bearer.
    """
    user = _authenticate_user(form.username, form.password, session)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    now = datetime.now(timezone.utc)
    claims = {"sub": str(user.id), "iat": now, "exp": now + ACCESS_TOKEN_LIFETIME}
    access_token = jwt.encode(claims, secret, algorithm=JWT_ALGORITHM)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return Token(access_token=access_token)
