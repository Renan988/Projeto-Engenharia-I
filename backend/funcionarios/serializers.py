"""
Serializers para a entidade Funcionario e Autenticação (US01 - RF01.01 a RF01.05).
"""

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Funcionario


class FuncionarioSerializer(serializers.ModelSerializer):
    """Serializer completo para leitura, criação e atualização de Funcionários."""

    senha = serializers.CharField(
        write_only=True,
        required=False,
        min_length=4,
        style={'input_type': 'password'},
        help_text='Senha de acesso do funcionário (armazenada de forma criptografada).',
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
    """Serializer para o endpoint de Login (RF01.05 - Login do Usuário)."""

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
        return attrs
