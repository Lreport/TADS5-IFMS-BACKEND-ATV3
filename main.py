from fastapi import FastAPI

from controllers.activity_controller import router


app = FastAPI(
    title="Gerenciador de Atividades",
    description=(
        "Cadastra as atividades das disciplinas atuais do curso"
    ),
)

app.include_router(router)
