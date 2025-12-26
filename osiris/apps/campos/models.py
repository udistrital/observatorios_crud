from django.db import models
from apps.elasticsearch_utils.models import AuditoriaModelo, ElasticCampo
# Create your models here.
import uuid
from asgiref.sync import async_to_sync



class EstructuraCamposModelo(AuditoriaModelo):
    observatorio = ElasticCampo(str)
    nombre =  ElasticCampo(str)
    mapeo = ElasticCampo(list)
    id_archivos = ElasticCampo(str)
    mapeo_archivos = ElasticCampo(list)

    indice = ".estructuras"

    def crear(self, es, nombre_indice):
        
        registro =  super().crear(es, nombre_indice)

        # --------------------------------------------------------------------
        # 1️⃣ CREAR O ASIGNAR id_archivos
        # --------------------------------------------------------------------
        if not registro.get("id_archivos"):
            nuevo_id_archivos = str(uuid.uuid4())   # Generamos un UUID único
            registro["id_archivos"] = nuevo_id_archivos

            # Guardar id_archivos dentro del documento principal
            es.update(
                index=nombre_indice,
                id=registro["id"],
                body={"doc": {"id_archivos": nuevo_id_archivos}}
            )

        # --------------------------------------------------------------------
        # 2️⃣ CREAR ÍNDICE PARA MAPEO (DATOS)
        # --------------------------------------------------------------------

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
        
        # --------------------------------------------------------------------
        # 3️⃣ CREAR ÍNDICE PARA ARCHIVOS (MAPEO_ARCHIVOS)
        # --------------------------------------------------------------------
        mapeo_archivos = registro.get("mapeo_archivos", [])

        if mapeo_archivos:

            mapeo_arch = self.obtener_mapeo(mapeo_archivos)

            id_arch = uuid.uuid5(uuid.NAMESPACE_DNS, registro["id_archivos"])

            try:
                es.indices.create(
                    index=str(id_arch),
                    body=mapeo_arch
                )
            except Exception as error:
                # Rollback: elimina todo lo anterior si falla
                es.indices.delete(index=str(id_unico), ignore=[404])
                es.delete(index=nombre_indice, id=registro.get("id"))
                raise error

        return registro
    
    @property
    def indice_id(self):
        id_unico = uuid.uuid5(uuid.NAMESPACE_DNS, str(self.id.obtener_valor()))
        return str(id_unico)

    # ------------------------------------------------------------------------
    # Propiedades del índice de archivos
    # ------------------------------------------------------------------------
    @property
    def indice_id_archivos(self):
        id_arch = self.id_archivos.obtener_valor()
        if not id_arch or not isinstance(id_arch, str):
            return None
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, id_arch))

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
    

    def obtener_campos_nuevos(self, mapeo,cliente, item):
        estructura =  self.get(cliente,nombre_indice=self.indice, item_id=item)
        mapeo_viejo = estructura.mapeo.obtener_valor()
        campos_nuevos = []
        mapeo_viejo = { campo["nombre"]: campo for campo in mapeo_viejo}
        for campo in mapeo:
            if campo.get("nombre") and not campo.get("valor_anterior"):
                if campo.get("nombre") not in mapeo_viejo.keys():
                    campos_nuevos.append(
                        campo
                    )


        return campos_nuevos



    def actualizar_mapeo(self, cliente, indice, body= {}):
        respuesta = cliente.update_by_query(
            index =  indice,
            body =  body,
            timeout = "10m",
        )

    def normalizar_mapeo(self, mapeo):
        """
        Mantiene valor_anterior SOLO si viene del frontend.
        """
        resultado = []
        for campo in mapeo:
            nuevo = {
                "nombre": campo["nombre"],
                "tipo": campo["tipo"],
            }
            if "valor_anterior" in campo:
                nuevo["valor_anterior"] = campo["valor_anterior"]
            resultado.append(nuevo)
        return resultado


    def actualizar(self, cliente, indice, item_id=None, datos=...):

        mapeo =  datos.get("mapeo")
        mapeo_archivos = datos.get("mapeo_archivos")

        if mapeo:  
            campos_cambiados = self.obtener_campos_viejos(mapeo)

            painless_script = ""
            for campo in campos_cambiados:
                old = campo["viejo"]
                new = campo["nuevo"]
                painless_script += f"""
                if (ctx._source.containsKey('{old}')) {{
                ctx._source['{new}'] = ctx._source.remove('{old}');
                }}
                """
            
            estructura = self.get(cliente,nombre_indice=indice, item_id=item_id)

            index_id = estructura.indice_id

            if len(painless_script)>0:

                body = {
                        "script": {
                            "lang": "painless",
                            "source": painless_script,
                        },
                        "query": {
                            "match_all": {}
                        }
                }
                
                self.actualizar_mapeo(cliente, index_id, body)

            
            campos_nuevos = self.obtener_campos_nuevos(mapeo, cliente, item_id)

            if len(campos_nuevos)> 0:
                nuevo_mapeo = self.obtener_mapeo(campos_nuevos)
                cliente.indices.put_mapping(
                    index =  index_id,
                    body = nuevo_mapeo["mappings"],
                )

        if mapeo_archivos:
            estructura = self.get(cliente, nombre_indice=indice, item_id=item_id)
            index_arch_id = estructura.indice_id_archivos

            # 🔹 Detectar renombres usando valor_anterior
            campos_cambiados_arch = [
                {
                    "viejo": c["valor_anterior"],
                    "nuevo": c["nombre"]
                }
                for c in mapeo_archivos
                if c.get("valor_anterior") and c["valor_anterior"] != c["nombre"]
            ]

            # 🔹 SOLO mover datos, NO mapping
            if campos_cambiados_arch:
                painless_script_arch = ""
                for campo in campos_cambiados_arch:
                    old = campo["viejo"]
                    new = campo["nuevo"]
                    painless_script_arch += f"""
                    if (ctx._source.containsKey('{old}')) {{
                        ctx._source['{new}'] = ctx._source.remove('{old}');
                    }}
                    """

                cliente.update_by_query(
                    index=index_arch_id,
                    body={
                        "script": {
                            "lang": "painless",
                            "source": painless_script_arch,
                        },
                        "query": {"match_all": {}}
                    },
                    timeout="10m"
                )

        if "mapeo" in datos:
            datos["mapeo"] = self.normalizar_mapeo(datos["mapeo"])

        if "mapeo_archivos" in datos:
            datos["mapeo_archivos"] = self.normalizar_mapeo(datos["mapeo_archivos"])


        estructura_actualizada = super().actualizar(
            cliente,
            indice,
            item_id,
            datos
        )

        return estructura_actualizada