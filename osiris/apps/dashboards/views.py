from django.shortcuts import render
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from .serializers import DashboardSerializer, DashboardUpdateSerializer, GraficoSerializer, GraficoUpdateSerializer
from apps.elasticsearch_utils.utils import get_elasticsearch_client
from elasticsearch import NotFoundError

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from rest_framework.response import Response
from .models import Dashboard, Grafico

class DashboardViewSet(ElasticsearchViewSet):
    elastic_model = Dashboard
    clase_serializador = DashboardSerializer
    cliente = get_elasticsearch_client()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = self.elastic_model.indice

        if not self.cliente.indices.exists(index=self._nombre_indice):
            response = self.cliente.indices.create(index=self._nombre_indice)

    def obtener_clase_serializador(self):

        if self.action == "update": return DashboardUpdateSerializer

        return super().obtener_clase_serializador()
    


class GraficoViewSet(ElasticsearchViewSet):
    elastic_model = Grafico
    clase_serializador = GraficoSerializer
    cliente = get_elasticsearch_client()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = kwargs.get("dashboard_id").lower() + "_dashboard"
        self.elastic_model.indice = self._nombre_indice
        try:
            dashboard = Dashboard().get(self.cliente, Dashboard.indice, kwargs.get("dashboard_id") )
        except NotFoundError:
            self.errors = {"dashboard_id" : ["Dashboard no encontrado"]}

    def obtener_clase_serializador(self):
        if self.action == "update": return GraficoUpdateSerializer
        return super().obtener_clase_serializador()
    
    @swagger_auto_schema(
        operation_description="Crea un nuevo Grafico asociado a un dashboard",
        request_body=GraficoSerializer,
        responses={
            201: GraficoSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Graficos"]
    )
    def create(self, request, *args, **kwargs):
        if hasattr(self, "errors"):
            return Response(self.errors, status=400)
        
        return super().create(request, *args, **kwargs)
    

    @swagger_auto_schema(
        operation_description="Obtiene un grafico en especifico",
        responses={
            201: GraficoSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Graficos"]
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        if hasattr(self, "errors"):
            return Response(self.errors, status=400)
        return super().retrieve(request, pk, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Obtiene un observatorio en especifico",
        responses={
            201: GraficoSerializer(many = True),
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Graficos"]
    )
    def list(self, request, *args, **kwargs):
        if hasattr(self, "errors"):
            return Response(self.errors, status=400)
        
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Inactiva un observatorio",
        request_body=GraficoSerializer,
        responses={
            201: {},
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Graficos"]
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        if hasattr(self, "errors"):
            return Response(self.errors, status=400)
        
        return super().destroy(request, pk, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza un observatorio",
        request_body=GraficoSerializer,
        responses={
            201: GraficoSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Graficos"]
    )
    def update(self, request, pk=None, *args, **kwargs):
        if hasattr(self, "errors"):
            return Response(self.errors, status=400)
        
        return super().update(request, pk, *args, **kwargs)


