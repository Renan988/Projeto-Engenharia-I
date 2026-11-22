# Validação integrada do CRUD com Supabase Auth

Este documento fecha a issue #16. Descreve como configurar as quatro camadas do sistema (Supabase Auth, PostgreSQL, Django e frontend), como provisionar o primeiro administrador sem expor credenciais e como executar a validação ponta a ponta.

## 1. Fluxo das camadas

1. O navegador envia e-mail e senha para a Server Action `loginAction` no Next.js.
2. O `@supabase/ssr` autentica no Supabase Auth e grava a sessão em cookies `httpOnly`.
3. Cada requisição ao Django leva o `access_token` no cabeçalho `Authorization: Bearer`.
4. O backend valida o token (assinatura, issuer, expiração) e resolve o `sub` para a linha de `FUNCIONARIO` por `supabaseUserId`.
5. As permissões administrativas são lidas do perfil persistido no PostgreSQL, nunca do token.

## 2. Configuração das camadas

### Supabase

1. Crie o projeto em https://supabase.com/.
2. Em **Project Settings -> API**, copie a URL, a chave `anon`/publishable, a `service_role` e o JWT secret.
3. Em **Connect -> Session pooler**, copie a URI PostgreSQL com a senha do banco.
4. Execute `backend/supabase_schema.sql` no SQL Editor para criar o gatilho de sincronização e o vínculo `supabaseUserId`.

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 8000
```

Preencha `backend/.env` com `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY` e `SUPABASE_JWT_SECRET`. A chave `service_role` fica apenas nesse arquivo, que é ignorado pelo Git. A API expõe a documentação em `http://localhost:8000/api/docs/`.

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Preencha `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` e `NEXT_PUBLIC_API_URL=http://localhost:8000/api`. A aplicação sobe em `http://localhost:3000`.

## 3. Primeiro administrador

Não existe `createsuperuser` com senha local. O procedimento abaixo evita deixar uma conta administrativa sem senha conhecida ou um segredo no repositório.

1. Crie a identidade no Supabase Auth pelo painel (**Authentication -> Users -> Add user**) ou pela Admin API com a chave `service_role`. Anote o `id` (UUID) devolvido.
2. Aplique as migrações do Django para garantir a coluna `supabaseUserId` e a tabela `FUNCIONARIO`.
3. Crie o perfil administrativo com uma das duas opções:

   a. Pelo SQL Editor, com parâmetro (substitua os valores abaixo pelos dados reais):

   ```sql
   INSERT INTO "FUNCIONARIO" ("supabaseUserId", "nome", "email", "isAdmin", "is_active")
   VALUES ('UUID_DA_IDENTIDADE', 'Administrador Intech', 'admin@intech.com.br', true, true);
   ```

   b. Pela API, autenticando com o token do próprio administrador e usando `PATCH` em `/api/funcionarios/{id}/` para definir `isAdmin: true`. Isso exige que o perfil já exista como funcionário comum, criado pelo gatilho do SQL.

4. Confirme o vínculo com `GET /api/funcionarios/me/` usando o token do administrador. A resposta deve trazer `isAdmin: true`.
5. Guarde a chave `service_role` apenas no cofre do projeto. Não a coloque no frontend, em issues, no README ou em arquivos versionados. Se ela tiver sido exposta, rotacione-a no painel do Supabase.

O gatilho `on_auth_user_created` cria perfis novos como funcionários comuns. A elevação a administrador depende de uma chamada autenticada de um administrador existente ou da inserção controlada acima.

## 4. Roteiro de validação ponta a ponta

Execute cada passo com as quatro camadas no ar. Marque o resultado antes de considerar a issue concluída.

| # | Ação | Resultado esperado |
| --- | --- | --- |
| 1 | Acessar `http://localhost:3000/login` e entrar com o administrador | Redirecionamento para `/dashboard` com o painel administrativo visível |
| 2 | Abrir `/funcionarios`, cadastrar nome, e-mail, senha inicial e perfil | Novo funcionário aparece na listagem; a identidade existe no Supabase Auth |
| 3 | Filtrar a listagem por nome e por e-mail | Somente os registros correspondentes são exibidos |
| 4 | Editar nome, e-mail de contato e perfil | Alterações persistem após recarregar a página |
| 5 | Excluir o funcionário criado e confirmar o modal | Registro desaparece da listagem padrão; perfil fica inativo no banco e a identidade é bloqueada no Auth |
| 6 | Reiniciar o backend (`Ctrl+C` e `runserver`) e entrar novamente | Login e as quatro operações continuam funcionando |
| 7 | Entrar com um funcionário comum | Controles administrativos ficam ocultos; chamadas diretas à API retornam 403 |
| 8 | Forçar falha do Auth (chave inválida ou serviço fora) durante um cadastro | Nenhum perfil órfão; erro 503 ou de validade conforme o caso |

Comandos úteis para a camada de API:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" http://localhost:8000/api/funcionarios/me/
curl -H "Authorization: Bearer <ACCESS_TOKEN>" http://localhost:8000/api/funcionarios/
curl -X POST -H "Authorization: Bearer <ACCESS_TOKEN>" -H "Content-Type: application/json" \
  -d '{"nome":"Teste","email":"teste@intech.com.br","senha":"senha123","isAdmin":false}' \
  http://localhost:8000/api/funcionarios/
```

## 5. Verificação automatizada

Executada em 22/11/2026 sobre o commit `59abbea` da `main`, com a issue #16 em aberto:

| Comando | Resultado |
| --- | --- |
| `python manage.py test funcionarios auditoria clientes speds` | 33 testes OK |
| `npm run test -- --run` | 23 testes OK em 4 arquivos |
| `npm run lint` | Passou com 1 aviso em `layout.tsx` |
| `npm run build` | Build de produção concluído |

Os testes do backend cobrem token válido e inválido, assinatura incorreta, expiração, emissor de outro projeto, desvio de relógio, vínculo identidade/perfil, perfil legado, persistência do vínculo em outra sessão, bloqueio de funcionário comum, CRUD completo, exclusão lógica e reversão em falhas de integração. Os testes do frontend cobrem login, cliente de API, formulário e tela de funcionários.

O roteiro da seção 4 depende de credenciais reais do Supabase e precisa ser executado no ambiente do projeto. Os testes automatizados não substituem essa execução: eles usam tokens gerados localmente e chamadas ao Auth simuladas com mocks.
