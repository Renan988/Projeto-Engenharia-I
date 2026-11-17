"""Configuração do Django Admin para a entidade Funcionario."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Funcionario


@admin.register(Funcionario)
class FuncionarioAdmin(BaseUserAdmin):
    list_display = ('idFuncionario', 'nome', 'email', 'isAdmin', 'is_active')
    list_filter = ('isAdmin', 'is_active')
    search_fields = ('nome', 'email')
    ordering = ('nome',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('nome',)}),
        ('Permissões e Nível de Acesso', {'fields': ('isAdmin', 'is_active')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('nome', 'email', 'password1', 'password2', 'isAdmin', 'is_active'),
            },
        ),
    )
