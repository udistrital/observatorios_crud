import json
import re

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from elasticsearch import NotFoundError


PATRON_ESTRUCTURA_DOCUMENTAL = re.compile(
    r"^atlas_estructura_documental_"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-"
    r"[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
PATRON_DOCUMENTO_GESTOR = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
    r"[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
PREFIJO_REFERENCIA = "v1_"
CAMPOS_REFERENCIA = {
    "proceso_id",
    "factor_id",
    "estructura_id",
    "documento_id",
}


class DocumentoNoAsociado(Exception):
    pass


class ReferenciaDocumentoInvalida(Exception):
    pass


def _obtener_fernet():
    try:
        clave = str(settings.DOCUMENT_REFERENCE_KEY or "").encode("ascii")
        return Fernet(clave)
    except (TypeError, UnicodeError, ValueError):
        raise RuntimeError(
            "La clave de referencias documentales no está configurada."
        )


def cifrar_referencia_documento(contexto):
    contenido = {
        campo: str(contexto.get(campo) or "").strip()
        for campo in CAMPOS_REFERENCIA
    }

    if any(not valor for valor in contenido.values()):
        raise ValueError("El contexto documental está incompleto.")

    plano = json.dumps(
        contenido,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    token = _obtener_fernet().encrypt(plano).decode("ascii").rstrip("=")
    return f"{PREFIJO_REFERENCIA}{token}"


def descifrar_referencia_documento(referencia):
    referencia = str(referencia or "").strip()

    if (
        not referencia.startswith(PREFIJO_REFERENCIA)
        or len(referencia) > 8192
    ):
        raise ReferenciaDocumentoInvalida

    token = referencia[len(PREFIJO_REFERENCIA):]
    token += "=" * (-len(token) % 4)

    try:
        plano = _obtener_fernet().decrypt(
            token.encode("ascii"),
            ttl=settings.DOCUMENT_REFERENCE_TTL_SECONDS,
        )
        contenido = json.loads(plano.decode("utf-8"))
    except (InvalidToken, UnicodeError, ValueError, json.JSONDecodeError):
        raise ReferenciaDocumentoInvalida

    if not isinstance(contenido, dict) or set(contenido) != CAMPOS_REFERENCIA:
        raise ReferenciaDocumentoInvalida

    contenido = {
        campo: str(contenido.get(campo) or "").strip()
        for campo in CAMPOS_REFERENCIA
    }

    if any(not valor for valor in contenido.values()):
        raise ReferenciaDocumentoInvalida

    return contenido


def _obtener_fuente(cliente, indice, documento_id):
    if not indice or not documento_id:
        raise DocumentoNoAsociado

    try:
        respuesta = cliente.get(index=indice, id=documento_id)
    except NotFoundError:
        raise DocumentoNoAsociado

    fuente = respuesta.get("_source")

    if not isinstance(fuente, dict):
        raise DocumentoNoAsociado

    id_fuente = fuente.get("id")

    if id_fuente and str(id_fuente) != str(documento_id):
        raise DocumentoNoAsociado

    if fuente.get("activo") is not True:
        raise DocumentoNoAsociado

    return fuente


def validar_asociacion_documento(
    cliente,
    proceso_id,
    factor_id,
    estructura_id,
    documento_id,
):
    proceso_id = str(proceso_id or "").strip()
    factor_id = str(factor_id or "").strip()
    estructura_id = str(estructura_id or "").strip()
    documento_id = str(documento_id or "").strip()

    if (
        not proceso_id
        or not factor_id
        or not PATRON_DOCUMENTO_GESTOR.fullmatch(documento_id)
        or not PATRON_ESTRUCTURA_DOCUMENTAL.fullmatch(estructura_id)
    ):
        raise DocumentoNoAsociado

    estructura = _obtener_fuente(cliente, estructura_id, estructura_id)

    if estructura.get("tipo_evidencia") != "Documental":
        raise DocumentoNoAsociado

    aspecto_id = str(estructura.get("aspecto_id") or "").strip()
    aspecto = _obtener_fuente(cliente, "atlas_aspectos", aspecto_id)
    caracteristica_id = str(
        aspecto.get("caracteristica_id") or ""
    ).strip()
    caracteristica = _obtener_fuente(
        cliente,
        "atlas_caracteristicas",
        caracteristica_id,
    )
    factor_derivado = str(caracteristica.get("factor_id") or "").strip()

    if factor_derivado != factor_id:
        raise DocumentoNoAsociado

    factor = _obtener_fuente(cliente, "atlas_factores", factor_id)

    if str(factor.get("proceso_id") or "").strip() != proceso_id:
        raise DocumentoNoAsociado

    _obtener_fuente(cliente, "atlas_procesos", proceso_id)

    campos = estructura.get("campos")
    registros = estructura.get("data")

    if not isinstance(campos, list) or not isinstance(registros, list):
        raise DocumentoNoAsociado

    campos_hash = [
        campo
        for campo in campos
        if isinstance(campo, dict)
        and campo.get("activo") is True
        and str(campo.get("nombre_campo") or "").strip().lower() == "hash"
        and campo.get("campo_id")
    ]

    if len(campos_hash) != 1:
        raise DocumentoNoAsociado

    campo_hash = campos_hash[0]
    campo_hash_id = campo_hash["campo_id"]
    nombre_hash = campo_hash.get("nombre_campo") or "hash"
    coincidencias = 0

    for registro in registros:
        if not isinstance(registro, dict) or registro.get("activo") is not True:
            continue

        valores = registro.get("valores")

        if isinstance(valores, dict) and campo_hash_id in valores:
            valor_hash = valores.get(campo_hash_id)
        else:
            valor_hash = registro.get(nombre_hash)

        if str(valor_hash or "").strip() == documento_id:
            coincidencias += 1

    if coincidencias != 1:
        raise DocumentoNoAsociado

    return {
        "proceso_id": proceso_id,
        "factor_id": factor_id,
        "estructura_id": estructura_id,
        "documento_id": documento_id,
    }
