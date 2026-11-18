"""
Serializers para a entidade Funcionario (US01 - RF01.01 a RF01.05).
Integrado exclusivamente ao Supabase Auth (sem emissão local de JWT pelo Django).
"""

from rest_framework import serializers

from config.supabase_client import SupabaseClient

from .models import Funcionario


class FuncionarioSerializer(serializers.ModelSerializer):
    """Serializer completo para leitura, criação e atualização de Funcionários."""

    senha = serializers.CharField(
        write_only=True,
        required=False,
        min_length=6,
        style={'input_type': 'password'},
        help_text='Senha de acesso do funcionário (criada no Supabase Auth).',
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
    Serializer de autenticação via Supabase Auth (RF01.05).
    Não emite JWT local pelo Django: delega a autenticação ao Supabase Auth
    e exige que o funcionário possua perfil associado persistido no backend.
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

        try:
            dados_supabase = SupabaseClient.sign_in_with_password(email=email, password=senha)
        except ValueError as exc:
            raise serializers.ValidationError({'detail': str(exc)})

        try:
            funcionario = Funcionario.objects.get(email__iexact=email)
        except Funcionario.DoesNotExist:
            raise serializers.ValidationError(
                {
                    'detail': (
                        'Usuário autenticado no Supabase não possui perfil de funcionário '
                        'associado no sistema.'
                    )
                }
            )

        if not funcionario.is_active:
            raise serializers.ValidationError({'detail': 'Perfil de funcionário inativo.'})

        attrs['funcionario'] = funcionario
        attrs['access'] = dados_supabase.get('access_token')
        attrs['refresh'] = dados_supabase.get('refresh_token')
        return attrs
