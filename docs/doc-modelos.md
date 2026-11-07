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

