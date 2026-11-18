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
- **Pelo Front-end (React):** O front-end pode usar o SDK do Supabase (`@supabase/supabase-js`) para fazer login e enviar o `access_token` no cabeçalho `Authorization: Bearer <token>`. A classe [`SupabaseJWTAuthentication`](funcionarios/authentication.py) valida o token e resolve a identidade autenticada (`sub`) para o perfil de `FUNCIONARIO` vinculado por `supabaseUserId`.
- **Pelo Back-end (`/api/funcionarios/login/`):** O endpoint de login do Django autentica diretamente no **Supabase Auth** via [`SupabaseClient.sign_in_with_password()`](config/supabase_client.py) e retorna os tokens do Supabase + dados do perfil (`Administrador` ou `Funcionário`).
- **Cadastro de Usuários (`POST /api/funcionarios/`):** Ao cadastrar um colaborador, a identidade (e-mail/senha) é criada no **Supabase Auth** via [`SupabaseClient.create_auth_user()`](config/supabase_client.py). O backend persiste apenas o perfil funcional e o identificador retornado pelo Supabase. Por isso, `SUPABASE_URL`, `SUPABASE_ANON_KEY` e `SUPABASE_SERVICE_ROLE_KEY` precisam estar configurados para o cadastro.
- **Django Admin:** a rota `/admin/` não é exposta. Toda autenticação é feita pelo Supabase Auth; a administração de usuários ocorre pela API (`/api/funcionarios/`) e a gestão de credenciais pelo painel do Supabase.

### Modelo de Funcionário e credenciais (Issue #19)
- A tabela `FUNCIONARIO` mantém apenas os campos de negócio: `idFuncionario`, `supabaseUserId`, `nome`, `email`, `isAdmin` e `is_active`.
- `supabaseUserId` é **único** e corresponde ao `id` da identidade em `auth.users` (Supabase Auth).
- **Senha e hash de senha não são armazenados nem retornados** pela tabela ou pela API de funcionários.
- Na criação, o campo `senha` é aceito apenas como *write-only*, é encaminhado ao Supabase Auth e nunca é gravado no backend.
- A autenticação resolve o token validado (`sub`) para o perfil vinculado, sem comparar senhas no Django.

### Migração de usuários existentes (sem expor senhas)
Bancos criados antes da Issue #19 ainda possuem a coluna `senha` e não têm `supabaseUserId`:

1. Aplique a migração do Django (funciona em banco limpo e existente):
   ```bash
   cd backend
   python manage.py migrate
   # 0002_supabase_user_id_remove_password: remove a coluna "senha" e adiciona "supabaseUserId"
   ```
2. Para bancos gerenciados apenas pelo SQL Editor do Supabase, execute o bloco idempotente de migração em [`supabase_schema.sql`](supabase_schema.sql), que remove `senha` e cria o vínculo único.
3. **Recriação/invitação das credenciais:** os hashes antigos são descartados. Cada funcionário deve ter (ou receber) uma identidade no **Supabase Auth** com o mesmo e-mail do perfil. Nenhuma senha antiga é exportada, lida ou registrada nesse processo.
4. **Vínculo automático no primeiro login:** ao autenticar, se o perfil ainda estiver com `supabaseUserId` nulo e o e-mail do token validado coincidir, o backend grava o vínculo uma única vez. Depois disso, a resolução passa a ser exclusivamente pelo `supabaseUserId`.
5. Se preferir vincular antecipadamente, crie os usuários no painel do Supabase Auth (ou via Admin API) com o e-mail do perfil. O gatilho de [`supabase_schema.sql`](supabase_schema.sql) também preenche o vínculo para novos usuários de Auth.

> Observação: como as credenciais deixam de existir no Django, não há `createsuperuser` com senha local. O primeiro administrador deve ser criado no Supabase Auth e ter um perfil com `isAdmin=True` (via API autenticada ou SQL).

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
| **Perfil Atual** | `GET /api/funcionarios/me/` | Retorna o perfil do usuário autenticado (Token Supabase) |
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
