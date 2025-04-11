from elasticsearch import Elasticsearch
from django.conf import settings
# from apps.utils.utils import BaseValidador

def get_elasticsearch_client():
    return Elasticsearch(settings.ES_HOST)


def convertir_django_ordering_a_elastic_ordering(indice: str, ordering: str):
    """
    Convierte un string de ordering en formato Django a formato Elasticsearch,
    permitiendo solo campos numéricos según el mapping del índice.
    
    :param cliente: Cliente de Elasticsearch.
    :param indice: Nombre del índice en Elasticsearch.
    :param ordering: String de ordenación en formato Django (ej: "-price,name").
    :return: Lista de diccionarios con formato de Elasticsearch.
    """
    if not ordering:
        return []

    cliente = get_elasticsearch_client()

    ordering_fields = ordering.split(",")
    mapeo = cliente.indices.get_mapping(index=indice)
    mapeo = mapeo[indice]["mappings"]["properties"]

    # Tipos numéricos permitidos en Elasticsearch
    tipos_numericos = {"integer", "long", "short", "byte", "float", "double"}

    elastic_sort = []
    for field in ordering_fields:
        order = "asc"
        if field.startswith("-"):
            field = field[1:]  # Eliminar el prefijo "-"
            order = "desc"

        # Solo agregar si el campo existe y es de tipo numérico
        if field in mapeo:
            if mapeo.get(field)["type"] in tipos_numericos:
                elastic_sort.append({field: {"order": order}})

    return elastic_sort

def obtener_filtros_indice(nombre_indice, filtros, filtros_excepcion=None):
    """
    Obtiene el mapping de un índice en Elasticsearch y genera filtros automáticamente.

    :param nombre_indice: Nombre del índice en Elasticsearch
    :param filtros: Diccionario con los filtros a aplicar
    :param filtros_excepcion: Lista de filtros a excluir
    :return: Lista de filtros generados dinámicamente
    """
    filtros_excepcion = filtros_excepcion or []

    # Obtener el mapping del índice
    cliente = get_elasticsearch_client()
    mapeo = cliente.indices.get_mapping(index=nombre_indice)
    propiedades = mapeo[nombre_indice]["mappings"]["properties"]

    def generar_filtro(item, valor):
        """Genera el filtro correspondiente según el tipo de campo."""
        tipo_campo = propiedades.get(item, {}).get("type")

        filtro_map = {
            "text": lambda: {"wildcard": {item: valor}} if "*" in valor else {"match": {item: valor}},
            "integer": lambda: {"term": {item: valor}},
            "boolean": lambda: {"term": {item: valor}},
            "date": lambda: {"range": {item: {"gte": valor}}},
            "keyword": lambda: {"term": {item: valor}},
            "float": lambda: {"term": {item: valor}},
            "long": lambda: {"term": {item: valor}},
            "short": lambda: {"term": {item: valor}},
            "byte": lambda: {"term": {item: valor}},
            "double": lambda: {"term": {item: valor}},
        }

        return filtro_map.get(tipo_campo, lambda: None)()

    # Filtrar y generar los filtros
    final_filtros = list(
        filter(None, map(lambda item: generar_filtro(*item), filtros.items()))
    )

    return final_filtros   

def obtener_operaciones_metricas():
    METRIC_AGGREGATIONS = [
        {"id": "avg", "nombre": "Average", "nombre_espanol": "Promedio"},
        {"id": "sum", "nombre": "Sum", "nombre_espanol": "Suma"},
        {"id": "min", "nombre": "Minimum", "nombre_espanol": "Mínimo"},
        {"id": "max", "nombre": "Maximum", "nombre_espanol": "Máximo"},
        {"id": "stats", "nombre": "Stats", "nombre_espanol": "Estadísticas"},
        {"id": "extended_stats", "nombre": "Extended Stats", "nombre_espanol": "Estadísticas Extendidas"},
        {"id": "value_count", "nombre": "Value Count", "nombre_espanol": "Conteo de Valores"},
        {"id": "cardinality", "nombre": "Cardinality", "nombre_espanol": "Cardinalidad"},
        {"id": "percentiles", "nombre": "Percentiles", "nombre_espanol": "Percentiles"},
        {"id": "percentile_ranks", "nombre": "Percentile Ranks", "nombre_espanol": "Rangos Percentiles"},
        {"id": "matrix_stats", "nombre": "Matrix Stats", "nombre_espanol": "Estadísticas de Matriz"},
        {"id": "geo_bounds", "nombre": "Geo Bounds", "nombre_espanol": "Límites Geográficos"},
        {"id": "geo_centroid", "nombre": "Geo Centroid", "nombre_espanol": "Centro Geográfico"},
    ]

    return {"operaciones": METRIC_AGGREGATIONS}

def obtener_operaciones_agrupacion():
    BUCKET_AGGREGATIONS = [
        {"id": "terms", "nombre": "Terms", "nombre_espanol": "Términos"},
        {"id": "histogram", "nombre": "Histogram", "nombre_espanol": "Histograma"},
        {"id": "range", "nombre": "Range", "nombre_espanol": "Rango"},
        {"id": "date_range", "nombre": "Date Range", "nombre_espanol": "Rango de Fechas"},
        {"id": "ip_range", "nombre": "IP Range", "nombre_espanol": "Rango IP"},
        {"id": "date_histogram", "nombre": "Date Histogram", "nombre_espanol": "Histograma de Fecha"},
        {"id": "geohash_grid", "nombre": "Geohash Grid", "nombre_espanol": "Cuadrícula Geohash"},
        {"id": "geo_tile_grid", "nombre": "Geo Tile Grid", "nombre_espanol": "Cuadrícula de Teselas Geográficas"},
        {"id": "geohex_grid", "nombre": "Geohex Grid", "nombre_espanol": "Cuadrícula Geohex"},
    ]

    return {"operaciones": BUCKET_AGGREGATIONS}