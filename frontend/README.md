# Frontend — Intech Sistemas (Controle de Fluxo de SPEDs)

Interface web moderna desenvolvida em **Next.js (App Router) + React 19 + TypeScript**, com **Server Actions** (`'use server'`), autenticação SSR com **`@supabase/ssr`** e integração com a API REST do **Django Backend**.

---

## 🛠️ Tecnologias e Ferramentas

- **Next.js 16 (App Router)** com **Turbopack** e **React 19**
- **TypeScript** para tipagem estática ponta a ponta
- **@supabase/ssr** e **@supabase/supabase-js** para autenticação via cookies (`httpOnly`) e SSR
- **Server Actions** para execução de ações seguras no servidor sem necessidade de rotas de API intermediárias (`route.js`)
- **Vitest + React Testing Library** para testes unitários automatizados
- **Oxlint** para análise estática e qualidade de código

---

## 🚀 Como Executar o Projeto Localmente

### 1. Pré-requisitos
- Node.js versão `>= 20.x` (recomendado Node 22+)
- Backend do sistema executando (por padrão em `http://localhost:8000`)
- Projeto no Supabase configurado (URL e Anon Key pública)

### 2. Instalação de Dependências
```bash
cd frontend
npm install
```

### 3. Configuração de Variáveis de Ambiente
Crie um arquivo `.env` na raiz da pasta `frontend/` copiando o modelo de `.env.example`:

```bash
cp .env.example .env
```

Preencha as variáveis públicas com os dados do seu projeto Supabase e da API Django:
```env
# URL base do projeto no Supabase
NEXT_PUBLIC_SUPABASE_URL=https://[SEU_PROJETO].supabase.co

# Chave anônima pública (anon key) do Supabase (NUNCA utilize a service_role_key no front-end!)
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOi...

# URL base da API REST do backend Django
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

> **Atenção:** Nunca adicione chaves `service_role` ou senhas no código do frontend. O frontend utiliza apenas a chave `anon` pública e gerencia sessões via cookies assinados.

### 4. Executando em Modo de Desenvolvimento
```bash
npm run dev
```
Acesse o aplicativo em `http://localhost:3000`.

---

## 📁 Estrutura de Diretórios (Next.js App Router)

```text
frontend/
├── middleware.ts             # Middleware interceptor para renovação de sessão e proteção de rotas
├── next.config.ts            # Configuração oficial do Next.js
├── vitest.config.ts          # Configuração dos testes unitários com Vitest
├── src/
│   ├── app/                  # Rotas e páginas do Next.js App Router
│   │   ├── layout.tsx        # Layout raiz da aplicação
│   │   ├── page.tsx          # Rota '/' com redirecionamento inteligente (/login ou /dashboard)
│   │   ├── login/
│   │   │   └── page.tsx      # Página pública de login
│   │   ├── dashboard/
│   │   │   └── page.tsx      # Dashboard autenticado via SSR com painel condicional de Administrador
│   │   └── actions/
│   │       └── auth.ts       # Server Actions ('use server'): loginAction e logoutAction
│   ├── api/                  # Utilitários de consumo da API Django
│   │   ├── client.ts         # Wrapper de fetch com injeção automática de Bearer Token
│   │   └── client.test.ts    # Testes unitários do cliente de API
│   ├── lib/
│   │   └── supabase/
│   │       ├── client.ts     # Cliente Supabase para o Browser (createBrowserClient)
│   │       ├── server.ts     # Cliente Supabase para Server Actions/SSR (createServerClient + cookies)
│   │       └── middleware.ts # Utilitário de renovação de sessão para o middleware
│   ├── components/
│   │   ├── common/           # Componentes atômicos reutilizáveis (Button, Input, Alert, Spinner)
│   │   └── auth/
│   │       ├── LoginForm.tsx      # Formulário com 'use client', useState e useActionState
│   │       └── LoginForm.test.tsx # Testes unitários de validação e submissão
│   ├── types/
│   │   └── auth.ts           # Interfaces TypeScript (FuncionarioProfile, etc.)
│   └── test/
│       └── setup.ts          # Setup global dos testes (@testing-library/jest-dom)
```

---

## 🔐 Fluxo de Autenticação e Server Actions

1. **Login via Server Action:** O formulário de login (`LoginForm.tsx`) submete as credenciais diretamente para a Server Action `loginAction()` em `app/actions/auth.ts`.
2. **Cookies de Sessão e SSR:** O `@supabase/ssr` autentica no Supabase Auth e grava os tokens de sessão em cookies seguros (`httpOnly`).
3. **Proteção Automática por Middleware:** O `middleware.ts` intercepta as rotas protegidas (`/dashboard`) e redireciona usuários não autenticados para `/login`. Se o usuário já estiver logado e acessar `/login`, é redirecionado para `/dashboard`.
4. **Resolução de Perfil no Backend:** O Server Component `DashboardPage` obtém a sessão do cookie, consulta `GET /api/funcionarios/me/` com o Bearer token e valida se `profile.isAdmin === true`.
5. **Logout:** A Server Action `logoutAction()` revoga a sessão no Supabase e limpa os cookies, redirecionando o usuário para `/login`.

---

## 🧪 Scripts Disponíveis

- **`npm run dev`**: Inicia o servidor Next.js em desenvolvimento (`http://localhost:3000`).
- **`npm run build`**: Gera o build otimizado de produção com checagem de tipos TypeScript.
- **`npm run start`**: Inicia o servidor em modo de produção.
- **`npm run test`**: Executa todos os testes unitários via Vitest.
- **`npm run lint`**: Executa a análise estática com o Oxlint.
