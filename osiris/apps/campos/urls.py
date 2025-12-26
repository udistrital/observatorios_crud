from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import TiposCamposVista, EstructuraCamposViewSet, ArchivosDatosView


router = DefaultRouter()
router.register(r'estructuras', EstructuraCamposViewSet, basename='estrutura')


urlpatterns = [
    path("tipos", TiposCamposVista.as_view()),
    path("archivos/<str:pk>/<str:id_documento>/", ArchivosDatosView.as_view()), # DELETE
    path("archivos/<str:pk>/", ArchivosDatosView.as_view()), # GET y POST
] + router.urls