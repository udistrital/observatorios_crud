from apps.validadores.validadores import BaseValidador
from apps.elasticsearch_utils.utils import get_elasticsearch_client

class ValidadorColumnasNoExistentes(BaseValidador):
    """
    Validador que verifica si existen columnas no permitidas en el DataFrame.
    """
    columnas_permitidas = []

    dependencias_requeridas = {
        "nombre_indice": str
    }


    def setup(self, *args, **kwargs):
        super().setup(**kwargs)
        nombre_indice = kwargs.get("nombre_indice")
        mapeo_indice = get_elasticsearch_client().indices.get_mapping(index=nombre_indice)
        propiedades = mapeo_indice[nombre_indice]["mappings"]["properties"]
        self.columnas_permitidas = [col for col in propiedades.keys()]


    def handle(self, df):
        columnas_no_permitidas = set(df.columns) - set(self.columnas_permitidas)
        if columnas_no_permitidas:
            columnas = ", ".join(columnas_no_permitidas)
            raise ValueError(f"Columnas no permitidas: {columnas}")
        

# #Validador de datos con base en el mapping de elasticsearch
# class ValidadorEstructuraColumnas(BaseValidador):
#     """
#     Validador que verifica si la estructura del DataFrame (tipos de columnas)
#     coincide con el mapping del índice en Elasticsearch.
#     """
#     dependencias_requeridas = {
#         "nombre_indice": str
#     }

#     def setup(self, *args, **kwargs):
#         super().setup(**kwargs)
#         nombre_indice = kwargs.get("nombre_indice")
#         mapeo_indice = get_elasticsearch_client().indices.get_mapping(index=nombre_indice)
#         self.propiedades = mapeo_indice[nombre_indice]["mappings"]["properties"]

#     def handle(self, df):
#         errores = []

#         # Mapear tipos de Elasticsearch a tipos de pandas
#         tipo_mapeo = {
#             "text": "object",
#             "keyword": "object",
#             "integer": "int64",
#             "long": "int64",
#             "short": "int64",
#             "byte": "int64",
#             "float": "float64",
#             "double": "float64",
#             "boolean": "bool",
#             "date": "datetime64[ns]",

#         }

#         for columna, tipo in self.propiedades.items():
#             tipo_esperado = tipo_mapeo.get(tipo.get("type"))
#             if columna in df.columns:
#                 tipo_real = str(df[columna].dtype)
#                 if tipo_real != tipo_esperado:
#                     errores.append(
#                         f"Columna '{columna}' tiene tipo '{tipo_real}', "
#                         f"pero se esperaba '{tipo_esperado}'."
#                     )
#             else:
#                 errores.append(f"Columna '{columna}' no está presente en el DataFrame.")

#         if errores:
#             raise ValueError("Errores de validación de estructura:\n" + "\n".join(errores))