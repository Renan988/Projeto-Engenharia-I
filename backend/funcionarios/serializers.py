"""
Serializers para a entidade Funcionario e Autenticação (US01 - RF01.01 a RF01.05).
Integrado ao Supabase Auth quando configurado no .env.
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from config.supabase_client import SupabaseClient

from .models import Funcionario


class FuncionarioSerializer(serializers.ModelSerializer):
    """Serializer completo para leitura, criação e atualização de Funcionários."""

    senha = serializers.CharField(
        write_only=True,
        required=False,
        min_length=6,
        style={'input_type': 'password'},
        help_text='Senha de acesso do funcionário (sincronizada com o Supabase Auth e criptografada).',
    )
    perfil = serializers.CharField(read_only=True)

    class Meta:
        model = Funcionario
        fields = [
            'idFuncionario',
            'nome',
            'email',
            'senha',
            'isAdmin',
            'perfil',
            'is_active',
        ]
        read_only_fields = ['idFuncionario', 'perfil']

    def validate(self, attrs):
        # Na criação (RF01.01), a senha é obrigatória
        if self.instance is None and not attrs.get('senha'):
            raise serializers.ValidationError(
                {'senha': 'A senha é obrigatória para cadastrar um novo usuário.'}
            )
        return attrs

    def create(self, validated_data):
        senha = validated_data.pop('senha')
        # Se o Supabase estiver configurado, cria também a conta no Supabase Auth
        if SupabaseClient.is_configured():
            SupabaseClient.create_auth_user(
                email=validated_data['email'],
                password=senha,
                nome=validated_data['nome'],
                is_admin=validated_data.get('isAdmin', False),
            )
        return Funcionario.objects.create_user(senha=senha, **validated_data)

    def update(self, instance: Funcionario, validated_data):
        senha = validated_data.pop('senha', None)
        return instance.manterFuncionario(
            nome=validated_data.get('nome', instance.nome),
            email=validated_data.get('email', instance.email),
            senha=senha,
            isAdmin=validated_data.get('isAdmin', instance.isAdmin),
        )


class LoginSerializer(serializers.Serializer):
    """
    Serializer para o endpoint de Login (RF01.05 - Login do Usuário).
    Quando o Supabase está configurado, autentica diretamente via Supabase Auth
    e sincroniza o registro na tabela FUNCIONARIO do banco PostgreSQL do Supabase.
    """

    email = serializers.EmailField(required=True)
    senha = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'},
    )

    def validate(self, attrs):
        email = attrs.get('email', '').strip().lower()
        senha = attrs.get('senha', '')

        # 1. Tenta autenticar via Supabase Auth se estiver configurado no .env
        if SupabaseClient.is_configured():
            try:
                dados_supabase = SupabaseClient.sign_in_with_password(email=email, password=senha)
                user_info = dados_supabase.get('user') or {}
                user_meta = user_info.get('user_metadata') or {}
                nome = user_meta.get('nome') or user_meta.get('full_name') or email.split('@')[0]
                is_admin = bool(user_meta.get('isAdmin', False))

                funcionario, created = Funcionario.objects.get_or_create(
                    email__iexact=email,
                    defaults={
                        'email': email,
                        'nome': nome,
                        'isAdmin': is_admin,
                    },
                )
                if created:
                    funcionario.set_password(senha)
                    funcionario.save()

                if not funcionario.is_active:
                    raise serializers.ValidationError({'detail': 'Usuário inativo.'})

                attrs['funcionario'] = funcionario
                attrs['access'] = dados_supabase.get('access_token')
                attrs['refresh'] = dados_supabase.get('refresh_token')
                attrs['provedor_auth'] = 'supabase'
                return attrs
            except ValueError:
                # Caso o usuário tenha sido criado localmente no banco, permite fallback abaixo
                pass

        # 2. Autenticação na tabela FUNCIONARIO + emissão de JWT
        try:
            funcionario = Funcionario.objects.get(email__iexact=email)
        except Funcionario.DoesNotExist:
            raise serializers.ValidationError(
                {'detail': 'Credenciais inválidas. Verifique seu e-mail e senha.'}
            )

        if not funcionario.solicitarAutorizacaoAcesso(senha):
            raise serializers.ValidationError(
                {'detail': 'Credenciais inválidas ou usuário inativo.'}
            )

        refresh = RefreshToken.for_user(funcionario)
        attrs['funcionario'] = funcionario
        attrs['access'] = str(refresh.access_token)
        attrs['refresh'] = str(refresh)
        attrs['provedor_auth'] = 'jwt_local'
        return attrs
