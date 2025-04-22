from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo
# Create your models here
from osiris.settings import ELASTICSEARCH_MAIN_INDEX
import uuid

class Dashboard(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    observatorio = ElasticCampo(str)

    indice =  "." + ELASTICSEARCH_MAIN_INDEX + "_dashboards"


    def crear(self, es, nombre_indice):
        
        registro =  super().crear(es, nombre_indice)

        id_unico = uuid.uuid5(uuid.NAMESPACE_DNS, str(registro.get("id")))

        try:
            es.indices.create(
                index=id_unico
            )
        except Exception as error:
            es.delete(index=nombre_indice, id=registro.get("id"))
            raise error


    @property
    def indice_id(self):
        id_unico = uuid.uuid5(uuid.NAMESPACE_DNS, str(self.id.obtener_valor()))
        return str(id_unico)

class Grafico(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    configuracion = ElasticCampo(dict)
    columna = ElasticCampo(int)
    fila = ElasticCampo(int)
    estructura = ElasticCampo(str)