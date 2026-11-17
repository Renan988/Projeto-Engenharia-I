"""
Serializers para a entidade Cliente (US02 - RF02.01 a RF02.04).
"""

from rest_framework import serializers

from .models import Cliente
from .services import consultar_dados_cnpj_api, formatar_cnpj, limpar_cnpj


class ClienteSerializer(serializers.ModelSerializer):
    """
    Serializer do Cliente.
    No cadastro (RF02.01), permite informar apenas o CNPJ, telefoneWhatsApp e emailContador,
    preenchendo automaticamente nomeEmpresa, razaoSocial e regimeTributario via API.
    Caso a API esteja indisponível ou o usuário informe manualmente, utiliza os dados enviados.
    """

    nomeEmpresa = serializers.CharField(max_length=150, required=False, allow_blank=True)
    razaoSocial = serializers.CharField(max_length=150, required=False, allow_blank=True)
    regimeTributario = serializers.CharField(max_length=50, required=False, allow_blank=True)
    prioridadeFila = serializers.IntegerField(source='ordem_prioridade_regime', read_only=True)

    class Meta:
        model = Cliente
        fields = [
            'idCli',
            'cnpj',
            'nomeEmpresa',
            'razaoSocial',
            'telefoneWhatsApp',
            'emailContador',
            'regimeTributario',
            'prioridadeFila',
        ]
        read_only_fields = ['idCli', 'prioridadeFila']

    def validate_cnpj(self, value: str) -> str:
        digitos = limpar_cnpj(value)
        if len(digitos) != 14:
            raise serializers.ValidationError('O CNPJ deve conter 14 dígitos numéricos.')
        cnpj_formatado = formatar_cnpj(digitos)

        qs = Cliente.objects.filter(cnpj=cnpj_formatado)
        if self.instance is not None:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Já existe um cliente cadastrado com este CNPJ.')

        return cnpj_formatado

    def validate(self, attrs):
        # Na criação (RF02.01), se faltar nomeEmpresa, razaoSocial ou regimeTributario, consulta a API
        if self.instance is None:
            cnpj = attrs.get('cnpj', '')
            nome_empresa = (attrs.get('nomeEmpresa') or '').strip()
            razao_social = (attrs.get('razaoSocial') or '').strip()
            regime = (attrs.get('regimeTributario') or '').strip()

            if not (nome_empresa and razao_social and regime):
                dados_api = consultar_dados_cnpj_api(cnpj)
                if not nome_empresa and dados_api.get('nomeEmpresa'):
                    nome_empresa = dados_api['nomeEmpresa']
                if not razao_social and dados_api.get('razaoSocial'):
                    razao_social = dados_api['razaoSocial']
                if not regime and dados_api.get('regimeTributario'):
                    regime = dados_api['regimeTributario']

            if not nome_empresa and razao_social:
                nome_empresa = razao_social
            if not razao_social and nome_empresa:
                razao_social = nome_empresa

            erros = {}
            if not nome_empresa:
                erros['nomeEmpresa'] = (
                    'Não foi possível obter o nome da empresa automaticamente via API. '
                    'Informe o campo nomeEmpresa manualmente.'
                )
            if not razao_social:
                erros['razaoSocial'] = (
                    'Não foi possível obter a razão social automaticamente via API. '
                    'Informe o campo razaoSocial manualmente.'
                )
            if not regime:
                erros['regimeTributario'] = (
                    'Não foi possível obter o regime tributário automaticamente via API. '
                    'Informe o campo regimeTributario manualmente.'
                )
            if erros:
                raise serializers.ValidationError(erros)

            attrs['nomeEmpresa'] = nome_empresa
            attrs['razaoSocial'] = razao_social
            attrs['regimeTributario'] = regime

        return attrs

    def update(self, instance: Cliente, validated_data):
        return instance.manterCliente(
            nomeEmpresa=validated_data.get('nomeEmpresa', instance.nomeEmpresa),
            razaoSocial=validated_data.get('razaoSocial', instance.razaoSocial),
            telefoneWhatsApp=validated_data.get('telefoneWhatsApp', instance.telefoneWhatsApp),
            emailContador=validated_data.get('emailContador', instance.emailContador),
            regimeTributario=validated_data.get('regimeTributario', instance.regimeTributario),
        )
