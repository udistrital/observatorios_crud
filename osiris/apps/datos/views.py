from django.shortcuts import render
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from rest_framework.response import Response
from rest_framework import status
from elasticsearch import helpers

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from osiris.settings import ELASTICSEARCH_MAIN_INDEX
from apps.utils.utils import ProcesadorRecursos

from .serializers import DatosSerializers
from apps.campos.models import EstructuraCamposModelo
from rest_framework.pagination import PageNumberPagination

class CustomPagination(PageNumberPagination):
    page_size = 5  # Valor por defecto
    page_size_query_param = 'page_size'  # Permite cambiar el tamaño con `?page_size=10`
    max_page_size = 500  # Límite máximo permitido


class DatosViewSet(ElasticsearchViewSet):

    procesador = ProcesadorRecursos()
    pagination_class = CustomPagination


    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = kwargs.get("estructura_id").lower()

    @swagger_auto_schema(
        operation_description="Lista los datos de una estructura de datos",
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def list(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        paginador = self.pagination_class()

        resultado_busqueda = cliente.search(
            index=self._nombre_indice,  #TODO manejar los índices con base en la sesión
            body=self.obtener_busqueda()
        )



        #TODO Serializar la respuesta de Elasticsearch
        resultados = [ {**item["_source"], "id" : item["_id"] } for item in resultado_busqueda['hits']['hits']]
        resutados_paginados = paginador.paginate_queryset(resultados, request)

        return paginador.get_paginated_response(resutados_paginados)
    
    @swagger_auto_schema(
        operation_description="Inactiva un campo en la estructura de campos",
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        return super().destroy(request, pk, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Obtiene un item en especifico de la estructura de datos",
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
        operation_description="Crea un dato dentro de una estructura o inserta masivamente un conjunto de datos ",
        request_body=DatosSerializers,
        responses={
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Datos"]
    )
    def create(self, request, *args, **kwargs):

        self.cliente = self.get_elasticsearch_client()
        datos_solicitud =  request.data
        formato =   datos_solicitud.get("formato", "FORM")
        estructura_pk =  kwargs.get("estructura_id")
        estructura =  EstructuraCamposModelo().get(self.cliente,EstructuraCamposModelo.obtener_indice() , estructura_pk)
        indice_id_estructura = estructura.id.obtener_valor().lower()



        if formato == "CSV":
            #TODO: agregar campo origin
            archivo = request.FILES['archivo']
            datos_procesados = self.procesador.procesar_csv(archivo)
            resultados = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura)) 
            resultados, errors = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura))  
            return Response({"message" : f"Se guardaron un total de {resultados}" , "errores" : errors})

        if formato == "JSON":
            #TODO: agregar campo origin
            archivo = request.FILES['archivo']
            datos_procesados = self.procesador.procesar_json(archivo)  
            resultados, errors = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura))  
            return Response({"message" : f"Se guardaron un total de {resultados}" , "errores" : errors})
        
        if formato == "FORM":
            
            datos_solicitud["origin"] = "FORM"
            respuesta =  self.cliente.index(
                index = estructura.id.obtener_valor().lower(),
                document= datos_solicitud
            )            
            return Response(respuesta)


        return Response({"status" :  "not supported yet"})
    



    @swagger_auto_schema(
        operation_description="Actualiza un dato referente a una estructura de datos",
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