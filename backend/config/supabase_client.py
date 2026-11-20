"""
Cliente de integração com o Supabase (Auth, Validação de Token JWT/JWKS e Data API).
Responsável por validar tokens emitidos pelo Supabase Auth (HS256, ES256/RS256 via JWKS
ou introspecção no endpoint /auth/v1/user), verificando expiração, assinatura e emissor (iss)
do projeto configurado.
"""

from typing import Any, Dict, Optional
from uuid import UUID

import jwt
import requests
from django.conf import settings


class SupabaseTokenError(Exception):
    """Exceção lançada quando um token do Supabase é inválido, expirado ou de outro projeto."""


class SupabaseAdminError(Exception):
    """Falha da API administrativa com um código estável e sem dados sensíveis."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class SupabaseClient:
    """Serviço utilitário para integração com Supabase Auth e PostgREST Data API."""

    JWT_CLOCK_SKEW_SECONDS = 10
    _jwks_client: Optional[jwt.PyJWKClient] = None
    _jwks_url_cached: Optional[str] = None

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
    def expected_issuer() -> Optional[str]:
        """Retorna o emissor (iss) esperado para tokens deste projeto Supabase."""
        url = (getattr(settings, 'SUPABASE_URL', '') or '').strip().rstrip('/')
        if url and 'seu-projeto.supabase.co' not in url:
            return f'{url}/auth/v1'
        return None

    @staticmethod
    def _headers(
        use_service_role: bool = False,
        bearer_token: str = None,
        prefer: str = None,
    ) -> Dict[str, str]:
        """
        Monta cabeçalhos HTTP para chamadas à API do Supabase.
        A chave service_role permanece estritamente no backend.
        """
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
    def _get_jwks_client(cls) -> Optional[jwt.PyJWKClient]:
        if not cls.is_configured():
            return None
        base_url = settings.SUPABASE_URL.rstrip('/')
        jwks_url = f'{base_url}/auth/v1/.well-known/jwks.json'
        if cls._jwks_client is None or cls._jwks_url_cached != jwks_url:
            cls._jwks_client = jwt.PyJWKClient(jwks_url)
            cls._jwks_url_cached = jwks_url
        return cls._jwks_client

    @classmethod
    def validate_access_token(cls, token: str) -> Dict[str, Any]:
        """
        Valida o access_token emitido pelo Supabase Auth:
        - Rejeita tokens malformados, com assinatura inválida ou expirados (exp).
        - Rejeita tokens destinados a outro projeto Supabase (verifica claim `iss`).
        - Contempla assinatura simétrica (HS256 via SUPABASE_JWT_SECRET) e assimétrica
          (ES256/RS256 via JWKS do projeto) ou validação direta no endpoint /auth/v1/user.
        """
        if not token or not isinstance(token, str):
            raise SupabaseTokenError('Token de autenticação ausente ou inválido.')

        # 1. Decodifica cabeçalho sem verificar assinatura para inspecionar formato e algoritmo
        try:
            unverified_header = jwt.get_unverified_header(token)
            unverified_claims = jwt.decode(
                token,
                options={'verify_signature': False, 'verify_exp': False},
            )
        except jwt.PyJWTError as exc:
            raise SupabaseTokenError('Token JWT malformado ou inválido.') from exc

        # 2. Verifica se o token pertence a este projeto Supabase (claim `iss`)
        expected_iss = cls.expected_issuer()
        token_iss = unverified_claims.get('iss')
        if expected_iss and token_iss and token_iss.rstrip('/') != expected_iss:
            raise SupabaseTokenError(
                'Token emitido para outro projeto Supabase (issuer inválido).'
            )

        alg = unverified_header.get('alg', 'HS256')
        jwt_secret = (getattr(settings, 'SUPABASE_JWT_SECRET', '') or '').strip()

        # 3. Se SUPABASE_JWT_SECRET estiver configurado e algoritmo for HS256, valida assinatura localmente
        if jwt_secret and jwt_secret != 'seu-jwt-secret-do-supabase' and alg == 'HS256':
            try:
                decode_kwargs: Dict[str, Any] = {
                    'algorithms': ['HS256'],
                    'options': {'verify_aud': False, 'verify_exp': True},
                    'leeway': cls.JWT_CLOCK_SKEW_SECONDS,
                }
                if expected_iss and token_iss:
                    decode_kwargs['issuer'] = expected_iss

                payload = jwt.decode(token, jwt_secret, **decode_kwargs)
                return {
                    'id': payload.get('sub'),
                    'email': payload.get('email'),
                    'iss': payload.get('iss'),
                    'role': payload.get('role'),
                }
            except jwt.ExpiredSignatureError as exc:
                raise SupabaseTokenError('Token de autenticação expirado.') from exc
            except jwt.InvalidIssuerError as exc:
                raise SupabaseTokenError(
                    'Token destinado a outro projeto Supabase.'
                ) from exc
            except jwt.PyJWTError as exc:
                raise SupabaseTokenError('Assinatura do token inválida.') from exc

        # 4. Se algoritmo for assimétrico (ES256/RS256), tenta validar via JWKS do projeto Supabase
        if alg in ('ES256', 'RS256') and cls.is_configured():
            try:
                jwks_client = cls._get_jwks_client()
                if jwks_client is not None:
                    signing_key = jwks_client.get_signing_key_from_jwt(token)
                    payload = jwt.decode(
                        token,
                        signing_key.key,
                        algorithms=[alg],
                        issuer=expected_iss if (expected_iss and token_iss) else None,
                        options={'verify_aud': False, 'verify_exp': True},
                        leeway=cls.JWT_CLOCK_SKEW_SECONDS,
                    )
                    return {
                        'id': payload.get('sub'),
                        'email': payload.get('email'),
                        'iss': payload.get('iss'),
                        'role': payload.get('role'),
                    }
            except jwt.ExpiredSignatureError as exc:
                raise SupabaseTokenError('Token de autenticação expirado.') from exc
            except jwt.PyJWTError as exc:
                raise SupabaseTokenError('Token inválido segundo JWKS do Supabase.') from exc
            except Exception:
                # Se falhar conexão ao endpoint JWKS, prossegue para validação em /auth/v1/user
                pass

        # 5. Verifica expiração (exp) antes de consultar o endpoint /auth/v1/user do Supabase
        try:
            jwt.decode(
                token,
                options={'verify_signature': False, 'verify_exp': True},
            )
        except jwt.ExpiredSignatureError as exc:
            raise SupabaseTokenError('Token de autenticação expirado.') from exc
        except jwt.PyJWTError as exc:
            raise SupabaseTokenError('Token inválido.') from exc

        # 6. Valida junto ao servidor Supabase Auth (/auth/v1/user) se configurado
        if cls.is_configured():
            base_url = settings.SUPABASE_URL.rstrip('/')
            url = f'{base_url}/auth/v1/user'
            try:
                resp = requests.get(
                    url,
                    headers=cls._headers(bearer_token=token),
                    timeout=4,
                )
                if resp.status_code == 200:
                    dados = resp.json()
                    return {
                        'id': dados.get('id'),
                        'email': dados.get('email'),
                        'iss': expected_iss,
                        'role': dados.get('role'),
                    }
                raise SupabaseTokenError('Token rejeitado pelo Supabase Auth.')
            except requests.RequestException as exc:
                raise SupabaseTokenError(
                    'Não foi possível validar o token junto ao Supabase Auth.'
                ) from exc

        raise SupabaseTokenError('Token inválido ou assinatura não pôde ser verificada.')

    @classmethod
    def sign_in_with_password(cls, email: str, password: str) -> Dict[str, Any]:
        """
        Autentica usuário via Supabase Auth (/auth/v1/token?grant_type=password).
        """
        if not cls.is_configured():
            raise ValueError('Supabase Auth não está configurado.')

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
                or 'Credenciais inválidas no Supabase Auth.'
            )
            raise ValueError(detalhe)
        return resp.json()

    # A exclusão lógica preserva a identidade para uma eventual reativação.
    AUTH_BAN_DURATION = '876000h'

    @classmethod
    def _auth_admin_request(cls, method, user_id=None, payload=None):
        service_key = (getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', '') or '').strip()
        issuer = cls.expected_issuer()
        if not issuer or not service_key or service_key == 'sua-service-role-key-do-supabase':
            raise SupabaseAdminError('not_configured')

        url = f'{issuer}/admin/users'
        if user_id is not None:
            url = f'{url}/{user_id}'
        try:
            response = requests.request(
                method, url, json=payload, headers=cls._headers(use_service_role=True),
                timeout=5, allow_redirects=False,
            )
        except requests.RequestException as exc:
            raise SupabaseAdminError('unavailable') from exc

        if 200 <= response.status_code < 300:
            return response

        try:
            error = response.json()
        except ValueError:
            error = {}
        if isinstance(error, dict):
            code = error.get('error_code') or error.get('code')
            if code in ('email_exists', 'user_already_exists', 'weak_password', 'user_not_found'):
                raise SupabaseAdminError(code)
        raise SupabaseAdminError('unavailable')

    @classmethod
    def create_auth_user(cls, email: str, password: str, nome: str, is_active: bool = True) -> UUID:
        payload = {
            'email': email,
            'password': password,
            'email_confirm': True,
            'user_metadata': {'nome': nome},
        }
        if not is_active:
            payload['ban_duration'] = cls.AUTH_BAN_DURATION
        response = cls._auth_admin_request('POST', payload=payload)
        try:
            return UUID(response.json()['id'])
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise SupabaseAdminError('unavailable') from exc

    @classmethod
    def set_auth_user_active(cls, user_id: UUID, is_active: bool):
        cls._auth_admin_request(
            'PUT', user_id=user_id,
            payload={'ban_duration': 'none' if is_active else cls.AUTH_BAN_DURATION},
        )

    @classmethod
    def delete_auth_user(cls, user_id: UUID):
        """Remove uma identidade cujo cadastro no Django não pôde ser concluído."""
        try:
            cls._auth_admin_request('DELETE', user_id=user_id)
        except SupabaseAdminError as exc:
            if exc.code != 'user_not_found':
                raise

    @classmethod
    def upsert_table_row(
        cls,
        table_name: str,
        payload: Dict[str, Any],
        on_conflict: str,
    ) -> bool:
        """Sincroniza um registro na tabela do Supabase via HTTPS REST API (porta 443)."""
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
