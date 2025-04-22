from django.urls import path
from .views import (VistaTipoOperaciones, 
                    VistaCamposSugeridos, 
                    VistaObtenerConfiguracionGrafico,
                    VistaProbarConfiguracionGrafico,
                    VistaObtenerDatosGrafico)
urlpatterns = [
    path('tipo_operaciones/', VistaTipoOperaciones.as_view(), name='tipo_operaciones'),
    path('campos_sugeridos/', VistaCamposSugeridos.as_view(), name='campos_sugeridos'),
    path('configuracion_grafico/', VistaObtenerConfiguracionGrafico.as_view(), name='configuracion_grafico'), 
    path('probar_configuracion/', VistaProbarConfiguracionGrafico.as_view(), name='probar_configuracion_grafico'),
    # path('datos/', VistaObtenerDatosGrafico.as_view(), name='datos_grafico'),
]

