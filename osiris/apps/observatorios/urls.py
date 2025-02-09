from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ObservatorioViewSet

router = DefaultRouter()
router.register(r'observatorios', ObservatorioViewSet, basename='Observatorio')

urlpatterns = [
] + router.urls