from django.urls import path
from .views import VistaTipoOperaciones, VistaCamposSugeridos, VistaObtenerConfiguracionGrafico
urlpatterns = [
    path('tipo_operaciones/', VistaTipoOperaciones.as_view(), name='tipo_operaciones'),
    path('campos_sugeridos/', VistaCamposSugeridos.as_view(), name='campos_sugeridos'),
    path('configuracion_grafico/', VistaObtenerConfiguracionGrafico.as_view(), name='configuracion_grafico')
]

