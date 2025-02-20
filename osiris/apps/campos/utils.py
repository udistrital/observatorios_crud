

ELASTICSEARCH_CAMPOS ={
    "text": {
        "nombre": "text",
        "nombre_espanol": "texto",
        "categoria": "textual",
        "descripcion": "Campo analizado para búsquedas completas; adecuado para texto no estructurado."
    },
    "keyword": {
        "nombre": "keyword",
        "nombre_espanol": "palabra clave",
        "categoria": "textual",
        "descripcion": "Campo no analizado, útil para valores exactos como etiquetas o identificadores."
    },
    "long": {
        "nombre": "long",
        "nombre_espanol": "largo",
        "categoria": "numerico",
        "descripcion": "Número entero de 64 bits."
    },
    "integer": {
        "nombre": "integer",
        "nombre_espanol": "entero",
        "categoria": "numerico",
        "descripcion": "Número entero de 32 bits."
    },
    "short": {
        "nombre": "short",
        "nombre_espanol": "corto",
        "categoria": "numerico",
        "descripcion": "Número entero de 16 bits."
    },
    "byte": {
        "nombre": "byte",
        "nombre_espanol": "byte",
        "categoria": "numerico",
        "descripcion": "Número entero de 8 bits."
    },
    "double": {
        "nombre": "double",
        "nombre_espanol": "doble",
        "categoria": "numerico",
        "descripcion": "Número de punto flotante de doble precisión."
    },
    "float": {
        "nombre": "float",
        "nombre_espanol": "flotante",
        "categoria": "numerico",
        "descripcion": "Número de punto flotante de precisión simple."
    },
    "half_float": {
        "nombre": "half_float",
        "nombre_espanol": "medio flotante",
        "categoria": "numerico",
        "descripcion": "Número de punto flotante de baja precisión para ahorrar espacio."
    },
    "scaled_float": {
        "nombre": "scaled_float",
        "nombre_espanol": "flotante escalado",
        "categoria": "numerico",
        "descripcion": "Número de punto flotante escalado con un multiplicador fijo, útil para optimizar cálculos."
    },
    "boolean": {
        "nombre": "boolean",
        "nombre_espanol": "booleano",
        "categoria": "booleano",
        "descripcion": "Campo booleano que acepta valores `true` o `false`."
    },
    "date": {
        "nombre": "date",
        "nombre_espanol": "fecha",
        "categoria": "fecha",
        "descripcion": "Campo de fecha, almacena fechas y horas en varios formatos."
    },
    "date_nanos": {
        "nombre": "date_nanos",
        "nombre_espanol": "fecha con nanosegundos",
        "categoria": "fecha",
        "descripcion": "Campo de fecha con precisión de nanosegundos."
    },
    "geo_point": {
        "nombre": "geo_point",
        "nombre_espanol": "punto geográfico",
        "categoria": "geoespacial",
        "descripcion": "Coordenadas geográficas (latitud y longitud)."
    },
    "geo_shape": {
        "nombre": "geo_shape",
        "nombre_espanol": "forma geográfica",
        "categoria": "geoespacial",
        "descripcion": "Formas geográficas complejas como polígonos, líneas y círculos."
    },
    "ip": {
        "nombre": "ip",
        "nombre_espanol": "dirección IP",
        "categoria": "especializado",
        "descripcion": "Direcciones IP en formatos IPv4 e IPv6."
    },
    "binary": {
        "nombre": "binary",
        "nombre_espanol": "binario",
        "categoria": "especializado",
        "descripcion": "Datos binarios codificados en Base64."
    },
    "object": {
        "nombre": "object",
        "nombre_espanol": "objeto",
        "categoria": "objeto",
        "descripcion": "Objeto JSON que no se indexa directamente, útil para datos anidados."
    },
    "nested": {
        "nombre": "nested",
        "nombre_espanol": "anidado",
        "categoria": "objeto",
        "descripcion": "Objeto anidado indexado como documentos independientes."
    },
    "token_count": {
        "nombre": "token_count",
        "nombre_espanol": "conteo de tokens",
        "categoria": "análisis de texto",
        "descripcion": "Almacena el número de tokens generados por el analizador de texto."
    },
    "integer_range": {
        "nombre": "integer_range",
        "nombre_espanol": "rango de enteros",
        "categoria": "rango",
        "descripcion": "Rango de valores enteros."
    },
    "float_range": {
        "nombre": "float_range",
        "nombre_espanol": "rango de flotantes",
        "categoria": "rango",
        "descripcion": "Rango de valores de punto flotante."
    },
    "long_range": {
        "nombre": "long_range",
        "nombre_espanol": "rango de largos",
        "categoria": "rango",
        "descripcion": "Rango de valores enteros largos."
    },
    "double_range": {
        "nombre": "double_range",
        "nombre_espanol": "rango de dobles",
        "categoria": "rango",
        "descripcion": "Rango de valores de punto flotante de doble precisión."
    },
    "date_range": {
        "nombre": "date_range",
        "nombre_espanol": "rango de fechas",
        "categoria": "rango",
        "descripcion": "Rango de fechas."
    },
    "ip_range": {
        "nombre": "ip_range",
        "nombre_espanol": "rango de IPs",
        "categoria": "rango",
        "descripcion": "Rango de direcciones IP."
    },
    "constant_keyword": {
        "nombre": "constant_keyword",
        "nombre_espanol": "palabra clave constante",
        "categoria": "constante",
        "descripcion": "Almacena un único valor constante para todos los documentos."
    },
    "flattened": {
        "nombre": "flattened",
        "nombre_espanol": "aplanado",
        "categoria": "experimental",
        "descripcion": "Almacena claves y valores de un JSON como un solo campo plano."
    },
    "shape": {
        "nombre": "shape",
        "nombre_espanol": "forma",
        "categoria": "experimental",
        "descripcion": "Almacena y busca formas geométricas no geográficas."
    }
}
