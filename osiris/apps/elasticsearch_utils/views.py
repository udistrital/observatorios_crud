from rest_framework import viewsets, status
from rest_framework.response import Response
from elasticsearch import Elasticsearch
from django.conf import settings
from osiris.settings import ES_HOST

class ElasticsearchViewSet(viewsets.ViewSet):

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._index_name = "sair_index"

    # Conectar a Elasticsearch
    def get_elasticsearch_client(self):
        return Elasticsearch(ES_HOST)

    def get_query(self):
        return {
            "query": {
                "match_all": {}
            }
        }
    
    def get_queryset(self):

        client =  self.get_elasticsearch_client()

        search_result = client.search(
            index=self._index_name,  #TODO manejar los indices con base a la sesion
            body= self.get_query()
        )




    # Método para listar los elementos en Elasticsearch
    def list(self, request,*args, **kwargs):
        
        client = self.get_elasticsearch_client()
        
        search_result = client.search(
            index=self._index_name,  #TODO manejar los indices con base a la sesion
            body= self.get_query()
        )

        #TODO Serializar la respuesta de Elasticsearch
        results = [ 
            {**item["_source"], "id": item["_id"]}  
            for item in search_result['hits']['hits']
            ]
        
        return Response(results)


    # Método para obtener un detalle de un objeto por su ID en Elasticsearch
    def retrieve(self, request, pk=None,  *args, **kwargs):
        
        client = self.get_elasticsearch_client()
        
        search_result = client.get(
            index=self._index_name,  #TODO manejar los indices con base a la sesion
            id=pk
        )
        return Response({**search_result['_source'] , "id": search_result['_id'] })

    # Método para crear un nuevo objeto en Elasticsearch
    def create(self, request,  *args, **kwargs):

        client = self.get_elasticsearch_client()
        data = request.data

        #TODO Manejar la logica del documento
        instance = self.elastic_model(**data)
        response = instance.create(client, self._index_name)
        
        return Response(response, status=status.HTTP_201_CREATED)
    

    # Método para actualizar un documento en Elasticsearch
    def update(self, request, pk=None, *args, **kwargs):
        client = self.get_elasticsearch_client()
        
        data = request.data
        _object = self.elastic_model(**data)
        
        response = client.update(
            index=self._index_name,  # El índice de Elasticsearch
            id=pk,
            body={"doc": _object.get_document() }
        )
        return Response(response)

    # Método para eliminar un documento de Elasticsearch
    def destroy(self, request, pk=None , *args, **kwargs):
        client = self.get_elasticsearch_client()
        
        #TODO logica de borrado de item
        response = client.update(
            index=self._index_name,  # El índice de Elasticsearch
            id=pk,
            body={"doc": {"is_active" : False } }
        )
        return Response(status=status.HTTP_204_NO_CONTENT)