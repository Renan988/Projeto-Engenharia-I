"""
Permissões customizadas baseadas nos Perfis de Usuários do Documento de Visão:
- Administrador: Gerencia colaboradores e seus níveis de acesso, e realiza qualquer função.
- Funcionário (Usuário): Acessa fila de atendimento, mantém clientes/SPEDs e visualiza dashboards.
"""

from rest_framework.permissions import BasePermission


class IsAdminFuncionario(BasePermission):
    """Permite acesso apenas a usuários autenticados com perfil de Administrador (isAdmin=True)."""

    message = 'Apenas administradores possuem permissão para executar esta operação.'

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'isAdmin', False)
        )
