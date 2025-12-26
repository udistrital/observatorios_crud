from django.urls import path
from .views import DatosViewSet, DatosArchivoViewSet

urlpatterns = [
    path('datos/<str:estructura_id>/', DatosViewSet.as_view({'get': 'list', 'post': 'create', 'delete': 'destroy'})),
    path('datos/<str:estructura_id>/<str:pk>/', DatosViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
    path('datosArchivo/<str:id_archivos>/',DatosArchivoViewSet.as_view({'get': 'list', 'post': 'create', 'delete': 'destroy'})),
    path('datosArchivo/<str:id_archivos>/<str:pk>/',DatosArchivoViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'})),
]
