from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo

class ArchivoDatoModelo(AuditoriaModelo):
    # No necesitas declarar campos porque son dinámicos
    indice = None  

    def crear(self, es, nombre_indice):
        """Insertar documento directo en un índice de archivos."""
        resp = es.index(index=nombre_indice, document=self.__dict__["_datos"])
        return resp

    def actualizar(self, es, indice, item_id=None, datos=None):
        resp = es.update(index=indice, id=item_id, body={"doc": datos})
        return resp

    def eliminar(self, es, indice, item_id=None):
        es.delete(index=indice, id=item_id)

