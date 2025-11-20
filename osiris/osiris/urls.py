from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from django.conf import settings

schema_view = get_schema_view(
    openapi.Info(
        title="Observatorios CRUD",
        default_version="v1",
        description="Documentación de la API de observatorios de la universidad Distrital Francisco Jose de Caldas",
        license=openapi.License(name="Licencia MIT"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("admin/", admin.site.urls),

    ### Documentación ###
    path("documentacion/swagger/", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    path("documentacion/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    re_path(r"documentacion/^swagger(?P<format>\.json|\.yaml)$", schema_view.without_ui(cache_timeout=0), name="schema-json"),

    ### Healthcheck ###
    path("/", include("apps.utils.urls")),
    
    ### Datos (Estructuras) ###
    path("api/<str:version>/", include("apps.datos.urls")),

    ### Observatorios ###
    path("api/<str:version>/", include("apps.observatorios.urls")),

    ### Campos ###
    path("api/<str:version>/campos/", include("apps.campos.urls")),

    ### Dashboards ###
    path("api/<str:version>/", include("apps.dashboards.urls")),

    ### Graficos ###
    path("api/<str:version>/constructor_graficos/", include("apps.graficos.urls")),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



    
    
