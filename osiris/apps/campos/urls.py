from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    TiposCamposVista,
    EstructuraCamposViewSet,
    ArchivosDatosView,
    DatosEstructuraDocumentoView,
)

router = DefaultRouter()
router.register(r"estructuras",EstructuraCamposViewSet,basename="estructura")

urlpatterns = [
    path(
        "tipos",
        TiposCamposVista.as_view(),
        name="tipos-campos"
    ),

    path(
        "datos/<str:pk>/",
        DatosEstructuraDocumentoView.as_view(),
        name="datos-estructura"
    ),
    path(
        "datos/<str:pk>/<str:id_documento>/",
        DatosEstructuraDocumentoView.as_view(),
        name="datos-estructura-detalle"
    ),

    path(
        "archivos/<str:pk>/",
        ArchivosDatosView.as_view(),
        name="archivos-estructura"
    ),
    path(
        "archivos/<str:pk>/<str:id_documento>/",
        ArchivosDatosView.as_view(),
        name="archivos-estructura-detalle"
    ),
] + router.urls
