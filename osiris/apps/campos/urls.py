from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TiposCamposVista, EstructuraCamposViewSet


router = DefaultRouter()
router.register(r'estructuras', EstructuraCamposViewSet, basename='estrutura')


urlpatterns = [
    path("tipos", TiposCamposVista.as_view()),
] + router.urls