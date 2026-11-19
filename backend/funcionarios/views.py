"""
Views e ViewSets para gerenciamento de Funcionários (US01 - RF01.01 a RF01.05).
Autenticação e autorização baseadas no token do Supabase Auth e no perfil persistido no banco.
"""

import django_filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auditoria.models import LogRastreabilidade

from .models import Funcionario
from .permissions import IsAdminFuncionario
from .serializers import (
    FuncionarioCreateSerializer,
    FuncionarioSerializer,
    LoginSerializer,
)


class FuncionarioFilter(django_filters.FilterSet):
    """Filtros para listagem de usuários por nome e e-mail (RF01.02)."""

    nome = django_filters.CharFilter(field_name='nome', lookup_expr='icontains')
    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains')
    isAdmin = django_filters.BooleanFilter(field_name='isAdmin')
    is_active = django_filters.BooleanFilter(field_name='is_active')

    class Meta:
        model = Funcionario
        fields = ['nome', 'email', 'isAdmin', 'is_active']


class FuncionarioViewSet(viewsets.ModelViewSet):
    """
    CRUD completo de Funcionários exclusivo para Administradores (US01):
    - RF01.01: Inserir Usuário (POST /api/funcionarios/)
    - RF01.02: Listar Usuários com filtros em nome e email (GET /api/funcionarios/?nome=...&email=...)
    - RF01.03: Atualizar Usuário (PUT/PATCH /api/funcionarios/{idFuncionario}/)
    - RF01.04: Inativar Usuário por ID ou informando o e-mail (DELETE /api/funcionarios/{id}/ ou /deletar-por-email/)
    """

    serializer_class = FuncionarioSerializer
    permission_classes = [IsAuthenticated, IsAdminFuncionario]
    filterset_class = FuncionarioFilter
    search_fields = ['nome', 'email']
    ordering_fields = ['idFuncionario', 'nome', 'email']

    def get_queryset(self):
        queryset = Funcionario.objects.all().order_by('nome')
        if 'is_active' not in self.request.query_params:
            return queryset.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        # A senha só é aceita na criação e é encaminhada ao Supabase Auth.
        if self.action == 'create':
            return FuncionarioCreateSerializer
        return FuncionarioSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        dados = {
            'detail': 'Usuário cadastrado com sucesso.',
            **serializer.data,
        }
        return Response(dados, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        novo_func = serializer.save()
        LogRastreabilidade.registrarLog(
            acao=f'Cadastrou o usuário {novo_func.nome} ({novo_func.email})',
            funcionario=self.request.user,
        )

    def perform_update(self, serializer):
        func_atualizado = serializer.save()
        LogRastreabilidade.registrarLog(
            acao=f'Atualizou os dados do usuário {func_atualizado.nome} ({func_atualizado.email})',
            funcionario=self.request.user,
        )

    def perform_destroy(self, instance: Funcionario):
        email_removido = instance.email
        nome_removido = instance.nome
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        LogRastreabilidade.registrarLog(
            acao=f'Inativou o usuário {nome_removido} ({email_removido})',
            funcionario=self.request.user,
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.pk == request.user.pk:
            return Response(
                {'detail': 'Não é permitido excluir o próprio usuário autenticado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email_removido = instance.email
        self.perform_destroy(instance)
        return Response(
            {'detail': f'Usuário "{email_removido}" inativado com sucesso.'},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['delete', 'post'],
        url_path='deletar-por-email',
    )
    def deletar_por_email(self, request):
        """Inativa um usuário informando o e-mail (RF01.04)."""
        email = (
            request.data.get('email')
            or request.query_params.get('email')
            or ''
        ).strip()
        if not email:
            return Response(
                {'detail': 'Informe o e-mail do usuário a ser deletado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            alvo = Funcionario.objects.get(email__iexact=email)
        except Funcionario.DoesNotExist:
            return Response(
                {'detail': f'Usuário com e-mail "{email}" não encontrado.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if alvo.pk == request.user.pk:
            return Response(
                {'detail': 'Não é permitido excluir o próprio usuário autenticado.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        self.perform_destroy(alvo)
        return Response(
            {'detail': f'Usuário "{email}" inativado com sucesso.'},
            status=status.HTTP_200_OK,
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me',
    )
    def me(self, request):
        """
        Retorna os dados do funcionário autenticado a partir do token validado do Supabase.
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class LoginAPIView(APIView):
    """
    Endpoint auxiliar de login via Supabase Auth (RF01.05).
    Nota: O frontend também pode autenticar diretamente pelo SDK @supabase/supabase-js
    e enviar o access_token no cabeçalho Authorization: Bearer <token>.
    """

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        funcionario: Funcionario = serializer.validated_data['funcionario']
        LogRastreabilidade.registrarLog(
            acao=f'Realizou login no sistema via Supabase Auth ({funcionario.perfil})',
            funcionario=funcionario,
        )

        return Response(
            {
                'provedor_auth': 'supabase',
                'access': serializer.validated_data['access'],
                'refresh': serializer.validated_data['refresh'],
                'usuario': FuncionarioSerializer(funcionario).data,
            },
            status=status.HTTP_200_OK,
        )
