from rest_framework import viewsets, status
from rest_framework.response import Response
from elasticsearch import Elasticsearch
from django.conf import settings
from osiris.settings import ES_HOST

class ElasticsearchViewSet(viewsets.ViewSet):

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = "sair_index"

    # Conectar a Elasticsearch
    def get_elasticsearch_client(self):
        return Elasticsearch(ES_HOST)

    def obtener_busqueda(self):
        return {
            "query": {
                "match_all": {}
            }
        }
    
    def get_queryset(self):
        cliente = self.get_elasticsearch_client()

        resultado_busqueda = cliente.search(
            index=self._nombre_indice,  #TODO manejar los índices con base en la sesión
            body=self.obtener_busqueda()
        )

    # Método para listar los elementos en Elasticsearch
    def list(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        
        resultado_busqueda = cliente.search(
            index=self._nombre_indice,  #TODO manejar los índices con base en la sesión
            body=self.obtener_busqueda()
        )

        #TODO Serializar la respuesta de Elasticsearch
        resultados = [ 
            {**item["_source"], "id": item["_id"]}  
            for item in resultado_busqueda['hits']['hits']
        ]
        
        return Response(resultados)

    # Método para obtener un detalle de un objeto por su ID en Elasticsearch
    def retrieve(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        
        resultado_busqueda = cliente.get(
            index=self._nombre_indice,  #TODO manejar los índices con base en la sesión
            id=pk
        )
        return Response({**resultado_busqueda['_source'], "id": resultado_busqueda['_id']})

    # Método para crear un nuevo objeto en Elasticsearch
    def create(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        datos = request.data

        #TODO Manejar la lógica del documento
        instancia = self.elastic_model(**datos)
        respuesta = instancia.crear(cliente, self._nombre_indice)
        
        return Response(respuesta, status=status.HTTP_201_CREATED)

    # Método para actualizar un documento en Elasticsearch
    def update(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        
        datos = request.data
        objeto = self.elastic_model(**datos)
        
        respuesta = cliente.update(
            index=self._nombre_indice,  # El índice de Elasticsearch
            id=pk,
            body={"doc": objeto.obtener_documento()}
        )
        return Response(respuesta)

    # Método para eliminar un documento de Elasticsearch
    def destroy(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        
        #TODO lógica de borrado de ítem
        respuesta = cliente.update(
            index=self._nombre_indice,  # El índice de Elasticsearch
            id=pk,
            body={"doc": {"activo": False}}
        )
        return Response(status=status.HTTP_204_NO_CONTENT)
