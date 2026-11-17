"""Configuração do Django Admin para a entidade Sped."""

from django.contrib import admin

from .models import Sped


@admin.register(Sped)
class SpedAdmin(admin.ModelAdmin):
    list_display = (
        'idSped',
        'cliente',
        'mesReferencia',
        'status',
        'ordemPrioridade',
        'arquivoRar',
        'atualizadoEm',
    )
    list_filter = ('status', 'mesReferencia', 'cliente__regimeTributario')
    search_fields = ('cliente__nomeEmpresa', 'cliente__cnpj', 'mesReferencia')
    ordering = ('ordemPrioridade', '-idSped')
