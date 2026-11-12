"""Testes automatizados para US03 (Manter SPED), US04 (Enviar SPED), US05 (Rastreabilidade) e US06 (Dashboard)."""

from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from auditoria.models import LogRastreabilidade
from clientes.models import Cliente
from funcionarios.models import Funcionario

from .models import Sped


class SpedWorkflowTests(APITestCase):
    def setUp(self):
        self.funcionario = Funcionario.objects.create_user(
            email='operador@intech.com.br',
            nome='Operador Fiscal',
            senha='senha123',
            isAdmin=False,
        )
        self.client.force_authenticate(user=self.funcionario)

        self.cliente_simples = Cliente.objects.create(
            cnpj='11.111.111/0001-11',
            nomeEmpresa='Mercado Simples',
            razaoSocial='Mercado Simples LTDA',
            telefoneWhatsApp='84988881111',
            emailContador='cont1@contabil.com',
            regimeTributario='Simples Nacional',
        )
        self.cliente_real = Cliente.objects.create(
            cnpj='22.222.222/0001-22',
            nomeEmpresa='Indústria Real',
            razaoSocial='Indústria Real S/A',
            telefoneWhatsApp='84988882222',
            emailContador='cont2@contabil.com',
            regimeTributario='Lucro Real',
        )

    def test_fluxo_completo_us03_us04_us05_us06(self):
        """Testa geração de fila priorizada, upload, progressão de status, envio e dashboard."""
        # RF03.01 - Gerar Fila de Atendimento
        resp_fila = self.client.post(
            '/api/speds/gerar-fila/',
            {'mesReferencia': '11/2026'},
            format='json',
        )
        self.assertEqual(resp_fila.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_fila.data['novos_speds_criados'], 2)

        # RF03.02 - Listar SPEDs Pendentes ordenados por prioridade (Lucro Real antes de Simples Nacional)
        resp_pendentes = self.client.get('/api/speds/fila-pendentes/?mesReferencia=11/2026')
        self.assertEqual(resp_pendentes.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp_pendentes.data), 2)
        self.assertEqual(
            resp_pendentes.data[0]['cliente_detalhes']['nomeEmpresa'],
            'Indústria Real',
        )
        id_sped = resp_pendentes.data[0]['idSped']

        # RF03.03 - Tentativa de pular de PENDENTE direto para ENVIADO deve ser bloqueada
        resp_invalido = self.client.patch(
            f'/api/speds/{id_sped}/atualizar-status/',
            {'novoStatus': 'ENVIADO'},
            format='json',
        )
        self.assertEqual(resp_invalido.status_code, status.HTTP_400_BAD_REQUEST)

        # RF03.04 - Anexar Arquivo do SPED (realiza upload e avança status para GERADO)
        arquivo_ficticio = SimpleUploadedFile(
            'sped_11_2026.rar',
            b'CONTEUDO_BINARIO_RAR_SPED',
            content_type='application/x-rar-compressed',
        )
        resp_upload = self.client.post(
            f'/api/speds/{id_sped}/upload/',
            {'arquivoRar': arquivo_ficticio},
            format='multipart',
        )
        self.assertEqual(resp_upload.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_upload.data['status'], Sped.StatusChoices.GERADO)

        # US04 (RF04.01 a RF04.04) - Enviar SPED ao contador + WhatsApp + Concluir Envio
        resp_enviar = self.client.post(f'/api/speds/{id_sped}/enviar/')
        self.assertEqual(resp_enviar.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_enviar.data['sped']['status'], Sped.StatusChoices.ENVIADO)
        self.assertIn(
            'Operador Fiscal',
            resp_enviar.data['resultado_envio']['mensagem_personalizada'],
        )
        self.assertIn(
            'Indústria Real',
            resp_enviar.data['resultado_envio']['mensagem_personalizada'],
        )

        # US05 - Verificar se os logs de rastreabilidade foram gravados automaticamente
        self.assertTrue(LogRastreabilidade.objects.filter(sped_id=id_sped).exists())

        # US06 - Dashboard Gerencial
        resp_dash = self.client.get('/api/auditoria/dashboard/?mesReferencia=11/2026')
        self.assertEqual(resp_dash.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_dash.data['demandas']['total'], 2)
        self.assertEqual(resp_dash.data['demandas']['enviados'], 1)
        self.assertEqual(resp_dash.data['demandas']['pendentes'], 1)
