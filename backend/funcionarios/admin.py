"""
Configuração do Django Admin para a entidade Funcionario.

O Admin do Django não é o ponto de entrada de autenticação do sistema: identidade
e senha são gerenciadas pelo Supabase Auth (Issue #19). Esta configuração expõe
apenas os dados do perfil funcional.
"""

from django.contrib import admin

from .models import Funcionario


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = (
        'idFuncionario',
        'nome',
        'email',
        'isAdmin',
        'is_active',
        'supabase_user_id',
    )
    list_filter = ('isAdmin', 'is_active')
    search_fields = ('nome', 'email', 'supabase_user_id')
    ordering = ('nome',)
    readonly_fields = ('supabase_user_id',)

    fieldsets = (
        (
            'Identidade (Supabase Auth)',
            {
                'fields': ('supabase_user_id', 'email'),
                'description': (
                    'O vínculo com a identidade e a senha são gerenciados pelo Supabase Auth.'
                ),
            },
        ),
        ('Informações Pessoais', {'fields': ('nome',)}),
        ('Permissões e Nível de Acesso', {'fields': ('isAdmin', 'is_active')}),
    )
