"""
Modelo de dados da entidade Funcionario (Tabela FUNCIONARIO).
Referência: docs/doc-modelos.md e docs/doc-visao.md (US01 - Manter Usuário).
"""

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class FuncionarioManager(BaseUserManager):
    """Gerenciador customizado para criação de Funcionários e Administradores."""

    def create_user(self, email: str, nome: str, senha: str = None, **extra_fields):
        if not email:
            raise ValueError('O campo de e-mail é obrigatório.')
        if not nome:
            raise ValueError('O campo nome é obrigatório.')

        email = self.normalize_email(email)
        is_admin = extra_fields.pop('isAdmin', False)
        extra_fields.setdefault('is_staff', is_admin)
        extra_fields.setdefault('is_superuser', is_admin)

        funcionario = self.model(
            email=email,
            nome=nome,
            isAdmin=is_admin,
            **extra_fields,
        )
        if senha:
            funcionario.set_password(senha)
        else:
            password = extra_fields.get('password')
            if password:
                funcionario.set_password(password)
            else:
                funcionario.set_unusable_password()

        funcionario.save(using=self._db)
        return funcionario

    def create_superuser(self, email: str, nome: str, password: str = None, **extra_fields):
        extra_fields['isAdmin'] = True
        extra_fields['is_staff'] = True
        extra_fields['is_superuser'] = True
        return self.create_user(
            email=email,
            nome=nome,
            senha=password,
            **extra_fields,
        )


class Funcionario(AbstractBaseUser, PermissionsMixin):
    """
    Entidade Funcionario conforme especificada no Documento de Modelos:
    - idFuncionario: SERIAL PK / Identity
    - nome: VARCHAR(150) Not Null
    - email: VARCHAR(150) Unique / Not Null
    - senha: VARCHAR(255) Not Null (criptografada)
    - isAdmin: BOOLEAN Not Null (define nível de acesso Administrador vs Funcionário)
    """

    idFuncionario = models.AutoField(
        primary_key=True,
        db_column='idFuncionario',
        verbose_name='ID do Funcionário',
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
    password = models.CharField(
        max_length=255,
        db_column='senha',
        verbose_name='Senha Criptografada',
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
        # Sincroniza flags do Django com isAdmin do modelo conceitual
        self.is_staff = bool(self.isAdmin)
        self.is_superuser = bool(self.isAdmin)
        super().save(*args, **kwargs)

    @property
    def senha(self) -> str:
        """Alias para compatibilidade direta com o diagrama de classes (atributo senha)."""
        return self.password

    @property
    def perfil(self) -> str:
        """Retorna a descrição textual do perfil conforme Documento de Visão."""
        return 'Administrador' if self.isAdmin else 'Funcionário'

    # Métodos do Diagrama de Classes (doc-modelos.md)
    def solicitarAutorizacaoAcesso(self, senha_texto: str) -> bool:
        """
        Valida as credenciais do funcionário e verifica se está autorizado a acessar o sistema.
        Corresponde ao método +solicitarAutorizacaoAcesso(): boolean do Modelo Conceitual.
        """
        return bool(self.is_active and self.check_password(senha_texto))

    def manterFuncionario(
        self,
        nome: str = None,
        email: str = None,
        senha: str = None,
        isAdmin: bool = None,
    ) -> 'Funcionario':
        """
        Atualiza os atributos do funcionário mantendo a senha criptografada.
        Corresponde ao método +manterFuncionario(funcionario: Funcionario): void do Modelo Conceitual.
        """
        if nome is not None:
            self.nome = nome
        if email is not None:
            self.email = self.__class__.objects.normalize_email(email)
        if isAdmin is not None:
            self.isAdmin = isAdmin
        if senha:
            self.set_password(senha)
        self.save()
        return self
