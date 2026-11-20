"""Operações que coordenam o perfil local e a identidade no Supabase Auth."""

import logging

from django.db import DatabaseError, IntegrityError, connection, transaction
from rest_framework.exceptions import APIException, NotFound, ValidationError

from auditoria.models import LogRastreabilidade
from config.supabase_client import SupabaseAdminError, SupabaseClient

from .models import Funcionario


logger = logging.getLogger(__name__)


class AuthIndisponivel(APIException):
    status_code = 503
    default_detail = 'Não foi possível concluir a operação no Supabase Auth. Tente novamente.'


class FalhaCadastro(APIException):
    status_code = 500
    default_detail = 'Não foi possível gravar o perfil do funcionário.'


def criar_funcionario(senha, autor, **perfil):
    try:
        identidade = SupabaseClient.create_auth_user(
            email=perfil['email'],
            password=senha,
            nome=perfil['nome'],
            is_active=perfil.get('is_active', True),
        )
    except SupabaseAdminError as exc:
        if exc.code in ('email_exists', 'user_already_exists'):
            raise ValidationError({'email': 'Esse e-mail já está cadastrado no Supabase Auth.'}) from exc
        if exc.code == 'weak_password':
            raise ValidationError({'senha': 'A senha não atende aos requisitos do Supabase Auth.'}) from exc
        if exc.code == 'not_configured':
            raise AuthIndisponivel('Configure a chave administrativa do Supabase Auth no backend.') from exc
        raise AuthIndisponivel() from exc

    try:
        with transaction.atomic():
            # O gatilho opcional pode criar o perfil durante a chamada ao Auth.
            # Reutilize somente o perfil com o UUID da identidade recém-criada.
            funcionario = Funcionario.objects.select_for_update().filter(
                supabase_user_id=identidade,
            ).first()
            if funcionario is None:
                funcionario = Funcionario.objects.create_user(supabase_user_id=identidade, **perfil)
            else:
                funcionario.manterFuncionario(**perfil)
            LogRastreabilidade.registrarLog(
                acao=f'Cadastrou o usuário {funcionario.nome} ({funcionario.email})',
                funcionario=autor,
            )
            return funcionario
    except DatabaseError as exc:
        reverter_cadastro(identidade)
        if isinstance(exc, IntegrityError) and Funcionario.objects.filter(
            email__iexact=perfil['email'],
        ).exists():
            raise ValidationError({'email': 'Esse e-mail já está cadastrado.'}) from exc
        raise FalhaCadastro() from exc


def reverter_cadastro(identidade):
    # Cada limpeza é tentada mesmo se a outra falhar.
    falhou = False
    try:
        # O gatilho pode criar o perfil mesmo em bancos provisionados pelo SQL,
        # onde as tabelas auxiliares de permissões do Django podem estar ausentes.
        campo = Funcionario._meta.get_field('supabase_user_id')
        valor = campo.get_db_prep_value(identidade, connection)
        with connection.cursor() as cursor:
            cursor.execute(
                'DELETE FROM "FUNCIONARIO" WHERE "supabaseUserId" = %s',
                [valor],
            )
    except DatabaseError:
        logger.error('Falha ao limpar o perfil recém-criado para a identidade %s.', identidade)
        falhou = True
    try:
        SupabaseClient.delete_auth_user(identidade)
    except SupabaseAdminError:
        logger.error('Falha ao reverter a criação da identidade Supabase %s.', identidade)
        falhou = True
    if falhou:
        raise FalhaCadastro(
            'O cadastro falhou e a reversão ficou incompleta. Solicite a conferência do cadastro.'
        )


def atualizar_funcionario(funcionario, **alteracoes):
    ativo = alteracoes.pop('is_active', None)
    erro_auth = None
    with transaction.atomic():
        try:
            funcionario = Funcionario.objects.select_for_update().get(pk=funcionario.pk)
        except Funcionario.DoesNotExist as exc:
            raise NotFound('Perfil de funcionário não encontrado.') from exc

        if ativo is False and funcionario.is_active:
            funcionario.is_active = False
            funcionario.save(update_fields=['is_active'])

        if ativo is not None and funcionario.supabase_user_id:
            try:
                SupabaseClient.set_auth_user_active(funcionario.supabase_user_id, ativo)
            except SupabaseAdminError as exc:
                if ativo or exc.code != 'user_not_found':
                    erro_auth = exc

        if erro_auth is None:
            if ativo is True:
                alteracoes['is_active'] = True
            return funcionario.manterFuncionario(**alteracoes) if alteracoes else funcionario

    if ativo is False:
        raise AuthIndisponivel(
            'O perfil foi inativado no Django, mas o bloqueio no Supabase Auth não foi confirmado. '
            'Repita a operação para concluir.'
        ) from erro_auth
    if erro_auth.code == 'user_not_found':
        raise ValidationError({'is_active': 'A identidade não foi encontrada no Supabase Auth.'}) from erro_auth
    raise AuthIndisponivel() from erro_auth
