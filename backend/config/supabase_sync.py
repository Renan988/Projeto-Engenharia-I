"""
Sinais (signals) do Django para sincronizar automaticamente as 4 tabelas do sistema
(FUNCIONARIO, CLIENTE, SPED, LOG_RASTREABILIDADE) com o Supabase via HTTPS (porta 443)
quando a rede Wi-Fi bloquear a porta 5432 do PostgreSQL.
"""

import sys

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from auditoria.models import LogRastreabilidade
from clientes.models import Cliente
from config.supabase_client import SupabaseClient
from funcionarios.models import Funcionario
from speds.models import Sped


def _deve_sincronizar_via_https() -> bool:
    """
    Ativa a sincronização via API HTTPS (porta 443) quando não estamos em testes
    automatizados e o banco padrão está em modo fallback por bloqueio da porta 5432.
    """
    if 'test' in sys.argv:
        return False
    engine = settings.DATABASES.get('default', {}).get('ENGINE', '')
    return 'sqlite3' in engine and SupabaseClient.is_configured()


@receiver(post_save, sender=Funcionario)
def sync_funcionario_save(sender, instance: Funcionario, **kwargs):
    if not _deve_sincronizar_via_https():
        return
    SupabaseClient.upsert_table_row(
        table_name='FUNCIONARIO',
        payload={
            'idFuncionario': instance.idFuncionario,
            'nome': instance.nome,
            'email': instance.email,
            'senha': instance.password,
            'isAdmin': instance.isAdmin,
            'is_active': instance.is_active,
            'is_staff': instance.is_staff,
            'is_superuser': instance.is_superuser,
        },
        on_conflict='email',
    )


@receiver(post_delete, sender=Funcionario)
def sync_funcionario_delete(sender, instance: Funcionario, **kwargs):
    if not _deve_sincronizar_via_https():
        return
    SupabaseClient.delete_table_row('FUNCIONARIO', 'idFuncionario', instance.idFuncionario)


@receiver(post_save, sender=Cliente)
def sync_cliente_save(sender, instance: Cliente, **kwargs):
    if not _deve_sincronizar_via_https():
        return
    SupabaseClient.upsert_table_row(
        table_name='CLIENTE',
        payload={
            'idCli': instance.idCli,
            'cnpj': instance.cnpj,
            'nomeEmpresa': instance.nomeEmpresa,
            'razaoSocial': instance.razaoSocial,
            'telefoneWhatsApp': instance.telefoneWhatsApp,
            'emailContador': instance.emailContador,
            'regimeTributario': instance.regimeTributario,
        },
        on_conflict='cnpj',
    )


@receiver(post_delete, sender=Cliente)
def sync_cliente_delete(sender, instance: Cliente, **kwargs):
    if not _deve_sincronizar_via_https():
        return
    SupabaseClient.delete_table_row('CLIENTE', 'idCli', instance.idCli)


@receiver(post_save, sender=Sped)
def sync_sped_save(sender, instance: Sped, **kwargs):
    if not _deve_sincronizar_via_https():
        return
    SupabaseClient.upsert_table_row(
        table_name='SPED',
        payload={
            'idSped': instance.idSped,
            'mesReferencia': instance.mesReferencia,
            'status': instance.status,
            'arquivoRar': instance.arquivoRar.name if instance.arquivoRar else None,
            'idCli': instance.cliente_id,
            'ordemPrioridade': instance.ordemPrioridade,
        },
        on_conflict='idSped',
    )


@receiver(post_delete, sender=Sped)
def sync_sped_delete(sender, instance: Sped, **kwargs):
    if not _deve_sincronizar_via_https():
        return
    SupabaseClient.delete_table_row('SPED', 'idSped', instance.idSped)


@receiver(post_save, sender=LogRastreabilidade)
def sync_log_save(sender, instance: LogRastreabilidade, **kwargs):
    if not _deve_sincronizar_via_https():
        return
    SupabaseClient.upsert_table_row(
        table_name='LOG_RASTREABILIDADE',
        payload={
            'idLog': instance.idLog,
            'acaoRealizada': instance.acaoRealizada,
            'idFuncionario': instance.funcionario_id,
            'idSped': instance.sped_id,
        },
        on_conflict='idLog',
    )
