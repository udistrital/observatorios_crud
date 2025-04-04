from apps.validadores.validadores import BaseValidador
from apps.elasticsearch_utils.utils import get_elasticsearch_client
import ipaddress
import pandas as pd
import numpy as np
import ipaddress
import json

class ValidadorEstructuraColumnas(BaseValidador):
    """
    Validador que verifica si la estructura del DataFrame (tipos de columnas)
    coincide con el mapping del índice en Elasticsearch.
    """
    dependencias_requeridas = {
        "nombre_indice": str
    }

    

    @staticmethod
    def is_integer(x):
        if isinstance(x, str) and x.isdigit():
            x = int(x)
        return isinstance(x, int) and not isinstance(x, bool)

    @staticmethod
    def is_float(x):
        try:
            return isinstance(float(x), float) if isinstance(x, (str, int, float)) else False
        except ValueError:
            return False

    @staticmethod
    def is_boolean(x):
        if isinstance(x, str):
            return x.lower() in ["true", "false"]
        return isinstance(x, bool) or pd.isna(x)

    @staticmethod
    def is_date(x):
        return pd.to_datetime(x, errors='coerce') is not pd.NaT

    @staticmethod
    def is_valid_ip(ip):
        try:
            ip = str(ip)  # Asegurar que es string
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False

    @staticmethod
    def is_geo_point(x):
        if isinstance(x, str):
            try:
                x = eval(x)  # Convertir string a tuple si está en formato "(lat, lon)"
            except:
                return False
        return isinstance(x, tuple) and len(x) == 2 and all(isinstance(i, (float, int)) for i in x)


    @staticmethod
    def is_geo_shape(x):
        if isinstance(x, str):
            try:
                x = json.loads(x)  # Convertir JSON string a dict
            except:
                return False
        return isinstance(x, dict) and "type" in x


    @staticmethod
    def is_object(x):
        if isinstance(x, str):
            try:
                x = json.loads(x)  # Intentar convertir JSON string a dict
                return isinstance(x, dict)
            except:
                return False
        return isinstance(x, dict)


    @staticmethod
    def is_nested(x):
        if isinstance(x, str):
            try:
                x = json.loads(x)  # Intentar convertir JSON string a lista de dicts
                return isinstance(x, list) and all(isinstance(i, dict) for i in x)
            except:
                return False
        return isinstance(x, list) and all(isinstance(i, dict) for i in x)

    @staticmethod
    def is_binary(x):
        return isinstance(x, bytes) or pd.isna(x)

    @staticmethod
    def is_text(x):
        return isinstance(x, str)


    funciones_validacion = {
        "integer": is_integer,
        "long": is_integer,
        "short": is_integer,
        "byte": is_integer,
        "double": is_float,
        "float": is_float,
        "half_float": is_float,
        "scaled_float": is_float,
        "boolean": is_boolean,
        "date": is_date,
        "ip": is_valid_ip,
        "geo_point": is_geo_point,
        "geo_shape": is_geo_shape,
        "object": is_object,
        "nested": is_nested,
        "binary": is_binary,
        "text": is_text,
        "keyword": is_text
    }


    def setup(self, *args, **kwargs):
        super().setup(**kwargs)
        nombre_indice = kwargs.get("nombre_indice")
        mapeo_indice = get_elasticsearch_client().indices.get_mapping(index=nombre_indice)
        self.propiedades = mapeo_indice[nombre_indice]["mappings"]["properties"]


    def handle(self, df):
        # Obtener las columnas que tienen validaciones
        columnas_a_validar = set(self.propiedades.keys()) & set(df.columns)

        for column in columnas_a_validar:
            es_type = self.propiedades[column].get("type")

            if es_type in self.funciones_validacion:
                validation_func = self.funciones_validacion[es_type]

                # Aplicar la validación usando `map()` en lugar de `apply()`
                incorrect = ~df[column].map(validation_func)

                if incorrect.any():
                    raise Exception(f"Columna '{column}' tiene valores no compatibles con '{es_type}'")

