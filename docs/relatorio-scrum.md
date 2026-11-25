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

O desenvolvimento foi organizado em duas Sprints (Sprint 1 e Sprint 2), com entregas integradas à branch `main`. A numeração das issues e dos pull requests registra o planejamento e a execução de cada Sprint:

| Sprint | Escopo / Incrementos | Issues / PRs | Entrega registrada |
| --- | --- | --- | --- |
| **Sprint 1** | Estrutura inicial e documentação base | Issues #1 a #9, PRs #1 a #5 | Criação do repositório, configuração do GitHub Projects, criação do diretório `docs/`, elaboração do Documento de Visão (`docs/doc-visao.md`), do Documento de Modelos (`docs/doc-modelos.md`) e do `README.md` inicial |
| **Sprint 2** | Infraestrutura, CRUD de funcionários, integração com Supabase Auth, testes e CI | Issues #10 a #27, PRs #12, #20 a #23, #25 e #26 | Estrutura de backend (Django REST) e frontend (Next.js), conexão com PostgreSQL do Supabase, autenticação e sincronização com Supabase Auth, ciclo de vida e interface completa de CRUD de funcionários, validação integrada, testes automatizados e pipeline de CI |

## 4. Revisões das Sprints

As revisões abaixo descrevem os incrementos apresentados em cada Sprint e as evidências correspondentes no projeto.

### Revisão da Sprint 1 — Repositório, GitHub Projects e Documentação

Na Sprint 1 foram estabelecidos a organização do projeto e os artefatos de engenharia de requisitos e modelagem:
- Criação e estruturação do repositório no GitHub e do quadro no GitHub Projects para acompanhamento das atividades.
- Criação do diretório `docs/` contendo o Documento de Visão (`docs/doc-visao.md`) e o Documento de Modelos (`docs/doc-modelos.md`), com diagrama de classes, diagrama entidade-relacionamento e dicionário de dados.
- Elaboração do `README.md` na raiz do projeto com a descrição da solução, tecnologias e equipe.

### Revisão da Sprint 2 — CRUD de Funcionários, Integração com Supabase e Validação

Na Sprint 2 foram entregues a infraestrutura das aplicações, o CRUD completo de funcionários integrado ao Supabase, a suíte de testes e a automação de CI:
- **Back-end e autenticação:** O modelo `Funcionario` deixou de armazenar senha local e passou a guardar `supabaseUserId`. O token do Supabase é validado no backend e o perfil é resolvido pelo `sub`. A suíte do Django cobre token inválido, expirado, assinatura incorreta, público diferente, perfil sem vínculo, desvio de relógio e verificação de `isAdmin` no banco, sem confiar no token do cliente.
- **Interface de CRUD:** A tela `/funcionarios` implementa criação, listagem com filtros por nome e e-mail, edição e exclusão lógica com componentes de formulário, modal de confirmação e alertas. Os testes do frontend verificam filtros, cadastro com senha inicial, edição sem campo de senha, estados vazio/erro e ocultação de controles administrativos para usuários comuns.
- **Login, ciclo de vida e CI:** O login usa Server Actions do Next.js e encerra a sessão quando o perfil está inativo no Django. A criação, o bloqueio, a reativação e a exclusão de funcionários operam identidades no Supabase Auth com reversão em caso de falha. Foram adicionados também o roteiro de validação integrada (`docs/validacao-integrada.md`) e o workflow de integração contínua (`.github/workflows/ci.yml`).

## 5. Retrospectivas das Sprints

A retrospectiva consolida os aprendizados da equipe ao longo da Sprint 1 e da Sprint 2.

### Sprint 1
**O que funcionou:**

- A definição prévia do Documento de Visão, da modelagem de dados (`docs/doc-modelos.md`) e do quadro no GitHub Projects deu clareza sobre as regras de negócio e facilitou a divisão de tarefas para a implementação técnica.

**O que precisou de ajuste:**

- Houve dificuldade inicial na organização dos papéis do Scrum, o que resultou na adoção de uma divisão dinâmica e rotativa dos papéis conforme a necessidade de cada etapa.
- Detalhar critérios de aceitação mais granulares nas issues técnicas para preparar a integração entre frontend, backend e autenticação na Sprint seguinte.

### Sprint 2
**O que funcionou:**

- Evolução incremental bem definida via Pull Requests revisados e integrados à `main`: primeiro infraestrutura, depois autenticação com Supabase Auth, seguida pela interface do CRUD e correções de sincronização.
- A migração para o Supabase Auth foi acompanhada de migração de banco, alteração de modelo, testes automatizados e atualização da documentação no mesmo conjunto de entregas.
- A apresentação e execução do CRUD de funcionários junto à professora em sala de aula transcorreu sem falhas, validando o fluxo planejado.

**O que precisou mudar e ações aplicadas:**

- Ocorreram erros relacionados à conexão e sincronização com o banco de dados e autenticação do Supabase (tratados e corrigidos por meio das issues #24 e #25 e da garantia de consistência do ciclo de vida na issue #18).
- O comando `python manage.py test` retornava 0 testes quando executado fora da pasta `backend/`. O diagnóstico foi documentado no `README.md` (exigindo execução a partir de `backend/`) e automatizado no workflow de CI (`.github/workflows/ci.yml`).
- O lint do frontend apontou um aviso menor em `src/app/layout.tsx` relacionado à exportação de metadados junto ao componente, registrado para acompanhamento sem impacto no build de produção.

## 6. CRUD em execução

A execução e validação prática do CRUD de funcionários integrado ao Supabase foi realizada junto à professora orientadora em sala de aula, e todas as operações (autenticação, cadastro, listagem com filtros, edição, exclusão lógica e controle de permissões) ocorreram conforme o planejado.

Além da validação presencial em sala de aula, a integridade do CRUD é comprovada pela suíte de testes automatizados e pelo build de produção do projeto:

| Verificação | Comando | Resultado |
| --- | --- | --- |
| Validação em sala de aula | Execução completa pela interface web com Supabase | Validado junto à professora; tudo ocorreu conforme o planejado |
| Testes do backend | `python manage.py test` (em `backend/`) | 33 testes OK |
| Testes do frontend | `npm run test -- --run` | 4 arquivos, 23 testes OK |
| Lint do frontend | `npm run lint` | Passou com 1 aviso em `layout.tsx` |
| Build de produção | `npm run build` | Compilou; rotas `/`, `/dashboard`, `/funcionarios` e `/login` geradas |

## 7. Validação integrada

A issue #16 definia a validação do fluxo completo com Supabase Auth, backend Django, PostgreSQL e frontend. O trabalho realizado cobriu três frentes:

- **Validação prática do fluxo:** O funcionamento ponta a ponta do CRUD com autenticação foi demonstrado e validado em sala de aula junto à professora orientadora.
- **Cobertura automatizada:** Os testes do backend verificam token, vínculo entre identidade e perfil, persistência do vínculo em outra sessão, bloqueio de funcionário comum, CRUD, exclusão lógica e falhas de integração. Os testes do frontend verificam a interface de login e de funcionários.
- **Documentação:** `docs/validacao-integrada.md` descreve a configuração das quatro camadas, o provisionamento seguro do primeiro administrador e o roteiro estruturado com as oito verificações ponta a ponta.

## 8. Organização do GitHub

Branches: a branch `main` é a padrão e recebeu os Pull Requests das Sprints 1 e 2 devidamente revisados e mergeados. O workflow de CI configurado em `.github/workflows/ci.yml` executa automaticamente os testes e o build a cada atualização.

Issues: 27 issues registradas e concluídas ao longo das Sprints 1 e 2. As issues de documentação, infraestrutura, autenticação, CRUD, validação integrada, CI e correções estão associadas aos respectivos PRs.

Testes registrados no GitHub: a issue #16 cobriu a validação integrada e seu roteiro documentado. A issue #27 registrou a padronização da descoberta dos testes e a inclusão do workflow `.github/workflows/ci.yml`, que executa os testes do Django, Vitest, lint e build do Next.js.

## 9. Evidências

- Histórico de commits: `git log --oneline --decorate`
- Estado da `main`: `59abbea`, igual a `origin/main`
- Documentos: `docs/doc-visao.md`, `docs/doc-modelos.md` e `docs/validacao-integrada.md`
- README: instruções de execução e testes
- Testes do backend: `backend/funcionarios/tests.py`
- Testes do frontend: arquivos `*.test.ts` e `*.test.tsx` em `frontend/src`
- Issues e PRs: https://github.com/Renan988/Projeto-Engenharia-I/issues
