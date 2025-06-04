from apps.elasticsearch_utils.utils import obtener_campos_operacion
import json
from apps.elasticsearch_utils.utils import (
    obtener_operaciones_metricas,
    obtener_operaciones_agrupacion
)
from django.conf import settings

BASE_QUERY = {
            "bool": {
            "should": [
                {
                "bool": {
                    "must_not": {
                    "exists": { "field": "_activo" }
                    }
                }
                },
                {
                "term": { "_activo": True }
                },

            ],
            "minimum_should_match": 1
            }
}

def get_configuracion_necesaria(tipo):
        metrica =  obtener_operaciones_metricas().get("operaciones", [])
        agrupaciones = obtener_operaciones_agrupacion().get("operaciones", [])

        configuracion = {
                    "tipo": tipo,
                    "datos_requeridos":
                    [
                        {
                            "tipo" : "metrica",
                            "valores" : metrica
                        },
                        {
                            "tipo" : "etiquetas",
                            "valores" : agrupaciones
                        }
                    ]
        }

        if tipo == "multiple_linea" or tipo == "heatmap":
             configuracion["datos_requeridos"].append(
                {
                    "tipo" : "agrupar",
                    "valores" : agrupaciones
                }
             )

        return configuracion

def base_metrica_etiquetas_configuracion(configuracion):
        
        metrica = configuracion.get("metrica")
        etiquetas = configuracion.get("etiquetas")
        
        if not metrica or not etiquetas:
            raise Exception("Métrica y etiquetas son necesarios.")
        
        metrica_agg = metrica.get("operacion")
        metrica_campo = metrica.get("campo")

        etiquetas_agg = etiquetas.get("operacion")
        etiquetas_campo = etiquetas.get("campo")

        etiquetas_agg_dict =  {
                                "field": etiquetas_campo,
                                }

        metrica_agg_dict = {metrica_agg: {
                                "field": metrica_campo
                            }}


        metrica_agg_dict[metrica_agg] = {
            **metrica_agg_dict[metrica_agg],
            **{
                item.get("valor"): configuracion["metrica"].get("opcionales", {}).get(item.get("valor"))
                for item in obtener_campos_operacion(metrica_agg).get("opcionales", [])
            },
            **{
                item.get("valor"): configuracion["metrica"].get("obligatorios", {}).get(item.get("valor"))
                for item in obtener_campos_operacion(metrica_agg).get("obligatorios", [])
            }
        }

        # Actualizar etiquetas_agg_dict
        etiquetas_agg_dict = {
            **etiquetas_agg_dict,
            **{
                item.get("valor"): configuracion["etiquetas"].get("opcionales", {}).get(item.get("valor"))
                for item in obtener_campos_operacion(etiquetas_agg).get("opcionales", [])
            },
            **{
                item.get("valor"): configuracion["etiquetas"].get("obligatorios", {}).get(item.get("valor"))
                for item in obtener_campos_operacion(etiquetas_agg).get("obligatorios", [])
            }
        }


        agg = {
                "etiquetas": {
                    etiquetas_agg: etiquetas_agg_dict,
                    "aggs": {
                        "metrica": metrica_agg_dict
                }
            }
        }

        return agg, metrica_agg, etiquetas_agg


def construir_datos_pie(configuracion, cliente, indice):
        
        agg, metrica_agg, etiquetas_agg = base_metrica_etiquetas_configuracion(configuracion)

        datos = cliente.search(
                index=indice,
                body={
                    "size": 0,
                    "query" : BASE_QUERY,
                    "aggs": agg
                }
            )
        
            
        datos_procesados = {}
        if "aggregations" in datos:
            datos_procesados = {
                "data" : {
                    "metrica" : [],
                    "etiquetas" : [],
                    "etiquetas_as_string" : []
                },
                "grafico_metadata" : {
                    "tipo" : configuracion.get("tipo"),
                    "metrica" : metrica_agg,
                    "etiquetas" : etiquetas_agg
                }
            }
            for etiqueta in datos["aggregations"]["etiquetas"]["buckets"]:
                datos_procesados["data"]["etiquetas"].append(etiqueta["key"])
                datos_procesados["data"]["etiquetas_as_string"].append(etiqueta.get("key_as_string"))
                datos_procesados["data"]["metrica"].append(etiqueta["metrica"]["value"])
                

        return datos_procesados

def construir_datos_barras(configuracion, cliente, indice):
        agg, metrica_agg, etiquetas_agg = base_metrica_etiquetas_configuracion(configuracion)


        datos = cliente.search(
                index=indice,
                body={
                    "size": 0,
                    "query" : BASE_QUERY,
                    "aggs": agg
                }
            )
            

        datos_procesados = {}
        if "aggregations" in datos:
            datos_procesados = {
                "data" : {
                    "metrica" : [],
                    "etiquetas" : [],
                    "etiquetas_as_string" : []
                },
                "grafico_metadata" : {
                    "tipo" : configuracion.get("tipo"),
                    "metrica" : metrica_agg,
                    "etiquetas" : etiquetas_agg
                }
            }
            for etiqueta in datos["aggregations"]["etiquetas"]["buckets"]:
                datos_procesados["data"]["etiquetas"].append(etiqueta["key"])
                datos_procesados["data"]["etiquetas_as_string"].append(etiqueta.get("key_as_string"))
                datos_procesados["data"]["metrica"].append(etiqueta["metrica"]["value"])

        return datos_procesados  

def construir_datos_linea(configuracion, cliente, indice):
        agg, metrica_agg, etiquetas_agg = base_metrica_etiquetas_configuracion(configuracion)


        datos = cliente.search(
                index=indice,
                body={
                    "size": 0,
                    "query" : BASE_QUERY,
                    "aggs": agg
                }
            )
            

        datos_procesados = {}
        if "aggregations" in datos:
            datos_procesados = {
                "data" : {
                    "metrica" : [],
                    "etiquetas" : [],
                    "etiquetas_as_string" : []
                },
                "grafico_metadata" : {
                    "tipo" : configuracion.get("tipo"),
                    "metrica" : metrica_agg,
                    "etiquetas" : etiquetas_agg
                }
            }
            for etiqueta in datos["aggregations"]["etiquetas"]["buckets"]:
                datos_procesados["data"]["etiquetas"].append(etiqueta["key"])
                datos_procesados["data"]["etiquetas_as_string"].append(etiqueta.get("key_as_string"))
                datos_procesados["data"]["metrica"].append(etiqueta["metrica"]["value"])

        return datos_procesados  

def construir_datos_multiple_linea(configuracion, cliente, indice):
        agg, metrica_agg, etiquetas_agg = base_metrica_etiquetas_configuracion(configuracion)

        agg["etiquetas"]["aggs"] = {
             "agrupacion" : {
                  configuracion.get("agrupar").get("operacion") : {
                      "field": configuracion.get("agrupar").get("campo")
                  },
                  "aggs" : agg["etiquetas"]["aggs"]
             }
        }

        datos = cliente.search(
                index=indice,
                body={
                    "size": 0,
                    "query" : BASE_QUERY,
                    "aggs": agg
                }
            )
            
        datos_procesados = {}
        if "aggregations" in datos:
            datos_procesados = {
                "data" : {
                    "metrica" : [],
                    "etiquetas" : [],
                    "etiquetas_as_string" : []
                },
                "grafico_metadata" : {
                    "tipo" : configuracion.get("tipo"),
                    "metrica" : metrica_agg,
                    "etiquetas" : etiquetas_agg
                }
            }
            temporal_metricas = {
                 
            }
            for etiqueta in datos["aggregations"]["etiquetas"]["buckets"]:
                datos_procesados["data"]["etiquetas"].append(etiqueta["key"])
                datos_procesados["data"]["etiquetas_as_string"].append(etiqueta.get("key_as_string"))

                for sub_etiqueta in etiqueta["agrupacion"]["buckets"]:
                       lista_metrica =  temporal_metricas.get(sub_etiqueta["key"], [])
                       lista_metrica.append(sub_etiqueta["metrica"]["value"])
                       temporal_metricas[sub_etiqueta["key"]] = lista_metrica
                
                datos_procesados["data"]["metrica"] = [ {"name" : key, "data" : value } for key, value in temporal_metricas.items() ]

        return datos_procesados

def construir_datos_heatmap(configuracion, cliente, indice):
    agg, metrica_agg, etiquetas_agg = base_metrica_etiquetas_configuracion(configuracion)

    print(agg, metrica_agg, etiquetas_agg)

    agg = {
         "agrupacion" : {
               configuracion.get("agrupar").get("operacion") : {
                    "field": configuracion.get("agrupar").get("campo")
                },
                "aggs" : agg
         }
    }

    datos = cliente.search(
            index=indice,
            body={
                "size": 0,
                "query" : BASE_QUERY,
                "aggs": agg
            }
        )
        
    datos_procesados = {}
    if "aggregations" in datos:
        datos_procesados = {
            "data" : {
                "series" : [],
            },
            "grafico_metadata" : {
                "tipo" : configuracion.get("tipo"),
                "metrica" : metrica_agg,
                "etiquetas" : etiquetas_agg
            }
        }

        for grupo in datos["aggregations"]["agrupacion"]["buckets"]:
            temporal_serie = {
                "name" : grupo["key"],
                "data" : [] 
             }
            for etiqueta in grupo["etiquetas"]["buckets"]:
                temporal_serie["data"].append({
                    "x" : etiqueta["key"],
                    "y" : etiqueta["metrica"]["value"]
                })

            datos_procesados["data"]["series"].append(temporal_serie)
            

    return datos_procesados


def construir_datos_de_grafica(configuracion, cliente, indice):
    tipo = configuracion.get("tipo")
    if tipo not in settings.GRAFICOS:
        raise Exception("Tipo de gráfico no soportado.")
            
    datos = {}

    if tipo == "pie":
        datos =  construir_datos_pie(configuracion, cliente, indice)
    
    if tipo == "barras":
        datos =  construir_datos_barras(configuracion, cliente, indice)
    
    if tipo == "linea":
         datos =  construir_datos_linea(configuracion, cliente, indice)

    if tipo == "multiple_linea":
        datos =  construir_datos_multiple_linea(configuracion, cliente, indice)

    if tipo == "heatmap":
        datos =  construir_datos_heatmap(configuracion, cliente, indice)

    return datos
    


    