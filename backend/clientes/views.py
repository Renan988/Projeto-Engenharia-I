"""
Views e ViewSets para gerenciamento de Clientes (US02 - RF02.01 a RF02.04).
"""

import django_filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auditoria.models import LogRastreabilidade

from .models import Cliente
from .serializers import ClienteSerializer
from .services import consultar_dados_cnpj_api, formatar_cnpj, limpar_cnpj


class ClienteFilter(django_filters.FilterSet):
    """Filtros para listagem de clientes (RF02.02): cnpj, nomeEmpresa, razaoSocial e regimeTributario."""

    cnpj = django_filters.CharFilter(method='filtrar_cnpj')
    nomeEmpresa = django_filters.CharFilter(field_name='nomeEmpresa', lookup_expr='icontains')
    razaoSocial = django_filters.CharFilter(field_name='razaoSocial', lookup_expr='icontains')
    regimeTributario = django_filters.CharFilter(
        field_name='regimeTributario',
        lookup_expr='icontains',
    )

    class Meta:
        model = Cliente
        fields = ['cnpj', 'nomeEmpresa', 'razaoSocial', 'regimeTributario']

    def filtrar_cnpj(self, queryset, name, value):
        digitos = limpar_cnpj(value)
        if len(digitos) == 14:
            return queryset.filter(cnpj=formatar_cnpj(digitos))
        return queryset.filter(cnpj__icontains=value)


class ClienteViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de Clientes acessível por Funcionários e Administradores (US02):
    - RF02.01: Inserir Cliente com consulta automática de CNPJ via API (POST /api/clientes/)
    - RF02.02: Listar Clientes com filtros (GET /api/clientes/?cnpj=...&nomeEmpresa=...&razaoSocial=...&regimeTributario=...)
    - RF02.03: Atualizar Cliente (PUT/PATCH /api/clientes/{idCli}/)
    - RF02.04: Deletar Cliente informando o CNPJ ou ID (DELETE /api/clientes/{idCli}/ ou /deletar-por-cnpj/)
    """

    queryset = Cliente.objects.all().order_by('nomeEmpresa')
    serializer_class = ClienteSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = ClienteFilter
    search_fields = ['cnpj', 'nomeEmpresa', 'razaoSocial', 'regimeTributario']
    ordering_fields = ['idCli', 'nomeEmpresa', 'razaoSocial', 'regimeTributario']

    def perform_create(self, serializer):
        cliente = serializer.save()
        LogRastreabilidade.registrarLog(
            acao=f'Cadastrou o cliente {cliente.nomeEmpresa} (CNPJ: {cliente.cnpj})',
            funcionario=self.request.user,
        )

    def perform_update(self, serializer):
        cliente = serializer.save()
        LogRastreabilidade.registrarLog(
            acao=f'Atualizou o cliente {cliente.nomeEmpresa} (CNPJ: {cliente.cnpj})',
            funcionario=self.request.user,
        )

    def perform_destroy(self, instance: Cliente):
        nome = instance.nomeEmpresa
        cnpj = instance.cnpj
        instance.delete()
        LogRastreabilidade.registrarLog(
            acao=f'Removeu o cliente {nome} (CNPJ: {cnpj})',
            funcionario=self.request.user,
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='consultar-cnpj',
    )
    def consultar_cnpj(self, request):
        """Consulta automaticamente dados da empresa e regime tributário pelo CNPJ via API (RF02.01)."""
        cnpj = (request.query_params.get('cnpj') or '').strip()
        if not cnpj:
            return Response(
                {'detail': 'Informe o parâmetro cnpj na query string.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dados = consultar_dados_cnpj_api(cnpj)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(dados, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['delete', 'post'],
        url_path='deletar-por-cnpj',
    )
    def deletar_por_cnpj(self, request):
        """Deleta um cliente informando o CNPJ (RF02.04)."""
        cnpj_informado = (
            request.data.get('cnpj')
            or request.query_params.get('cnpj')
            or ''
        ).strip()
        if not cnpj_informado:
            return Response(
                {'detail': 'Informe o CNPJ do cliente a ser deletado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        cnpj_formatado = formatar_cnpj(cnpj_informado)
        cliente = (
            Cliente.objects.filter(cnpj=cnpj_formatado).first()
            or Cliente.objects.filter(cnpj=cnpj_informado).first()
        )
        if not cliente:
            return Response(
                {'detail': f'Cliente com CNPJ "{cnpj_informado}" não encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        self.perform_destroy(cliente)
        return Response(
            {'detail': f'Cliente com CNPJ "{cnpj_formatado}" deletado com sucesso.'},
            status=status.HTTP_200_OK,
        )
