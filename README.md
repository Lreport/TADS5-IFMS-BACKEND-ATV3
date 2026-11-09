# TADS5-IFMS-BACKEND-ATV2


Prof. Rogério, a base dessa atividade, é feita com o projeto da atividade anterior a essa, eu pensei em continuar essa atividade no mesmo repositório mas para garantir uma melhor organização, acabei criando esse repositório para uma melhor organização das atividades. Vlw Rogério, é nois 

Link atividade anterior: https://github.com/Lreport/fastAPI-IFMS

vou deixar a seguir como executar o projeto assim como deixei no da atividade passada.

## Como executar

1. Abra a pasta do projeto no VS Code e abra um terminal.
2. Na primeira execução, crie o ambiente virtual e instale as dependências:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

3. Antes de iniciar o servidor, execute a migração para criar as tabelas do banco de dados:

   ```powershell
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```

4. Inicie o servidor:

   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

5. Com o servidor em execução, acesse o [Swagger](http://127.0.0.1:8000/docs).

Deixe o terminal aberto enquanto usa o sistema. Para encerrar, de **Ctrl+C**.