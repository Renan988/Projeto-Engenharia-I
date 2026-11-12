"""
Modelo de dados da entidade LogRastreabilidade (Tabela LOG_RASTREABILIDADE).
Referência: docs/doc-modelos.md e docs/doc-visao.md (US05 - Rastreabilidade Automática e US06 - Dashboard Gerencial).
"""

from typing import Any, Dict

from django.conf import settings
from django.db import models
from django.db.models import Count, Q


class LogRastreabilidade(models.Model):
    """
    Entidade LogRastreabilidade conforme especificada no Documento de Modelos:
    - idLog: SERIAL PK / Identity
    - dataHora: TIMESTAMP Not Null
    - acaoRealizada: VARCHAR(250) Not Null
    - idFuncionario: INTEGER FK Not Null
    - idSped: INTEGER FK Nullable ("Nulo se for ação geral")
    """

    idLog = models.AutoField(
        primary_key=True,
        db_column='idLog',
        verbose_name='ID do Log',
    )
    dataHora = models.DateTimeField(
        auto_now_add=True,
        db_column='dataHora',
        verbose_name='Data e Hora',
    )
    acaoRealizada = models.CharField(
        max_length=250,
        db_column='acaoRealizada',
        verbose_name='Ação Realizada',
    )
    funcionario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='logs',
        db_column='idFuncionario',
        verbose_name='Funcionário Responsável',
    )
    sped = models.ForeignKey(
        'speds.Sped',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='logs',
        db_column='idSped',
        verbose_name='SPED Vinculado',
    )

    class Meta:
        db_table = 'LOG_RASTREABILIDADE'
        verbose_name = 'Log de Rastreabilidade'
        verbose_name_plural = 'Logs de Rastreabilidade'
        ordering = ['-dataHora', '-idLog']

    def __str__(self) -> str:
        return f'[{self.dataHora:%d/%m/%Y %H:%M:%S}] {self.funcionario.nome}: {self.acaoRealizada}'

    # Métodos do Diagrama de Classes (doc-modelos.md)
    @classmethod
    def registrarLog(
        cls,
        acao: str,
        funcionario,
        sped=None,
    ) -> 'LogRastreabilidade':
        """
        RF05.01 - Registrar Log de Mudança de Status (quando `sped` é informado)
        RF05.02 - Registrar Log de Ações Gerais (quando `sped` é None)
        Corresponde ao método +registrarLog(acao: String, funcionario: Funcionario): void do Modelo Conceitual.
        """
        return cls.objects.create(
            acaoRealizada=(acao or '')[:250],
            funcionario=funcionario,
            sped=sped,
        )

    @classmethod
    def gerarDashboard(cls, mes_referencia: str = None) -> Dict[str, Any]:
        """
        US06 - Dashboard Gerencial:
        - RF06.01 - Visualizar Produtividade: Exibe indicadores da produtividade mensal da equipe.
        - RF06.02 - Visualizar Demandas: Exibe o andamento das demandas fiscais do mês na fila de atendimento.
        Corresponde ao método +gerarDashboard(): Dashboard do Modelo Conceitual.
        """
        from funcionarios.models import Funcionario
        from speds.models import Sped

        speds_qs = Sped.objects.select_related('cliente').all()
        logs_qs = cls.objects.select_related('funcionario', 'sped').all()

        if mes_referencia:
            speds_qs = speds_qs.filter(mesReferencia=mes_referencia)
            logs_qs = logs_qs.filter(
                Q(sped__mesReferencia=mes_referencia)
                | Q(acaoRealizada__icontains=mes_referencia)
            )

        total_speds = speds_qs.count()
        pendentes = speds_qs.filter(status=Sped.StatusChoices.PENDENTE).count()
        gerados = speds_qs.filter(status=Sped.StatusChoices.GERADO).count()
        enviados = speds_qs.filter(status=Sped.StatusChoices.ENVIADO).count()

        taxa_conclusao = round((enviados / total_speds) * 100, 2) if total_speds > 0 else 0.0

        # Distribuição de demandas por Regime Tributário (RF06.02)
        demandas_por_regime = list(
            speds_qs.values(regimeTributario=models.F('cliente__regimeTributario'))
            .annotate(
                total=Count('idSped'),
                pendentes=Count('idSped', filter=Q(status=Sped.StatusChoices.PENDENTE)),
                gerados=Count('idSped', filter=Q(status=Sped.StatusChoices.GERADO)),
                enviados=Count('idSped', filter=Q(status=Sped.StatusChoices.ENVIADO)),
            )
            .order_by('regimeTributario')
        )

        # Produtividade da equipe por funcionário (RF06.01)
        produtividade_equipe = []
        for func in Funcionario.objects.filter(is_active=True).order_by('nome'):
            logs_func = logs_qs.filter(funcionario=func)
            speds_gerados_func = logs_func.filter(
                sped__isnull=False,
                acaoRealizada__icontains='GERADO',
            ).values('sped_id').distinct().count()
            speds_enviados_func = logs_func.filter(
                sped__isnull=False,
                acaoRealizada__icontains='ENVIADO',
            ).values('sped_id').distinct().count()

            produtividade_equipe.append(
                {
                    'idFuncionario': func.idFuncionario,
                    'nome': func.nome,
                    'email': func.email,
                    'perfil': func.perfil,
                    'total_acoes_registradas': logs_func.count(),
                    'speds_gerados': speds_gerados_func,
                    'speds_enviados': speds_enviados_func,
                }
            )

        return {
            'mesReferencia': mes_referencia or 'TODOS',
            'demandas': {
                'total': total_speds,
                'pendentes': pendentes,
                'gerados': gerados,
                'enviados': enviados,
                'percentual_concluido': taxa_conclusao,
                'por_regime_tributario': demandas_por_regime,
            },
            'produtividade_equipe': produtividade_equipe,
        }
