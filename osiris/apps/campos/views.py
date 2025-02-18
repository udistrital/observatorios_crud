from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from elasticsearch import Elasticsearch, helpers
import pandas as pd

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

### Modulos Externos ###
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from apps.elasticsearch_utils.utils import get_elasticsearch_client
from apps.utils.utils import ProcesadorRecursos

### Modulos Internos ###
from .utils import ELASTICSEARCH_CAMPOS
from .models import EstructuraCamposModelo

class EstructuraCamposViewSet(ElasticsearchViewSet): 
    elastic_model = EstructuraCamposModelo
    procesador = ProcesadorRecursos()
    cliente =  get_elasticsearch_client()

    @action(detail=True, methods=['post'])
    def insertar(self, request, pk=None, **kwargs):
        
        datos_solicitud =  request.data
        formato =   datos_solicitud.get("formato", "FORM")
        estructura =  self.elastic_model().get(self.cliente, self._nombre_indice, pk)
        indice_id_estructura = estructura.id.obtener_valor().lower()

        if formato == "CSV":
            #TODO: agregar campo origin
            archivo = request.FILES['archivo']
            datos_procesados = self.procesador.procesar_csv(archivo)
            resultados = helpers.bulk(self.cliente, self.elastic_model.generar_datos_masivos(datos_procesados, indice_id_estructura)) 
            resultados, errors = helpers.bulk(self.cliente, self.elastic_model.generar_datos_masivos(datos_procesados, indice_id_estructura))  
            return Response({"message" : f"Se guardaron un total de {resultados}" , "errores" : errors})

        if formato == "JSON":
            #TODO: agregar campo origin
            archivo = request.FILES['archivo']
            datos_procesados = self.procesador.procesar_json(archivo)  
            resultados, errors = helpers.bulk(self.cliente, self.elastic_model.generar_datos_masivos(datos_procesados, indice_id_estructura))  
            return Response({"message" : f"Se guardaron un total de {resultados}" , "errores" : errors})
        
        if formato == "FORM":
            
            datos_solicitud["origin"] = "FORM"
            respuesta =  self.cliente.index(
                index = estructura.id.obtener_valor().lower(),
                document= datos_solicitud
            )            
            return Response(respuesta)


        return Response({"status" :  "not supported yet"})

     

class TiposCamposVista(APIView):
    @swagger_auto_schema(
        operation_summary="Obtener los campos de Elasticsearch",
        operation_description="Devuelve un diccionario con los tipos de campos utilizados en Elasticsearch.",
        responses={200: openapi.Response(
            description="Lista de tipos de campos en Elasticsearch",
            examples={
                "application/json": ELASTICSEARCH_CAMPOS
            }
        )},
        tags=["Campos"]
    )

    def get(self, request, *args, **kwargs):          
          return Response(ELASTICSEARCH_CAMPOS, status=status.HTTP_200_OK)
     
    