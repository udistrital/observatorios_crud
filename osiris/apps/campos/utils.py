import base64
import ipaddress
import json
import re
from datetime import datetime


ELASTICSEARCH_CAMPOS = {
    "text": {"label": "Texto", "value": "text"},
    "keyword": {"label": "Palabra clave", "value": "keyword"},
    "long": {"label": "Largo", "value": "long"},
    "integer": {"label": "Entero", "value": "integer"},
    "short": {"label": "Corto", "value": "short"},
    "byte": {"label": "Byte", "value": "byte"},
    "double": {"label": "Doble", "value": "double"},
    "float": {"label": "Flotante", "value": "float"},
    "half_float": {"label": "Medio flotante", "value": "half_float"},
    "scaled_float": {"label": "Flotante escalado", "value": "scaled_float"},
    "boolean": {"label": "Booleano", "value": "boolean"},
    "date": {"label": "Fecha", "value": "date"},
    "date_nanos": {"label": "Fecha con nanosegundos", "value": "date_nanos"},
    "geo_point": {"label": "Punto geográfico", "value": "geo_point"},
    "geo_shape": {"label": "Forma geográfica", "value": "geo_shape"},
    "ip": {"label": "Dirección IP", "value": "ip"},
    "binary": {"label": "Binario", "value": "binary"},
    "object": {"label": "Objeto", "value": "object"},
    "nested": {"label": "Anidado", "value": "nested"},
    "token_count": {"label": "Conteo de tokens", "value": "token_count"},
    "integer_range": {"label": "Rango de enteros", "value": "integer_range"},
    "float_range": {"label": "Rango de flotantes", "value": "float_range"},
    "long_range": {"label": "Rango de largos", "value": "long_range"},
    "double_range": {"label": "Rango de dobles", "value": "double_range"},
    "date_range": {"label": "Rango de fechas", "value": "date_range"},
    "ip_range": {"label": "Rango de IPs", "value": "ip_range"},
    "constant_keyword": {
        "label": "Palabra clave constante",
        "value": "constant_keyword",
    },
    "flattened": {"label": "Aplanado", "value": "flattened"},
    "shape": {"label": "Forma", "value": "shape"},
}


TIPOS_TEXTO = {
    "text",
    "keyword",
    "constant_keyword",
    "token_count",
}

TIPOS_ENTEROS = {
    "long": None,
    "integer": (-2147483648, 2147483647),
    "short": (-32768, 32767),
    "byte": (-128, 127),
}

TIPOS_DECIMALES = {
    "double",
    "float",
    "half_float",
    "scaled_float",
}

TIPOS_JSON = {
    "object",
    "nested",
    "flattened",
    "geo_shape",
    "shape",
}

TIPOS_RANGO = {
    "integer_range",
    "float_range",
    "long_range",
    "double_range",
    "date_range",
    "ip_range",
}


def obtener_tipos_campos():
    return list(ELASTICSEARCH_CAMPOS.values())


def validar_nombre_campo(nombre_campo):
    if not isinstance(nombre_campo, str):
        raise ValueError("El nombre del campo debe ser texto.")

    nombre_campo = nombre_campo.strip()

    if not nombre_campo:
        raise ValueError("El nombre del campo es obligatorio.")

    if not re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", nombre_campo):
        raise ValueError(
            "El nombre del campo solo puede tener letras, números y guion bajo. "
            "Debe iniciar con letra o guion bajo."
        )

    return nombre_campo


def validar_tipo_campo(tipo_campo):
    if not isinstance(tipo_campo, str):
        raise ValueError("El tipo del campo debe ser texto.")

    tipo_campo = tipo_campo.strip()

    if tipo_campo not in ELASTICSEARCH_CAMPOS:
        raise ValueError(
            f"Tipo de campo inválido '{tipo_campo}'. "
            f"Permitidos: {list(ELASTICSEARCH_CAMPOS.keys())}"
        )

    return tipo_campo


def normalizar_campos(campos):
    if campos is None:
        return []

    if not isinstance(campos, list):
        raise ValueError("El campo campos debe ser una lista.")

    resultado = []
    nombres = set()

    for campo in campos:
        if not isinstance(campo, dict):
            raise ValueError("Cada campo debe ser un objeto.")

        nombre_campo = validar_nombre_campo(campo.get("nombre_campo"))
        tipo_campo = validar_tipo_campo(campo.get("tipo_campo", "text"))

        nombre_normalizado = nombre_campo.lower()

        if nombre_normalizado in nombres:
            raise ValueError(f"El campo '{nombre_campo}' está repetido.")

        nombres.add(nombre_normalizado)

        resultado.append(
            {
                "nombre_campo": nombre_campo,
                "tipo_campo": tipo_campo,
            }
        )

    return resultado


def normalizar_fecha(valor):
    if valor in [None, ""]:
        return None

    if isinstance(valor, datetime):
        return valor.date().isoformat()

    formatos = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
    ]

    for formato in formatos:
        try:
            return datetime.strptime(str(valor), formato).date().isoformat()
        except ValueError:
            continue

    raise ValueError("Debe tener formato YYYY-MM-DD o DD/MM/YYYY.")


def validar_entero(nombre_campo, tipo_campo, valor):
    if valor in [None, ""]:
        return None

    if isinstance(valor, bool):
        raise ValueError(f"El campo '{nombre_campo}' debe ser entero.")

    try:
        numero = int(valor)
    except Exception:
        raise ValueError(f"El campo '{nombre_campo}' debe ser entero.")

    rango = TIPOS_ENTEROS.get(tipo_campo)

    if rango:
        minimo, maximo = rango

        if numero < minimo or numero > maximo:
            raise ValueError(
                f"El campo '{nombre_campo}' debe estar entre {minimo} y {maximo}."
            )

    return numero


def validar_decimal(nombre_campo, valor):
    if valor in [None, ""]:
        return None

    if isinstance(valor, bool):
        raise ValueError(f"El campo '{nombre_campo}' debe ser numérico.")

    try:
        return float(valor)
    except Exception:
        raise ValueError(f"El campo '{nombre_campo}' debe ser numérico.")


def validar_booleano(nombre_campo, valor):
    if valor in [None, ""]:
        return None

    if isinstance(valor, bool):
        return valor

    if isinstance(valor, str):
        valor_normalizado = valor.strip().lower()

        if valor_normalizado in ["true", "1", "si", "sí"]:
            return True

        if valor_normalizado in ["false", "0", "no"]:
            return False

    raise ValueError(f"El campo '{nombre_campo}' debe ser booleano.")


def validar_ip(nombre_campo, valor):
    if valor in [None, ""]:
        return None

    try:
        return str(ipaddress.ip_address(valor))
    except Exception:
        raise ValueError(f"El campo '{nombre_campo}' debe ser una IP válida.")


def validar_binary(nombre_campo, valor):
    if valor in [None, ""]:
        return None

    if not isinstance(valor, str):
        raise ValueError(f"El campo '{nombre_campo}' debe ser base64.")

    try:
        base64.b64decode(valor, validate=True)
        return valor
    except Exception:
        raise ValueError(f"El campo '{nombre_campo}' debe ser base64 válido.")


def normalizar_json(nombre_campo, valor):
    if valor in [None, ""]:
        return None

    if isinstance(valor, (dict, list)):
        return valor

    if isinstance(valor, str):
        try:
            return json.loads(valor)
        except Exception:
            raise ValueError(f"El campo '{nombre_campo}' debe ser JSON válido.")

    raise ValueError(f"El campo '{nombre_campo}' debe ser un objeto o arreglo JSON.")


def validar_geo_point(nombre_campo, valor):
    if valor in [None, ""]:
        return None

    if isinstance(valor, dict):
        if "lat" not in valor or "lon" not in valor:
            raise ValueError(
                f"El campo '{nombre_campo}' debe contener lat y lon."
            )

        return {
            "lat": float(valor["lat"]),
            "lon": float(valor["lon"]),
        }

    if isinstance(valor, str):
        partes = valor.split(",")

        if len(partes) != 2:
            raise ValueError(
                f"El campo '{nombre_campo}' debe tener formato 'lat,lon'."
            )

        return {
            "lat": float(partes[0].strip()),
            "lon": float(partes[1].strip()),
        }

    raise ValueError(
        f"El campo '{nombre_campo}' debe ser un objeto {{lat, lon}} o texto 'lat,lon'."
    )


def validar_rango(nombre_campo, tipo_campo, valor):
    valor = normalizar_json(nombre_campo, valor)

    if valor is None:
        return None

    if not isinstance(valor, dict):
        raise ValueError(f"El campo '{nombre_campo}' debe ser un objeto de rango.")

    claves_validas = {"gte", "gt", "lte", "lt"}

    if not any(clave in valor for clave in claves_validas):
        raise ValueError(
            f"El campo '{nombre_campo}' debe tener al menos gte, gt, lte o lt."
        )

    resultado = {}

    for clave, dato in valor.items():
        if clave not in claves_validas:
            raise ValueError(
                f"El campo '{nombre_campo}' tiene una clave inválida: {clave}."
            )

        if tipo_campo == "date_range":
            resultado[clave] = normalizar_fecha(dato)
        elif tipo_campo == "ip_range":
            resultado[clave] = validar_ip(nombre_campo, dato)
        elif tipo_campo in ["integer_range", "long_range"]:
            resultado[clave] = validar_entero(nombre_campo, "long", dato)
        else:
            resultado[clave] = validar_decimal(nombre_campo, dato)

    return resultado


def validar_valor_por_tipo(nombre_campo, tipo_campo, valor):
    if tipo_campo in TIPOS_TEXTO:
        if valor in [None, ""]:
            return None

        return str(valor)

    if tipo_campo in TIPOS_ENTEROS:
        return validar_entero(nombre_campo, tipo_campo, valor)

    if tipo_campo in TIPOS_DECIMALES:
        return validar_decimal(nombre_campo, valor)

    if tipo_campo == "boolean":
        return validar_booleano(nombre_campo, valor)

    if tipo_campo in ["date", "date_nanos"]:
        return normalizar_fecha(valor)

    if tipo_campo == "ip":
        return validar_ip(nombre_campo, valor)

    if tipo_campo == "binary":
        return validar_binary(nombre_campo, valor)

    if tipo_campo == "geo_point":
        return validar_geo_point(nombre_campo, valor)

    if tipo_campo in TIPOS_JSON:
        return normalizar_json(nombre_campo, valor)

    if tipo_campo in TIPOS_RANGO:
        return validar_rango(nombre_campo, tipo_campo, valor)

    if valor in [None, ""]:
        return None

    return valor


def obtener_campos_por_nombre(campos):
    return {
        campo["nombre_campo"]: campo
        for campo in normalizar_campos(campos)
    }


def validar_registro_con_campos(campos, data):
    if not isinstance(data, dict):
        raise ValueError("El registro debe ser un objeto JSON.")

    campos_por_nombre = obtener_campos_por_nombre(campos)

    errores = {}
    registro = {}

    for clave in data.keys():
        if clave not in campos_por_nombre:
            errores[clave] = "Este campo no existe en la estructura."

    for nombre_campo, campo in campos_por_nombre.items():
        tipo_campo = campo.get("tipo_campo", "text")
        valor = data.get(nombre_campo)

        try:
            registro[nombre_campo] = validar_valor_por_tipo(
                nombre_campo,
                tipo_campo,
                valor
            )
        except ValueError as error:
            errores[nombre_campo] = str(error)

    if errores:
        raise ValueError(errores)

    return registro


def eliminar_campos_de_data(data, campos_eliminados):
    if not isinstance(data, list):
        return []

    if not campos_eliminados:
        return data

    campos_eliminados = set(campos_eliminados)
    resultado = []

    for fila in data:
        if not isinstance(fila, dict):
            resultado.append(fila)
            continue

        nueva_fila = {
            clave: valor
            for clave, valor in fila.items()
            if clave not in campos_eliminados
        }

        resultado.append(nueva_fila)

    return resultado


def aplicar_filtros(filas, params):
    filtros = {
        clave: valor
        for clave, valor in params.items()
        if clave not in ["page", "page_size", "ordering"]
        and valor not in [None, ""]
    }

    if not filtros:
        return filas

    resultado = []

    for fila in filas:
        cumple = True

        for clave, valor in filtros.items():
            valor_fila = fila.get(clave)

            if valor_fila is None:
                cumple = False
                break

            if str(valor).lower() not in str(valor_fila).lower():
                cumple = False
                break

        if cumple:
            resultado.append(fila)

    return resultado


def aplicar_ordenamiento(filas, ordering):
    if not ordering:
        return filas

    descendente = ordering.startswith("-")
    campo = ordering[1:] if descendente else ordering

    return sorted(
        filas,
        key=lambda item: item.get(campo) if item.get(campo) is not None else "",
        reverse=descendente
    )


def paginar_resultados(filas, page, page_size):
    total = len(filas)
    inicio = (page - 1) * page_size
    fin = inicio + page_size

    return {
        "count": total,
        "next": page + 1 if fin < total else None,
        "previous": page - 1 if inicio > 0 else None,
        "results": filas[inicio:fin],
    }
