# Backend - Controle de Fluxo de SPEDs (Intech Sistemas)

API REST desenvolvida em **Python + Django + Django REST Framework**, construída a partir do [Documento de Visão](../docs/doc-visao.md) e do [Documento de Modelos](../docs/doc-modelos.md).

## Estrutura de Pastas do Backend

```text
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                 # Configurações centrais do projeto Django, rotas e CORS/JWT
├── funcionarios/           # US01 - Manter Usuário (Tabela FUNCIONARIO e Login JWT)
├── clientes/               # US02 - Manter Cliente (Tabela CLIENTE e integração API CNPJ)
├── speds/                  # US03 e US04 - Manter e Enviar SPED (Tabela SPED, E-mail e WhatsApp)
└── auditoria/              # US05 e US06 - Rastreabilidade Automática e Dashboard Gerencial
```

## Como Executar

```bash
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver
```

- **Documentação Interativa (Swagger UI):** `http://127.0.0.1:8000/api/docs/`
- **Documentação ReDoc:** `http://127.0.0.1:8000/api/redoc/`

## Principais Endpoints

| Módulo / História de Usuário | Método e Rota | Requisito Funcional |
| :--- | :--- | :--- |
| **Autenticação** | `POST /api/funcionarios/login/` | RF01.05 - Login do Usuário |
| **Usuários (Admin)** | `GET/POST /api/funcionarios/` | RF01.01, RF01.02 - Inserir e Listar Usuários |
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
