from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo
# Create your models here.



class EstructuraCamposModelo(AuditoriaModelo):
    observatorio = ElasticCampo(str)
    nombre =  ElasticCampo(str)
    mapeo = ElasticCampo(dict)

    def crear(self, es, nombre_indice):
        
        registro =  super().crear(es, nombre_indice)
        mapeo =  registro["mapeo"]


        es.indices.create(
            index=registro.get("id").lower(),
            body={"mappings": {"properties" : mapeo } },
        )

    def __str__(self):
        return f"{self.nombre.obtener_valor()} - {self.id}"

    
