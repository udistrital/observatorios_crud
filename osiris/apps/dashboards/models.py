from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo
# Create your models here
import uuid

class Dashboard(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    observatorio = ElasticCampo(str)
    columnas =  ElasticCampo(int)

    indice = "atlas_dashboards"
    prefijo_aplicacion = "atlas"
    contexto_indice = "dashboard"


    def crear(self, es, nombre_indice):
        
        registro =  super().crear(es, nombre_indice)

        id_unico = uuid.uuid5(uuid.NAMESPACE_DNS, str(registro.get("id")))
        nombre_indice_dashboard = (
            f"{self.prefijo_aplicacion}_{self.contexto_indice}_{id_unico}"
        )

        try:
            es.indices.create(
                index=nombre_indice_dashboard
            )
        except Exception as error:
            es.delete(index=nombre_indice, id=registro.get("id"))
            raise error


    @property
    def indice_id(self):
        id_unico = uuid.uuid5(uuid.NAMESPACE_DNS, str(self.id.obtener_valor()))
        return f"{self.prefijo_aplicacion}_{self.contexto_indice}_{id_unico}"

class Grafico(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    configuracion = ElasticCampo(dict)
    columna = ElasticCampo(int)
    fila = ElasticCampo(int)
    estructura = ElasticCampo(str)
