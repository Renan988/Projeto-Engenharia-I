# Documento de Modelos

Neste documento temos o modelo Conceitual (UML) ou de Dados (Entidade-Relacionamento). Temos também a descrição das entidades e o dicionário de dados.

## Modelo Conceitual

### Diagrama de Classes usando Mermaid

```mermaid
classDiagram
    class Funcionario {
        -Int idFuncionario
        -String nome
        -String email
        -String senha
        -Boolean isAdmin
        +solicitarAutorizacaoAcesso() boolean
        +manterFuncionario(funcionario: Funcionario) void
    }
    
    class LogRastreabilidade {
        -Int idLog
        -Date dataHora
        -String acaoRealizada
        +registrarLog(acao: String, funcionario: Funcionario) void
        +gerarDashboard() Dashboard
    }
    
    class Cliente {
        -Int idCli
        -String cnpj
        -String nomeEmpresa
        -String razaoSocial
        -String telefoneWhatsApp
        -String emailContador
        -String regimeTributario
        +consultarRegimeAPI() void
        +manterCliente(cliente: Cliente) void
    }
    
    class Sped {
        -Int idSped
        -String mesReferencia
        -Int status
        -File arquivoRar
        +atualizarStatus(novoStatus: String) void
        +realizarUpload(arquivo: File) void
        +enviarEmailContador() void
        +marcarSped(sped: Sped) void
        +enviarSped(sped: Sped) void
    }

    Funcionario "1" -- "*" LogRastreabilidade
    Cliente "1" -- "*" Sped
    LogRastreabilidade "0" -- "1" Sped
    
    note for Sped "Observação: O status do SPED deve ser PENDENTE, GERADO ou ENVIADO."
```

### Descrição das Entidades

Descrição sucinta das entidades presentes no sistema.

| Entidade | Descrição |
|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Funcionario | Entidade que representa um Funcionário tem as informações: Int idFuncionario, String nome, String email, String senha, Boolean isAdmin, +solicitarAutorizacaoAcesso(), +manterFuncionario(). |
| LogRastreabilidade | Entidade que representa o log do sistema tem as informações: Int idLog, Date dataHora, String acaoRealizada, +registrarLog(), +gerarDashboard(). |
| Cliente | Entidade que representa um Cliente tem as informações: Int idCli, String cnpj, String razaoSocial, String telefoneWhatsApp, String emailContador, String regimeTributario, +consultarRegimeAPI(), +manterCliente(). |
| Sped | Entidade que representa um registro SPED tem as informações: Int idSped, String mesReferencia, Int status, File arquivoRar, +atualizarStatus(), +realizarUpload(), +enviarEmailContador(), +marcarSped(), +enviarSped(). |

## Modelo de Dados (Entidade-Relacionamento)

```mermaid
erDiagram
    FUNCIONARIO ||--o{ LOG_RASTREABILIDADE : "realiza"
    CLIENTE ||--o{ SPED : "possui"
    SPED |o--o{ LOG_RASTREABILIDADE : "vinculado_a"

    FUNCIONARIO {
        int idFuncionario PK
        string nome
        string email
        string senha
        boolean isAdmin
    }

    LOG_RASTREABILIDADE {
        int idLog PK
        datetime dataHora
        string acaoRealizada
        int idFuncionario FK
        int idSped FK "Nulo se for ação geral"
    }

    CLIENTE {
        int idCli PK
        string cnpj
        string nomeEmpresa
        string razaoSocial
        string telefoneWhatsApp
        string emailContador
        string regimeTributario
    }

    SPED {
        int idSped PK
        string mesReferencia
        int status "PENDENTE, GERADO, ENVIADO"
        string arquivoRar
        int idCli FK
    }
```

### Dicionário de Dados

| Tabela | FUNCIONARIO |
| --- | --- |
| Descrição | Armazena as informações dos funcionários que utilizam e administram o sistema. |
| Observação | O campo `isAdmin` define se o funcionário possui privilégios de administrador. |

| Nome | Descrição | Tipo de Dado | Tamanho | Restrições de Domínio |
| --- | --- | --- | --- | --- |
| idFuncionario | identificador gerado pelo SGBD | SERIAL | --- | PK / Identity |
| nome | nome completo do funcionário | VARCHAR | 150 | Not Null |
| email | e-mail de acesso do funcionário | VARCHAR | 150 | Unique / Not Null |
| senha | senha criptografada de acesso | VARCHAR | 255 | Not Null |
| isAdmin | flag de privilégio administrador | BOOLEAN | --- | Not Null |

| Tabela | LOG_RASTREABILIDADE |
| --- | --- |
| Descrição | Armazena o registro (histórico) das ações executadas no sistema. |
| Observação | Usado para auditoria de ações realizadas pelos funcionários. Pode estar atrelado a um SPED (opcional). |

| Nome | Descrição | Tipo de Dado | Tamanho | Restrições de Domínio |
| --- | --- | --- | --- | --- |
| idLog | identificador gerado pelo SGBD | SERIAL | --- | PK / Identity |
| dataHora | data e hora exata da ação | TIMESTAMP | --- | Not Null |
| acaoRealizada | descrição detalhada da ação | VARCHAR | 250 | Not Null |
| idFuncionario | funcionário responsável pela ação | INTEGER | --- | FK / Not Null |
| idSped | SPED associado à ação (se houver) | INTEGER | --- | FK |

| Tabela | CLIENTE |
| --- | --- |
| Descrição | Armazena os dados das empresas (clientes) vinculadas ao sistema. |
| Observação | Os clientes são as entidades para as quais os arquivos do SPED são gerados. A chave primária é o CNPJ. |

| Nome | Descrição | Tipo de Dado | Tamanho | Restrições de Domínio |
| --- | --- | --- | --- | --- |
| cnpj | CNPJ do cliente | VARCHAR | 18 | PK / Not Null |
| nomeEmpresa| nome da empresa | VARCHAR| 150 | Not Null |
| razaoSocial | razão social do cliente | VARCHAR | 150 | Not Null |
| telefoneWhatsApp | número de contato (WhatsApp) | VARCHAR | 20 | --- |
| emailContador | e-mail do contador responsável | VARCHAR | 150 | Not Null |
| regimeTributario | regime tributário do cliente | VARCHAR | 50 | Not Null |

| Tabela | SPED |
| --- | --- |
| Descrição | Armazena os registros e os arquivos RAR referentes aos SPEDs dos clientes. |
| Observação | O status armazena textualmente a situação do arquivo (PENDENTE, GERADO, ENVIADO). |

| Nome | Descrição | Tipo de Dado | Tamanho | Restrições de Domínio |
| --- | --- | --- | --- | --- |
| idSped | identificador gerado pelo SGBD | SERIAL | --- | PK / Identity |
| mesReferencia | mês e ano de referência (MM/AAAA) | VARCHAR | 7 | Not Null |
| status | status atual do SPED | VARCHAR | 15 | Not Null (Check: Enum) |
| arquivoRar | arquivo binário anexado | BYTEA | --- | --- |
| cnpj_cliente | CNPJ do cliente titular do SPED | VARCHAR | 18 | FK / Not Null |