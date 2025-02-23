from django.shortcuts import render
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from rest_framework.response import Response
from rest_framework import status
# Create your views here.

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class DatosViewSet(ElasticsearchViewSet):

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = kwargs.get("estructura_id").lower()

    @swagger_auto_schema(
        operation_description="Crea una nueva estructura de campos",
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Crea una nueva estructura de campos",
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        return super().destroy(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Crea una nueva estructura de campos",
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        
        try:
            resultado = cliente.get(index=self._nombre_indice, id=pk)
            return Response({**resultado['_source'], "id": resultado['_id']})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Crea una nueva estructura de campos",
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def create(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        datos = request.data

        try:
            respuesta = cliente.index(index=self._nombre_indice, body=datos)
            return Response(respuesta, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Crea una nueva estructura de campos",
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def update(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        datos = request.data

        try:
            respuesta = cliente.update(
                index=self._nombre_indice,
                id=pk,
                body={"doc": datos}
            )
            return Response(respuesta)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)