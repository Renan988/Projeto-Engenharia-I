"""
Modelo de dados da entidade Sped (Tabela SPED).
Referência: docs/doc-modelos.md e docs/doc-visao.md (US03 - Manter SPED e US04 - Enviar SPED).
"""

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

from clientes.models import Cliente

from .services import (
    enviar_email_com_retentativa,
    enviar_notificacao_whatsapp_com_retentativa,
    gerar_mensagem_personalizada,
)

validador_mes_referencia = RegexValidator(
    regex=r'^(0[1-9]|1[0-2])/\d{4}$',
    message='O mês de referência deve estar no formato MM/AAAA (ex.: 11/2026).',
)


class Sped(models.Model):
    """
    Entidade Sped conforme especificada no Documento de Modelos:
    - idSped: SERIAL PK / Identity
    - mesReferencia: VARCHAR(7) Not Null (MM/AAAA)
    - status: VARCHAR(15) Not Null (Check Enum: PENDENTE, GERADO, ENVIADO)
    - arquivoRar: Arquivo anexado do SPED
    - cliente (idCli / cnpj_cliente): FK para Cliente Not Null
    """

    class StatusChoices(models.TextChoices):
        PENDENTE = 'PENDENTE', 'Pendente'
        GERADO = 'GERADO', 'Gerado'
        ENVIADO = 'ENVIADO', 'Enviado'

    FLUXO_PROGRESSIVO = {
        StatusChoices.PENDENTE: [StatusChoices.GERADO],
        StatusChoices.GERADO: [StatusChoices.ENVIADO],
        StatusChoices.ENVIADO: [],
    }

    idSped = models.AutoField(
        primary_key=True,
        db_column='idSped',
        verbose_name='ID do SPED',
    )
    mesReferencia = models.CharField(
        max_length=7,
        validators=[validador_mes_referencia],
        db_column='mesReferencia',
        verbose_name='Mês de Referência (MM/AAAA)',
    )
    status = models.CharField(
        max_length=15,
        choices=StatusChoices.choices,
        default=StatusChoices.PENDENTE,
        db_column='status',
        verbose_name='Status do SPED',
    )
    arquivoRar = models.FileField(
        upload_to='speds/%Y/%m/',
        null=True,
        blank=True,
        db_column='arquivoRar',
        verbose_name='Arquivo RAR do SPED',
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE,
        related_name='speds',
        db_column='idCli',
        verbose_name='Cliente',
    )
    ordemPrioridade = models.PositiveSmallIntegerField(
        default=3,
        db_column='ordemPrioridade',
        verbose_name='Ordem de Prioridade na Fila',
    )
    criadoEm = models.DateTimeField(
        auto_now_add=True,
        db_column='criadoEm',
        verbose_name='Criado em',
    )
    atualizadoEm = models.DateTimeField(
        auto_now=True,
        db_column='atualizadoEm',
        verbose_name='Atualizado em',
    )

    class Meta:
        db_table = 'SPED'
        verbose_name = 'SPED'
        verbose_name_plural = 'SPEDs'
        ordering = ['ordemPrioridade', 'cliente__nomeEmpresa', '-idSped']
        constraints = [
            models.UniqueConstraint(
                fields=['cliente', 'mesReferencia'],
                name='unique_sped_cliente_mes_referencia',
            )
        ]

    def __str__(self) -> str:
        return f'SPED #{self.idSped} - {self.cliente.nomeEmpresa} ({self.mesReferencia}) [{self.status}]'

    def save(self, *args, **kwargs):
        if self.cliente_id:
            self.ordemPrioridade = self.cliente.ordem_prioridade_regime
        super().save(*args, **kwargs)

    @property
    def cnpj_cliente(self) -> str:
        """Compatibilidade direta com o dicionário de dados (coluna/atributo cnpj_cliente)."""
        return self.cliente.cnpj if self.cliente_id else ''

    # Métodos do Diagrama de Classes (doc-modelos.md)
    def atualizarStatus(self, novoStatus: str, funcionario=None) -> 'Sped':
        """
        RF03.03 - Atualizar Status do SPED seguindo o fluxo progressivo (PENDENTE > GERADO > ENVIADO),
        registrando o histórico automaticamente em LogRastreabilidade (RF05.01).
        Corresponde ao método +atualizarStatus(novoStatus: String): void do Modelo Conceitual.
        """
        novo_status_upper = (novoStatus or '').strip().upper()
        if novo_status_upper not in self.StatusChoices.values:
            raise ValidationError(
                f'Status inválido "{novoStatus}". Os valores permitidos são: PENDENTE, GERADO, ENVIADO.'
            )

        status_anterior = self.status
        if novo_status_upper == status_anterior:
            return self

        permitidos = self.FLUXO_PROGRESSIVO.get(status_anterior, [])
        if novo_status_upper not in permitidos:
            raise ValidationError(
                f'Transição de status inválida: não é permitido mudar de {status_anterior} para '
                f'{novo_status_upper}. O fluxo deve seguir a ordem progressiva PENDENTE > GERADO > ENVIADO.'
            )

        self.status = novo_status_upper
        self.save(update_fields=['status', 'atualizadoEm'])

        if funcionario is not None:
            from auditoria.models import LogRastreabilidade

            LogRastreabilidade.registrarLog(
                acao=(
                    f'Alterou o status do SPED ({self.mesReferencia} - {self.cliente.nomeEmpresa}) '
                    f'de {status_anterior} para {self.status}'
                ),
                funcionario=funcionario,
                sped=self,
            )

        return self

    def realizarUpload(self, arquivo, funcionario=None) -> 'Sped':
        """
        RF03.04 - Anexar Arquivo do SPED: realiza o upload do arquivo SPED gerado e
        atualiza o status para GERADO caso esteja PENDENTE.
        Corresponde ao método +realizarUpload(arquivo: File): void do Modelo Conceitual.
        """
        status_anterior = self.status
        self.arquivoRar = arquivo
        if self.status == self.StatusChoices.PENDENTE:
            self.status = self.StatusChoices.GERADO
        self.save()

        if funcionario is not None:
            from auditoria.models import LogRastreabilidade

            detalhe_status = (
                f' e alterou status de {status_anterior} para {self.status}'
                if status_anterior != self.status
                else ''
            )
            LogRastreabilidade.registrarLog(
                acao=(
                    f'Realizou upload do arquivo SPED ({self.mesReferencia}) '
                    f'do cliente {self.cliente.nomeEmpresa}{detalhe_status}'
                ),
                funcionario=funcionario,
                sped=self,
            )
        return self

    def marcarSped(self, novo_status: str = 'GERADO', funcionario=None) -> 'Sped':
        """
        Corresponde ao método +marcarSped(sped: Sped): void do Modelo Conceitual.
        """
        return self.atualizarStatus(novo_status, funcionario=funcionario)

    def enviarEmailContador(self, funcionario=None) -> dict:
        """
        RF04.01 - Enviar SPED por E-mail ao contador configurado no cadastro do cliente.
        Corresponde ao método +enviarEmailContador(): void do Modelo Conceitual.
        """
        nome_func = getattr(funcionario, 'nome', 'Equipe Intech Sistemas')
        mensagem_email = gerar_mensagem_personalizada(
            nome_funcionario=nome_func,
            nome_cliente=self.cliente.nomeEmpresa,
            mes_referencia=self.mesReferencia,
            destinatario='contador',
        )
        assunto = f'Arquivo SPED - {self.cliente.nomeEmpresa} - Competência {self.mesReferencia}'
        caminho = self.arquivoRar.path if self.arquivoRar else None

        return enviar_email_com_retentativa(
            destinatario_email=self.cliente.emailContador,
            assunto=assunto,
            corpo_mensagem=mensagem_email,
            caminho_arquivo=caminho,
        )

    def enviarSped(self, funcionario=None) -> dict:
        """
        US04 - Enviar SPED (RF04.01, RF04.02, RF04.03, RF04.04):
        1. Verifica se o SPED já está GERADO (ou possui arquivo anexado).
        2. Personaliza mensagens com nome do funcionário logado e nome do cliente (RF04.03).
        3. Envia o arquivo SPED por e-mail ao contador do cliente (RF04.01).
        4. Notifica o cliente via WhatsApp (RF04.02).
        5. Atualiza o status do SPED para ENVIADO (RF04.04) e registra LogRastreabilidade (RF05.01).
        Corresponde ao método +enviarSped(sped: Sped): void do Modelo Conceitual.
        """
        if self.status == self.StatusChoices.PENDENTE:
            if self.arquivoRar:
                self.atualizarStatus(self.StatusChoices.GERADO, funcionario=funcionario)
            else:
                raise ValidationError(
                    'Não é possível enviar um SPED com status PENDENTE sem antes gerar/anexar o arquivo.'
                )

        nome_func = getattr(funcionario, 'nome', 'Equipe Intech Sistemas')
        mensagem_whatsapp = gerar_mensagem_personalizada(
            nome_funcionario=nome_func,
            nome_cliente=self.cliente.nomeEmpresa,
            mes_referencia=self.mesReferencia,
            destinatario='cliente',
        )

        resultado_email = self.enviarEmailContador(funcionario=funcionario)
        if not resultado_email.get('sucesso'):
            raise ValidationError(
                f'Falha no envio de e-mail para o contador ({self.cliente.emailContador}): '
                f'{resultado_email.get("erro")}. Tente novamente posteriormente.'
            )

        resultado_whatsapp = enviar_notificacao_whatsapp_com_retentativa(
            telefone=self.cliente.telefoneWhatsApp,
            mensagem=mensagem_whatsapp,
        )

        # RF04.04 - Concluir Envio: atualiza o status para ENVIADO
        if self.status != self.StatusChoices.ENVIADO:
            self.atualizarStatus(self.StatusChoices.ENVIADO, funcionario=funcionario)

        if funcionario is not None:
            from auditoria.models import LogRastreabilidade

            LogRastreabilidade.registrarLog(
                acao=(
                    f'Enviou o SPED ({self.mesReferencia}) do cliente {self.cliente.nomeEmpresa} '
                    f'ao contador ({self.cliente.emailContador}) e notificou via WhatsApp'
                ),
                funcionario=funcionario,
                sped=self,
            )

        return {
            'sped_id': self.idSped,
            'status': self.status,
            'email_contador': resultado_email,
            'notificacao_whatsapp': resultado_whatsapp,
            'mensagem_personalizada': mensagem_whatsapp,
        }
