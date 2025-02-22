from django.urls import path
from .views import DatosViewSet

urlpatterns = [
    # Endpoint para listar o crear datos dentro de una estructura
    path('datos/<str:estructura_id>/', DatosViewSet.as_view({'get': 'list', 'post': 'create'})),

    # Endpoint para recuperar, actualizar o eliminar un dato específico dentro de una estructura
    path('datos/<str:estructura_id>/<str:pk>/', DatosViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]
