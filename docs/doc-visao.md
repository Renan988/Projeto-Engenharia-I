# Documento de Visão

Documento construído a partir do **Modelo BSI - Doc 001 - Documento de Visão** que pode ser encontrado no
link: https://docs.google.com/document/d/1DPBcyGHgflmz5RDsZQ2X8KVBPoEF5PdAz9BBNFyLa6A/edit?usp=sharing

## Descrição do Projeto

O projeto consiste no desenvolvimento de um **sistema de controle de fluxo (workflow)** para automatizar e organizar o processo de geração mensal de SPEDs da empresa **Intech Sistemas**, que atua no ramo de tecnologia da informação, oferecendo soluções em desenvolvimento de sistemas, suporte técnico, automação comercial, integração de serviços fiscais e soluções para gestão empresarial.

### Problema

Atualmente, a Intech Sistemas realiza o controle da geração mensal de SPEDs de forma manual, utilizando planilhas e ferramentas externas de comunicação, o que gera gargalos operacionais, falhas de comunicação entre os funcionários e falta de rastreabilidade das atividades realizadas. Esse processo descentralizado dificulta o acompanhamento da fila de atendimento, aumenta o risco de esquecimentos e atrasos no envio dos arquivos fiscais, podendo causar problemas e multas para os clientes da empresa.

### Solução Proposta

A solução proposta consiste no desenvolvimento de um sistema de controle de fluxo (workflow) para automatizar e organizar o processo de geração mensal de SPEDs da Intech Sistemas, permitindo o gerenciamento centralizado da fila de atendimento com priorização baseada no regime tributário dos clientes. O sistema terá funcionalidades de rastreabilidade, controle de status, registro automático das atividades e acompanhamento gerencial, buscando reduzir falhas operacionais, melhorar a comunicação interna e aumentar a eficiência do processo.

### Escopo

O sistema de controle de fluxo para geração mensal de SPEDs será responsável por centralizar e organizar todo o processo operacional realizado pela Intech Sistemas. Através do sistema será possível realizar o cadastro e gerenciamento de clientes, controle de usuários com diferentes níveis de acesso, consulta automática do regime tributário via API utilizando o CNPJ, definição automática da fila de prioridade para geração dos SPEDs e acompanhamento completo do fluxo de trabalho através de status progressivos. Além disso, o sistema permitirá registrar automaticamente logs de rastreabilidade das atividades realizadas pelos funcionários, armazenando informações de data, hora e usuário responsável por cada alteração no processo. O sistema também contará com dashboards gerenciais para acompanhamento da produtividade mensal da equipe e monitoramento do andamento das demandas fiscais.

## Equipe e Definição de Papéis

A equipe adota o **Scrum** como framework de gerenciamento do trabalho, com os papéis **rotativos entre os membros ao longo das Sprints**. Os papéis do Scrum são:

- **Product Owner (PO / Dono do Produto)**: único responsável por gerenciar o Product Backlog e maximizar o valor do trabalho entregue pela equipe. Define e prioriza as funcionalidades, comunica claramente a visão do produto para a equipe e os stakeholders e decide o que deve ser desenvolvido e em qual ordem.
- **Scrum Master**: atua como um líder servidor e facilitador do Scrum, garantindo que o framework seja compreendido e aplicado corretamente. Remove impedimentos que bloqueiam o progresso do time, auxilia a equipe a se auto-organizar e protege o grupo de interferências externas, atuando como coach sem exercer controle hierárquico tradicional.
- **Desenvolvedores (Developers)**: grupo de profissionais multifuncionais responsável por criar o incremento do produto a cada Sprint. Planejam como realizar o trabalho do Sprint Backlog, criam itens de qualidade, realizam testes e se auto-organizam para cumprir a meta definida.

Membro     |     Papel   |   E-mail   |
---------  | ----------- | ---------- |
Karliane | Cliente (Professora/Orientadora) | karliane.vale@ufrn.br
Eriky | Product Owner, Scrum Master e Developer (rotativo por Sprint) | eriky.medeiros.706@ufrn.edu.br
Felipe | Product Owner, Scrum Master e Developer (rotativo por Sprint) | —
Jefferson | Product Owner, Scrum Master e Developer (rotativo por Sprint) | —
José Samuel | Product Owner, Scrum Master e Developer (rotativo por Sprint) | jose.lima.146@ufrn.edu.br
Renan | Product Owner, Scrum Master e Developer (rotativo por Sprint) | renan.medeiros.150@ufrn.edu.br

### Matriz de Competências

Membro     |     Competências   |
---------  | ----------- |
Eriky | TypeScript, Django (Python), Supabase/PostgreSQL, Git/GitHub, Modelagem UML |
Felipe | TypeScript, Supabase/PostgreSQL, Git/GitHub, Modelagem UML |
Jefferson | Django (Python), Supabase/PostgreSQL, Git/GitHub, Modelagem UML |
José Samuel | TypeScript, Django (Python), Git/GitHub, Metodologias Ágeis (Scrum) |
Renan | TypeScript, Django (Python), Supabase/PostgreSQL, Git/GitHub, Metodologias Ágeis (Scrum) |
