"""Define as disciplinas, os dados de entrada e saida e as operacoes no banco."""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Boolean, Enum as SQLAlchemyEnum, String, false, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from database import Base


class Subject(str, Enum):
    """Lista as disciplinas aceitas no cadastro."""

    APIS_AND_MICROSERVICES = "APIs e Microserviços"
    INTELLIGENT_AGENTS = "Agentes Inteligentes"
    EXTENSION_IV = "Atividade de Extensão IV"
    ASYNC_COMMUNICATION_AND_OBSERVABILITY = "Comunicação Assíncrona e Observabilidade"
    BACK_END_FRAMEWORKS = "Frameworks Back-End"
    STATISTICS = "Fundamentos de Estatística"
    PROJECT_MANAGEMENT = "Gestão de Projetos"


class ActivityInput(BaseModel):
    """Valida os dados enviados no cadastro e na atualizacao."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = Field(min_length=1, max_length=100, description="Titulo da atividade.")
    subject: Subject = Field(description="Disciplina da atividade.")
    description: str | None = Field(
        default=None, max_length=500, description="Detalhes opcionais da atividade."
    )
    done: bool = Field(default=False, description="Indica se a atividade foi concluida.")


class ActivityOutput(ActivityInput):
    """Inclui o ID gerado pela API nos dados de saida."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(gt=0, description="Identificador gerado pela API.")


class Activity(Base):
    """Mapeia os dados de uma atividade para a tabela do banco."""

    __tablename__ = "activities"
    __table_args__ = {"sqlite_autoincrement": True}

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    subject: Mapped[Subject] = mapped_column(
        SQLAlchemyEnum(
            Subject,
            values_callable=lambda subjects: [subject.value for subject in subjects],
            native_enum=False,
            create_constraint=True,
            validate_strings=True,
            name="activity_subject",
        )
    )
    description: Mapped[str | None] = mapped_column(String(500), default=None)
    done: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())


def create(data: ActivityInput, session: Session) -> Activity:
    """Cria uma atividade no banco e gera seu identificador.

    Args:
        data (ActivityInput): Dados validados da nova atividade.
        session (Session): Sessao do banco usada na operacao.

    Returns:
        Activity: Atividade criada com o identificador gerado.
    """
    activity = Activity(**data.model_dump())
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def get_all(
    session: Session, subject: Subject | None = None, done: bool | None = None
) -> list[Activity]:
    """Lista as atividades e aplica os filtros informados.

    Args:
        session (Session): Sessao do banco usada na consulta.
        subject (Subject | None, optional): Disciplina usada no filtro. None inclui
            todas as disciplinas. Padrao: None.
        done (bool | None, optional): True inclui concluidas e False inclui pendentes.
            None inclui ambas. Padrao: None.

    Returns:
        list[Activity]: Atividades que correspondem aos filtros, ou uma lista vazia.
    """
    statement = select(Activity).order_by(Activity.id)
    if subject is not None:
        statement = statement.where(Activity.subject == subject)
    if done is not None:
        statement = statement.where(Activity.done == done)
    return list(session.scalars(statement).all())


def get_by_id(activity_id: int, session: Session) -> Activity | None:
    """Busca uma atividade pelo identificador.

    Args:
        activity_id (int): Identificador da atividade procurada.
        session (Session): Sessao do banco usada na consulta.

    Returns:
        Activity | None: Atividade encontrada, ou None quando o ID nao existe.
    """
    return session.get(Activity, activity_id)


def update(activity_id: int, data: ActivityInput, session: Session) -> Activity | None:
    """Substitui os dados de uma atividade e mantem seu identificador.

    Args:
        activity_id (int): Identificador da atividade que sera atualizada.
        data (ActivityInput): Novos dados. Campos opcionais omitidos usam
            description=None e done=False.
        session (Session): Sessao do banco usada na operacao.

    Returns:
        Activity | None: Atividade atualizada, ou None quando o ID nao existe.
    """
    activity = get_by_id(activity_id, session)
    if activity is None:
        return None
    for field, value in data.model_dump().items():
        setattr(activity, field, value)
    session.commit()
    session.refresh(activity)
    return activity


def delete(activity_id: int, session: Session) -> bool:
    """Remove uma atividade do banco.

    Args:
        activity_id (int): Identificador da atividade que sera removida.
        session (Session): Sessao do banco usada na operacao.

    Returns:
        bool: True quando a atividade foi removida, ou False quando nao existe.
    """
    activity = get_by_id(activity_id, session)
    if activity is None:
        return False
    session.delete(activity)
    session.commit()
    return True
