# Backend - Controle de Fluxo de SPEDs (Intech Sistemas)

API REST desenvolvida em **Python + Django + Django REST Framework + Supabase**, construída a partir do [Documento de Visão](../docs/doc-visao.md) e do [Documento de Modelos](../docs/doc-modelos.md).

## Integração com o Supabase (Banco de Dados na Nuvem + Autenticação)

O back-end utiliza o **Supabase** tanto como banco de dados PostgreSQL na nuvem (sem depender de banco local no notebook) quanto como provedor de **Autenticação e Login (Supabase Auth)**:

1. Crie um projeto gratuito em [supabase.com](https://supabase.com/).
2. No painel do seu projeto no Supabase, clique em **Connect** (no topo) -> aba **ORMs / Connection String** -> selecione **Session pooler (porta 5432)** e copie a URI no arquivo `backend/.env`:
   ```env
   DATABASE_URL=postgresql://postgres.[SEU_PROJECT_REF]:[SUA_SENHA]@aws-0-sa-east-1.pooler.supabase.com:5432/postgres
   ```
3. Vá em **Project Settings -> API** no painel do Supabase e copie as chaves para o seu `backend/.env`:
   ```env
   SUPABASE_URL=https://[SEU_PROJECT_REF].supabase.co
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...
   SUPABASE_JWT_SECRET=seu-jwt-secret
   ```
4. Rode as migrações para criar as tabelas (`FUNCIONARIO`, `CLIENTE`, `SPED`, `LOG_RASTREABILIDADE`) diretamente no banco PostgreSQL do Supabase:
   ```bash
   cd backend
   source .venv/bin/activate
   python manage.py migrate
   python manage.py runserver
   ```

### Como funciona o Login com o Supabase Auth:
- **Pelo Front-end (React):** O front-end pode usar o SDK do Supabase (`@supabase/supabase-js`) para fazer login e enviar o `access_token` no cabeçalho `Authorization: Bearer <token>`. A classe [`SupabaseJWTAuthentication`](funcionarios/authentication.py) valida o token do Supabase e sincroniza automaticamente o usuário com a tabela `FUNCIONARIO`.
- **Pelo Back-end (`/api/funcionarios/login/`):** O endpoint de login do Django autentica diretamente no **Supabase Auth** via [`SupabaseClient.sign_in_with_password()`](config/supabase_client.py) e retorna os tokens do Supabase + dados do perfil (`Administrador` ou `Funcionário`).
- **Cadastro de Usuários (`POST /api/funcionarios/`):** Ao cadastrar um colaborador pelo sistema, ele também é criado automaticamente no **Supabase Auth** via [`SupabaseClient.create_auth_user()`](config/supabase_client.py).

## Estrutura de Pastas do Backend

```text
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── config/
│   ├── settings.py         # Configurações do Django, Supabase PostgreSQL e JWT
│   ├── supabase_client.py  # Cliente de integração com o Supabase Auth (GoTrue)
│   └── urls.py             # Rotas principais e Swagger/Redoc
├── funcionarios/           # US01 - Manter Usuário (Tabela FUNCIONARIO + SupabaseJWTAuthentication)
├── clientes/               # US02 - Manter Cliente (Tabela CLIENTE e integração API CNPJ)
├── speds/                  # US03 e US04 - Manter e Enviar SPED (Tabela SPED, E-mail e WhatsApp)
└── auditoria/              # US05 e US06 - Rastreabilidade Automática e Dashboard Gerencial
```

## Principais Endpoints

| Módulo / História de Usuário | Método e Rota | Requisito Funcional |
| :--- | :--- | :--- |
| **Autenticação (Supabase)** | `POST /api/funcionarios/login/` | RF01.05 - Login do Usuário via Supabase Auth |
| **Perfil Atual** | `GET /api/funcionarios/me/` | Retorna usuário autenticado (Token Supabase ou JWT) |
| **Usuários (Admin)** | `GET/POST /api/funcionarios/` | RF01.01, RF01.02 - Inserir (no Supabase + Banco) e Listar |
| **Usuários (Admin)** | `PUT/PATCH/DELETE /api/funcionarios/{id}/` | RF01.03, RF01.04 - Atualizar e Deletar Usuário |
| **Usuários (Admin)** | `DELETE /api/funcionarios/deletar-por-email/?email=...` | RF01.04 - Deletar Usuário por E-mail |
| **Clientes** | `GET /api/clientes/consultar-cnpj/?cnpj=...` | RF02.01 - Consulta Automática de CNPJ via API |
| **Clientes** | `GET/POST /api/clientes/` | RF02.01, RF02.02 - Inserir e Listar Clientes |
| **Clientes** | `PUT/PATCH/DELETE /api/clientes/{idCli}/` | RF02.03, RF02.04 - Atualizar e Deletar Cliente |
| **Clientes** | `DELETE /api/clientes/deletar-por-cnpj/?cnpj=...` | RF02.04 - Deletar Cliente por CNPJ |
| **SPEDs (Fila)** | `POST /api/speds/gerar-fila/` | RF03.01 - Gerar Fila de Atendimento Priorizada |
| **SPEDs (Fila)** | `GET /api/speds/fila-pendentes/` | RF03.02 - Listar SPEDs Pendentes por Prioridade |
| **SPEDs (Fluxo)** | `PATCH /api/speds/{idSped}/atualizar-status/` | RF03.03 - Atualizar Status (`PENDENTE > GERADO > ENVIADO`) |
| **SPEDs (Upload)** | `POST /api/speds/{idSped}/upload/` | RF03.04 - Anexar Arquivo RAR do SPED |
| **SPEDs (Envio)** | `POST /api/speds/{idSped}/enviar/` | RF04.01 a RF04.04 - E-mail ao Contador + WhatsApp Cliente |
| **Auditoria** | `GET /api/auditoria/logs/` | RF05.01, RF05.02 - Logs de Rastreabilidade |
| **Dashboard** | `GET /api/auditoria/dashboard/` | RF06.01, RF06.02 - Produtividade e Demandas do Mês |
