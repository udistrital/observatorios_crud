from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo
# Create your models here.
import uuid
from asgiref.sync import async_to_sync



class EstructuraCamposModelo(AuditoriaModelo):
    observatorio = ElasticCampo(str)
    nombre =  ElasticCampo(str)
    mapeo = ElasticCampo(list)

    indice = ".estructuras"

    def crear(self, es, nombre_indice):
        
        registro =  super().crear(es, nombre_indice)
        mapeo =  registro["mapeo"]

        mapeo = self.obtener_mapeo(mapeo)
        mapeo["mappings"]["dynamic_templates"] = [
            {
                "strings_as_keywords": {
                    "match_mapping_type": "string",
                    "mapping": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword",
                                "ignore_above": 256
                            }
                        }
                    }
                }
            }
        ]

        id_unico = uuid.uuid5(uuid.NAMESPACE_DNS, str(registro.get("id")))

        try:
            es.indices.create(
                index=id_unico,
                body=mapeo,
            )
        except Exception as error:
            es.delete(index=nombre_indice, id=registro.get("id"))
            raise error
        
        return registro
    
    @property
    def indice_id(self):
        id_unico = uuid.uuid5(uuid.NAMESPACE_DNS, str(self.id.obtener_valor()))
        return str(id_unico)

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
                "type": field["tipo"] if field["tipo"] != "text" else "keyword",
            }

        return es_mapping
    
    def obtener_campos_viejos(self, mapeo):

        campos_nuevos = []
        for campo in mapeo:
            if campo.get("valor_anterior") and campo.get("valor_anterior") != campo.get("nombre"):
                campos_nuevos.append(
                    {
                        "viejo" : campo.get("valor_anterior"),
                        "nuevo" : campo.get("nombre"), 
                    }
                    )
                
        return campos_nuevos


    async def actualizar_mapeo(self, cliente, indice, body= {}):
        respuesta = cliente.update_by_query(
            index =  indice,
            body =  body
        )

        print (respuesta)


    def actualizar(self, cliente, indice, item_id=None, datos=...):

        mapeo =  datos.get("mapeo")

        campos_nuevos = self.obtener_campos_viejos(mapeo)

        painless_script = ""
        for campo in campos_nuevos:
            old = campo["viejo"]
            new = campo["nuevo"]
            painless_script += f"""
            if (ctx._source.containsKey('{old}')) {{
            ctx._source['{new}'] = ctx._source.remove('{old}');
            }}
            """
        
        estructura = self.get(cliente, item_id=item_id)

        index_id = estructura.indice_id

        body = {
                "script": {
                    "lang": "painless",
                    "source": painless_script,
                },
                "query": {
                    "match_all": {}
                }
        }
        
        async_to_sync(self.actualizar_mapeo)(cliente, index_id, body)

        resultados_updates =  super().actualizar(cliente, indice, item_id, datos)
        return resultados_updates