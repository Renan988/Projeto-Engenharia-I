"""
Cliente de integração com o Supabase (Auth, Validação de Token JWT/JWKS e Data API).
Responsável por validar tokens emitidos pelo Supabase Auth (HS256, ES256/RS256 via JWKS
ou introspecção no endpoint /auth/v1/user), verificando expiração, assinatura e emissor (iss)
do projeto configurado.
"""

from typing import Any, Dict, Optional

import jwt
import requests
from django.conf import settings


class SupabaseTokenError(Exception):
    """Exceção lançada quando um token do Supabase é inválido, expirado ou de outro projeto."""


class SupabaseClient:
    """Serviço utilitário para integração com Supabase Auth e PostgREST Data API."""

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
        metadata = {'nome': nome}

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
                dados = resp.json()
                # O endpoint /signup pode responder {"user": {...}} e o /admin/users
                # responde o próprio usuário; normaliza para sempre devolver a identidade.
                return dados.get('user') or dados
        except (requests.RequestException, ValueError):
            pass
        return None

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
