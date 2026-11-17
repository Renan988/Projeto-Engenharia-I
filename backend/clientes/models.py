"""
Modelo de dados da entidade Cliente (Tabela CLIENTE).
Referência: docs/doc-modelos.md e docs/doc-visao.md (US02 - Manter Cliente).
"""

from django.db import models

from .services import consultar_dados_cnpj_api, formatar_cnpj


class Cliente(models.Model):
    """
    Entidade Cliente conforme especificada no Documento de Modelos:
    - idCli: SERIAL PK / Identity
    - cnpj: VARCHAR(18) Unique / Not Null
    - nomeEmpresa: VARCHAR(150) Not Null
    - razaoSocial: VARCHAR(150) Not Null
    - telefoneWhatsApp: VARCHAR(20)
    - emailContador: VARCHAR(150) Not Null
    - regimeTributario: VARCHAR(50) Not Null
    """

    class RegimeTributarioChoices(models.TextChoices):
        LUCRO_REAL = 'Lucro Real', 'Lucro Real'
        LUCRO_PRESUMIDO = 'Lucro Presumido', 'Lucro Presumido'
        SIMPLES_NACIONAL = 'Simples Nacional', 'Simples Nacional'
        MEI = 'MEI', 'MEI'
        OUTROS = 'Outros', 'Outros'

    idCli = models.AutoField(
        primary_key=True,
        db_column='idCli',
        verbose_name='ID do Cliente',
    )
    cnpj = models.CharField(
        max_length=18,
        unique=True,
        db_column='cnpj',
        verbose_name='CNPJ',
    )
    nomeEmpresa = models.CharField(
        max_length=150,
        db_column='nomeEmpresa',
        verbose_name='Nome da Empresa',
    )
    razaoSocial = models.CharField(
        max_length=150,
        db_column='razaoSocial',
        verbose_name='Razão Social',
    )
    telefoneWhatsApp = models.CharField(
        max_length=20,
        blank=True,
        default='',
        db_column='telefoneWhatsApp',
        verbose_name='Telefone / WhatsApp',
    )
    emailContador = models.EmailField(
        max_length=150,
        db_column='emailContador',
        verbose_name='E-mail do Contador',
    )
    regimeTributario = models.CharField(
        max_length=50,
        db_column='regimeTributario',
        verbose_name='Regime Tributário',
    )

    class Meta:
        db_table = 'CLIENTE'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nomeEmpresa']

    def __str__(self) -> str:
        return f'{self.nomeEmpresa} ({self.cnpj}) - {self.regimeTributario}'

    def save(self, *args, **kwargs):
        if self.cnpj:
            self.cnpj = formatar_cnpj(self.cnpj)
        super().save(*args, **kwargs)

    @property
    def ordem_prioridade_regime(self) -> int:
        """
        Define o peso de prioridade para a fila de atendimento dos SPEDs (RF03.01):
        1 - Lucro Real (maior complexidade e prazos fiscais rigorosos)
        2 - Lucro Presumido
        3 - Simples Nacional
        4 - MEI / Outros
        """
        regime_upper = (self.regimeTributario or '').upper()
        if 'REAL' in regime_upper:
            return 1
        if 'PRESUMIDO' in regime_upper:
            return 2
        if 'SIMPLES' in regime_upper:
            return 3
        if 'MEI' in regime_upper:
            return 4
        return 5

    # Métodos do Diagrama de Classes (doc-modelos.md)
    def consultarRegimeAPI(self) -> dict:
        """
        Consulta automaticamente os dados da empresa e regime tributário via API usando o CNPJ.
        Corresponde ao método +consultarRegimeAPI(): void do Modelo Conceitual (RF02.01).
        """
        dados = consultar_dados_cnpj_api(self.cnpj)
        if dados.get('api_disponivel'):
            if not self.nomeEmpresa and dados.get('nomeEmpresa'):
                self.nomeEmpresa = dados['nomeEmpresa']
            if not self.razaoSocial and dados.get('razaoSocial'):
                self.razaoSocial = dados['razaoSocial']
            if not self.regimeTributario and dados.get('regimeTributario'):
                self.regimeTributario = dados['regimeTributario']
        return dados

    def manterCliente(
        self,
        nomeEmpresa: str = None,
        razaoSocial: str = None,
        telefoneWhatsApp: str = None,
        emailContador: str = None,
        regimeTributario: str = None,
    ) -> 'Cliente':
        """
        Atualiza os dados cadastrais do cliente (RF02.03).
        Corresponde ao método +manterCliente(cliente: Cliente): void do Modelo Conceitual.
        """
        if nomeEmpresa is not None:
            self.nomeEmpresa = nomeEmpresa
        if razaoSocial is not None:
            self.razaoSocial = razaoSocial
        if telefoneWhatsApp is not None:
            self.telefoneWhatsApp = telefoneWhatsApp
        if emailContador is not None:
            self.emailContador = emailContador
        if regimeTributario is not None:
            self.regimeTributario = regimeTributario
        self.save()
        return self
