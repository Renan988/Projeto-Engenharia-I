"""Testes automatizados para US01 - Manter Usuário (RF01.01 a RF01.05)."""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Funcionario


class FuncionarioUS01Tests(APITestCase):
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

    def test_rf01_05_login_usuario(self):
        """RF01.05 - Login do Usuário com e-mail e senha."""
        url = reverse('funcionario-login')
        resp = self.client.post(
            url,
            {'email': 'admin@intech.com.br', 'senha': 'senha123'},
            format='json',
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertEqual(resp.data['usuario']['perfil'], 'Administrador')

    def test_rf01_01_a_04_crud_usuario_por_admin(self):
        """RF01.01, RF01.02, RF01.03, RF01.04 - CRUD de usuários pelo Administrador."""
        self.client.force_authenticate(user=self.admin)

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
