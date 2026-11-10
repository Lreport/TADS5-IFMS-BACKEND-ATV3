"""Cria a conta do aluno a partir de credenciais digitadas no terminal."""

import sys
from getpass import GetPassWarning, getpass
from warnings import catch_warnings, simplefilter

from email_validator import EmailNotValidError, validate_email
from passlib.exc import PasswordSizeError
from passlib.hash import argon2
from sqlalchemy.exc import IntegrityError

from database import SessionLocal
from models.user import User


# As execucoes do comando disputam a mesma chave, mesmo se forem simultaneas.
STUDENT_USER_ID = 1
MIN_PASSWORD_LENGTH = 4


def main() -> int:
    """Cria a conta do aluno com as credenciais informadas no terminal.

    Returns:
        int: 0 quando a conta é criada ou 1 quando o cadastro é recusado ou cancelado.
    """
    with SessionLocal() as session:
        if session.get(User, STUDENT_USER_ID) is not None:
            print("Já existe uma conta de aluno.", file=sys.stderr)
            return 1

    try:
        email = validate_email(
            input("E-mail do aluno: ").strip(), check_deliverability=False
        ).normalized
        with catch_warnings():
            simplefilter("error", GetPassWarning)
            password = getpass(f"Senha (mínimo de {MIN_PASSWORD_LENGTH} caracteres): ")
            confirmation = getpass("Confirme a senha: ")
    except EmailNotValidError:
        print("Informe um endereço de e-mail válido.", file=sys.stderr)
        return 1
    except (EOFError, GetPassWarning):
        print("Execute o comando em um terminal interativo.", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCriação da conta cancelada.", file=sys.stderr)
        return 1

    if len(password) < MIN_PASSWORD_LENGTH or not password.strip():
        print(
            f"Informe uma senha preenchida com pelo menos {MIN_PASSWORD_LENGTH} caracteres.",
            file=sys.stderr,
        )
        return 1
    if password != confirmation:
        print("As senhas não coincidem.", file=sys.stderr)
        return 1

    try:
        password_hash = argon2.hash(password)
        user = User(id=STUDENT_USER_ID, email=email, password_hash=password_hash)
        with SessionLocal.begin() as session:
            session.add(user)
    except PasswordSizeError:
        print("A senha excede o tamanho aceito pelo Passlib.", file=sys.stderr)
        return 1
    except IntegrityError:
        print("Já existe uma conta de aluno ou esse e-mail está em uso.", file=sys.stderr)
        return 1

    print("Conta de aluno criada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
