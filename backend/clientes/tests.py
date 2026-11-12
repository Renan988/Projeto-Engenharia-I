"""Testes automatizados para US02 - Manter Cliente (RF02.01 a RF02.04)."""

from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

from funcionarios.models import Funcionario

from .models import Cliente


class ClienteUS02Tests(APITestCase):
    def setUp(self):
        self.funcionario = Funcionario.objects.create_user(
            email='func@intech.com.br',
            nome='Funcionário Teste',
            senha='senha123',
            isAdmin=False,
        )
        self.client.force_authenticate(user=self.funcionario)

    @patch('clientes.serializers.consultar_dados_cnpj_api')
    def test_rf02_01_a_04_crud_cliente_com_consulta_api(self, mock_api):
        """RF02.01 a RF02.04 - Cadastro via CNPJ com consulta automática, filtro, atualização e exclusão."""
        mock_api.return_value = {
            'cnpj': '12.345.678/0001-99',
            'nomeEmpresa': 'Tech Soluções',
            'razaoSocial': 'Tech Soluções Empresariais LTDA',
            'regimeTributario': 'Lucro Real',
            'api_disponivel': True,
        }

        # RF02.01 - Inserir Cliente informando CNPJ, telefoneWhatsApp e emailContador
        resp_create = self.client.post(
            '/api/clientes/',
            {
                'cnpj': '12345678000199',
                'telefoneWhatsApp': '84999990000',
                'emailContador': 'contador@contabilidade.com.br',
            },
            format='json',
        )
        self.assertEqual(resp_create.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp_create.data['nomeEmpresa'], 'Tech Soluções')
        self.assertEqual(resp_create.data['regimeTributario'], 'Lucro Real')
        self.assertEqual(resp_create.data['prioridadeFila'], 1)

        # RF02.02 - Listar Clientes com filtros
        resp_list = self.client.get('/api/clientes/?regimeTributario=Lucro Real')
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_list.data), 1)

        # RF02.03 - Atualizar Cliente
        id_cli = resp_create.data['idCli']
        resp_update = self.client.patch(
            f'/api/clientes/{id_cli}/',
            {'regimeTributario': 'Simples Nacional'},
            format='json',
        )
        self.assertEqual(resp_update.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_update.data['regimeTributario'], 'Simples Nacional')

        # RF02.04 - Deletar Cliente informando o CNPJ
        resp_del = self.client.delete(
            '/api/clientes/deletar-por-cnpj/?cnpj=12.345.678/0001-99'
        )
        self.assertEqual(resp_del.status_code, status.HTTP_200_OK)
        self.assertEqual(Cliente.objects.count(), 0)
