"""
Views e ViewSets para o fluxo de trabalho de SPEDs (US03 e US04).
"""

import django_filters
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from auditoria.models import LogRastreabilidade
from clientes.models import Cliente
from clientes.services import formatar_cnpj

from .models import Sped
from .serializers import (
    AtualizarStatusSpedSerializer,
    GerarFilaSpedSerializer,
    SpedSerializer,
    UploadArquivoSpedSerializer,
)


class SpedFilter(django_filters.FilterSet):
    """Filtros para consulta da fila de SPEDs."""

    mesReferencia = django_filters.CharFilter(field_name='mesReferencia', lookup_expr='exact')
    status = django_filters.CharFilter(field_name='status', lookup_expr='iexact')
    idCli = django_filters.NumberFilter(field_name='cliente__idCli')
    cnpj_cliente = django_filters.CharFilter(method='filtrar_cnpj_cliente')
    regimeTributario = django_filters.CharFilter(
        field_name='cliente__regimeTributario',
        lookup_expr='icontains',
    )

    class Meta:
        model = Sped
        fields = ['mesReferencia', 'status', 'idCli', 'cnpj_cliente', 'regimeTributario']

    def filtrar_cnpj_cliente(self, queryset, name, value):
        cnpj_fmt = formatar_cnpj(value)
        return queryset.filter(cliente__cnpj__icontains=cnpj_fmt)


class SpedViewSet(viewsets.ModelViewSet):
    """
    Gerenciamento do fluxo de trabalho de SPEDs (US03 e US04):
    - RF03.01: Gerar Fila de Atendimento priorizada por regime tributário (POST /api/speds/gerar-fila/)
    - RF03.02: Listar SPEDs Pendentes ordenados por prioridade (GET /api/speds/fila-pendentes/)
    - RF03.03: Atualizar Status do SPED no fluxo progressivo (PATCH /api/speds/{idSped}/atualizar-status/)
    - RF03.04: Anexar Arquivo do SPED (POST /api/speds/{idSped}/upload/)
    - US04 (RF04.01 a RF04.04): Enviar SPED ao contador por e-mail e notificar cliente via WhatsApp (POST /api/speds/{idSped}/enviar/)
    """

    queryset = (
        Sped.objects.select_related('cliente')
        .all()
        .order_by('ordemPrioridade', 'cliente__nomeEmpresa', '-idSped')
    )
    serializer_class = SpedSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filterset_class = SpedFilter
    search_fields = [
        'mesReferencia',
        'status',
        'cliente__nomeEmpresa',
        'cliente__razaoSocial',
        'cliente__cnpj',
        'cliente__regimeTributario',
    ]
    ordering_fields = ['ordemPrioridade', 'mesReferencia', 'status', 'criadoEm', 'idSped']

    def perform_create(self, serializer):
        sped: Sped = serializer.save()
        LogRastreabilidade.registrarLog(
            acao=(
                f'Criou registro SPED ({sped.mesReferencia}) para o cliente '
                f'{sped.cliente.nomeEmpresa} com status {sped.status}'
            ),
            funcionario=self.request.user,
            sped=sped,
        )

    @action(
        detail=False,
        methods=['post'],
        url_path='gerar-fila',
        serializer_class=GerarFilaSpedSerializer,
    )
    def gerar_fila(self, request):
        """
        RF03.01 - Gerar Fila de Atendimento: monta automaticamente a fila de prioridade
        para geração dos SPEDs do mês com base no regime tributário dos clientes.
        """
        serializer = GerarFilaSpedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mes_referencia = serializer.validated_data['mesReferencia']

        clientes = Cliente.objects.all()
        criados = 0
        for cliente in clientes:
            _, created = Sped.objects.get_or_create(
                cliente=cliente,
                mesReferencia=mes_referencia,
                defaults={
                    'status': Sped.StatusChoices.PENDENTE,
                    'ordemPrioridade': cliente.ordem_prioridade_regime,
                },
            )
            if created:
                criados += 1

        LogRastreabilidade.registrarLog(
            acao=(
                f'Gerou a fila de atendimento de SPEDs para a competência {mes_referencia} '
                f'({criados} novos registros criados)'
            ),
            funcionario=request.user,
        )

        fila = (
            Sped.objects.select_related('cliente')
            .filter(mesReferencia=mes_referencia)
            .order_by('ordemPrioridade', 'cliente__nomeEmpresa')
        )
        return Response(
            {
                'mesReferencia': mes_referencia,
                'novos_speds_criados': criados,
                'total_na_fila': fila.count(),
                'fila': SpedSerializer(fila, many=True, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['get'],
        url_path='fila-pendentes',
    )
    def fila_pendentes(self, request):
        """
        RF03.02 - Listar SPEDs Pendentes: retorna a fila de atendimento de SPEDs pendentes,
        ordenada automaticamente por prioridade de regime tributário.
        """
        mes_referencia = request.query_params.get('mesReferencia')
        qs = self.get_queryset().filter(status=Sped.StatusChoices.PENDENTE)
        if mes_referencia:
            qs = qs.filter(mesReferencia=mes_referencia)

        serializer = SpedSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=['patch', 'post'],
        url_path='atualizar-status',
        serializer_class=AtualizarStatusSpedSerializer,
    )
    def atualizar_status(self, request, pk=None):
        """
        RF03.03 - Atualizar Status do SPED seguindo o fluxo progressivo
        (PENDENTE > GERADO > ENVIADO) e registrando LogRastreabilidade.
        """
        sped: Sped = self.get_object()
        serializer = AtualizarStatusSpedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            sped.atualizarStatus(
                novoStatus=serializer.validated_data['novoStatus'],
                funcionario=request.user,
            )
        except DjangoValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            SpedSerializer(sped, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post', 'patch'],
        url_path='upload',
        parser_classes=[MultiPartParser, FormParser],
        serializer_class=UploadArquivoSpedSerializer,
    )
    def upload_arquivo(self, request, pk=None):
        """RF03.04 - Anexar Arquivo do SPED: realiza o upload do arquivo SPED (.rar)."""
        sped: Sped = self.get_object()
        serializer = UploadArquivoSpedSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sped.realizarUpload(
            arquivo=serializer.validated_data['arquivoRar'],
            funcionario=request.user,
        )
        return Response(
            SpedSerializer(sped, context={'request': request}).data,
            status=status.HTTP_200_OK,
        )

    @action(
        detail=True,
        methods=['post'],
        url_path='enviar',
    )
    def enviar(self, request, pk=None):
        """
        US04 - Enviar SPED (RF04.01, RF04.02, RF04.03, RF04.04):
        Envia o SPED por e-mail ao contador, notifica o cliente via WhatsApp
        com template personalizado e conclui alterando o status para ENVIADO.
        """
        sped: Sped = self.get_object()
        try:
            resultado = sped.enviarSped(funcionario=request.user)
        except DjangoValidationError as exc:
            return Response(
                {'detail': exc.message if hasattr(exc, 'message') else exc.messages},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                'detail': 'SPED enviado com sucesso ao contador e cliente notificado.',
                'resultado_envio': resultado,
                'sped': SpedSerializer(sped, context={'request': request}).data,
            },
            status=status.HTTP_200_OK,
        )
