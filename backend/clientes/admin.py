"""Configuração do Django Admin para a entidade Cliente."""

from django.contrib import admin

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = (
        'idCli',
        'cnpj',
        'nomeEmpresa',
        'razaoSocial',
        'regimeTributario',
        'emailContador',
        'telefoneWhatsApp',
    )
    list_filter = ('regimeTributario',)
    search_fields = ('cnpj', 'nomeEmpresa', 'razaoSocial', 'emailContador')
    ordering = ('nomeEmpresa',)
