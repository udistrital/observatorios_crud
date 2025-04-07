from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.elasticsearch_utils.utils import (
    get_elasticsearch_client,
    obtener_operaciones_metricas,
    obtener_operaciones_agrupacion
)
import json



class VistaTipoOperaciones(APIView):
    def get(self, request, *args, **kwargs):
        tipo_operaciones = [
            {"id": 1, "nombre": "terms", "nombre_espanol": "términos"},
            {"id": 2, "nombre": "avg", "nombre_espanol": "promedio"},
            {"id": 3, "nombre": "sum", "nombre_espanol": "suma"},
            {"id": 4, "nombre": "min", "nombre_espanol": "mínimo"},
            {"id": 5, "nombre": "max", "nombre_espanol": "máximo"},
            {"id": 6, "nombre": "stats", "nombre_espanol": "estadísticas"},
            {"id": 7, "nombre": "extended_stats", "nombre_espanol": "estadísticas extendidas"},
            {"id": 8, "nombre": "value_count", "nombre_espanol": "conteo de valores"},
            {"id": 9, "nombre": "percentiles", "nombre_espanol": "percentiles"},
            {"id": 10, "nombre": "percentile_ranks", "nombre_espanol": "rangos percentiles"},
            {"id": 11, "nombre": "cardinality", "nombre_espanol": "cardinalidad"},
            {"id": 12, "nombre": "range", "nombre_espanol": "rango"},
            {"id": 13, "nombre": "date_range", "nombre_espanol": "rango de fechas"},
            {"id": 14, "nombre": "ip_range", "nombre_espanol": "rango de IP"},
            {"id": 15, "nombre": "histogram", "nombre_espanol": "histograma"},
            {"id": 16, "nombre": "date_histogram", "nombre_espanol": "histograma de fechas"},
            {"id": 17, "nombre": "geo_distance", "nombre_espanol": "distancia geográfica"},
            {"id": 18, "nombre": "filter", "nombre_espanol": "filtro"},
            {"id": 19, "nombre": "filters", "nombre_espanol": "filtros"},
            {"id": 20, "nombre": "missing", "nombre_espanol": "faltante"},
            {"id": 21, "nombre": "nested", "nombre_espanol": "anidado"},
            {"id": 22, "nombre": "reverse_nested", "nombre_espanol": "anidado inverso"},
            {"id": 23, "nombre": "children", "nombre_espanol": "hijos"},
            {"id": 24, "nombre": "composite", "nombre_espanol": "compuesto"},
            {"id": 25, "nombre": "matrix_stats", "nombre_espanol": "estadísticas de matriz"},
            {"id": 26, "nombre": "scripted_metric", "nombre_espanol": "métrica programada"},
            {"id": 27, "nombre": "top_hits", "nombre_espanol": "mejores resultados"}
        ]
        return Response({"operaciones": tipo_operaciones})
    


class VistaCamposSugeridos(APIView):
    #TODO: obtener los AGGREGATION_TYPES desde el util de elasticsearch
    AGGREGATION_TYPES = {
        
        # Metric aggregations
        "avg": ["integer", "long", "float", "double", "scaled_float"],
        "cardinality": ["keyword", "text", "integer", "long", "float", "double"],
        "extended_stats": ["integer", "long", "float", "double"],
        "geo_bounds": ["geo_point"],
        "geo_centroid": ["geo_point"],
        "max": ["integer", "long", "float", "double", "date", "scaled_float"],
        "min": ["integer", "long", "float", "double", "date", "scaled_float"],
        "percentile_ranks": ["integer", "long", "float", "double"],
        "percentiles": ["integer", "long", "float", "double"],
        "stats": ["integer", "long", "float", "double"],
        "sum": ["integer", "long", "float", "double", "scaled_float"],
        "value_count": ["keyword", "text", "integer", "long", "float", "double", "boolean", "date"],
        "matrix_stats": ["float", "double", "integer", "long"],
        
        # Bucket aggregations
        "terms": ["keyword", "text", "boolean", "ip", "integer", "long", "float", "double"],
        "histogram": ["integer", "long", "float", "double", "scaled_float"],
        "range": ["integer", "long", "float", "double", "date"],
        "date_range": ["date"],
        "ip_range": ["ip"],
        "date_histogram": ["date"],
        "geohash_grid": ["geo_point"],
        "geo_tile_grid": ["geo_point"],
        "geohex_grid": ["geo_point"],
    }

    def get(self, request, *args, **kwargs):

        operacion = request.query_params.get("operacion")
        index_id = request.query_params.get("estructura")

        es = get_elasticsearch_client()

        if not operacion or not index_id:
            return Response({"detail": "operation and index_id are required."},
                            status=status.HTTP_400_BAD_REQUEST)

        if operacion not in self.AGGREGATION_TYPES:
            return Response({"detail": f"Invalid aggregation type. Supported: {list(self.AGGREGATION_TYPES.keys())}"},
                            status=status.HTTP_400_BAD_REQUEST)

        index_id = index_id.lower()
        try:
            mapping = es.indices.get_mapping(index=index_id)
        except Exception as e:
            return Response({"detail": f"Index not found or error: {str(e)}"},
                            status=status.HTTP_404_NOT_FOUND)

        fields = self.extract_fields(mapping, index_id)
        valid_types = self.AGGREGATION_TYPES[operacion]
        print(fields)

        if operacion == "terms":
            result = [f for f, t in fields if t in valid_types or f.endswith(".keyword")]
        else:
            result = [f for f, t in fields if t in valid_types]

        return Response({"operacion": operacion, "campos_recomendados": result})
    

    def extract_fields(self, mapping, index_id):
         

        properties = mapping[index_id]["mappings"].get("properties", {})
        fields = []

        def recursive_extract(props, path=""):
            #add .keyword to all fields type text

            for field, meta in props.items():
                full_path = f"{path}.{field}" if path else field
                if "type" in meta:
                    if meta["type"] == "text":
                        # Add the .keyword version of the text field
                        fields.append((f"{full_path}.keyword", "keyword"))
                    else:
                        fields.append((full_path, meta["type"]))
                elif "properties" in meta:
                    recursive_extract(meta["properties"], full_path)

        recursive_extract(properties)
        return fields
    

class VistaObtenerConfiguracionGrafico(APIView):

    def get(self, request, *args, **kwargs):

        metrica =  obtener_operaciones_metricas().get("operaciones", [])
        agrupaciones = obtener_operaciones_agrupacion().get("operaciones", [])

        tipo = request.query_params.get("tipo")
        configuracion = {}


        if tipo == "pie" or tipo == "barras":
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

        
        return Response(configuracion)


class VistaProbarConfiguracionGrafico(APIView):
    def post(self, request, *args, **kwargs):
        cliente = get_elasticsearch_client()
        configuracion = request.data.get("configuracion")
        indice = request.data.get("estructura")
        
        if not configuracion or not indice:
            return Response({"error": "condifuracion y estructura son necesarios"},
                            status=status.HTTP_400_BAD_REQUEST)
        

        indice = indice.lower()
        tipo = configuracion.get("tipo")
        if tipo not in ["pie", "barras"]:
            return Response({"error": "Tipo de gráfico no soportado."},
                            status=status.HTTP_400_BAD_REQUEST)
        
        else:
            metrica = configuracion.get("metrica")
            etiquetas = configuracion.get("etiquetas")
            
            if not metrica or not etiquetas:
                return Response({"error": "Métrica y etiquetas son necesarios."},
                                status=status.HTTP_400_BAD_REQUEST)
            
            metrica_agg = metrica.get("operacion")
            metrica_campo = metrica.get("campo")

            etiquetas_agg = etiquetas.get("operacion")
            etiquetas_campo = etiquetas.get("campo")

            datos = cliente.search(
                index=indice,
                body={
                    "size": 0,
                    "aggs": {
                        "etiquetas": {
                            etiquetas_agg: {
                                "field": etiquetas_campo,
                            },
                            "aggs": {
                                "metrica": {
                                    metrica_agg: {
                                        "field": metrica_campo
                                    }
                                }
                            }
                        }
                    }
                }
            )
            

            print (datos)
            if "aggregations" in datos:
                datos_procesados = {
                    "data" : {
                        "metrica" : [],
                        "etiquetas" : [],
                        "etiquetas_as_string" : []
                    },
                    "grafico_metadata" : {
                        "tipo" : tipo,
                        "metrica" : metrica_agg,
                        "etiquetas" : etiquetas_agg
                    }
                }
                for etiqueta in datos["aggregations"]["etiquetas"]["buckets"]:
                    datos_procesados["data"]["etiquetas"].append(etiqueta["key"])
                    datos_procesados["data"]["etiquetas_as_string"].append(etiqueta.get("key_as_string"))
                    datos_procesados["data"]["metrica"].append(etiqueta["metrica"]["value"])
                    
                return Response(datos_procesados)
            else:
                return Response({"error": "No se encontraron resultados."},
                                status=status.HTTP_404_NOT_FOUND)
            
        return Response({"error": "Configuration tested successfully."})
