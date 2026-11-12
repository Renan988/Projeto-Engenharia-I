"""
Serviço de integração externa para consulta de dados cadastrais e regime tributário via CNPJ (RF02.01).
Inclui tratamento de falhas e fallback para cadastro manual conforme matriz de riscos (doc-visao.md).
"""

import re
from typing import Any, Dict

import requests
from django.conf import settings


def limpar_cnpj(cnpj: str) -> str:
    """Remove caracteres não numéricos do CNPJ."""
    return re.sub(r'\D', '', cnpj or '')


def formatar_cnpj(cnpj: str) -> str:
    """Formata um CNPJ de 14 dígitos no padrão XX.XXX.XXX/XXXX-XX."""
    apenas_digitos = limpar_cnpj(cnpj)
    if len(apenas_digitos) == 14:
        return (
            f'{apenas_digitos[:2]}.{apenas_digitos[2:5]}.{apenas_digitos[5:8]}/'
            f'{apenas_digitos[8:12]}-{apenas_digitos[12:14]}'
        )
    return cnpj.strip()


def inferir_regime_tributario(dados_api: Dict[str, Any]) -> str:
    """
    Infere o regime tributário a partir do retorno da BrasilAPI / Receita Federal.
    Prioriza MEI -> Simples Nacional -> Regime Tributário explícito -> Lucro Presumido/Real.
    """
    if dados_api.get('opcao_pelo_mei') is True:
        return 'MEI'
    if dados_api.get('opcao_pelo_simples') is True:
        return 'Simples Nacional'

    regimes = dados_api.get('regime_tributario')
    if isinstance(regimes, list) and regimes:
        # Pega o registro do ano mais recente
        ultimo = sorted(regimes, key=lambda item: item.get('ano', 0))[-1]
        forma = (ultimo.get('forma_de_tributacao') or '').upper()
        if 'REAL' in forma:
            return 'Lucro Real'
        if 'PRESUMIDO' in forma:
            return 'Lucro Presumido'
        if 'SIMPLES' in forma:
            return 'Simples Nacional'
        if forma:
            return forma.title()

    porte = (dados_api.get('porte') or '').upper()
    if 'DEMAIS' in porte:
        return 'Lucro Presumido'

    return 'Simples Nacional'


def consultar_dados_cnpj_api(cnpj: str) -> Dict[str, Any]:
    """
    Consulta automaticamente os dados da empresa e o regime tributário via API pública (BrasilAPI).
    Em caso de indisponibilidade, retorna flag `api_disponivel=False` permitindo cadastro manual
    (mitigação de risco prevista em docs/doc-visao.md).
    """
    cnpj_limpo = limpar_cnpj(cnpj)
    if len(cnpj_limpo) != 14:
        raise ValueError('O CNPJ deve conter exatamente 14 dígitos numéricos.')

    base_url = getattr(settings, 'CNPJ_API_URL', 'https://brasilapi.com.br/api/cnpj/v1').rstrip('/')
    timeout = getattr(settings, 'CNPJ_API_TIMEOUT', 4)
    url = f'{base_url}/{cnpj_limpo}'

    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            payload = response.json()
            razao_social = (payload.get('razao_social') or '').strip()
            nome_fantasia = (payload.get('nome_fantasia') or razao_social).strip()
            regime = inferir_regime_tributario(payload)
            return {
                'cnpj': formatar_cnpj(cnpj_limpo),
                'nomeEmpresa': nome_fantasia or razao_social,
                'razaoSocial': razao_social or nome_fantasia,
                'regimeTributario': regime,
                'api_disponivel': True,
            }
    except requests.RequestException:
        pass

    return {
        'cnpj': formatar_cnpj(cnpj_limpo),
        'nomeEmpresa': '',
        'razaoSocial': '',
        'regimeTributario': '',
        'api_disponivel': False,
        'aviso': (
            'API de consulta de CNPJ indisponível no momento. '
            'Preencha manualmente os dados do cliente.'
        ),
    }
