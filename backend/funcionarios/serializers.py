"""
Serializers para a entidade Funcionario (US01 - RF01.01 a RF01.05).

A partir da Issue #19, o backend persiste apenas o perfil funcional. Identidade,
e-mail de login e senha pertencem ao Supabase Auth:
- Nenhuma resposta da API expõe senha ou hash.
- Na criação, a senha é somente de escrita e encaminhada ao Supabase Auth,
  que devolve o identificador vinculado ao perfil (`supabaseUserId`).
- Atualizações de perfil não alteram credenciais.
"""

from rest_framework import serializers

from config.supabase_client import SupabaseClient

from .models import Funcionario


class FuncionarioSerializer(serializers.ModelSerializer):
    """Serializer do perfil funcional para leitura e atualização."""

    perfil = serializers.CharField(read_only=True)

    class Meta:
        model = Funcionario
        fields = [
            'idFuncionario',
            'supabase_user_id',
            'nome',
            'email',
            'isAdmin',
            'perfil',
            'is_active',
        ]
        read_only_fields = ['idFuncionario', 'supabase_user_id', 'perfil']

    def update(self, instance: Funcionario, validated_data):
        return instance.manterFuncionario(
            nome=validated_data.get('nome'),
            email=validated_data.get('email'),
            isAdmin=validated_data.get('isAdmin'),
            is_active=validated_data.get('is_active'),
        )


class FuncionarioCreateSerializer(FuncionarioSerializer):
    """
    Serializer de criação de perfil (RF01.01).

    A senha é write-only e usada apenas para criar a identidade no Supabase Auth.
    Ela nunca é gravada na tabela FUNCIONARIO nem retornada pela API.
    """

    senha = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6,
        style={'input_type': 'password'},
        help_text=(
            'Senha de acesso criada no Supabase Auth. Não é armazenada pelo backend '
            'e não é retornada pela API.'
        ),
    )

    class Meta(FuncionarioSerializer.Meta):
        fields = FuncionarioSerializer.Meta.fields + ['senha']

    def create(self, validated_data):
        senha = validated_data.pop('senha')

        identidade_supabase = SupabaseClient.create_auth_user(
            email=validated_data['email'],
            password=senha,
            nome=validated_data['nome'],
            is_admin=validated_data.get('isAdmin', False),
        )
        if not identidade_supabase or not identidade_supabase.get('id'):
            raise serializers.ValidationError(
                {
                    'detail': (
                        'Não foi possível criar a identidade no Supabase Auth. '
                        'Verifique se o Supabase está configurado e tente novamente.'
                    )
                }
            )

        validated_data['supabase_user_id'] = identidade_supabase['id']
        return Funcionario.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """
    Serializer de autenticação via Supabase Auth (RF01.05).

    Não emite JWT local pelo Django: delega a autenticação ao Supabase Auth e
    resolve o perfil de funcionário pelo identificador da identidade autenticada.
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

        usuario_supabase = dados_supabase.get('user') or {}
        funcionario = Funcionario.objects.resolver_por_identidade_supabase(
            usuario_supabase.get('id'),
            email=usuario_supabase.get('email') or email,
        )
        if funcionario is None:
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
