from apps.elasticsearch_utils.views import ElasticsearchViewSet

from .serializers import ObservatorioSerializer, ObservatorioUPdateSerializer
from .models import ObservatorioModelo

from osiris.settings import ELASTICSEARCH_MAIN_INDEX
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class ObservatorioViewSet(ElasticsearchViewSet):
    
    elastic_model = ObservatorioModelo
    clase_serializador = ObservatorioSerializer

    def obtener_clase_serializador(self):
        if self.action == "update":
            return ObservatorioUPdateSerializer
        return self.clase_serializador

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = ELASTICSEARCH_MAIN_INDEX + "_observatorios"

    @swagger_auto_schema(
        operation_description="Crea un nuevo observatorio",
        request_body=ObservatorioSerializer,
        responses={
            201: ObservatorioSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Observatorios"]
    )
    def create(self, request, *args, **kwargs):

        client = self.get_elasticsearch_client()

        if not client.indices.exists(index=self._nombre_indice):  
            client.indices.create(index=self._nombre_indice)
        return super().create(request, *args, **kwargs)
    

    @swagger_auto_schema(
        operation_description="Obtiene un observatorio en especifico",
        responses={
            201: ObservatorioSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Observatorios"]
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        return super().retrieve(request, pk, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Obtiene un observatorio en especifico",
        responses={
            201: ObservatorioSerializer(many = True),
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Observatorios"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Inactiva un observatorio",
        request_body=ObservatorioSerializer,
        responses={
            201: {},
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Observatorios"]
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        return super().destroy(request, pk, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza un observatorio",
        request_body=ObservatorioSerializer,
        responses={
            201: ObservatorioSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Observatorios"]
    )
    def update(self, request, pk=None, *args, **kwargs):
        return super().update(request, pk, *args, **kwargs)