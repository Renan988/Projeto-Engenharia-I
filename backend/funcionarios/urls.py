"""Rotas da API para Funcionários (US01) com autenticação via Supabase Auth."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import FuncionarioViewSet, LoginAPIView

router = DefaultRouter()
router.register(r'', FuncionarioViewSet, basename='funcionario')

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='funcionario-login'),
    path('', include(router.urls)),
]
