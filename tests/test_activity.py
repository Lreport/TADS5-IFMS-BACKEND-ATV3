"""Verifica o contrato HTTP das atividades e a persistencia no SQLite."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from models.activity import Subject


def test_create_and_get_activity(client: TestClient) -> None:
    """Mantem o formulario, os campos de saida e a validacao de espacos.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
    """
    response = client.post(
        "/activities",
        data={
            "title": "  Atividade de banco de dados  ",
            "subject": Subject.APIS_AND_MICROSERVICES.value,
            "description": "  Configurar SQLite  ",
        },
    )
    assert response.status_code == 201
    activity = response.json()
    assert activity == {
        "id": activity["id"],
        "title": "Atividade de banco de dados",
        "subject": Subject.APIS_AND_MICROSERVICES.value,
        "description": "Configurar SQLite",
        "done": False,
    }
    assert activity["id"] > 0
    response = client.get(f"/activities/{activity['id']}")
    assert response.status_code == 200
    assert response.json() == activity
    assert client.get("/activities").json() == [activity]


@pytest.mark.parametrize(
    ("filters", "expected_titles"),
    [
        ({}, ["API pendente", "Estatistica concluida", "API concluida"]),
        ({"done": "false"}, ["API pendente"]),
        ({"done": "true"}, ["Estatistica concluida", "API concluida"]),
        (
            {"subject": Subject.APIS_AND_MICROSERVICES.value},
            ["API pendente", "API concluida"],
        ),
        (
            {"subject": Subject.APIS_AND_MICROSERVICES.value, "done": "true"},
            ["API concluida"],
        ),
        ({"subject": Subject.STATISTICS.value, "done": "false"}, []),
    ],
)
def test_list_activities_filters(
    client: TestClient, filters: dict, expected_titles: list[str]
) -> None:
    """Aplica os filtros opcionais e mantem a ordem de cadastro.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
        filters (dict): Filtros enviados nos parametros de consulta.
        expected_titles (list[str]): Titulos esperados, na ordem de cadastro.
    """
    activities = [
        ("API pendente", Subject.APIS_AND_MICROSERVICES, False),
        ("Estatistica concluida", Subject.STATISTICS, True),
        ("API concluida", Subject.APIS_AND_MICROSERVICES, True),
    ]
    for title, subject, done in activities:
        response = client.post(
            "/activities",
            data={"title": title, "subject": subject.value, "done": str(done).lower()},
        )
        assert response.status_code == 201

    response = client.get("/activities", params=filters)
    assert response.status_code == 200
    assert [activity["title"] for activity in response.json()] == expected_titles


def test_update_activity_replaces_all_fields(client: TestClient) -> None:
    """Mantem o ID e restaura os padroes dos campos omitidos no PUT.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
    """
    activity = client.post(
        "/activities",
        data={
            "title": "Titulo anterior",
            "subject": Subject.APIS_AND_MICROSERVICES.value,
            "description": "Descricao anterior",
            "done": "true",
        },
    ).json()
    response = client.put(
        f"/activities/{activity['id']}",
        data={"title": "Novo titulo", "subject": Subject.STATISTICS.value},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": activity["id"],
        "title": "Novo titulo",
        "subject": Subject.STATISTICS.value,
        "description": None,
        "done": False,
    }
    assert client.get(f"/activities/{activity['id']}").json() == response.json()


def test_delete_activity_and_keep_identifiers_unique(client: TestClient) -> None:
    """Exclui sem corpo na resposta e nao reutiliza o ID removido.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
    """
    data = {"title": "Atividade", "subject": Subject.APIS_AND_MICROSERVICES.value}
    activity = client.post("/activities", data=data).json()
    response = client.delete(f"/activities/{activity['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/activities/{activity['id']}").status_code == 404
    assert client.get("/activities").json() == []
    new_activity = client.post("/activities", data=data).json()
    assert new_activity["id"] > activity["id"]


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_missing_activity(client: TestClient, method: str) -> None:
    """Mantem o erro 404 e sua mensagem para IDs inexistentes.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
        method (str): Metodo HTTP usado para consultar, atualizar ou excluir.
    """
    data = {"title": "Atividade", "subject": Subject.APIS_AND_MICROSERVICES.value}
    response = client.request(
        method, "/activities/999", data=data if method == "PUT" else None
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Atividade nao encontrada."}


@pytest.mark.parametrize(
    "invalid_fields",
    [
        {"title": " "},
        {"title": "x" * 101},
        {"description": "x" * 501},
        {"subject": "Disciplina inexistente"},
        {"done": "invalido"},
        {"extra": "Campo desconhecido"},
    ],
)
def test_invalid_form_does_not_create_activity(
    client: TestClient, invalid_fields: dict
) -> None:
    """Rejeita formularios invalidos antes de persistir os dados.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
        invalid_fields (dict): Campos invalidos adicionados ao formulario.
    """
    data = {"title": "Atividade", "subject": Subject.APIS_AND_MICROSERVICES.value}
    response = client.post("/activities", data={**data, **invalid_fields})
    assert response.status_code == 422
    assert client.get("/activities").json() == []


@pytest.mark.parametrize("activity_id", ["0", "-1", "invalido"])
def test_invalid_activity_id(client: TestClient, activity_id: str) -> None:
    """Exige um identificador inteiro e positivo.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
        activity_id (str): Identificador invalido usado no caminho da requisicao.
    """
    assert client.get(f"/activities/{activity_id}").status_code == 422


def test_activity_persists_in_another_process(
    client: TestClient, database_engine: Engine
) -> None:
    """Consulta em outro processo uma atividade cadastrada pela API.

    Args:
        client (TestClient): Cliente HTTP da API com banco temporario.
        database_engine (Engine): Engine do banco que sera aberto em outro processo.
    """
    response = client.post(
        "/activities",
        data={"title": "Atividade persistida", "subject": Subject.STATISTICS.value},
    )
    assert response.status_code == 201
    activity = response.json()
    script = """
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models.activity import Activity, ActivityOutput

engine = create_engine(sys.argv[1])
with Session(engine) as session:
    activity = session.get(Activity, int(sys.argv[2]))
    print(ActivityOutput.model_validate(activity).model_dump_json())
engine.dispose()
"""
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            str(database_engine.url),
            str(activity["id"]),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
        timeout=30,
    )
    assert json.loads(result.stdout) == activity
