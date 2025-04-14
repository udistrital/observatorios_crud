from django.db import models
from apps.elasticsearch_utils.models import ElasticCampo, ImagenCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
# Create your models here.
from osiris.settings import ELASTICSEARCH_MAIN_INDEX
from apps.elasticsearch_utils.utils import get_elasticsearch_client


class ObservatorioModelo(AuditoriaModelo):
    nombre =  ElasticCampo(str)
    descripcion =  ElasticCampo(str)
    imagen =  ImagenCampo(str, guardar_en="observatorios_imagenes")
    indice =  ELASTICSEARCH_MAIN_INDEX + "_observatorios"
    observatorio_id = ElasticCampo(str)


    def get(self, es, nombre_indice=..., item_id=None):
        #obtener por observaotrio_id
        if item_id is not None:
            cliente = get_elasticsearch_client()
            resultado_busqueda = cliente.search(
                index=self.indice,
                body={
                    "query": {
                        "term": {
                            "observatorio_id.keyword": item_id
                        }
                    }
                }
            )
            
            if resultado_busqueda["hits"]["total"]["value"] > 0:
                documento =  resultado_busqueda["hits"]["hits"][0]["_source"]
                return self.__class__(**{**documento, "id": resultado_busqueda["hits"]["hits"][0]["_id"]})
        return None
    
    def eliminar(self, cliente, indice, item_id=None):
        item = cliente.search(
            index=self.indice,
            body={
                "query": {
                    "term": {
                        "observatorio_id.keyword": item_id
                    }
                }
            }
        )
        if item["hits"]["total"]["value"] > 0:
            item_id = item["hits"]["hits"][0]["_id"]
            resultado = cliente.update(
                index=self.indice,
                id=item_id,
                body={
                    "doc": {
                        "activo": False
                    }
                }
            )

            return resultado

        return super().eliminar(cliente, indice, item_id)
    

    def crear(self, es, nombre_indice):
        documento = super().crear(es, nombre_indice)

        cliente =  get_elasticsearch_client()
        id = documento.get("id")
        
        maximo_numero_id = cliente.search(
            index=self.indice,
            body={
                "query": {
                    "match_all": {}
                },
                "size": 0,
                "aggs": {
                    "max_id": {
                        "max": {
                            "field": "numero"
                        }
                    }
                }
            }
        )
        maximo_numero_id = maximo_numero_id["aggregations"]["max_id"]["value"] or 0
        maximo_numero_id += 1
        maximo_numero_id = int(maximo_numero_id)

        observatorio_id = "observatorio_" + str(maximo_numero_id) 

        cliente.update(
            index=self.indice,
            id=id,
            body={
                "doc": {
                    "observatorio_id": observatorio_id,
                    "numero": maximo_numero_id
                }
            }
        )


        return {**documento, "observatorio_id": observatorio_id}