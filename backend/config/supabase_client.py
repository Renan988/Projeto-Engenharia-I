"""
Cliente de integração com o Supabase (Auth, PostgREST Data API e Storage).
Conecta o back-end Django diretamente aos serviços de Autenticação (GoTrue)
e Banco de Dados via HTTPS (porta 443) do Supabase.
"""

from typing import Any, Dict, Optional

import jwt
import requests
from django.conf import settings


class SupabaseClient:
    """Serviço utilitário para integração com Supabase Auth e PostgREST Data API."""

    @staticmethod
    def is_configured() -> bool:
        """Verifica se as credenciais do projeto Supabase foram definidas no .env."""
        url = (getattr(settings, 'SUPABASE_URL', '') or '').strip()
        key = (getattr(settings, 'SUPABASE_ANON_KEY', '') or '').strip()
        return bool(
            url
            and key
            and 'seu-projeto.supabase.co' not in url
            and key != 'sua-anon-public-key-do-supabase'
        )

    @staticmethod
    def _headers(
        use_service_role: bool = False,
        bearer_token: str = None,
        prefer: str = None,
    ) -> Dict[str, str]:
        anon_key = (getattr(settings, 'SUPABASE_ANON_KEY', '') or '').strip()
        service_key = (getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '') or '').strip()
        api_key = service_key if (use_service_role and service_key) else anon_key
        headers = {
            'apikey': api_key,
            'Content-Type': 'application/json',
        }
        token = bearer_token or (api_key if api_key.startswith('eyJ') else None)
        if token:
            headers['Authorization'] = f'Bearer {token}'
        if prefer:
            headers['Prefer'] = prefer
        return headers

    @classmethod
    def sign_in_with_password(cls, email: str, password: str) -> Dict[str, Any]:
        """
        Realiza login diretamente no Supabase Auth (/auth/v1/token?grant_type=password).
        Retorna access_token, refresh_token e dados do usuário no Supabase.
        """
        base_url = settings.SUPABASE_URL.rstrip('/')
        url = f'{base_url}/auth/v1/token?grant_type=password'
        resp = requests.post(
            url,
            json={'email': email, 'password': password},
            headers=cls._headers(),
            timeout=5,
        )
        if resp.status_code != 200:
            dados_erro = resp.json() if resp.content else {}
            detalhe = (
                dados_erro.get('error_description')
                or dados_erro.get('msg')
                or 'Credenciais inválidas no Supabase.'
            )
            raise ValueError(detalhe)
        return resp.json()

    @classmethod
    def get_user_from_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """
        Valida o token JWT gerado pelo Supabase Auth.
        Se SUPABASE_JWT_SECRET estiver configurado, valida localmente em < 1ms;
        caso contrário, consulta o endpoint /auth/v1/user do Supabase via HTTPS (porta 443).
        """
        jwt_secret = (getattr(settings, 'SUPABASE_JWT_SECRET', '') or '').strip()
        if jwt_secret and jwt_secret != 'seu-jwt-secret-do-supabase':
            try:
                payload = jwt.decode(
                    token,
                    jwt_secret,
                    algorithms=['HS256'],
                    options={'verify_aud': False},
                )
                return {
                    'id': payload.get('sub'),
                    'email': payload.get('email'),
                    'user_metadata': payload.get('user_metadata') or {},
                    'app_metadata': payload.get('app_metadata') or {},
                }
            except jwt.PyJWTError:
                pass

        if not cls.is_configured():
            return None

        base_url = settings.SUPABASE_URL.rstrip('/')
        url = f'{base_url}/auth/v1/user'
        try:
            resp = requests.get(
                url,
                headers=cls._headers(bearer_token=token),
                timeout=4,
            )
            if resp.status_code == 200:
                return resp.json()
        except requests.RequestException:
            pass
        return None

    @classmethod
    def create_auth_user(
        cls,
        email: str,
        password: str,
        nome: str,
        is_admin: bool = False,
    ) -> Optional[Dict[str, Any]]:
        """
        Cria um usuário no Supabase Auth quando um Administrador cadastra um Funcionário (RF01.01).
        """
        if not cls.is_configured():
            return None

        base_url = settings.SUPABASE_URL.rstrip('/')
        service_key = (getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '') or '').strip()
        metadata = {'nome': nome, 'isAdmin': is_admin}

        try:
            if service_key and service_key != 'sua-service-role-key-do-supabase':
                url = f'{base_url}/auth/v1/admin/users'
                resp = requests.post(
                    url,
                    json={
                        'email': email,
                        'password': password,
                        'email_confirm': True,
                        'user_metadata': metadata,
                    },
                    headers=cls._headers(use_service_role=True),
                    timeout=5,
                )
            else:
                url = f'{base_url}/auth/v1/signup'
                resp = requests.post(
                    url,
                    json={
                        'email': email,
                        'password': password,
                        'data': metadata,
                    },
                    headers=cls._headers(),
                    timeout=5,
                )

            if resp.status_code in (200, 201):
                return resp.json()
        except requests.RequestException:
            pass
        return None

    @classmethod
    def upsert_table_row(
        cls,
        table_name: str,
        payload: Dict[str, Any],
        on_conflict: str,
    ) -> bool:
        """
        Sincroniza um registro diretamente na tabela do Supabase via HTTPS REST API (porta 443)
        quando a porta 5432 estiver bloqueada pelo firewall da rede Wi-Fi.
        """
        if not cls.is_configured():
            return False

        base_url = settings.SUPABASE_URL.rstrip('/')
        url = f'{base_url}/rest/v1/{table_name}?on_conflict={on_conflict}'
        try:
            resp = requests.post(
                url,
                json=payload,
                headers=cls._headers(
                    use_service_role=True,
                    prefer='resolution=merge-duplicates,return=minimal',
                ),
                timeout=4,
            )
            return resp.status_code in (200, 201, 204)
        except requests.RequestException:
            return False

    @classmethod
    def delete_table_row(cls, table_name: str, pk_column: str, pk_value: Any) -> bool:
        """Remove um registro na tabela do Supabase via HTTPS REST API (porta 443)."""
        if not cls.is_configured():
            return False

        base_url = settings.SUPABASE_URL.rstrip('/')
        url = f'{base_url}/rest/v1/{table_name}?{pk_column}=eq.{pk_value}'
        try:
            resp = requests.delete(
                url,
                headers=cls._headers(use_service_role=True),
                timeout=4,
            )
            return resp.status_code in (200, 204)
        except requests.RequestException:
            return False
