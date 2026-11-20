"""
Testes automatizados para US01 (Manter Usuário) e integração com o Supabase Auth.

Cobre os critérios de aceite da Issue #19:
- Perfil funcional mantém apenas nome, email, isAdmin e o vínculo único com o Supabase.
- A tabela/API de funcionários não armazena nem retorna senha ou hash.
- O backend resolve a identidade autenticada (`sub`) para o perfil correspondente.
- Perfis legados (sem vínculo) são associados pelo e-mail no primeiro login autenticado.
- Criação encaminha a senha ao Supabase e persiste o identificador devolvido.
- Tokens inválidos, expirados, de outro projeto ou sem perfil retornam 401.
"""

import time
import uuid
from unittest.mock import patch

import jwt
import requests
from django.db import DatabaseError, connection
from django.test import SimpleTestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from config.supabase_client import SupabaseAdminError, SupabaseClient

from .models import Funcionario

SEGREDO_SUPABASE_TESTE = 'segredo-jwt-supabase-teste-1234567890-seguro'
URL_PROJETO_SUPABASE = 'https://ssdoivoyzxddfhqbguhy.supabase.co'
ISSUER_PROJETO = f'{URL_PROJETO_SUPABASE}/auth/v1'

ADMIN_SUB = '11111111-1111-4111-8111-111111111111'
COLAB_SUB = '22222222-2222-4222-8222-222222222222'


def gerar_token_supabase(
    email: str,
    sub: str = COLAB_SUB,
    segredo: str = SEGREDO_SUPABASE_TESTE,
    exp_offset: int = 3600,
    iss: str = ISSUER_PROJETO,
    extra_claims: dict = None,
) -> str:
    payload = {
        'email': email,
        'aud': 'authenticated',
        'role': 'authenticated',
        'iss': iss,
        'iat': int(time.time()),
        'exp': int(time.time()) + exp_offset,
    }
    if sub is not None:
        payload['sub'] = sub
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
            supabase_user_id=ADMIN_SUB,
        )
        self.funcionario = Funcionario.objects.create_user(
            email='colab@intech.com.br',
            nome='Colaborador Intech',
            supabase_user_id=COLAB_SUB,
            isAdmin=False,
        )

    def test_endpoint_protegido_sem_autenticacao_retorna_401(self):
        """Endpoints protegidos devem retornar 401 Unauthorized sem autenticação válida."""
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_modelo_e_tabela_nao_possuem_senha(self):
        """A senha/hash não pode existir no modelo nem na tabela FUNCIONARIO."""
        nomes_de_campos = {campo.name for campo in Funcionario._meta.get_fields()}
        self.assertNotIn('password', nomes_de_campos)
        self.assertNotIn('senha', nomes_de_campos)
        self.assertIn('supabase_user_id', nomes_de_campos)

        with connection.cursor() as cursor:
            colunas = {
                coluna.name
                for coluna in connection.introspection.get_table_description(
                    cursor, 'FUNCIONARIO'
                )
            }
        self.assertNotIn('senha', colunas)
        self.assertIn('supabaseUserId', colunas)

    def test_token_supabase_valido_identifica_funcionario_pelo_sub(self):
        """A identidade (`sub`) resolve o perfil, mesmo com e-mail divergente no token."""
        token = gerar_token_supabase(
            email='email-divergente@intech.com.br',
            sub=COLAB_SUB,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['idFuncionario'], self.funcionario.idFuncionario)
        self.assertEqual(resp.data['supabase_user_id'], COLAB_SUB)
        self.assertFalse(resp.data['isAdmin'])
        self.assertNotIn('senha', resp.data)
        self.assertNotIn('password', resp.data)

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

    def test_token_sem_identidade_retorna_401(self):
        """Token válido sem `sub` não permite resolver a identidade."""
        token_sem_sub = gerar_token_supabase(email='colab@intech.com.br', sub=None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_sem_sub}')
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_usuario_sem_perfil_associado_retorna_401(self):
        """Token válido do Supabase para usuário sem perfil FUNCIONARIO deve ser rejeitado."""
        token_sem_perfil = gerar_token_supabase(
            email='nao.cadastrado@intech.com.br',
            sub=str(uuid.uuid4()),
        )
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_sem_perfil}')
        resp = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_perfil_legado_e_vinculado_pelo_email_no_primeiro_login(self):
        """
        Perfil sem `supabaseUserId` (criado antes da Issue #19) é vinculado uma única
        vez ao e-mail autenticado, sem qualquer senha no backend.
        """
        legado = Funcionario.objects.create_user(
            email='legado@intech.com.br',
            nome='Perfil Legado',
        )
        nova_identidade = str(uuid.uuid4())

        token = gerar_token_supabase(email='legado@intech.com.br', sub=nova_identidade)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        resp = self.client.get('/api/funcionarios/me/')

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        legado.refresh_from_db()
        self.assertEqual(str(legado.supabase_user_id), nova_identidade)

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

    def test_funcionario_nao_admin_bloqueado_em_todas_operacoes_crud(self):
        """
        Garante que usuários autenticados sem perfil de Administrador (isAdmin=False)
        recebam 403 Forbidden em todas as operações de CRUD de funcionários.
        """
        token_colab = gerar_token_supabase(email='colab@intech.com.br', sub=COLAB_SUB)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_colab}')

        # Listagem
        self.assertEqual(
            self.client.get('/api/funcionarios/').status_code,
            status.HTTP_403_FORBIDDEN,
        )
        # Detalhe
        self.assertEqual(
            self.client.get(f'/api/funcionarios/{self.admin.idFuncionario}/').status_code,
            status.HTTP_403_FORBIDDEN,
        )
        # Criação
        self.assertEqual(
            self.client.post(
                '/api/funcionarios/',
                {
                    'nome': 'Tentativa Sem Permissão',
                    'email': 'bloqueado@intech.com.br',
                    'senha': 'senha123',
                    'isAdmin': False,
                },
                format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        # Atualização (PATCH / PUT)
        self.assertEqual(
            self.client.patch(
                f'/api/funcionarios/{self.funcionario.idFuncionario}/',
                {'nome': 'Alterado'},
                format='json',
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        # Exclusão por ID e por e-mail
        self.assertEqual(
            self.client.delete(
                f'/api/funcionarios/{self.admin.idFuncionario}/'
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            self.client.delete(
                '/api/funcionarios/deletar-por-email/?email=admin@intech.com.br'
            ).status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_admin_nao_pode_excluir_proprio_usuario_por_id(self):
        """Administrador não pode remover o próprio registro via DELETE /api/funcionarios/{id}/."""
        token_admin = gerar_token_supabase(email='admin@intech.com.br', sub=ADMIN_SUB)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}')

        resp = self.client.delete(f'/api/funcionarios/{self.admin.idFuncionario}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(
            Funcionario.objects.filter(idFuncionario=self.admin.idFuncionario).exists()
        )

    @patch('funcionarios.services.SupabaseClient.set_auth_user_active')
    @patch('funcionarios.services.SupabaseClient.create_auth_user')
    def test_rf01_01_a_04_crud_usuario_por_admin_com_token_supabase(self, mock_create_auth_user, mock_set_active):
        """RF01.01 a RF01.04 - CRUD de perfis pelo Administrador autenticado no Supabase."""
        identidade_novo = uuid.uuid4()
        mock_create_auth_user.return_value = identidade_novo

        token_admin = gerar_token_supabase(email='admin@intech.com.br', sub=ADMIN_SUB)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}')

        # RF01.01 - Inserir Usuário (identidade criada no Supabase, perfil no backend)
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
        self.assertNotIn('senha', resp_create.data)
        mock_create_auth_user.assert_called_once()

        novo = Funcionario.objects.get(email='novo@intech.com.br')
        self.assertEqual(novo.supabase_user_id, identidade_novo)

        # RF01.02 - Listar Usuários com filtro
        resp_list = self.client.get('/api/funcionarios/?nome=Novo&email=novo@intech')
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_list.data), 1)
        self.assertNotIn('senha', resp_list.data[0])

        # RF01.03 - Atualizar Usuário (sem tratar senha no perfil)
        id_novo = resp_create.data['idFuncionario']
        resp_update = self.client.patch(
            f'/api/funcionarios/{id_novo}/',
            {'nome': 'Funcionário Atualizado', 'email': 'contato@intech.com.br', 'isAdmin': True},
            format='json',
        )
        self.assertEqual(resp_update.status_code, status.HTTP_200_OK)
        self.assertTrue(resp_update.data['isAdmin'])
        self.assertEqual(resp_update.data['nome'], 'Funcionário Atualizado')
        self.assertEqual(resp_update.data['email'], 'contato@intech.com.br')
        mock_set_active.assert_not_called()

        # RF01.04 - Inativar Usuário informando o e-mail (Exclusão Lógica)
        resp_delete = self.client.delete(
            '/api/funcionarios/deletar-por-email/?email=contato@intech.com.br'
        )
        self.assertEqual(resp_delete.status_code, status.HTTP_200_OK)
        mock_set_active.assert_called_once_with(identidade_novo, False)
        novo_inativo = Funcionario.objects.get(email='contato@intech.com.br')
        self.assertFalse(novo_inativo.is_active)
        # Na listagem padrão de ativos, o funcionário inativado não aparece
        resp_list_after = self.client.get('/api/funcionarios/?email=contato@intech.com.br')
        self.assertEqual(len(resp_list_after.data), 0)

    @patch('funcionarios.services.SupabaseClient.set_auth_user_active')
    def test_exclusao_logica_por_id_inativa_usuario_e_rejeita_autenticacao(self, mock_set_active):
        """RF01.04 - Exclusão lógica inativa o usuário (is_active=False) e bloqueia novas autenticações."""
        token_admin = gerar_token_supabase(email='admin@intech.com.br', sub=ADMIN_SUB)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}')

        resp_del = self.client.delete(f'/api/funcionarios/{self.funcionario.idFuncionario}/')
        self.assertEqual(resp_del.status_code, status.HTTP_200_OK)

        self.funcionario.refresh_from_db()
        self.assertFalse(self.funcionario.is_active)
        mock_set_active.assert_called_once_with(uuid.UUID(COLAB_SUB), False)

        # Usuário inativo tenta acessar /api/funcionarios/me/ e recebe 401
        token_inativo = gerar_token_supabase(email='colab@intech.com.br', sub=COLAB_SUB)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_inativo}')
        resp_me = self.client.get('/api/funcionarios/me/')
        self.assertEqual(resp_me.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('inativo', resp_me.data.get('detail', '').lower())

    @patch('funcionarios.services.SupabaseClient.create_auth_user')
    def test_criacao_sem_supabase_nao_cria_perfil_orfao(self, mock_create_auth_user):
        """Se o Supabase Auth não criar a identidade, nenhum perfil é persistido."""
        mock_create_auth_user.side_effect = SupabaseAdminError('unavailable')
        token_admin = gerar_token_supabase(email='admin@intech.com.br', sub=ADMIN_SUB)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token_admin}')

        resp = self.client.post(
            '/api/funcionarios/',
            {
                'nome': 'Sem Identidade',
                'email': 'sem.identidade@intech.com.br',
                'senha': 'senha456',
            },
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertFalse(
            Funcionario.objects.filter(email='sem.identidade@intech.com.br').exists()
        )

    @patch('funcionarios.serializers.SupabaseClient.sign_in_with_password')
    def test_login_resolve_perfil_pela_identidade_supabase(self, mock_sign_in):
        """Login delega a senha ao Supabase e resolve o perfil pelo id autenticado."""
        mock_sign_in.return_value = {
            'access_token': 'token-supabase',
            'refresh_token': 'refresh-supabase',
            'user': {'id': COLAB_SUB, 'email': 'colab@intech.com.br'},
        }

        resp = self.client.post(
            '/api/funcionarios/login/',
            {'email': 'colab@intech.com.br', 'senha': 'senha123'},
            format='json',
        )

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['provedor_auth'], 'supabase')
        self.assertEqual(resp.data['usuario']['idFuncionario'], self.funcionario.idFuncionario)
        self.assertNotIn('senha', resp.data['usuario'])
        mock_sign_in.assert_called_once_with(
            email='colab@intech.com.br',
            password='senha123',
        )

    def autenticar_admin(self):
        token = gerar_token_supabase(email=self.admin.email, sub=ADMIN_SUB)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    @patch('funcionarios.services.SupabaseClient.create_auth_user')
    def test_valida_dados_antes_de_chamar_auth(self, mock_create):
        self.autenticar_admin()
        resposta = self.client.post('/api/funcionarios/', {
            'nome': '', 'email': self.funcionario.email.upper(), 'senha': 'curta',
        }, format='json')

        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(set(resposta.data), {'nome', 'email', 'senha'})
        mock_create.assert_not_called()

    @patch('funcionarios.services.SupabaseClient.create_auth_user')
    def test_email_duplicado_no_auth_retorna_erro_no_campo(self, mock_create):
        self.autenticar_admin()
        mock_create.side_effect = SupabaseAdminError('email_exists')
        resposta = self.client.post('/api/funcionarios/', {
            'nome': 'Novo', 'email': 'novo@example.com', 'senha': 'senha123',
        }, format='json')

        self.assertEqual(resposta.status_code, 400)
        self.assertIn('já está cadastrado', resposta.data['email'])
        self.assertFalse(Funcionario.objects.filter(email='novo@example.com').exists())

    @patch('funcionarios.services.SupabaseClient.create_auth_user')
    def test_reutiliza_perfil_criado_pelo_gatilho_com_mesmo_uuid(self, mock_create):
        self.autenticar_admin()
        identidade = uuid.uuid4()

        def criar_perfil_do_gatilho(**dados):
            Funcionario.objects.create_user(
                nome=dados['nome'], email=dados['email'], supabase_user_id=identidade,
            )
            return identidade

        mock_create.side_effect = criar_perfil_do_gatilho
        resposta = self.client.post('/api/funcionarios/', {
            'nome': 'Novo Admin', 'email': 'novo@example.com', 'senha': ' senha123 ', 'isAdmin': True,
        }, format='json')

        self.assertEqual(resposta.status_code, 201)
        perfil = Funcionario.objects.get(supabase_user_id=identidade)
        self.assertEqual(perfil.pk, resposta.data['idFuncionario'])
        self.assertTrue(perfil.isAdmin)
        mock_create.assert_called_once_with(
            nome='Novo Admin', email='novo@example.com', password=' senha123 ', is_active=True,
        )

    @patch('funcionarios.services.SupabaseClient.delete_auth_user')
    @patch('funcionarios.services.SupabaseClient.create_auth_user')
    @patch.object(Funcionario.objects, 'create_user', side_effect=DatabaseError('erro simulado'))
    def test_falha_ao_salvar_perfil_reverte_identidade(self, mock_save, mock_create, mock_delete):
        self.autenticar_admin()
        identidade = uuid.uuid4()
        mock_create.return_value = identidade
        resposta = self.client.post('/api/funcionarios/', {
            'nome': 'Novo', 'email': 'novo@example.com', 'senha': 'senha123',
        }, format='json')

        self.assertEqual(resposta.status_code, 500)
        mock_save.assert_called_once()
        mock_delete.assert_called_once_with(identidade)
        self.assertFalse(Funcionario.objects.filter(supabase_user_id=identidade).exists())

    @patch('funcionarios.services.LogRastreabilidade.registrarLog', side_effect=DatabaseError)
    @patch('funcionarios.services.SupabaseClient.delete_auth_user')
    @patch('funcionarios.services.SupabaseClient.create_auth_user')
    def test_falha_de_auditoria_remove_perfil_gerado_pelo_gatilho(self, mock_create, mock_delete, mock_log):
        self.autenticar_admin()
        identidade = uuid.uuid4()

        def criar_perfil_do_gatilho(**dados):
            Funcionario.objects.create_user(
                nome=dados['nome'], email=dados['email'], supabase_user_id=identidade,
            )
            return identidade

        mock_create.side_effect = criar_perfil_do_gatilho
        resposta = self.client.post('/api/funcionarios/', {
            'nome': 'Novo', 'email': 'novo@example.com', 'senha': 'senha123',
        }, format='json')

        self.assertEqual(resposta.status_code, 500)
        mock_log.assert_called_once()
        mock_delete.assert_called_once_with(identidade)
        self.assertFalse(Funcionario.objects.filter(supabase_user_id=identidade).exists())

    @patch('funcionarios.services.SupabaseClient.set_auth_user_active')
    def test_falha_ao_inativar_no_auth_mantem_perfil_inativo_e_permite_repetir(self, mock_set_active):
        self.autenticar_admin()
        mock_set_active.side_effect = [SupabaseAdminError('unavailable'), None]
        url = f'/api/funcionarios/{self.funcionario.pk}/'

        resposta = self.client.delete(url)
        self.assertEqual(resposta.status_code, 503)
        self.assertIn('Repita', resposta.data['detail'])
        self.funcionario.refresh_from_db()
        self.assertFalse(self.funcionario.is_active)

        self.assertEqual(self.client.delete(url).status_code, 200)
        self.assertEqual(mock_set_active.call_count, 2)

    @patch('funcionarios.services.SupabaseClient.set_auth_user_active')
    def test_reativacao_so_altera_perfil_apos_confirmacao_do_auth(self, mock_set_active):
        self.autenticar_admin()
        self.funcionario.is_active = False
        self.funcionario.save(update_fields=['is_active'])
        mock_set_active.side_effect = [SupabaseAdminError('unavailable'), None]
        url = f'/api/funcionarios/{self.funcionario.pk}/'

        self.assertEqual(self.client.patch(url, {'is_active': True}, format='json').status_code, 503)
        self.funcionario.refresh_from_db()
        self.assertFalse(self.funcionario.is_active)
        self.assertEqual(self.client.patch(url, {'is_active': True}, format='json').status_code, 200)
        self.funcionario.refresh_from_db()
        self.assertTrue(self.funcionario.is_active)

    @patch('funcionarios.services.SupabaseClient.set_auth_user_active')
    def test_atualizacao_de_perfil_rejeita_senha_inativacao_propria_e_perfil_inexistente(self, mock_set_active):
        self.autenticar_admin()
        url = f'/api/funcionarios/{self.admin.pk}/'
        self.assertEqual(self.client.patch(url, {'senha': 'nova-senha'}, format='json').status_code, 400)
        self.assertEqual(self.client.patch(url, {'is_active': False}, format='json').status_code, 400)
        self.assertEqual(self.client.delete('/api/funcionarios/9999/').status_code, 404)
        self.assertEqual(self.client.delete(
            f'/api/funcionarios/deletar-por-email/?email={self.admin.email}',
        ).status_code, 400)
        mock_set_active.assert_not_called()


@override_settings(
    SUPABASE_URL=URL_PROJETO_SUPABASE,
    SUPABASE_ANON_KEY='sb_publishable_teste',
    SUPABASE_SERVICE_ROLE_KEY='sb_secret_teste',
)
class SupabaseAdminClientTests(SimpleTestCase):
    @override_settings(SUPABASE_SERVICE_ROLE_KEY='')
    @patch('config.supabase_client.requests.request')
    def test_sem_chave_privilegiada_nao_chama_signup_publico(self, request):
        with self.assertRaisesMessage(SupabaseAdminError, 'not_configured'):
            SupabaseClient.create_auth_user('novo@example.com', 'senha123', 'Novo')
        request.assert_not_called()

    @patch('config.supabase_client.requests.request')
    def test_cria_identidade_com_chave_administrativa_e_bloqueio_inicial(self, request):
        request.return_value.status_code = 201
        request.return_value.json.return_value = {'id': COLAB_SUB}

        identidade = SupabaseClient.create_auth_user('novo@example.com', 'senha123', 'Novo', is_active=False)

        self.assertEqual(identidade, uuid.UUID(COLAB_SUB))
        request.assert_called_once_with(
            'POST', f'{ISSUER_PROJETO}/admin/users',
            json={
                'email': 'novo@example.com', 'password': 'senha123', 'email_confirm': True,
                'user_metadata': {'nome': 'Novo'}, 'ban_duration': SupabaseClient.AUTH_BAN_DURATION,
            },
            headers={'apikey': 'sb_secret_teste', 'Content-Type': 'application/json'},
            timeout=5, allow_redirects=False,
        )

    @patch('config.supabase_client.requests.request')
    def test_bloqueia_e_reativa_por_uuid(self, request):
        request.return_value.status_code = 200
        identidade = uuid.UUID(COLAB_SUB)
        for ativo, duracao in [(False, SupabaseClient.AUTH_BAN_DURATION), (True, 'none')]:
            with self.subTest(ativo=ativo):
                SupabaseClient.set_auth_user_active(identidade, ativo)
                self.assertEqual(request.call_args.args, ('PUT', f'{ISSUER_PROJETO}/admin/users/{identidade}'))
                self.assertEqual(request.call_args.kwargs['json'], {'ban_duration': duracao})

    @patch('config.supabase_client.requests.request')
    def test_trata_email_duplicado_e_timeout_sem_expor_resposta_do_provedor(self, request):
        request.return_value.status_code = 422
        request.return_value.json.return_value = {'error_code': 'email_exists', 'msg': 'Detalhe privado'}
        with self.assertRaisesMessage(SupabaseAdminError, 'email_exists'):
            SupabaseClient.create_auth_user('novo@example.com', 'senha123', 'Novo')

        request.side_effect = requests.Timeout('Detalhe privado')
        with self.assertRaisesMessage(SupabaseAdminError, 'unavailable'):
            SupabaseClient.create_auth_user('novo@example.com', 'senha123', 'Novo')
