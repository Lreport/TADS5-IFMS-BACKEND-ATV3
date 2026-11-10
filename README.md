# TADS5-IFMS-BACKEND-ATV3

## Como rodar ?

Abra o terminal na pasta do repositório

1. Crie o ambiente virtual, instale as dependências e faça as migrações:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```

2. Crie a conta do aluno

   ```powershell
   .\.venv\Scripts\python.exe -m create_user
   ```

   Coloque o e-mail e uma senha. O terminal pede a confirmação da senha e oculta a digitação. O SQLite guarda o hash da senha.

3. Gere um chave de assinatura e inicie a API no mesmo terminal:

   ```powershell
   $env:JWT_SECRET_KEY = .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload
   ```

   A chave fica no ambiente desse terminal. Ao gerar outra chave, faça login novamente para obter um novo token. Para encerrar o servidor, pressione `Ctrl+C`.

## Como testar o login pelo Swagger

1. Abra o [Swagger da API](http://127.0.0.1:8000/docs).
2. No **GET /activities**, clique em **Try it out** e depois em **Execute**. Sem uma autenticação.
3. Clique em **Authorize**. Digite o email do aluno em `username` e a senha em `password`. Deixe os campos de cliente vazios. Clique em **Authorize** e depois em **Close**. O Swagger chama `POST /token` e passa a enviar o JWT como `Authorization: Bearer <token>`.
4. Execute **GET /activities** de novo. A resposta que se espera é **200**, com a lista de atividades ou `[]` se o banco estiver vazio.

O token dura 30 minutos. Quando ele expirar, faça login novamente pelo botão **Authorize**. As rotas de cadastro, atualização, exclusão e consulta de atividades exigem autenticação.