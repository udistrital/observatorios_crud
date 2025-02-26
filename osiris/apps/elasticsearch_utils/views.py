from rest_framework import viewsets, status
from rest_framework.response import Response
from elasticsearch import Elasticsearch
from django.conf import settings
from osiris.settings import ES_HOST

import json
class ElasticsearchViewSet(viewsets.ViewSet):

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self._nombre_indice = "sair_index"

    # Conectar a Elasticsearch
    def get_elasticsearch_client(self):
        return Elasticsearch(ES_HOST)

    def obtener_busqueda(self):
        return {
            "size": 10000,
            "query": {
                "bool": {
                    "must": [],
                    "filter": [],
                    "should": [],
                    "must_not": []
                }
            }
        }
    
    
    def obtener_clase_serializador(self):
        return self.clase_serializador


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
            self.elastic_model(**{**item["_source"], "id": item["_id"]}).obtener_documento( imagen_en_base64 = True )      
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

        if hasattr(self, "clase_serializador"):
            serializador =  self.clase_serializador(data= datos)
            
            if serializador.is_valid():
                datos = serializador.data
                valores_limpiados = {clave: valores[0] for clave, valores in request.FILES.lists()}
                datos.update(valores_limpiados)
            else:
                return Response(serializador.errors, status=status.HTTP_400_BAD_REQUEST)


        #TODO Manejar la lógica del documento
        instancia = self.elastic_model(**datos)
        respuesta = instancia.crear(cliente, self._nombre_indice)
        
        return Response(respuesta, status=status.HTTP_201_CREATED)

    # Método para actualizar un documento en Elasticsearch
    #TODO Manejar existencia en el ID
    def update(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        
        datos = request.data

        if hasattr(self, "clase_serializador"):
            serializador =  self.obtener_clase_serializador()(data= datos)
            serializador.is_valid()
            datos = serializador.validated_data
            valores_limpiados = {clave: valores[0] for clave, valores in request.FILES.lists()}
            datos.update(valores_limpiados)        

        print(datos, serializador.errors, serializador.validated_data, sep="||||||")
        objeto = self.elastic_model().get(cliente, item_id = pk)
        objeto.set(**datos)
        print(objeto.obtener_documento(), "<<<< Documento")
        respuesta = cliente.update(
            index=self._nombre_indice,  # El índice de Elasticsearch
            id=pk,
            body={"doc": objeto.obtener_documento()}
        )

        objeto.guardar_campos_archivos(cliente, self._nombre_indice)
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
