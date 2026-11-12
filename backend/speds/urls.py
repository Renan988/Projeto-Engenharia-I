"""Rotas da API para o módulo de SPEDs (US03 e US04)."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SpedViewSet

router = DefaultRouter()
router.register(r'', SpedViewSet, basename='sped')

urlpatterns = [
    path('', include(router.urls)),
]
