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

    clase_serializador = EstructuraSerializer

    def obtener_busqueda(self, *args, **kwargs):
        busqueda =  {
            "size": 10000,
            "query": {
                "bool": {
                    "must": [
                    ]
                }
            }
        }
    

        if "observatorio" in kwargs and kwargs.get("observatorio") is not None:
            busqueda["query"]["bool"]["must"].append(
                    {
                        "term" : {"observatorio.keyword" :kwargs.get("observatorio") }
                    }
                )

        return busqueda

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
        observatorio = request.query_params.get("observatorio")
        cliente = self.get_elasticsearch_client()
        
        resultado_busqueda = cliente.search(
            index=self._nombre_indice,  #TODO manejar los índices con base en la sesión
            body=self.obtener_busqueda( observatorio =  observatorio)
        )

        resultados = [ 
            self.elastic_model(**{**item["_source"], "id": item["_id"]}).obtener_documento( imagen_en_base64 = True )      
            for item in resultado_busqueda['hits']['hits']
        ]

        return Response(resultados)
    
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
     
    