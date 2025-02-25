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
from .serializers import EstructuraSerializer

class EstructuraCamposViewSet(ElasticsearchViewSet): 
    elastic_model = EstructuraCamposModelo
    procesador = ProcesadorRecursos()
    cliente =  get_elasticsearch_client()

    

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = self.elastic_model.obtener_indice()

        if not self.cliente.indices.exists(index=self._nombre_indice):  
            self.cliente.indices.create(index=self._nombre_indice)

    
    @swagger_auto_schema(
        operation_description="Crea una nueva estructura de campos",
        request_body=EstructuraSerializer,
        responses={
            201: EstructuraSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Estructura de campos"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    

    @swagger_auto_schema(
        operation_description="Obtiene una estructura de campos",
        responses={
            201: EstructuraSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Estructura de campos"]
    )
    def retrieve(self, request, pk=None, *args, **kwargs):
        return super().retrieve(request, pk, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Obtiene una estructura en especifico",
        responses={
            201: EstructuraSerializer(many = True),
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Estructura de campos"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Inactiva una estructura de campos",
        request_body=EstructuraSerializer,
        responses={
            201: {},
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Estructura de campos"]
    )
    def destroy(self, request, pk=None, *args, **kwargs):
        return super().destroy(request, pk, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Actualiza una estructura de campos",
        request_body=EstructuraSerializer,
        responses={
            201: EstructuraSerializer,
            400: openapi.Response(description="Solicitud inválida"),
        },
        tags=["Estructura de campos"]
    )
    def update(self, request, pk=None, *args, **kwargs):
        return super().update(request, pk, *args, **kwargs)





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
        tags=["Estructura de campos"]
    )

    def get(self, request, *args, **kwargs):          
          return Response(ELASTICSEARCH_CAMPOS, status=status.HTTP_200_OK)
     
    