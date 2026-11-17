"""
Serializers para a entidade LogRastreabilidade e indicadores do Dashboard Gerencial (US05 e US06).
"""

from rest_framework import serializers

from .models import LogRastreabilidade


class LogRastreabilidadeSerializer(serializers.ModelSerializer):
    """Serializer de leitura para auditoria de logs de rastreabilidade (US05)."""

    idFuncionario = serializers.IntegerField(source='funcionario.idFuncionario', read_only=True)
    nomeFuncionario = serializers.CharField(source='funcionario.nome', read_only=True)
    emailFuncionario = serializers.EmailField(source='funcionario.email', read_only=True)
    idSped = serializers.IntegerField(source='sped.idSped', read_only=True, allow_null=True)
    mesReferenciaSped = serializers.CharField(
        source='sped.mesReferencia',
        read_only=True,
        allow_null=True,
    )
    nomeClienteSped = serializers.CharField(
        source='sped.cliente.nomeEmpresa',
        read_only=True,
        allow_null=True,
    )

    class Meta:
        model = LogRastreabilidade
        fields = [
            'idLog',
            'dataHora',
            'acaoRealizada',
            'idFuncionario',
            'nomeFuncionario',
            'emailFuncionario',
            'idSped',
            'mesReferenciaSped',
            'nomeClienteSped',
        ]
        read_only_fields = fields
