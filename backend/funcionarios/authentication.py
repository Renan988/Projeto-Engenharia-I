"""
Classe de autenticação DRF integrada ao Supabase Auth.
Permite que o Front-end (React) autentique diretamente no Supabase Auth e envie
o Bearer Token para o Django, sincronizando automaticamente com a tabela FUNCIONARIO.
Também mantém compatibilidade com o JWT nativo do Django (SimpleJWT).
"""

from typing import Optional, Tuple

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from config.supabase_client import SupabaseClient

from .models import Funcionario


class SupabaseJWTAuthentication(BaseAuthentication):
    """
    Autentica requisições usando o Access Token emitido pelo Supabase Auth.
    Caso o token pertença a um usuário válido no Supabase que ainda não tenha registro
    local na tabela FUNCIONARIO, sincroniza-o automaticamente.
    """

    keyword = 'Bearer'

    def authenticate(self, request) -> Optional[Tuple[Funcionario, dict]]:
        auth = get_authorization_header(request).split()
        if not auth or auth[0].lower() != self.keyword.lower().encode():
            return None

        if len(auth) == 1 or len(auth) > 2:
            return None

        try:
            token = auth[1].decode('utf-8')
        except UnicodeError:
            raise AuthenticationFailed('Token de autenticação contém caracteres inválidos.')

        dados_usuario = SupabaseClient.get_user_from_token(token)
        if not dados_usuario or not dados_usuario.get('email'):
            # Retorna None para permitir que o próximo autenticador (SimpleJWT) tente validar
            return None

        email = dados_usuario['email'].strip().lower()
        user_meta = dados_usuario.get('user_metadata') or {}
        nome = user_meta.get('nome') or user_meta.get('full_name') or email.split('@')[0]
        is_admin = bool(user_meta.get('isAdmin', False))

        funcionario, _ = Funcionario.objects.get_or_create(
            email__iexact=email,
            defaults={
                'email': email,
                'nome': nome,
                'isAdmin': is_admin,
            },
        )

        if not funcionario.is_active:
            raise AuthenticationFailed('Usuário inativo.')

        return (funcionario, dados_usuario)
