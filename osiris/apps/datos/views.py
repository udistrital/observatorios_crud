from apps.elasticsearch_utils.views import ElasticsearchViewSet
from apps.elasticsearch_utils.utils import obtener_filtros_indice, convertir_django_ordering_a_elastic_ordering, get_elasticsearch_client
from rest_framework.response import Response
from rest_framework import status
from rest_framework.pagination import PageNumberPagination

from elasticsearch import helpers
from .validadores import ValidadorColumnasNoExistentes
from .models import ArchivoDatoModelo
from apps.campos.models import EstructuraCamposModelo

import csv
import json
import io

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from apps.utils.utils import ProcesadorRecursos
from apps.elasticsearch_utils.validadores import ValidadorEstructuraColumnas

from .serializers import DatosSerializers
from apps.campos.models import EstructuraCamposModelo
from rest_framework.pagination import PageNumberPagination

from django.http import HttpResponse

class CustomPagination(PageNumberPagination):
    page_size = 50  # Valor por defecto
    page_size_query_param = 'page_size'  # Permite cambiar el tamaño con `?page_size=10`
    max_page_size = 10000  # Límite máximo permitido


class DatosArchivoPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 10000

class DatosViewSet(ElasticsearchViewSet):

    procesador = ProcesadorRecursos()
    pagination_class = CustomPagination
    
    procesador.VALIDADORES.append(
        ValidadorColumnasNoExistentes()   
    )
    procesador.VALIDADORES.append(
        ValidadorEstructuraColumnas()
    )

    #TODO: Manejar el size de manera dinamca
    def obtener_busqueda(self, *args, **kwargs):

        ordenamiento = None
        filtros = []

        excepciones_filtros = ["page_size", "ordering"]
        if "filtros" in kwargs.keys():
            filtros = obtener_filtros_indice(nombre_indice = self._nombre_indice, filtros = kwargs["filtros"], filtros_excepcion = excepciones_filtros)

            if "ordering" in kwargs.get("filtros"):
                ordenamiento = kwargs.get("filtros").get("ordering")
                ordenamiento = convertir_django_ordering_a_elastic_ordering(self._nombre_indice,ordenamiento)



        busqueda_elastic = {
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
                    },

                ],
                "minimum_should_match": 1
                }
            }
        }

        if len(filtros) > 0:
            busqueda_elastic["query"]["bool"]["must"] = filtros
        
        if ordenamiento:
            busqueda_elastic["sort"] = ordenamiento

        return busqueda_elastic

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        cliente = get_elasticsearch_client()
        esturctura = EstructuraCamposModelo().get(cliente, EstructuraCamposModelo.obtener_indice(),item_id=kwargs.get("estructura_id")) 
        self._nombre_indice = esturctura.indice_id

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
        query_params = request.query_params


        resultado_busqueda = cliente.search(
            index=self._nombre_indice,  #TODO manejar los índices con base en la sesión
            body=self.obtener_busqueda(filtros =  query_params)
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

        else:
            cliente = self.get_elasticsearch_client()
        
            #TODO lógica de borrado de ítem
            respuesta = cliente.update(
                index=self._nombre_indice,  # El índice de Elasticsearch
                id=pk,
                body={"doc": {"_activo": False}}
            )

            #return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(respuesta)

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
        indice_id_estructura = estructura.indice_id

        #Parametrización de los validadores
        self.procesador.inicializar_datos_validadores(
            **{
                "nombre_indice" : indice_id_estructura
            }
        )


        if formato == "CSV":
            #TODO: agregar campo origin
            archivo = request.FILES['archivo']

            # Verificar el separador
            # archivo.seek(0)  # Reiniciar el puntero del archivo
            # sniffer = csv.Sniffer()
            # primera_linea = archivo.readline().decode('latin-1')

            # if not sniffer.has_header(primera_linea):
            #     return Response({"message": "El archivo CSV no tiene un encabezado válido"}, status=status.HTTP_400_BAD_REQUEST)

            # delimitador_detectado = sniffer.sniff(primera_linea).delimiter
            # if delimitador_detectado != ',':
            #     return Response({"message": f"El archivo CSV tiene un separador inválido: '{delimitador_detectado}'. Se espera ','"},
            #                     status=status.HTTP_400_BAD_REQUEST)
            

            # archivo.seek(0)  # Reiniciar el puntero después de la detección



            csv_buffer = io.StringIO(archivo.read().decode('utf-8'))
            datos_procesados, errors = self.procesador.procesar_csv(csv_buffer)
            
            if errors:
                return Response({"error": errors}, status=400)

            resultados, errors = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura))  
            
            return Response({"message" : f"Se guardaron un total de {resultados}" , "errores" : errors})

        if formato == "JSON":
            #TODO: agregar campo origin
            archivo = request.FILES['archivo']
            try:
                contenido = archivo.read().decode('utf-8')  
                datos_procesados = json.loads(contenido)  # Cargar el JSON
                if not isinstance(datos_procesados, list):  
                    return Response({"error": "El archivo JSON debe contener una lista de objetos"}, status=400)
                
                datos_procesados, errors = self.procesador.procesar_json(datos_procesados)

                if errors:
                    return Response({"error": errors}, status=400)

                # Guardar los datos en Elasticsearch
                resultados, errors = helpers.bulk(self.cliente, estructura.generar_datos_masivos(datos_procesados, indice_id_estructura))  
                return Response({"message": f"Se guardaron un total de {resultados}", "errores": errors})
            
            except json.JSONDecodeError:
                return Response({"error": "El archivo no es un JSON válido"}, status=400)
        
        if formato == "FORM":
            
            respuesta =  self.cliente.index(
                index = indice_id_estructura,
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


class DatosArchivoViewSet(ElasticsearchViewSet):
    elastic_model = ArchivoDatoModelo
    pagination_class = DatosArchivoPagination

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        self._id_archivos = kwargs.get("id_archivos")
        cliente = self.get_elasticsearch_client()

        resultado = cliente.search(
            index=EstructuraCamposModelo.indice,
            body={
                "query": {
                    "term": {
                        "id_archivos.keyword": self._id_archivos
                    }
                }
            }
        )

        # Si no existe esa estructura de archivos
        if not resultado["hits"]["hits"]:
            self._nombre_indice = None
            self._mapeo_archivos = []
            return

        hit = resultado["hits"]["hits"][0]
        estructura = EstructuraCamposModelo(**{
            **hit["_source"],
            "id": hit["_id"]
        })

        # Índice donde realmente viven los archivos
        self._nombre_indice = estructura.indice_id_archivos
        self._mapeo_archivos = estructura.mapeo_archivos.obtener_valor() or []


    # ---------------------------------------------------------
    # LIST — con paginación real como DatosViewSet
    # ---------------------------------------------------------
    def list(self, request, *args, **kwargs):

        if not self._nombre_indice:
            return Response({"error": "id_archivos no encontrado"}, status=404)

        cliente = self.get_elasticsearch_client()
        paginador = self.pagination_class()

        resultado = cliente.search(
            index=self._nombre_indice,
            body={"query": {"match_all": {}}},
            size=10000
        )

        documentos = []
        for h in resultado["hits"]["hits"]:
            fila = {"id": h["_id"]}

            for campo in self._mapeo_archivos:
                nombre = campo.get("nombre")
                fila[nombre] = h["_source"].get(nombre)

            documentos.append(fila)

        resultados_paginados = paginador.paginate_queryset(documentos, request)

        return paginador.get_paginated_response(resultados_paginados)


    # ---------------------------------------------------------
    # RETRIEVE
    # ---------------------------------------------------------
    def retrieve(self, request, *args, **kwargs):
        pk = kwargs.get("pk")

        if not self._nombre_indice:
            return Response({"error": "id_archivos no encontrado"}, status=404)

        cliente = self.get_elasticsearch_client()

        try:
            resp = cliente.get(index=self._nombre_indice, id=pk)
        except:
            return Response({"error": "Documento no encontrado"}, status=404)

        data = {"id": resp["_id"]}
        for campo in self._mapeo_archivos:
            nombre = campo["nombre"]
            data[nombre] = resp["_source"].get(nombre)

        return Response(data)


    # ---------------------------------------------------------
    # CREATE
    # ---------------------------------------------------------
    def create(self, request, *args, **kwargs):
        if not self._nombre_indice:
            return Response({"error": "id_archivos no encontrado"}, status=404)

        cliente = self.get_elasticsearch_client()

        nuevo_doc = {}
        for campo in self._mapeo_archivos:
            nombre = campo["nombre"]
            nuevo_doc[nombre] = request.data.get(nombre)

        resp = cliente.index(index=self._nombre_indice, document=nuevo_doc)
        return Response(resp, status=201)


    # ---------------------------------------------------------
    # UPDATE
    # ---------------------------------------------------------
    def update(self, request, *args, **kwargs):
        pk = kwargs.get("pk")

        if not self._nombre_indice:
            return Response({"error": "id_archivos no encontrado"}, status=404)

        cliente = self.get_elasticsearch_client()

        payload = request.data
        resp = cliente.update(
            index=self._nombre_indice,
            id=pk,
            body={"doc": payload}
        )

        return Response(resp)


    # ---------------------------------------------------------
    # DELETE
    # ---------------------------------------------------------
    def destroy(self, request, *args, **kwargs):
        pk = kwargs.get("pk")

        if not self._nombre_indice:
            return Response({"error": "id_archivos no encontrado"}, status=404)

        cliente = self.get_elasticsearch_client()

        resp = cliente.delete(index=self._nombre_indice, id=pk)
        return Response(resp, status=200)



