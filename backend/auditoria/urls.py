"""Rotas da API para Rastreabilidade (US05) e Dashboard Gerencial (US06)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import DashboardGerencialAPIView, LogRastreabilidadeViewSet

router = DefaultRouter()
router.register(r'logs', LogRastreabilidadeViewSet, basename='log-rastreabilidade')

urlpatterns = [
    path('dashboard/', DashboardGerencialAPIView.as_view(), name='dashboard-gerencial'),
    path('', include(router.urls)),
]
