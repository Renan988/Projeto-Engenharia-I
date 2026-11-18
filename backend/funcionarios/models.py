"""
Modelo de dados da entidade Funcionario (Tabela FUNCIONARIO).
Referência: docs/doc-modelos.md e docs/doc-visao.md (US01 - Manter Usuário).

A partir da Issue #19, identidade e senha são gerenciadas exclusivamente pelo
Supabase Auth (schema `auth.users`). A tabela FUNCIONARIO guarda apenas o perfil
funcional (nome, e-mail de exibição, nível de acesso) e o vínculo único com o
identificador da identidade Supabase (`supabaseUserId`).
"""

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class FuncionarioManager(BaseUserManager):
    """Gerenciador de perfis de Funcionário (sem armazenamento de senhas)."""

    def create_user(self, email: str, nome: str, isAdmin: bool = False, **extra_fields):
        """
        Cria o perfil funcional de um Funcionário.

        Credenciais não são persistidas neste modelo: qualquer argumento de senha
        recebido por compatibilidade é descartado. O usuário correspondente deve
        ser criado no Supabase Auth e vinculado por `supabase_user_id`.
        """
        if not email:
            raise ValueError('O campo de e-mail é obrigatório.')
        if not nome:
            raise ValueError('O campo nome é obrigatório.')

        email = self.normalize_email(email)
        extra_fields.pop('password', None)
        extra_fields.pop('senha', None)

        isAdmin = bool(isAdmin)
        extra_fields.setdefault('is_staff', isAdmin)
        extra_fields.setdefault('is_superuser', isAdmin)

        funcionario = self.model(
            email=email,
            nome=nome,
            isAdmin=isAdmin,
            **extra_fields,
        )
        funcionario.save(using=self._db)
        return funcionario

    def create_superuser(self, email: str, nome: str, password: str = None, **extra_fields):
        """
        Mantém compatibilidade com o comando `createsuperuser` do Django.

        O argumento `password` é ignorado: a autenticação ocorre no Supabase Auth.
        """
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self.create_user(
            email=email,
            nome=nome,
            isAdmin=True,
            **extra_fields,
        )

    def resolver_por_identidade_supabase(
        self,
        supabase_user_id: str,
        email: str = None,
    ):
        """
        Resolve o perfil de Funcionário a partir do identificador da identidade
        autenticada no Supabase Auth (`sub` do token).

        Perfis criados antes da Issue #19 ainda não possuem vínculo. Para esses,
        o vínculo é feito uma única vez pelo e-mail informado no token já validado
        pelo Supabase, sem qualquer armazenamento de senha. Retorna `None` quando
        não existe perfil correspondente.
        """
        if not supabase_user_id:
            return None

        try:
            identidade = uuid.UUID(str(supabase_user_id))
        except (AttributeError, TypeError, ValueError):
            return None

        funcionario = self.filter(supabase_user_id=identidade).first()
        if funcionario is not None or not email:
            return funcionario

        # Migração transparente de perfis legados (supabaseUserId ainda nulo).
        funcionario = self.filter(
            email__iexact=email.strip(),
            supabase_user_id__isnull=True,
        ).first()
        if funcionario is not None:
            funcionario.supabase_user_id = identidade
            funcionario.save(update_fields=['supabase_user_id'])

        return funcionario


class Funcionario(AbstractBaseUser, PermissionsMixin):
    """
    Perfil funcional do Funcionário, associado 1:1 a uma identidade do Supabase Auth:
    - idFuncionario: SERIAL PK / Identity
    - supabaseUserId: UUID único da identidade em auth.users (Supabase Auth)
    - nome: VARCHAR(150) Not Null
    - email: VARCHAR(150) Unique / Not Null (e-mail de exibição/contato)
    - isAdmin: BOOLEAN Not Null (define nível de acesso Administrador vs Funcionário)

    Senha e hash de senha NÃO pertencem a este modelo nem à tabela FUNCIONARIO:
    são gerenciados exclusivamente pelo Supabase Auth.
    """

    # Remove o campo `password` herdado de AbstractBaseUser (e a coluna `senha`).
    password = None

    idFuncionario = models.AutoField(
        primary_key=True,
        db_column='idFuncionario',
        verbose_name='ID do Funcionário',
    )
    supabase_user_id = models.UUIDField(
        unique=True,
        null=True,
        blank=True,
        db_column='supabaseUserId',
        verbose_name='ID do Usuário no Supabase Auth',
        help_text='Identificador único da identidade autenticada em auth.users.',
    )
    nome = models.CharField(
        max_length=150,
        db_column='nome',
        verbose_name='Nome Completo',
    )
    email = models.EmailField(
        max_length=150,
        unique=True,
        db_column='email',
        verbose_name='E-mail',
    )
    isAdmin = models.BooleanField(
        default=False,
        db_column='isAdmin',
        verbose_name='Administrador',
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Ativo',
    )
    is_staff = models.BooleanField(
        default=False,
        verbose_name='Acesso ao Admin',
    )

    objects = FuncionarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        db_table = 'FUNCIONARIO'
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome']

    def __str__(self) -> str:
        perfil = 'Administrador' if self.isAdmin else 'Funcionário'
        return f'{self.nome} ({self.email}) - {perfil}'

    def save(self, *args, **kwargs):
        # Mantém as flags internas do Django coerentes com o nível de acesso.
        if not kwargs.get('update_fields'):
            self.is_staff = bool(self.isAdmin)
            self.is_superuser = bool(self.isAdmin)
        super().save(*args, **kwargs)

    @property
    def perfil(self) -> str:
        """Retorna a descrição textual do perfil conforme Documento de Visão."""
        return 'Administrador' if self.isAdmin else 'Funcionário'

    # Métodos do Diagrama de Classes (doc-modelos.md)
    def solicitarAutorizacaoAcesso(self) -> bool:
        """
        Indica se o perfil pode acessar o sistema.

        A verificação de credenciais (e-mail/senha) é responsabilidade exclusiva
        do Supabase Auth; aqui validamos apenas o vínculo de identidade e o status.
        Corresponde ao método +solicitarAutorizacaoAcesso(): boolean do Modelo Conceitual.
        """
        return bool(self.is_active and self.supabase_user_id)

    def manterFuncionario(
        self,
        nome: str = None,
        email: str = None,
        isAdmin: bool = None,
        is_active: bool = None,
    ) -> 'Funcionario':
        """
        Atualiza os dados do perfil funcional do funcionário.

        Não altera credenciais: e-mail de login e senha são gerenciados pelo
        Supabase Auth.
        Corresponde ao método +manterFuncionario(funcionario: Funcionario): void
        do Modelo Conceitual.
        """
        if nome is not None:
            self.nome = nome
        if email is not None:
            self.email = self.__class__.objects.normalize_email(email)
        if isAdmin is not None:
            self.isAdmin = isAdmin
        if is_active is not None:
            self.is_active = is_active
        self.save()
        return self
