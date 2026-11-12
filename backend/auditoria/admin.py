"""Configuração do Django Admin para LogRastreabilidade."""

from django.contrib import admin

from .models import LogRastreabilidade


@admin.register(LogRastreabilidade)
class LogRastreabilidadeAdmin(admin.ModelAdmin):
    list_display = ('idLog', 'dataHora', 'funcionario', 'acaoRealizada', 'sped')
    list_filter = ('dataHora', 'funcionario')
    search_fields = ('acaoRealizada', 'funcionario__nome', 'funcionario__email')
    readonly_fields = ('idLog', 'dataHora', 'acaoRealizada', 'funcionario', 'sped')
    ordering = ('-dataHora',)
