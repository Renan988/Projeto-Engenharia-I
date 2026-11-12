"""
Serviços de domínio do módulo SPED (US03 e US04):
- RF04.01: Envio de SPED por e-mail ao contador com mecanismo de retentativa.
- RF04.02: Notificação ao cliente via API de WhatsApp com mecanismo de retentativa.
- RF04.03: Personalização dinâmica de template de mensagem (nome do usuário logado e nome do cliente).
"""

import os
import time
from typing import Any, Dict

import requests
from django.conf import settings
from django.core.mail import EmailMessage


def gerar_mensagem_personalizada(
    nome_funcionario: str,
    nome_cliente: str,
    mes_referencia: str,
    destinatario: str = 'cliente',
) -> str:
    """
    RF04.03 - Personalizar Mensagem (Template):
    Gera mensagens dinâmicas que incluem automaticamente o nome do usuário logado
    e o nome do cliente vinculado ao SPED.
    """
    if destinatario == 'contador':
        return (
            f'Olá! Aqui é {nome_funcionario}, da equipe Intech Sistemas.\n\n'
            f'Segue em anexo o arquivo SPED referente à competência {mes_referencia} '
            f'do cliente {nome_cliente}.\n\n'
            f'Atenciosamente,\n'
            f'{nome_funcionario} - Intech Sistemas'
        )
    return (
        f'Olá, {nome_cliente}! Aqui é {nome_funcionario}, da Intech Sistemas. '
        f'Informamos que o seu arquivo SPED referente ao mês {mes_referencia} '
        f'já foi gerado e encaminhado para o e-mail da sua contabilidade.'
    )


def enviar_email_com_retentativa(
    destinatario_email: str,
    assunto: str,
    corpo_mensagem: str,
    caminho_arquivo: str = None,
) -> Dict[str, Any]:
    """
    RF04.01 - Enviar SPED por E-mail ao contador com mecanismo de retentativa
    (mitigação do risco de indisponibilidade do serviço de e-mail - RNF007).
    """
    max_tentativas = max(1, int(getattr(settings, 'EMAIL_MAX_RETRIES', 3)))
    remetente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@intechsistemas.com.br')
    ultimo_erro = None

    for tentativa in range(1, max_tentativas + 1):
        try:
            email = EmailMessage(
                subject=assunto,
                body=corpo_mensagem,
                from_email=remetente,
                to=[destinatario_email],
            )
            if caminho_arquivo and os.path.exists(caminho_arquivo):
                email.attach_file(caminho_arquivo)
            email.send(fail_silently=False)
            return {
                'sucesso': True,
                'tentativas': tentativa,
                'destinatario': destinatario_email,
            }
        except Exception as exc:
            ultimo_erro = str(exc)
            if tentativa < max_tentativas:
                time.sleep(0.2)

    return {
        'sucesso': False,
        'tentativas': max_tentativas,
        'destinatario': destinatario_email,
        'erro': ultimo_erro or 'Falha ao enviar e-mail.',
    }


def enviar_notificacao_whatsapp_com_retentativa(
    telefone: str,
    mensagem: str,
) -> Dict[str, Any]:
    """
    RF04.02 - Notificar Cliente via WhatsApp com mecanismo de retentativa
    (mitigação do risco de indisponibilidade/instabilidade da API do WhatsApp - RNF006).
    Caso WHATSAPP_API_URL não esteja configurada em ambiente de desenvolvimento,
    simula o disparo registrando a mensagem gerada.
    """
    if not telefone:
        return {
            'sucesso': False,
            'simulado': False,
            'motivo': 'Cliente não possui telefone/WhatsApp cadastrado.',
            'mensagem': mensagem,
        }

    api_url = (getattr(settings, 'WHATSAPP_API_URL', '') or '').strip()
    api_token = (getattr(settings, 'WHATSAPP_API_TOKEN', '') or '').strip()
    max_tentativas = max(1, int(getattr(settings, 'WHATSAPP_MAX_RETRIES', 3)))

    if not api_url:
        # Modo de desenvolvimento/simulação quando credenciais de API externa não estão definidas
        return {
            'sucesso': True,
            'simulado': True,
            'tentativas': 1,
            'telefone': telefone,
            'mensagem': mensagem,
        }

    headers = {'Content-Type': 'application/json'}
    if api_token:
        headers['Authorization'] = f'Bearer {api_token}'

    ultimo_erro = None
    for tentativa in range(1, max_tentativas + 1):
        try:
            resp = requests.post(
                api_url,
                json={'phone': telefone, 'message': mensagem},
                headers=headers,
                timeout=4,
            )
            if 200 <= resp.status_code < 300:
                return {
                    'sucesso': True,
                    'simulado': False,
                    'tentativas': tentativa,
                    'telefone': telefone,
                    'mensagem': mensagem,
                }
            ultimo_erro = f'Status HTTP {resp.status_code}'
        except requests.RequestException as exc:
            ultimo_erro = str(exc)

        if tentativa < max_tentativas:
            time.sleep(0.2)

    return {
        'sucesso': False,
        'simulado': False,
        'tentativas': max_tentativas,
        'telefone': telefone,
        'mensagem': mensagem,
        'erro': ultimo_erro or 'API de WhatsApp indisponível após retentativas.',
    }
