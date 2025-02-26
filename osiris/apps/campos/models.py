from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo
# Create your models here.



class EstructuraCamposModelo(AuditoriaModelo):
    observatorio = ElasticCampo(str)
    nombre =  ElasticCampo(str)
    mapeo = ElasticCampo(list)

    indice = ".estructuras"

    def crear(self, es, nombre_indice):
        
        registro =  super().crear(es, nombre_indice)
        mapeo =  registro["mapeo"]

        mapeo = self.obtener_mapeo(mapeo)
        print(mapeo)
        es.indices.create(
            index=registro.get("id").lower(),
            body={"mappings": {"properties" : mapeo } },
        )

    def __str__(self):
        return f"{self.nombre.obtener_valor()} - {self.id}"

    @staticmethod
    def obtener_indice():
        return ".estructuras"
    


    def obtener_mapeo(self, mapeo):
        """
        Convierte los datos en un formato de mapeo de Elasticsearch.
        """
        es_mapping = {
            "mappings": {
                "properties": {}
            }
        }

        for field in mapeo:
            es_mapping["mappings"]["properties"][field["nombre"]] = {
                "type": field["tipo"]
            }

        return es_mapping