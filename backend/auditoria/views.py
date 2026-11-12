"""
Views para consulta de Logs de Rastreabilidade (US05) e Dashboard Gerencial (US06).
"""

import django_filters
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LogRastreabilidade
from .serializers import LogRastreabilidadeSerializer


class LogRastreabilidadeFilter(django_filters.FilterSet):
    """Filtros para consulta do histórico de auditoria (US05)."""

    idFuncionario = django_filters.NumberFilter(field_name='funcionario__idFuncionario')
    idSped = django_filters.NumberFilter(field_name='sped__idSped')
    acaoRealizada = django_filters.CharFilter(field_name='acaoRealizada', lookup_expr='icontains')
    apenas_sped = django_filters.BooleanFilter(method='filtrar_apenas_sped')

    class Meta:
        model = LogRastreabilidade
        fields = ['idFuncionario', 'idSped', 'acaoRealizada']

    def filtrar_apenas_sped(self, queryset, name, value):
        if value is True:
            return queryset.filter(sped__isnull=False)
        if value is False:
            return queryset.filter(sped__isnull=True)
        return queryset


class LogRastreabilidadeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Listagem e detalhamento de Logs de Rastreabilidade (US05 - RF05.01 e RF05.02).
    Somente leitura para preservar a integridade da trilha de auditoria.
    """

    queryset = (
        LogRastreabilidade.objects.select_related('funcionario', 'sped', 'sped__cliente')
        .all()
        .order_by('-dataHora', '-idLog')
    )
    serializer_class = LogRastreabilidadeSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = LogRastreabilidadeFilter
    search_fields = ['acaoRealizada', 'funcionario__nome', 'funcionario__email']
    ordering_fields = ['dataHora', 'idLog']


class DashboardGerencialAPIView(APIView):
    """
    US06 - Dashboard Gerencial:
    - RF06.01: Visualizar Produtividade mensal da equipe.
    - RF06.02: Visualizar Demandas fiscais do mês na fila de atendimento.
    Aceita parâmetro opcional `?mesReferencia=MM/AAAA`.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        mes_referencia = (request.query_params.get('mesReferencia') or '').strip() or None
        dados_dashboard = LogRastreabilidade.gerarDashboard(mes_referencia=mes_referencia)

        # Inclui os últimos 10 logs de rastreabilidade para acompanhamento em tempo real
        ultimos_logs = LogRastreabilidade.objects.select_related(
            'funcionario', 'sped', 'sped__cliente'
        )[:10]
        dados_dashboard['ultimas_atividades'] = LogRastreabilidadeSerializer(
            ultimos_logs, many=True
        ).data

        return Response(dados_dashboard, status=status.HTTP_200_OK)
