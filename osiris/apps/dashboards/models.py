from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo
# Create your models here
from osiris.settings import ELASTICSEARCH_MAIN_INDEX

class Dashboard(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    observatorio = ElasticCampo(str)

    indice =  "." + ELASTICSEARCH_MAIN_INDEX + "_dashboards"


    def crear(self, es, nombre_indice):
        
        registro =  super().crear(es, nombre_indice)

        es.indices.create(
            index=registro.get("id").lower() + "_dashboard",
        )

class Grafico(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    configuracion = ElasticCampo(dict)