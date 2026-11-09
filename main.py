from fastapi import FastAPI

from controllers.activity_controller import router as activity_router
from controllers.auth_controller import router as auth_router


app = FastAPI(
    title="Gerenciador de Atividades",
    description=(
        "Cadastra as atividades das disciplinas atuais do curso"
    ),
)

app.include_router(activity_router)
app.include_router(auth_router)
