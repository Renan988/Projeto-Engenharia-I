"""Testes unitários do módulo de Auditoria (US05 e US06)."""

from django.test import TestCase

from funcionarios.models import Funcionario

from .models import LogRastreabilidade


class AuditoriaTests(TestCase):
    def test_registrar_log_geral_e_dashboard(self):
        func = Funcionario.objects.create_user(
            email='auditor@intech.com.br',
            nome='Auditor Fiscal',
            senha='senha123',
        )
        log = LogRastreabilidade.registrarLog(
            acao='Executou verificação de conformidade LGPD',
            funcionario=func,
        )
        self.assertIsNotNone(log.idLog)
        self.assertIsNone(log.sped)

        dashboard = LogRastreabilidade.gerarDashboard()
        self.assertIn('demandas', dashboard)
        self.assertIn('produtividade_equipe', dashboard)
