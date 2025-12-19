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
from .serializers import EstructuraSerializer, EstructuraUpdateSerializer

class EstructuraCamposViewSet(ElasticsearchViewSet): 
    elastic_model = EstructuraCamposModelo
    procesador = ProcesadorRecursos()
    cliente =  get_elasticsearch_client()

    clase_serializador = EstructuraSerializer

    def obtener_clase_serializador(self):
        if self.action == "update":
            return EstructuraUpdateSerializer
        
        return super().obtener_clase_serializador()

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

        for item in resultado_busqueda["hits"]["hits"]:
            for campo in item["_source"]["mapeo"]:
                if "valor_anterior" not in campo:
                    campo["valor_anterior"] = campo.get("nombre")

            for campo in item["_source"].get("mapeo_archivos", []):
                if "valor_anterior" not in campo:
                    campo["valor_anterior"] = campo.get("nombre")

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

class ArchivosDatosView(APIView):

    @swagger_auto_schema(
        operation_description="Obtiene los datos asociados al mapeo_archivos de una estructura",
        responses={200: openapi.Response("Datos de archivos obtenidos correctamente")},
        tags=["Estructura de campos"]
    )
    def get(self, request, pk, *args, **kwargs):

        cliente = get_elasticsearch_client()

        # 1. Buscar estructura por id_archivos (NO por su _id)
        resultado = cliente.search(
            index=EstructuraCamposModelo.indice,
            body={
                "query": {
                    "term": {
                        "id_archivos.keyword": pk
                    }
                }
            }
        )

        if not resultado["hits"]["hits"]:
            return Response(
                {"detalle": "No existe estructura con ese id_archivos."},
                status=404
            )

        hit = resultado["hits"]["hits"][0]
        estructura = EstructuraCamposModelo(**{**hit["_source"], "id": hit["_id"]})

        # 2. Obtener mapeo_archivos
        mapeo_archivos = estructura.mapeo_archivos.obtener_valor() or []

        if not mapeo_archivos:
            return Response(
                {"detalle": "La estructura no tiene mapeo_archivos definido"},
                status=200
            )

        # 3. Consultar documentos del índice de archivos
        index_archivos = estructura.indice_id_archivos

        resultado_archivos = cliente.search(
            index=index_archivos,
            body={"query": {"match_all": {}}},
            size=10000
        )

        documentos = []

        for h in resultado_archivos["hits"]["hits"]:
            doc = h["_source"]
            fila = {"id": h["_id"]}  # IMPORTANTE: agregar id al registro

            for campo in mapeo_archivos:
                nombre = campo.get("nombre")
                fila[nombre] = doc.get(nombre)

            documentos.append(fila)

        # ===========================
        # PAGINACIÓN MANUAL
        # ===========================
        page = int(request.GET.get("page", 1))
        page_size = int(request.GET.get("page_size", 10))

        total = len(documentos)
        inicio = (page - 1) * page_size
        fin = inicio + page_size

        paginados = documentos[inicio:fin]

        next_page = None
        previous_page = None

        if fin < total:
            next_page = page + 1

        if inicio > 0:
            previous_page = page - 1

        return Response({
            "count": total,
            "next": next_page,
            "previous": previous_page,
            "results": paginados
        }, status=200)


    def post(self, request, pk, *args, **kwargs):
        cliente = get_elasticsearch_client()

        # 1. Buscar estructura por id_archivos (NO por su _id)
        resultado = cliente.search(
            index=EstructuraCamposModelo.indice,
            body={
                "query": {
                    "term": {
                        "id_archivos.keyword": pk
                    }
                }
            }
        )

        if not resultado["hits"]["hits"]:
            return Response(
                {"detalle": "No existe estructura con ese id_archivos."},
                status=404
            )

        hit = resultado["hits"]["hits"][0]
        estructura = EstructuraCamposModelo(**{**hit["_source"], "id": hit["_id"]})

        # 2. Obtener índice donde se guardan los archivos
        index_archivos = estructura.indice_id_archivos

        # 3. Obtener mapeo_archivos
        mapeo_archivos = estructura.mapeo_archivos.obtener_valor() or []

        # 4. Construir documento desde los campos
        nuevo_doc = {}

        for campo in mapeo_archivos:
            nombre = campo.get("nombre")
            nuevo_doc[nombre] = request.data.get(nombre)

        # 5. Insertar documento en Elasticsearch
        resp = cliente.index(index=index_archivos, document=nuevo_doc)

        return Response(resp, status=status.HTTP_201_CREATED)

    def delete(self, request, pk, id_documento=None, *args, **kwargs):
        cliente = get_elasticsearch_client()

        # 1. Buscar estructura según id_archivos = pk
        resultado = cliente.search(
            index=EstructuraCamposModelo.indice,
            body={
                "query": {
                    "term": {
                        "id_archivos.keyword": pk
                    }
                }
            }
        )

        if not resultado["hits"]["hits"]:
            return Response(
                {"detalle": "No existe estructura con ese id_archivos."},
                status=404
            )

        hit = resultado["hits"]["hits"][0]
        estructura = EstructuraCamposModelo(**{**hit["_source"], "id": hit["_id"]})

        # 2. Obtener índice donde viven los archivos
        index_archivos = estructura.indice_id_archivos

        # 3. Eliminar el documento en Elasticsearch
        try:
            resp = cliente.delete(
                index=index_archivos,
                id=id_documento
            )
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        # 4. Respuesta idéntica al DELETE de /datos/
        return Response(resp, status=200)


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
     
    