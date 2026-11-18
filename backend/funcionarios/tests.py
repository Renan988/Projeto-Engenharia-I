"""
Testes automatizados para US01 (Manter Usuário) e Integração de Autenticação Supabase (Issue #13).
Cobre todos os critérios de aceite:
- Token válido do Supabase
- Token inválido / assinatura incorreta / malformado
- Token expirado
- Token destinado a outro projeto Supabase (issuer inválido)
- Usuário autenticado no Supabase sem perfil associado na tabela FUNCIONARIO
- Endpoints protegidos retornando 401 sem autenticação válida
- Permissões de Administrador verificadas no perfil persistido no backend (e não em claims/body do cliente)
"""

import time

import jwt
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Funcionario

SEGREDO_SUPABASE_TESTE = 'segredo-jwt-supabase-teste-1234567890-seguro'
URL_PROJETO_SUPABASE = 'https://ssdoivoyzxddfhqbguhy.supabase.co'
ISSUER_PROJETO = f'{URL_PROJETO_SUPABASE}/auth/v1'


def gerar_token_supabase(
    email: str,
    segredo: str = SEGREDO_SUPABASE_TESTE,
    exp_offset: int = 3600,
    iss: str = ISSUER_PROJETO,
    extra_claims: dict = None,
) -> str:
    payload = {
        'sub': 'uuid-supabase-user',
        'email': email,
        'aud': 'authenticated',
        'role': 'authenticated',
        'iss': iss,
        'iat': int(time.time()),
        'exp': int(time.time()) + exp_offset,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, segredo, algorithm='HS256')


@override_settings(
    SUPABASE_URL=URL_PROJETO_SUPABASE,
    SUPABASE_ANON_KEY='sb_publishable_teste',
    SUPABASE_JWT_SECRET=SEGREDO_SUPABASE_TESTE,
)
class SupabaseAuthAndFuncionarioTests(APITestCase):
    def setUp(self):
        self.admin = Funcionario.objects.create_superuser(
            email='admin@intech.com.br',
            nome='Administrador Intech',
            password='senha123',
        )
        self.funcionario = Funcionario.objects.create_user(
            email='colab@intech.com.br',
            nome='Colaborador Intech',
            senha='senha123',
            isAdmin=False,
        )

    def test_endpoint_protegido_sem_autenticacao_retorna_401(self):
        """Endpoints protegidos devem retornar 401 Unauthorized sem autenticação válida."""
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_supabase_valido_identifica_funcionario(self):
        """Token válido do Supabase autentica e identifica o funcionário associado no banco."""
        token = gerar_token_supabase(email='colab@intech.com.br')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['email'], 'colab@intech.com.br')
        self.assertEqual(resp.data['idFuncionario'], self.funcionario.idFuncionario)
        self.assertFalse(resp.data['isAdmin'])

    def test_token_supabase_invalido_ou_assinatura_incorreta_retorna_401(self):
        """Backend rejeita tokens com assinatura inválida ou malformados com 401."""
        token_assinatura_errada = gerar_token_supabase(
            email='colab@intech.com.br',
            segredo='outro-segredo-invalido-qualquer-000000',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_assinatura_errada}')
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Token malformado
        self.client.credentials(HTTP_AUTHORIZATION='Bearer token.malformado.invalido')
        resp_malformado = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp_malformado.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_supabase_expirado_retorna_401(self):
        """Backend rejeita tokens expirados com 401 Unauthorized."""
        token_expirado = gerar_token_supabase(
            email='colab@intech.com.br',
            exp_offset=-3600,  # Expirado há 1 hora
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_expirado}')
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_destinado_a_outro_projeto_retorna_401(self):
        """Backend rejeita tokens emitidos para outro projeto Supabase (issuer divergente)."""
        token_outro_projeto = gerar_token_supabase(
            email='colab@intech.com.br',
            iss='https://outro-projeto-diferente.supabase.co/auth/v1',
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_outro_projeto}')
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sem_perfil_associado_retorna_401(self):
        """Token válido do Supabase para usuário sem perfil na tabela FUNCIONARIO deve ser rejeitado (401)."""
        token_sem_perfil = gerar_token_supabase(email='nao.cadastrado@intech.com.br')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_sem_perfil}')
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_permissao_admin_verificada_no_banco_e_nao_no_token_do_cliente(self):
        """
        Mesmo que o cliente envie user_metadata={'isAdmin': True} no token,
        o backend verifica a permissão no perfil persistido no banco (colab.isAdmin=False -> 403).
        """
        token_forjado = gerar_token_supabase(
            email='colab@intech.com.br',
            extra_claims={'user_metadata': {'isAdmin': True}, 'role': 'service_role'},
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_forjado}')
        resp = self.client.get('/api/funcionarios/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_rf01_01_a_04_crud_usuario_por_admin_com_token_supabase(self):
        """RF01.01 a RF01.04 - CRUD de usuários pelo Administrador autenticado via token Supabase."""
        token_admin = gerar_token_supabase(email='admin@intech.com.br')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}')

        # RF01.01 - Inserir Usuário
        resp_create = self.client.post(
            '/api/funcionarios/',
            {
                'nome': 'Novo Funcionário',
                'email': 'novo@intech.com.br',
                'senha': 'senha456',
                'isAdmin': False,
            },
            format='json',
        )
        self.assertEqual(resp_create.status_code, status.HTTP_201_CREATED)

        # RF01.02 - Listar Usuários com filtro
        resp_list = self.client.get('/api/funcionarios/?nome=Novo&email=novo@intech')
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_list.data), 1)

        # RF01.03 - Atualizar Usuário
        id_novo = resp_create.data['idFuncionario']
        resp_update = self.client.patch(
            f'/api/funcionarios/{id_novo}/',
            {'nome': 'Funcionário Atualizado', 'isAdmin': True},
            format='json',
        )
        self.assertEqual(resp_update.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_update.data['isAdmin'])

        # RF01.04 - Deletar Usuário informando o e-mail
        resp_delete = self.client.delete(
            '/api/funcionarios/deletar-por-email/?email=novo@intech.com.br'
        )
        self.assertEqual(resp_delete.status_code, status.HTTP_200_OK)
        self.assertFalse(Funcionario.objects.filter(email='novo@intech.com.br').exists())
