from django.shortcuts import render
from apps.elasticsearch_utils.views import ElasticsearchViewSet
from .serializers import DashboardSerializer, DashboardUpdateSerializer, GraficoSerializer, GraficoUpdateSerializer
from apps.elasticsearch_utils.utils import get_elasticsearch_client
from elasticsearch import NotFoundError

from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


from rest_framework.response import Response
from .models import Dashboard, Grafico
from rest_framework.decorators import action
from apps.graficos.utils import construir_datos_de_grafica
from apps.campos.models import EstructuraCamposModelo
from elasticsearch import helpers

class DashboardViewSet(ElasticsearchViewSet):
    elastic_model = Dashboard
    clase_serializador = DashboardSerializer
    cliente = get_elasticsearch_client()

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
        self._nombre_indice = self.elastic_model.indice

        if not self.cliente.indices.exists(index=self._nombre_indice):
            response = self.cliente.indices.create(index=self._nombre_indice)

    def obtener_clase_serializador(self):

        if self.action == "update": return DashboardUpdateSerializer

        return super().obtener_clase_serializador()


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
    

    def update(self, request, pk=None, *args, **kwargs):
        
        respuesta =  super().update(request, pk, *args, **kwargs)
        
        cliente =  get_elasticsearch_client()
        orden =  request.data.get("orden")

        dashboard = self.elastic_model().get(
            es=cliente,
            nombre_indice=self._nombre_indice,
            item_id=pk
        )

        dashboard_indice =  dashboard.indice_id

        graficos =  cliente.search(
            index=dashboard_indice,
            body={
                "query": {
                    "match_all": {}
                }
            }
        )

        if(orden):
            posiciones_a_actualizar =  []

            for posicion in orden:
                if posicion["slot"] != posicion["item"]:
                    columna_nueva , fila_nueva = posicion["item"].split("_")
                    columna_vieja , fila_vieja = posicion["slot"].split("_")

                    grafico  = next((item for item in graficos["hits"]["hits"] if item["_source"]["columna"] == int(columna_vieja) and item["_source"]["fila"] == int(fila_vieja)), None)

                    print(grafico)


                    if grafico:
                        
                        posiciones_a_actualizar.append({
                            "_op_type": "update",  
                            "_index": dashboard_indice,
                            "_id": grafico["_id"],
                            "doc": {
                                "columna": int(columna_nueva), 
                                "fila": int(fila_nueva),    
                            }
                        })
                        
            if posiciones_a_actualizar:
                response = helpers.bulk(cliente, posiciones_a_actualizar)
        
        return respuesta


    


class GraficoViewSet(ElasticsearchViewSet):
    elastic_model = Grafico
    clase_serializador = GraficoSerializer
    cliente = get_elasticsearch_client()

    def obtener_busqueda(self, *args, **kwargs):
        busqueda_elastic = {
            "size" : 10000,
            "query": {
                "bool": {
                "should": [
                    {
                    "bool": {
                        "must_not": {
                        "exists": { "field": "activo" }
                        }
                    }
                    },
                    {
                    "term": { "activo": True }
                    },

                ],
                "minimum_should_match": 1
                }
            }
        }

        return busqueda_elastic


    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = kwargs.get("dashboard_id").lower() + "_dashboard"
        self.elastic_model.indice = self._nombre_indice
        try:
            dashboard = Dashboard().get(self.cliente, Dashboard.indice, kwargs.get("dashboard_id") )
            self._nombre_indice = dashboard.indice_id
        except NotFoundError:
            self.errors = {"Dashboard id" : ["Dashboard no encontrado"]}

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
    


    @action(detail=True, methods=["get"])
    def construir(self, request, *args, **kwargs):
        """
        Construye el grafico a partir de la configuracion
        """
        id_grafico = kwargs.get("pk")
        grafico =  self.elastic_model().get(self.cliente, nombre_indice=self._nombre_indice, item_id=id_grafico)
        
        if not grafico:
            return Response({"error": "No se encontró el grafico"}, status=404)
        
        configuracion = grafico.configuracion.obtener_valor()
        estructura_id = grafico.estructura.obtener_valor()
        estructura = EstructuraCamposModelo().get(self.cliente, EstructuraCamposModelo.indice, item_id=estructura_id)
        
        if not estructura:
            return Response({"error": "No se encontró la estructura"}, status=404)
        
        datos = construir_datos_de_grafica(
            configuracion= configuracion,
            cliente= self.cliente,
            indice= estructura.indice_id
        )

        return Response(datos)




