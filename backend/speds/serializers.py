"""
Serializers para a entidade Sped e operações de Fila, Upload e Envio (US03 e US04).
"""

from rest_framework import serializers

from clientes.models import Cliente
from clientes.serializers import ClienteSerializer
from clientes.services import formatar_cnpj

from .models import Sped


class SpedSerializer(serializers.ModelSerializer):
    """
    Serializer principal da entidade Sped.
    Aceita vínculo com o cliente tanto por `idCli` quanto por `cnpj_cliente`.
    """

    idCli = serializers.PrimaryKeyRelatedField(
        source='cliente',
        queryset=Cliente.objects.all(),
        required=False,
    )
    cnpj_cliente = serializers.CharField(
        required=False,
        help_text='CNPJ do cliente titular do SPED (alternativa ao idCli).',
    )
    cliente_detalhes = ClienteSerializer(source='cliente', read_only=True)

    class Meta:
        model = Sped
        fields = [
            'idSped',
            'mesReferencia',
            'status',
            'arquivoRar',
            'idCli',
            'cnpj_cliente',
            'ordemPrioridade',
            'cliente_detalhes',
            'criadoEm',
            'atualizadoEm',
        ]
        read_only_fields = ['idSped', 'ordemPrioridade', 'criadoEm', 'atualizadoEm']

    def validate(self, attrs):
        cliente = attrs.get('cliente')
        cnpj_informado = attrs.pop('cnpj_cliente', None)

        if not cliente and cnpj_informado:
            cnpj_fmt = formatar_cnpj(cnpj_informado)
            cliente = (
                Cliente.objects.filter(cnpj=cnpj_fmt).first()
                or Cliente.objects.filter(cnpj=cnpj_informado).first()
            )
            if not cliente:
                raise serializers.ValidationError(
                    {'cnpj_cliente': f'Cliente com CNPJ "{cnpj_informado}" não encontrado.'}
                )
            attrs['cliente'] = cliente

        if self.instance is None and not attrs.get('cliente'):
            raise serializers.ValidationError(
                {'idCli': 'Informe o idCli ou o cnpj_cliente do titular do SPED.'}
            )

        # Verifica duplicidade de (cliente, mesReferencia)
        cliente_alvo = attrs.get('cliente') or getattr(self.instance, 'cliente', None)
        mes_alvo = attrs.get('mesReferencia') or getattr(self.instance, 'mesReferencia', None)
        if cliente_alvo and mes_alvo:
            qs = Sped.objects.filter(cliente=cliente_alvo, mesReferencia=mes_alvo)
            if self.instance is not None:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {
                        'mesReferencia': (
                            f'Já existe um SPED cadastrado para o cliente "{cliente_alvo.nomeEmpresa}" '
                            f'na competência {mes_alvo}.'
                        )
                    }
                )

        return attrs

    def to_representation(self, instance: Sped):
        data = super().to_representation(instance)
        data['cnpj_cliente'] = instance.cnpj_cliente
        return data


class AtualizarStatusSpedSerializer(serializers.Serializer):
    """Serializer para atualização progressiva de status do SPED (RF03.03)."""

    novoStatus = serializers.ChoiceField(
        choices=Sped.StatusChoices.choices,
        help_text='Novo status seguindo o fluxo progressivo: PENDENTE > GERADO > ENVIADO.',
    )


class UploadArquivoSpedSerializer(serializers.Serializer):
    """Serializer para upload do arquivo RAR/SPED gerado (RF03.04)."""

    arquivoRar = serializers.FileField(
        required=True,
        help_text='Arquivo SPED (.rar, .zip ou .txt) a ser anexado.',
    )


class GerarFilaSpedSerializer(serializers.Serializer):
    """Serializer para geração automática da fila mensal de SPEDs (RF03.01)."""

    mesReferencia = serializers.RegexField(
        regex=r'^(0[1-9]|1[0-2])/\d{4}$',
        required=True,
        help_text='Mês e ano de referência no formato MM/AAAA (ex.: 11/2026).',
    )
