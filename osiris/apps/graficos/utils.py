from apps.elasticsearch_utils.utils import obtener_campos_operacion
import json


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



def construir_datos_de_grafica(configuracion, cliente, indice):
    tipo = configuracion.get("tipo")
    if tipo not in ["pie", "barras", "linea"]:
        raise Exception("Tipo de gráfico no soportado.")
            
    datos = {}

    if tipo == "pie":
        datos =  construir_datos_pie(configuracion, cliente, indice)
    elif tipo == "barras":
        datos =  construir_datos_barras(configuracion, cliente, indice)

    elif tipo == "linea":
         datos =  construir_datos_linea(configuracion, cliente, indice)

    return datos
    


    