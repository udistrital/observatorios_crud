import re
import uuid
from datetime import datetime


TIPOS_CAMPOS_PERMITIDOS = [
    "text",
    "keyword",
    "long",
    "integer",
    "short",
    "byte",
    "double",
    "float",
    "half_float",
    "scaled_float",
    "boolean",
    "date",
    "date_nanos",
    "geo_point",
    "geo_shape",
    "ip",
    "binary",
    "object",
    "nested",
    "token_count",
    "integer_range",
    "float_range",
    "long_range",
    "double_range",
    "date_range",
    "ip_range",
    "constant_keyword",
    "flattened",
    "shape",
]


def generar_campo_id():
    return f"campo_{uuid.uuid4().hex[:12]}"


def obtener_mapping_tipo_campo(tipo_campo):
    if tipo_campo == "text":
        return {
            "type": "text",
            "fields": {
                "keyword": {
                    "type": "keyword"
                }
            }
        }

    if tipo_campo in ["keyword", "constant_keyword"]:
        return {
            "type": tipo_campo
        }

    if tipo_campo == "token_count":
        return {
            "type": "token_count",
            "analyzer": "standard"
        }

    if tipo_campo == "scaled_float":
        return {
            "type": "scaled_float",
            "scaling_factor": 100
        }

    if tipo_campo in [
        "long",
        "integer",
        "short",
        "byte",
        "double",
        "float",
        "half_float",
        "boolean",
        "date",
        "date_nanos",
        "geo_point",
        "geo_shape",
        "ip",
        "binary",
        "object",
        "nested",
        "integer_range",
        "float_range",
        "long_range",
        "double_range",
        "date_range",
        "ip_range",
        "flattened",
        "shape",
    ]:
        return {
            "type": tipo_campo
        }

    return {
        "type": "keyword"
    }


def validar_nombre_campo(nombre_campo):
    if not nombre_campo:
        raise ValueError("El nombre del campo es obligatorio.")

    if not isinstance(nombre_campo, str):
        raise ValueError("El nombre del campo debe ser texto.")

    nombre_campo = nombre_campo.strip()

    if not nombre_campo:
        raise ValueError("El nombre del campo es obligatorio.")

    return nombre_campo


def normalizar_tipo_campo(tipo_campo):
    if not tipo_campo:
        return "text"

    tipo_campo = str(tipo_campo).strip()

    if tipo_campo not in TIPOS_CAMPOS_PERMITIDOS:
        raise ValueError(
            f"El tipo de campo '{tipo_campo}' no está permitido."
        )

    return tipo_campo


def convertir_valor_por_tipo(valor, tipo_campo):
    if valor in [None, ""]:
        return None

    if tipo_campo in ["text", "keyword", "constant_keyword"]:
        return str(valor)

    if tipo_campo in ["integer", "long", "short", "byte"]:
        try:
            return int(valor)
        except Exception:
            raise ValueError("Debe ser un número entero.")

    if tipo_campo in ["double", "float", "half_float", "scaled_float"]:
        try:
            return float(valor)
        except Exception:
            raise ValueError("Debe ser un número decimal.")

    if tipo_campo == "boolean":
        if isinstance(valor, bool):
            return valor

        if isinstance(valor, str):
            valor_normalizado = valor.strip().lower()

            if valor_normalizado in ["true", "1", "si", "sí"]:
                return True

            if valor_normalizado in ["false", "0", "no"]:
                return False

        raise ValueError("Debe ser verdadero o falso.")

    if tipo_campo in ["date", "date_nanos"]:
        if not isinstance(valor, str):
            raise ValueError("Debe ser una fecha válida.")

        valor = valor.strip()

        formatos = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%d/%m/%Y",
        ]

        for formato in formatos:
            try:
                datetime.strptime(valor, formato)
                return valor
            except Exception:
                continue

        raise ValueError("Debe tener formato YYYY-MM-DD, ISO 8601 o DD/MM/YYYY.")

    return valor


def normalizar_campos_con_ids(campos_entrantes, campos_actuales=None):
    campos_actuales = campos_actuales or []
    campos_entrantes = campos_entrantes or []

    campos_actuales_por_id = {
        campo.get("campo_id"): campo
        for campo in campos_actuales
        if campo.get("campo_id")
    }

    campos_resultado = []
    migraciones = []

    for index, campo in enumerate(campos_entrantes, start=1):
        nombre_campo = validar_nombre_campo(campo.get("nombre_campo"))
        tipo_campo = normalizar_tipo_campo(campo.get("tipo_campo", "text"))
        campo_id = campo.get("campo_id")
        orden = campo.get("orden") or index
        activo = campo.get("activo", True)
        migrar_data = campo.get("migrar_data", False)

        if campo_id and campo_id in campos_actuales_por_id:
            campo_actual = campos_actuales_por_id[campo_id]
            tipo_actual = campo_actual.get("tipo_campo")

            if tipo_actual == tipo_campo:
                campos_resultado.append(
                    {
                        "campo_id": campo_id,
                        "orden": orden,
                        "nombre_campo": nombre_campo,
                        "tipo_campo": tipo_campo,
                        "activo": activo,
                    }
                )
            else:
                nuevo_campo_id = generar_campo_id()

                campos_resultado.append(
                    {
                        "campo_id": nuevo_campo_id,
                        "orden": orden,
                        "nombre_campo": nombre_campo,
                        "tipo_campo": tipo_campo,
                        "activo": activo,
                    }
                )

                migraciones.append(
                    {
                        "campo_anterior_id": campo_id,
                        "campo_nuevo_id": nuevo_campo_id,
                        "tipo_nuevo": tipo_campo,
                        "migrar_data": bool(migrar_data),
                    }
                )
        else:
            nuevo_campo_id = campo_id or generar_campo_id()

            campos_resultado.append(
                {
                    "campo_id": nuevo_campo_id,
                    "orden": orden,
                    "nombre_campo": nombre_campo,
                    "tipo_campo": tipo_campo,
                    "activo": activo,
                }
            )

    campos_resultado = sorted(
        campos_resultado,
        key=lambda item: item.get("orden") or 999999
    )

    return campos_resultado, migraciones


def construir_valores_registro(campos, data_usuario):
    if not isinstance(data_usuario, dict):
        raise ValueError("El registro debe ser un objeto JSON.")

    valores_entrada = data_usuario.get("valores")

    if not isinstance(valores_entrada, dict):
        valores_entrada = data_usuario

    valores = {}

    for campo in campos or []:
        if campo.get("activo") is False:
            continue

        campo_id = campo.get("campo_id")
        nombre_campo = campo.get("nombre_campo")
        tipo_campo = campo.get("tipo_campo", "text")

        if not campo_id:
            continue

        valor = None

        if campo_id in valores_entrada:
            valor = valores_entrada.get(campo_id)
        elif nombre_campo in valores_entrada:
            valor = valores_entrada.get(nombre_campo)

        try:
            valores[campo_id] = convertir_valor_por_tipo(
                valor,
                tipo_campo
            )
        except ValueError as error:
            raise ValueError(
                {
                    nombre_campo: error.args[0]
                }
            )

    return valores


def aplicar_migraciones_data(data, migraciones, campos):
    if not migraciones:
        return data

    campos_por_id = {
        campo.get("campo_id"): campo
        for campo in campos or []
        if campo.get("campo_id")
    }

    data_resultado = []

    for fila in data or []:
        if not isinstance(fila, dict):
            continue

        valores = fila.get("valores", {})

        if not isinstance(valores, dict):
            valores = {}

        for migracion in migraciones:
            campo_anterior_id = migracion.get("campo_anterior_id")
            campo_nuevo_id = migracion.get("campo_nuevo_id")
            migrar_data = migracion.get("migrar_data", False)

            valor_anterior = valores.pop(campo_anterior_id, None)

            if migrar_data and campo_nuevo_id:
                campo_nuevo = campos_por_id.get(campo_nuevo_id)

                if campo_nuevo:
                    try:
                        valores[campo_nuevo_id] = convertir_valor_por_tipo(
                            valor_anterior,
                            campo_nuevo.get("tipo_campo")
                        )
                    except ValueError:
                        valores[campo_nuevo_id] = None

        fila["valores"] = valores
        data_resultado.append(fila)

    return data_resultado

def obtener_tipos_campos():
    return [
        {"label": "Texto", "value": "text"},
        {"label": "Palabra clave", "value": "keyword"},
        {"label": "Largo", "value": "long"},
        {"label": "Entero", "value": "integer"},
        {"label": "Corto", "value": "short"},
        {"label": "Byte", "value": "byte"},
        {"label": "Doble", "value": "double"},
        {"label": "Flotante", "value": "float"},
        {"label": "Medio flotante", "value": "half_float"},
        {"label": "Flotante escalado", "value": "scaled_float"},
        {"label": "Booleano", "value": "boolean"},
        {"label": "Fecha", "value": "date"},
        {"label": "Fecha con nanosegundos", "value": "date_nanos"},
        {"label": "Punto geográfico", "value": "geo_point"},
        {"label": "Forma geográfica", "value": "geo_shape"},
        {"label": "Dirección IP", "value": "ip"},
        {"label": "Binario", "value": "binary"},
        {"label": "Objeto", "value": "object"},
        {"label": "Anidado", "value": "nested"},
        {"label": "Conteo de tokens", "value": "token_count"},
        {"label": "Rango de enteros", "value": "integer_range"},
        {"label": "Rango de flotantes", "value": "float_range"},
        {"label": "Rango de largos", "value": "long_range"},
        {"label": "Rango de dobles", "value": "double_range"},
        {"label": "Rango de fechas", "value": "date_range"},
        {"label": "Rango de IPs", "value": "ip_range"},
        {"label": "Palabra clave constante", "value": "constant_keyword"},
        {"label": "Aplanado", "value": "flattened"},
        {"label": "Forma", "value": "shape"},
    ]

def aplicar_filtros(filas, query_params):
    if not isinstance(filas, list):
        return []

    filtros_excluidos = {
        "page",
        "page_size",
        "ordering",
        "format",
    }

    resultado = filas

    for clave, valor in query_params.items():
        if clave in filtros_excluidos:
            continue

        if valor in [None, ""]:
            continue

        valor_busqueda = str(valor).lower()

        resultado = [
            fila
            for fila in resultado
            if valor_busqueda in str(fila.get(clave, "")).lower()
        ]

    return resultado


def aplicar_ordenamiento(filas, ordering=None):
    if not ordering:
        return filas

    if not isinstance(filas, list):
        return []

    descendente = False
    campo = ordering

    if ordering.startswith("-"):
        descendente = True
        campo = ordering[1:]

    try:
        return sorted(
            filas,
            key=lambda fila: (
                fila.get(campo) is None,
                fila.get(campo)
            ),
            reverse=descendente
        )
    except Exception:
        return filas


def paginar_resultados(filas, page=1, page_size=10):
    if not isinstance(filas, list):
        filas = []

    try:
        page = int(page)
    except Exception:
        page = 1

    try:
        page_size = int(page_size)
    except Exception:
        page_size = 10

    if page < 1:
        page = 1

    if page_size < 1:
        page_size = 10

    total = len(filas)
    inicio = (page - 1) * page_size
    fin = inicio + page_size

    return {
        "count": total,
        "page": page,
        "page_size": page_size,
        "results": filas[inicio:fin],
    }


def eliminar_campos_de_data(data, campos_eliminados):
    if not isinstance(data, list):
        return []

    if not campos_eliminados:
        return data

    resultado = []

    for fila in data:
        if not isinstance(fila, dict):
            resultado.append(fila)
            continue

        valores = fila.get("valores")

        if isinstance(valores, dict):
            for campo in campos_eliminados:
                valores.pop(campo, None)

            fila["valores"] = valores

        for campo in campos_eliminados:
            fila.pop(campo, None)

        resultado.append(fila)

    return resultado
