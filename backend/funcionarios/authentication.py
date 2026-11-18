"""
Autenticação exclusiva via Supabase Auth para o Django REST Framework.

Atende aos critérios de aceite da Issue #19:
- Valida tokens emitidos pelo Supabase e rejeita tokens inválidos, expirados ou
  de outro projeto (401).
- Resolve a identidade autenticada (`sub`) para o perfil de Funcionário vinculado
  por `supabaseUserId`, sem armazenar ou comparar senhas no backend.
- Perfis legados ainda sem vínculo são associados uma única vez pelo e-mail do
  token já validado (fluxo de migração documentado em backend/README.md).
- As permissões de Administrador (isAdmin) vêm estritamente do perfil persistido
  no backend, jamais de metadados ou papéis enviados pelo cliente.
- Retorna 401 Unauthorized (via authenticate_header) quando não há autenticação válida.
"""

from typing import Optional, Tuple

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from config.supabase_client import SupabaseClient, SupabaseTokenError

from .models import Funcionario


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    Autenticador principal e único da API baseado em Bearer Token do Supabase Auth.
    """

    keyword = 'Bearer'

    def authenticate(self, request) -> Optional[Tuple[Funcionario, dict]]:
        auth = get_authorization_header(request).split()
        if not auth:
            return None

        if auth[0].lower() != self.keyword.lower().encode():
            raise AuthenticationFailed('Cabeçalho de autorização inválido. Utilize Bearer token.')

        if len(auth) == 1:
            raise AuthenticationFailed('Token de autenticação não informado.')
        if len(auth) > 2:
            raise AuthenticationFailed('Cabeçalho de autorização malformado.')

        try:
            token = auth[1].decode('utf-8')
        except UnicodeError as exc:
            raise AuthenticationFailed('Token contém caracteres inválidos.') from exc

        try:
            dados_token = SupabaseClient.validate_access_token(token)
        except SupabaseTokenError as exc:
            raise AuthenticationFailed(str(exc)) from exc

        identidade_supabase = dados_token.get('id')
        if not identidade_supabase:
            raise AuthenticationFailed(
                'O token do Supabase não contém um identificador de usuário válido.'
            )

        email = (dados_token.get('email') or '').strip().lower()

        # Resolve a identidade autenticada para o perfil funcional persistido no backend.
        funcionario = Funcionario.objects.resolver_por_identidade_supabase(
            identidade_supabase,
            email=email,
        )
        if funcionario is None:
            raise AuthenticationFailed(
                'Usuário autenticado no Supabase não possui perfil de funcionário associado no sistema.'
            )

        if not funcionario.is_active:
            raise AuthenticationFailed('Perfil de funcionário inativo.')

        return (funcionario, dados_token)

    def authenticate_header(self, request) -> str:
        """
        Garante que endpoints protegidos retornem HTTP 401 Unauthorized
        (e não 403 Forbidden) quando não houver autenticação válida.
        """
        return f'{self.keyword} realm="api"'
