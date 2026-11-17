"""Rotas da API para Funcionários e Autenticação (US01)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import FuncionarioViewSet, LoginAPIView

router = DefaultRouter()
router.register(r'', FuncionarioViewSet, basename='funcionario')

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='funcionario-login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('', include(router.urls)),
]
