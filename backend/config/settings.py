"""
Configurações do Django para o Sistema de Controle de Fluxo (Workflow) de SPEDs - Intech Sistemas.
Integrado com Supabase (Banco de Dados PostgreSQL + Autenticação exclusiva via Supabase Auth).
"""

import os
import socket
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-intech-sistemas-sped-workflow-dev-key',
)

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver').split(',')
    if host.strip()
]

# Aplicações instaladas (separadas por domínio conforme Documento de Modelos)
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Bibliotecas de terceiros
    'corsheaders',
    'rest_framework',
    'django_filters',
    'drf_spectacular',
    # Apps do domínio do projeto
    'funcionarios.apps.FuncionariosConfig',
    'clientes.apps.ClientesConfig',
    'speds.apps.SpedsConfig',
    'auditoria.apps.AuditoriaConfig',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ==============================================================================
# BANCO DE DADOS E SUPABASE (PostgreSQL na nuvem + Autenticação via Supabase Auth)
# ==============================================================================
DATABASE_URL = os.getenv('DATABASE_URL', '').strip()
IS_POSTGRES = DATABASE_URL.startswith(('postgres://', 'postgresql://'))


def _porta_postgres_acessivel(db_url: str) -> bool:
    """
    Verifica rapidamente (1.5s) se a rede atual permite saída na porta 5432/6543.
    """
    try:
        parsed = urlparse(db_url)
        host = parsed.hostname
        port = parsed.port or 5432
        if not host or '[' in db_url:
            return False
        with socket.create_connection((host, port), timeout=1.5):
            return True
    except OSError:
        return False


if IS_POSTGRES and _porta_postgres_acessivel(DATABASE_URL):
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0 if ':6543/' in DATABASE_URL else 600,
            ssl_require='supabase.co' in DATABASE_URL,
        )
    }
    DATABASES['default'].setdefault('OPTIONS', {})['connect_timeout'] = 5
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Credenciais do Supabase Auth / API (A service_role permanece estritamente no backend)
SUPABASE_URL = os.getenv('SUPABASE_URL', '').strip()
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY', '').strip()
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY', '').strip()
SUPABASE_JWT_SECRET = os.getenv('SUPABASE_JWT_SECRET', '').strip()

# Modelo customizado de Usuário / Funcionário (US01 / Tabela FUNCIONARIO)
# O modelo não possui senha: identidade e credenciais pertencem ao Supabase Auth.
AUTH_USER_MODEL = 'funcionarios.Funcionario'

# Internacionalização
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Fortaleza'
USE_I18N = True
USE_TZ = True

# Arquivos estáticos e de mídia (Uploads de arquivos .rar do SPED - RF03.04)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuração do Django REST Framework:
# Autenticação única e exclusiva via Supabase Auth (sem emissão/renovação legada de JWT pelo Django)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'funcionarios.authentication.SupabaseJWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Documentação OpenAPI / Swagger
SPECTACULAR_SETTINGS = {
    'TITLE': 'Intech Sistemas - API de Controle de Fluxo de SPEDs',
    'DESCRIPTION': (
        'Sistema de controle de fluxo (workflow) para automatizar e organizar '
        'o processo de geração mensal de SPEDs da Intech Sistemas (Django + Supabase Auth).'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS (Integração com o Front-end React + TypeScript)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000',
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

# Configurações de E-mail (RF04.01 / RNF007)
EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend',
)
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@intechsistemas.com.br')
EMAIL_MAX_RETRIES = int(os.getenv('EMAIL_MAX_RETRIES', '3'))

# Configurações de API Externa de CNPJ (RF02.01 / RNF002)
CNPJ_API_URL = os.getenv('CNPJ_API_URL', 'https://brasilapi.com.br/api/cnpj/v1')
CNPJ_API_TIMEOUT = int(os.getenv('CNPJ_API_TIMEOUT', '4'))

# Configurações de API de Mensageria WhatsApp (RF04.02 / RNF006)
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL', '')
WHATSAPP_API_TOKEN = os.getenv('WHATSAPP_API_TOKEN', '')
WHATSAPP_MAX_RETRIES = int(os.getenv('WHATSAPP_MAX_RETRIES', '3'))
