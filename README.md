# Projeto-Engenharia-I — Intech Sistemas (Controle de Fluxo de SPEDs)

Sistema web para controle, rastreabilidade e envio automatizado de arquivos de SPED Fiscal para clientes e contadores da Intech Sistemas.

---

## 👥 Contribuidores
- Eriky Rayan B. de Medeiros
- Felipe Eduardo Silva Fernandes
- Jefferson Willame Sena de Medeiros
- José Samuel Silva Lima
- Renan Medeiros Nogueira

---

## 🛠️ Tecnologias

| Tecnologia | Área de Responsabilidade | Descrição do Papel no Projeto |
| :--- | :--- | :--- |
| **Next.js (App Router) + React 19 + TypeScript** | Front-end / Desenvolvimento Cliente | Interface web moderna com SSR, Server Actions, validação estática e testes unitários. |
| **Django + Django REST Framework** | Back-end / Regras de Negócio | API principal com arquitetura REST, validação de permissões e regras fiscais. |
| **Supabase** | Banco de Dados / Autenticação (BaaS) | Banco PostgreSQL em nuvem e provedor de autenticação/sessão (Supabase Auth). |

---

## 🚀 Como Subir o Projeto e Testar

Siga o passo a passo abaixo para rodar e testar tanto o **Back-end** quanto o **Front-end** localmente.

### 1. Pré-requisitos
- **Git**
- **Python 3.10+** (recomendado Python 3.12 ou 3.14)
- **Node.js 20+** (recomendado Node 22+) e **npm**
- Conta e projeto ativo no [Supabase](https://supabase.com/)

---

### 2. Configurando e Executando o Back-end (Django)

1. **Acesse a pasta do backend:**
   ```bash
   cd backend
   ```

2. **Crie e ative o ambiente virtual:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # No Linux/macOS
   # No Windows: .venv\Scripts\activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure as variáveis de ambiente:**
   Copie o arquivo de exemplo e preencha as credenciais do Supabase:
   ```bash
   cp .env.example .env
   ```
   *Certifique-se de preencher `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` e `SUPABASE_JWT_SECRET`.*

5. **Execute as migrações do banco de dados:**
   ```bash
   python manage.py migrate
   ```

6. **Inicie o servidor de desenvolvimento:**
   ```bash
   python manage.py runserver 8000
   ```
   *O backend ficará disponível em `http://localhost:8000` (Swagger em `http://localhost:8000/api/docs/`).*

---

### 3. Configurando e Executando o Front-end (Next.js)

Em um novo terminal:

1. **Acesse a pasta do frontend:**
   ```bash
   cd frontend
   ```

2. **Instale as dependências:**
   ```bash
   npm install
   ```

3. **Configure as variáveis de ambiente:**
   Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```
   *Verifique se `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` e `NEXT_PUBLIC_API_URL` apontam para o seu Supabase e `http://localhost:8000/api`.*

4. **Inicie o servidor de desenvolvimento:**
   ```bash
   npm run dev
   ```
   *Acesse a aplicação no navegador em `http://localhost:3000`.*

---

## 🧪 Como Executar os Testes Automatizados

### Testes do Front-end (Vitest + Testing Library)
Na pasta `frontend/`:
```bash
# Executa todos os testes unitários (LoginForm e cliente de API)
npm run test

# Executa o linter para checagem estática
npm run lint

# Valida compilação TypeScript e build de produção do Next.js
npm run build
```

### Testes do Back-end (Django Test Suite)
Na pasta `backend/` com a `.venv` ativada. Execute os comandos dentro de `backend/`: a descoberta do Django começa no diretório atual e não encontra os testes se `manage.py test` for chamado a partir da raiz do repositório.
```bash
# Executa toda a suíte de testes do backend
python manage.py test

# Executa testes específicos de autenticação e funcionários
python manage.py test funcionarios
```

---

## 📖 Documentação Detalhada
- **Arquitetura do Front-end:** Consulte [frontend/README.md](frontend/README.md)
- **Documentação da API e Banco:** Consulte [backend/README.md](backend/README.md)
- **Documento de Visão:** Consulte [docs/doc-visao.md](docs/doc-visao.md)
- **Documento de Modelos:** Consulte [docs/doc-modelos.md](docs/doc-modelos.md)
- **Validação integrada e primeiro administrador:** Consulte [docs/validacao-integrada.md](docs/validacao-integrada.md)
- **Relatório Scrum:** Consulte [docs/relatorio-scrum.pdf](docs/relatorio-scrum.pdf)
