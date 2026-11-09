"""Recebe as requisicoes HTTP e chama as operacoes do model."""

from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Path,
    Query,
    Response,
    status,
)
from sqlalchemy.orm import Session

from controllers.auth_controller import require_authenticated_user
from database import get_session
from models import activity as activity_model
from models.activity import Activity, ActivityInput, ActivityOutput, Subject


router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
    dependencies=[Depends(require_authenticated_user)],
    responses={401: {"description": "Autenticação Bearer obrigatória."}},
)


@router.post(
    "",
    response_model=ActivityOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar uma atividade",
)
def create_activity(
    data: Annotated[ActivityInput, Form()],
    session: Annotated[Session, Depends(get_session)],
) -> Activity:
    """Recebe o formulario e cadastra uma atividade.

    Args:
        data (ActivityInput): Dados validados recebidos nos campos do formulario.
        session (Session): Sessao do banco recebida por injecao de dependencia.

    Returns:
        Activity: Atividade cadastrada, usada no corpo da resposta HTTP 201.
    """
    return activity_model.create(data, session)


@router.get(
    "",
    response_model=list[ActivityOutput],
    summary="Listar atividades",
)
def list_activities(
    session: Annotated[Session, Depends(get_session)],
    subject: Annotated[
        Subject | None, Query(description="Filtrar pelo nome completo da disciplina.")
    ] = None,
    done: Annotated[
        bool | None, Query(description="Filtrar atividades concluidas ou pendentes.")
    ] = None,
) -> list[Activity]:
    """Consulta as atividades com filtros opcionais.

    Args:
        session (Session): Sessao do banco recebida por injecao de dependencia.
        subject (Subject | None, optional): Disciplina usada no filtro. None inclui
            todas as disciplinas. Padrao: None.
        done (bool | None, optional): True inclui concluidas e False inclui pendentes.
            None inclui ambas. Padrao: None.

    Returns:
        list[Activity]: Lista de atividades que correspondem aos filtros.
    """
    return activity_model.get_all(session, subject, done)


@router.get(
    "/{activity_id}",
    response_model=ActivityOutput,
    summary="Consultar uma atividade",
    responses={404: {"description": "Atividade nao encontrada."}},
)
def get_activity(
    activity_id: Annotated[int, Path(gt=0, description="ID da atividade.")],
    session: Annotated[Session, Depends(get_session)],
) -> Activity:
    """Consulta uma atividade pelo identificador.

    Args:
        activity_id (int): Identificador positivo recebido no caminho da requisicao.
        session (Session): Sessao do banco recebida por injecao de dependencia.

    Raises:
        HTTPException: Erro HTTP 404 quando a atividade nao existe.

    Returns:
        Activity: Dados da atividade encontrada.
    """
    activity = activity_model.get_by_id(activity_id, session)
    if activity is None:
        raise HTTPException(status_code=404, detail="Atividade nao encontrada.")
    return activity


@router.put(
    "/{activity_id}",
    response_model=ActivityOutput,
    summary="Substituir os dados de uma atividade",
    responses={404: {"description": "Atividade nao encontrada."}},
)
def update_activity(
    activity_id: Annotated[int, Path(gt=0, description="ID da atividade.")],
    data: Annotated[ActivityInput, Form()],
    session: Annotated[Session, Depends(get_session)],
) -> Activity:
    """Substitui os dados de uma atividade existente.

    Args:
        activity_id (int): Identificador positivo da atividade que sera atualizada.
        data (ActivityInput): Novos dados. Campos opcionais omitidos usam
            description=None e done=False.
        session (Session): Sessao do banco recebida por injecao de dependencia.

    Raises:
        HTTPException: Erro HTTP 404 quando a atividade nao existe.

    Returns:
        Activity: Atividade atualizada com o mesmo identificador.
    """
    activity = activity_model.update(activity_id, data, session)
    if activity is None:
        raise HTTPException(status_code=404, detail="Atividade nao encontrada.")
    return activity


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Excluir uma atividade",
    responses={404: {"description": "Atividade nao encontrada."}},
)
def delete_activity(
    activity_id: Annotated[int, Path(gt=0, description="ID da atividade.")],
    session: Annotated[Session, Depends(get_session)],
) -> Response:
    """Exclui uma atividade pelo identificador.

    Args:
        activity_id (int): Identificador positivo da atividade que sera removida.
        session (Session): Sessao do banco recebida por injecao de dependencia.

    Raises:
        HTTPException: Erro HTTP 404 quando a atividade nao existe.

    Returns:
        Response: Resposta HTTP 204 sem corpo.
    """
    if not activity_model.delete(activity_id, session):
        raise HTTPException(status_code=404, detail="Atividade nao encontrada.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
