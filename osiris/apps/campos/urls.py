from django.urls import path

from .views import (
    TiposCamposVista,
    EstructuraCamposViewSet,
    ArchivosDatosView,
    DatosEstructuraDocumentoView,
)


estructura_lista = EstructuraCamposViewSet.as_view({
    "get": "list",
    "post": "create",
})

estructura_detalle = EstructuraCamposViewSet.as_view({
    "get": "retrieve",
    "put": "update",
    "patch": "partial_update",
    "delete": "destroy",
})


urlpatterns = [
    path(
        "tipos",
        TiposCamposVista.as_view(),
        name="tipos-campos"
    ),

    path(
        "estructuras/",
        estructura_lista,
        name="estructura-lista"
    ),

    path(
        "estructuras/<str:pk>/",
        estructura_detalle,
        name="estructura-detalle"
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
]
