# Relatório de Prática Scrum

Sistema de Controle de Fluxo de Geração de SPEDs — Intech Sistemas

| Campo | Informação |
| --- | --- |
| Disciplina | Engenharia de Software I |
| Projeto | Intech Sistemas — Controle de Fluxo de SPEDs |
| Professora orientadora | Karliane Vale |
| Repositório | github.com/Renan988/Projeto-Engenharia-I |
| Versão | 1.1 (final) |
| Data | 22 de novembro de 2026 |
| Commit de referência | 59abbea (main) |
| Pull request | #28 — revisão pendente |

| Integrante | Papéis exercidos no Scrum |
| --- | --- |
| Eriky Rayan B. de Medeiros | Product Owner, Scrum Master e Developer |
| Felipe Eduardo Silva Fernandes | Product Owner, Scrum Master e Developer |
| Jefferson Willame Sena de Medeiros | Product Owner, Scrum Master e Developer |
| José Samuel Silva Lima | Product Owner, Scrum Master e Developer |
| Renan Medeiros Nogueira | Product Owner, Scrum Master e Developer |

Os papéis são rotativos entre os integrantes a cada Sprint.

<!-- PAGE_BREAK -->

## Sumário

1. Visão do produto
2. Product Backlog
3. Sprint Backlog e execução
4. Revisões das Sprints
5. Retrospectivas das Sprints
6. CRUD em execução
7. Validação integrada
8. Organização do GitHub
9. Evidências

<!-- PAGE_BREAK -->

## 1. Visão do produto

A Intech Sistemas controlava a geração mensal dos SPEDs com planilhas e mensagens externas. O documento de visão registra três problemas concretos: gargalos na fila de atendimento, falhas de comunicação entre funcionários e ausência de rastreabilidade das alterações.

A solução descrita centraliza a fila, ordena os atendimentos pelo regime tributário do cliente, registra logs de rastreabilidade e mostra indicadores em um dashboard. O escopo está registrado em `docs/doc-visao.md` e os modelos conceitual e de dados em `docs/doc-modelos.md`.

A equipe adota o Scrum com papéis rotativos entre os cinco integrantes. A professora Karliane Vale é a cliente do projeto.

Tecnologias adotadas: Django REST Framework no backend, Next.js com React 19 e TypeScript no frontend, PostgreSQL e Supabase Auth como serviços gerenciados.

## 2. Product Backlog

Os itens abaixo correspondem aos requisitos funcionais do documento de visão. A ordem segue a dependência técnica entre eles: primeiro a infraestrutura e a identidade, depois as entidades de domínio e por fim as integrações externas.

| Ordem | Épico / requisito | Descrição resumida | Prioridade |
| --- | --- | --- | --- |
| 1 | US01 / RF01.01 a RF01.05 | Manter usuário e autenticar pelo Supabase Auth | Alta |
| 2 | US02 / RF02.01 a RF02.04 | Manter cliente e consultar regime tributário pelo CNPJ | Alta |
| 3 | US03 / RF03.01 a RF03.04 | Fila de atendimento, status do SPED e upload do arquivo | Alta |
| 4 | US04 / RF04.01 a RF04.04 | Envio por e-mail, notificação por WhatsApp e conclusão do envio | Alta |
| 5 | US05 / RF05.01 e RF05.02 | Registro automático de logs de rastreabilidade | Média |
| 6 | US06 / RF06.01 e RF06.02 | Dashboard de produtividade e demandas | Média |
| 7 | RNF001 a RNF007 | Segurança, desempenho, disponibilidade, usabilidade, compatibilidade e dependências externas | Média |

Critérios de aceitação usados para os itens entregues até aqui estão nas issues do GitHub. Por exemplo, a issue #16 define que um administrador deve executar as quatro operações de CRUD pela interface, que um funcionário comum não pode fazer operações administrativas e que falhas de integração precisam ser testadas.

## 3. Sprint Backlog e execução

O histórico do GitHub mostra seis entregas integradas à `main`, entre 7 e 20 de novembro de 2026. A numeração das issues e dos PRs foi usada para reconstruir o que foi planejado e o que foi concluído em cada incremento.

| Incremento | Issues / PR | Entrega registrada no `main` |
| --- | --- | --- |
| Documentação e infraestrutura | #1 a #12, PRs #1 a #5 e #12 | Documento de visão, modelos, README, estrutura inicial de backend e frontend |
| Back-end e autenticação | #13, #14, #19 a #21, PRs #20 e #21 | Conexão com PostgreSQL do Supabase, migração de JWT legado para Supabase Auth, modelo de funcionário sem senha local |
| Interface de CRUD | #15, #23, PR #23 | Tela de funcionários com criação, listagem com filtros, edição e exclusão lógica |
| Login no frontend | #17, #22, PR #22 | Login e sessão com Supabase Auth em Next.js App Router |
| Sincronização de login | #24, #25, PR #25 | Correção da sincronização com o Supabase Auth e da exclusão lógica |
| Ciclo de vida dos funcionários | #18, #26, PR #26 | Criação, bloqueio, reativação e exclusão no Supabase Auth com reversão em caso de falha |

## 4. Revisões das Sprints

As revisões abaixo descrevem o incremento apresentado e a evidência encontrada no repositório.

### Revisão da documentação e da infraestrutura

Foram entregues o documento de visão, o diagrama de classes, o diagrama entidade-relacionamento, o dicionário de dados e o README com instruções de execução. O resultado está em `docs/doc-visao.md`, `docs/doc-modelos.md` e nos READMEs da raiz, backend e frontend. A validação integrada e o provisionamento do primeiro administrador passaram a ter um roteiro próprio em `docs/validacao-integrada.md`.

### Revisão do back-end e da autenticação

O modelo `Funcionario` deixou de armazenar senha e passou a guardar `supabaseUserId`. O token do Supabase é validado no backend e o perfil é resolvido pelo `sub`. A suíte do Django cobre token inválido, expirado, assinatura incorreta, público diferente, perfil sem vínculo, desvio de relógio e verificação de `isAdmin` no banco, sem confiar no token do cliente.

### Revisão da interface de CRUD

A tela `/funcionarios` usa componentes de formulário, confirmação de exclusão, alertas e botões. Os testes do frontend verificam filtros por nome e e-mail, cadastro com senha inicial, edição sem campo de senha, estado vazio, estado de erro e modal de confirmação. Também verificam que controles administrativos ficam ocultos para usuários comuns.

### Revisão do login e do ciclo de vida

O login usa Server Actions do Next.js e encerra a sessão quando o perfil está inativo no Django. A criação e a exclusão de funcionários passaram a operar identidades no Supabase Auth. Os testes do backend cobrem a reversão da identidade quando falha o salvamento do perfil, quando falha a auditoria e quando a criação retorna erro.

## 5. Retrospectivas das Sprints

A retrospectiva é reconstruída a partir do que os commits e o estado atual mostram. Não havia ata de reunião salva no repositório, então os pontos abaixo são observações sobre o trabalho entregue, não transcrição de uma reunião.

O que funcionou:

- Foram registrados 10 PRs com base em `main`. Todos estão fechados e merged.
- Houve evolução incremental: primeiro infraestrutura, depois autenticação, depois CRUD e por fim correções de sincronização.
- A migração para Supabase Auth foi acompanhada de migração de banco, alteração de modelo, testes e documentação no mesmo conjunto de commits.

O que precisa mudar:

- O comando `python manage.py test` retornou 0 testes em uma execução a partir da raiz do repositório. O diagnóstico foi corrigido: dentro de `backend/`, o comando padrão encontra os 33 testes. O README agora deixa essa exigência explícita, e a issue #27 registrou a inclusão do workflow de CI.
- A validação ponta a ponta com credenciais reais do Supabase ainda não foi executada. O roteiro está em `docs/validacao-integrada.md`, e a issue #16 foi fechada com essa ressalva registrada.
- O lint do frontend aponta um aviso em `src/app/layout.tsx`: o arquivo exporta algo além de componentes e isso atrapalha o Fast Refresh.
- Não há workflow de CI no repositório. Testes e build foram executados localmente para este relatório.

Ações combinadas a partir desses pontos:

- Padronizar a descoberta dos testes do Django e atualizar o README.
- Manter o roteiro de validação integrada atualizado conforme o ambiente de execução.
- Corrigir o aviso do lint no layout do frontend.

## 6. CRUD em execução

O CRUD de funcionários está implementado no backend e na interface. A verificação feita neste relatório usou o commit `59abbea`:

| Verificação | Comando | Resultado |
| --- | --- | --- |
| Testes do backend | `python manage.py test funcionarios auditoria clientes speds` | 33 testes OK |
| Testes do frontend | `npm run test -- --run` | 4 arquivos, 23 testes OK |
| Lint do frontend | `npm run lint` | Passou com 1 aviso em `layout.tsx` |
| Build de produção | `npm run build` | Compilou; rotas `/`, `/dashboard`, `/funcionarios` e `/login` geradas |

A operação real contra o Supabase não foi executada porque as credenciais locais não foram usadas neste relatório. O que está comprovado é a suíte automatizada e o build.

## 7. Validação integrada

A issue #16 definia a validação do fluxo completo com Supabase Auth, backend Django, PostgreSQL e frontend. O trabalho realizado cobriu duas frentes:

- Cobertura automatizada: os testes do backend verificam token, vínculo entre identidade e perfil, persistência do vínculo em outra sessão, bloqueio de funcionário comum, CRUD, exclusão lógica e falhas de integração. Os testes do frontend verificam a interface de login e de funcionários.
- Documentação: `docs/validacao-integrada.md` descreve a configuração das quatro camadas, o provisionamento seguro do primeiro administrador e um roteiro com oito verificações manuais, incluindo a continuidade das operações após reiniciar o backend.

A execução do roteiro manual depende das credenciais do projeto Supabase e das duas aplicações rodando. Ela não foi feita neste relatório. A issue #16 foi fechada com comentário registrando a evidência automatizada e essa limitação.

## 8. Organização do GitHub

Branches: existem 12 branches remotas, incluindo `docs/relatorio-final-ci`. `main` é a padrão e recebeu 10 PRs mergeados. Há um PR aberto, #28, aguardando revisão de Eriky Rayan.

Issues: 27 issues registradas, 26 fechadas e 1 aberta (#27). As issues de documentação, infraestrutura, autenticação, CRUD e correções estão associadas aos respectivos PRs.

GitHub Projects: a API clássica de Projects retornou 404. A consulta ao Projects v2 falhou por falta do escopo `read:project` no token disponível. Não foi possível confirmar nem alterar o quadro com as permissões atuais. As issues, PRs e branches foram organizados conforme o histórico do repositório e o estado verificado pela API.

Testes registrados no GitHub: a issue #16 cobria a validação integrada e foi fechada com o roteiro documentado. A issue #27 pedia a correção da descoberta dos testes e a inclusão de CI; a descoberta já funcionava no diretório correto, e o workflow `.github/workflows/ci.yml` passou a rodar testes Django, Vitest, lint e build nos pull requests.

## 9. Evidências

- Histórico de commits: `git log --oneline --decorate`
- Estado da `main`: `59abbea`, igual a `origin/main`
- Documentos: `docs/doc-visao.md`, `docs/doc-modelos.md` e `docs/validacao-integrada.md`
- README: instruções de execução e testes
- Testes do backend: `backend/funcionarios/tests.py`
- Testes do frontend: arquivos `*.test.ts` e `*.test.tsx` em `frontend/src`
- Issues e PRs: https://github.com/Renan988/Projeto-Engenharia-I/issues
