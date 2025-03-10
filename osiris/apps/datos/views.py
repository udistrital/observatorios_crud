from django.shortcuts import render
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from rest_framework.response import Response
from rest_framework import status
from elasticsearch import helpers

import csv
import json
import io

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

    #TODO: Manejar el size de manera dinamca
    def obtener_busqueda(self):
        return {
            "size" : 10000,
            "query": {
                "bool": {
                "should": [
                    {
                    "bool": {
                        "must_not": {
                        "exists": { "field": "_activo" }
                        }
                    }
                    },
                    {
                    "term": { "_activo": True }
                    }
                ],
                "minimum_should_match": 1
                }
            }
        }

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
        if not pk:
            update_query = {
                "script": {
                    "source": "ctx._source['_activo'] = false",  # Reemplaza con el campo y valor deseado
                    "lang": "painless"
                }
            }
            cliente = self.get_elasticsearch_client()
            response = cliente.update_by_query(index=self._nombre_indice, body=update_query)

            return Response(response)
            
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

            # Verificar el separador
            archivo.seek(0)  # Reiniciar el puntero del archivo
            sniffer = csv.Sniffer()
            primera_linea = archivo.readline().decode('latin-1')

            if not sniffer.has_header(primera_linea):
                return Response({"message": "El archivo CSV no tiene un encabezado válido"}, status=status.HTTP_400_BAD_REQUEST)

            delimitador_detectado = sniffer.sniff(primera_linea).delimiter
            if delimitador_detectado != ',':
                return Response({"message": f"El archivo CSV tiene un separador inválido: '{delimitador_detectado}'. Se espera ','"},
                                status=status.HTTP_400_BAD_REQUEST)
            

            print(type(archivo))
            archivo.seek(0)  # Reiniciar el puntero después de la detección






            csv_buffer = io.StringIO(archivo.read().decode('latin-1'))
            datos_procesados = self.procesador.procesar_csv(csv_buffer)
            resultados = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura)) 
            resultados, errors = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura))  
            
            return Response({"message" : f"Se guardaron un total de {resultados}" , "errores" : errors})

        if formato == "JSON":
            #TODO: agregar campo origin
            archivo = request.FILES['archivo']
            try:
                contenido = archivo.read().decode('latin-1')  
                datos_procesados = json.loads(contenido)  # Cargar el JSON
                if not isinstance(datos_procesados, list):  
                    return Response({"error": "El archivo JSON debe contener una lista de objetos"}, status=400)

                resultados, errors = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura))  
                return Response({"message": f"Se guardaron un total de {resultados}", "errores": errors})
            
            except json.JSONDecodeError:
                return Response({"error": "El archivo no es un JSON válido"}, status=400)
        
        if formato == "FORM":
            
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