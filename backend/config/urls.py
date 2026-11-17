"""
Configuração de rotas principais (URLs) da API do Sistema de Controle de Fluxo de SPEDs.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)


def api_root(request):
    """Endpoint raiz de verificação de disponibilidade (Health Check - RNF003)."""
    return JsonResponse(
        {
            'sistema': 'Intech Sistemas - Controle de Fluxo de SPEDs',
            'status': 'online',
            'versao': '1.0.0',
            'documentacao': {
                'swagger': '/api/docs/',
                'redoc': '/api/redoc/',
                'schema': '/api/schema/',
            },
            'endpoints': {
                'funcionarios_e_auth': '/api/funcionarios/',
                'clientes': '/api/clientes/',
                'speds': '/api/speds/',
                'auditoria_e_dashboard': '/api/auditoria/',
            },
        }
    )


urlpatterns = [
    path('', api_root, name='api-root'),
    path('admin/', admin.site.urls),
    # Documentação OpenAPI / Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
    # Rotas dos Módulos de Domínio
    path('api/funcionarios/', include('funcionarios.urls')),
    path('api/clientes/', include('clientes.urls')),
    path('api/speds/', include('speds.urls')),
    path('api/auditoria/', include('auditoria.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
