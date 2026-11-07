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
    Sped *--> LogRastreabilidade
    
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
    FUNCIONARIO {
        int idFuncionario PK
        string nome
        string email
        string senha
        boolean isAdmin
    }

    LOG_RASTREABILIDADE {
        int idLog PK
        date dataHora
        string acaoRealizada
        int idFuncionario FK
        int idSped FK
    }

    CLIENTE {
        int idCli PK
        string cnpj
        string razaoSocial
        string telefoneWhatsApp
        string emailContador
        string regimeTributario
    }

    SPED {
        int idSped PK
        string mesReferencia
        int status
        blob arquivoRar
        int idCli FK
    }

    FUNCIONARIO ||--o{ LOG_RASTREABILIDADE : "gera"
    CLIENTE ||--o{ SPED : "possui"
    SPED ||--o{ LOG_RASTREABILIDADE : "contem"
```