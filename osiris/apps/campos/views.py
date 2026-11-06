import io
import logging
import os
import pwd
import signal
import subprocess
import tempfile
import threading
import zipfile
from pathlib import Path
from xml.etree import ElementTree

import olefile
from django.conf import settings
from django.http import HttpResponse
from elasticsearch import NotFoundError
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .models import EstructuraCamposModelo
from .serializers import EstructuraUpdateSerializer
from .utils import (
    aplicar_filtros,
    aplicar_migraciones_data,
    aplicar_ordenamiento,
    construir_valores_registro,
    eliminar_campos_de_data,
    normalizar_campos_con_ids,
    obtener_mapping_tipo_campo,
    obtener_tipos_campos,
    paginar_resultados,
)


logger = logging.getLogger(__name__)

TIPOS_OFFICE_PERMITIDOS = {
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
MIMES_GENERICOS = {"", "application/octet-stream"}
FIRMA_OLE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
SEMAFORO_CONVERSION = threading.BoundedSemaphore(1)


class ErrorVistaPrevia(Exception):
    def __init__(self, mensaje, codigo_estado):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo_estado = codigo_estado


def _validar_paquete_ooxml(contenido, extension):
    try:
        with zipfile.ZipFile(io.BytesIO(contenido)) as paquete:
            miembros = paquete.infolist()

            if len(miembros) > 5000:
                raise ErrorVistaPrevia(
                    "El documento Office contiene demasiados elementos.",
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            maximo_expandido = settings.DOCUMENT_PREVIEW_MAX_BYTES * 20
            total_expandido = 0
            nombres = set()

            for miembro in miembros:
                total_expandido += miembro.file_size
                nombres.add(miembro.filename.lower())

                if miembro.flag_bits & 0x1:
                    raise ErrorVistaPrevia(
                        "No se pueden previsualizar documentos cifrados.",
                        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    )

                if (
                    miembro.file_size > 1024 * 1024
                    and miembro.file_size > max(1, miembro.compress_size) * 200
                ):
                    raise ErrorVistaPrevia(
                        "El documento Office no es seguro para previsualizar.",
                        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    )

            if total_expandido > maximo_expandido:
                raise ErrorVistaPrevia(
                    "El documento Office expandido supera el limite permitido.",
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                )

            parte_principal = (
                "word/document.xml"
                if extension == ".docx"
                else "xl/workbook.xml"
            )
            content_type_principal = (
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document.main+xml"
                if extension == ".docx"
                else "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet.main+xml"
            )

            if (
                "[content_types].xml" not in nombres
                or parte_principal not in nombres
            ):
                raise ErrorVistaPrevia(
                    "El contenido no corresponde con la extension del documento.",
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            tipos_xml = ElementTree.fromstring(
                paquete.read("[Content_Types].xml")
            )
            tipos_declarados = {
                elemento.attrib.get("ContentType", "").lower()
                for elemento in tipos_xml
            }

            if content_type_principal not in tipos_declarados:
                raise ErrorVistaPrevia(
                    "El contenido no corresponde con la extension del documento.",
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            if (
                any(nombre.endswith("vbaproject.bin") for nombre in nombres)
                or any("macroenabled" in tipo for tipo in tipos_declarados)
            ):
                raise ErrorVistaPrevia(
                    "No se pueden previsualizar documentos con macros.",
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            for miembro in miembros:
                if not miembro.filename.lower().endswith(".rels"):
                    continue

                relaciones = ElementTree.fromstring(paquete.read(miembro))

                if any(
                    relacion.attrib.get("TargetMode", "").lower() == "external"
                    for relacion in relaciones
                ):
                    raise ErrorVistaPrevia(
                        "No se pueden previsualizar documentos con recursos externos.",
                        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    )
    except zipfile.BadZipFile as error:
        raise ErrorVistaPrevia(
            "El contenido no corresponde con la extension del documento.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        ) from error
    except ElementTree.ParseError as error:
        raise ErrorVistaPrevia(
            "El documento Office contiene metadatos invalidos.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        ) from error


def _validar_documento_ole(contenido, extension):
    try:
        with olefile.OleFileIO(io.BytesIO(contenido)) as documento:
            nombres = {
                "/".join(ruta).lower()
                for ruta in documento.listdir(streams=True, storages=True)
            }

            if any(
                "vba" in nombre
                or "macros" in nombre
                or "encryptedpackage" in nombre
                for nombre in nombres
            ):
                raise ErrorVistaPrevia(
                    "No se pueden previsualizar documentos cifrados o con macros.",
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )

            parte_requerida = "worddocument" if extension == ".doc" else "workbook"

            if extension == ".xls":
                tiene_parte = parte_requerida in nombres or "book" in nombres
            else:
                tiene_parte = parte_requerida in nombres

            if not tiene_parte:
                raise ErrorVistaPrevia(
                    "El contenido no corresponde con la extension del documento.",
                    status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                )
    except (OSError, olefile.OleFileError) as error:
        raise ErrorVistaPrevia(
            "El contenido no corresponde con la extension del documento.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        ) from error


def validar_y_leer_documento_office(archivo):
    nombre = Path(str(archivo.name or "")).name
    extension = Path(nombre).suffix.lower()
    mime_esperado = TIPOS_OFFICE_PERMITIDOS.get(extension)

    if not mime_esperado:
        raise ErrorVistaPrevia(
            "Solo se pueden previsualizar documentos Word o Excel.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    mime_recibido = str(archivo.content_type or "").split(";", 1)[0].lower()

    if mime_recibido not in MIMES_GENERICOS and mime_recibido != mime_esperado:
        raise ErrorVistaPrevia(
            "El tipo MIME no corresponde con la extension del documento.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    if archivo.size and archivo.size > settings.DOCUMENT_PREVIEW_MAX_BYTES:
        raise ErrorVistaPrevia(
            "El documento supera el limite permitido para vista previa.",
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    partes = []
    total = 0

    for parte in archivo.chunks():
        total += len(parte)

        if total > settings.DOCUMENT_PREVIEW_MAX_BYTES:
            raise ErrorVistaPrevia(
                "El documento supera el limite permitido para vista previa.",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        partes.append(parte)

    contenido = b"".join(partes)

    if not contenido:
        raise ErrorVistaPrevia(
            "Debe enviar un documento con contenido.",
            status.HTTP_400_BAD_REQUEST,
        )

    if extension in {".docx", ".xlsx"}:
        _validar_paquete_ooxml(contenido, extension)
    elif contenido.startswith(FIRMA_OLE):
        _validar_documento_ole(contenido, extension)
    else:
        raise ErrorVistaPrevia(
            "El contenido no corresponde con la extension del documento.",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    return contenido, extension


def convertir_documento_office_pdf(contenido, extension):
    with tempfile.TemporaryDirectory(prefix="observatorios-preview-") as temporal:
        directorio_temporal = Path(temporal)
        directorio_salida = directorio_temporal / "salida"
        perfil = directorio_temporal / "perfil-libreoffice"
        archivo_entrada = directorio_temporal / f"documento{extension}"
        archivo_salida = directorio_salida / "documento.pdf"

        directorio_salida.mkdir()
        perfil.mkdir()
        archivo_entrada.write_bytes(contenido)

        identidad_proceso = {}

        if os.geteuid() == 0 and settings.LIBREOFFICE_USER:
            try:
                usuario = pwd.getpwnam(settings.LIBREOFFICE_USER)
            except KeyError as error:
                raise ErrorVistaPrevia(
                    "El usuario del conversor no esta disponible.",
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                ) from error

            for ruta in (
                directorio_temporal,
                directorio_salida,
                perfil,
                archivo_entrada,
            ):
                os.chown(ruta, usuario.pw_uid, usuario.pw_gid)

            identidad_proceso = {
                "user": usuario.pw_uid,
                "group": usuario.pw_gid,
            }

        comando = [
            settings.LIBREOFFICE_EXECUTABLE,
            "--headless",
            "--nologo",
            "--nodefault",
            "--nolockcheck",
            "--nofirststartwizard",
            "--safe-mode",
            f"-env:UserInstallation={perfil.resolve().as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(directorio_salida),
            str(archivo_entrada),
        ]

        try:
            proceso = subprocess.Popen(
                comando,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                env={
                    "HOME": str(directorio_temporal),
                    "LANG": "C.UTF-8",
                    "LC_ALL": "C.UTF-8",
                    "PATH": "/usr/bin:/bin",
                    "SAL_USE_VCLPLUGIN": "svp",
                    "TMPDIR": str(directorio_temporal),
                },
                **identidad_proceso,
            )
        except OSError as error:
            raise ErrorVistaPrevia(
                "El conversor de documentos no esta disponible.",
                status.HTTP_503_SERVICE_UNAVAILABLE,
            ) from error

        try:
            proceso.communicate(timeout=settings.DOCUMENT_PREVIEW_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as error:
            try:
                os.killpg(proceso.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

            proceso.communicate()
            raise ErrorVistaPrevia(
                "La conversion excedio el tiempo permitido.",
                status.HTTP_504_GATEWAY_TIMEOUT,
            ) from error

        if proceso.returncode != 0 or not archivo_salida.is_file():
            raise ErrorVistaPrevia(
                "No fue posible generar la vista previa del documento.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if archivo_salida.stat().st_size > settings.DOCUMENT_PREVIEW_MAX_PDF_BYTES:
            raise ErrorVistaPrevia(
                "La vista previa generada supera el limite permitido.",
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        pdf = archivo_salida.read_bytes()

        if not pdf.startswith(b"%PDF-"):
            raise ErrorVistaPrevia(
                "El conversor no genero una vista previa PDF valida.",
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        return pdf


class VistaPreviaDocumentoView(APIView):
    parser_classes = [MultiPartParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "document_preview"

    def post(self, request, *args, **kwargs):
        autorizacion = request.headers.get("Authorization", "")

        if not autorizacion.startswith("Bearer ") or not autorizacion[7:].strip():
            response = Response(
                {
                    "status": "error",
                    "message": "Se requiere autenticacion para generar la vista previa.",
                    "data": None,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
            response["WWW-Authenticate"] = "Bearer"
            return response

        archivo = request.FILES.get("archivo")

        if archivo is None:
            return Response(
                {
                    "status": "error",
                    "message": "Debe enviar el archivo que desea previsualizar.",
                    "data": None,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        contenido = None
        extension = None

        try:
            contenido, extension = validar_y_leer_documento_office(archivo)
        except ErrorVistaPrevia as error:
            return Response(
                {
                    "status": "error",
                    "message": error.mensaje,
                    "data": None,
                },
                status=error.codigo_estado,
            )
        except Exception:
            logger.exception("Error inesperado al generar una vista previa documental")
            return Response(
                {
                    "status": "error",
                    "message": "No fue posible generar la vista previa del documento.",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not SEMAFORO_CONVERSION.acquire(blocking=False):
            return Response(
                {
                    "status": "error",
                    "message": "El servicio de vista previa esta ocupado.",
                    "data": None,
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        try:
            pdf = convertir_documento_office_pdf(contenido, extension)
        except ErrorVistaPrevia as error:
            return Response(
                {
                    "status": "error",
                    "message": error.mensaje,
                    "data": None,
                },
                status=error.codigo_estado,
            )
        except Exception:
            logger.exception("Error inesperado al convertir una vista previa documental")
            return Response(
                {
                    "status": "error",
                    "message": "No fue posible generar la vista previa del documento.",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            SEMAFORO_CONVERSION.release()

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'inline; filename="vista-previa.pdf"'
        response["Content-Length"] = str(len(pdf))
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class TiposCamposVista(APIView):
    def get(self, request, *args, **kwargs):
        return Response(
            obtener_tipos_campos(),
            status=status.HTTP_200_OK
        )


class EstructuraCamposViewSet(ViewSet):
    """
    ViewSet para consultar o actualizar los campos y la data de una estructura.

    No crea estructuras nuevas. La creación inicial se realiza desde apps.estructuras.
    """

    CAMPOS_SISTEMA_DATA = {
        "id",
        "activo",
        "fecha_creacion",
        "fecha_modificacion",
    }

    def get_elasticsearch_client(self):
        return get_elasticsearch_client()

    def list(self, request, *args, **kwargs):
        return Response(
            {
                "detalle": (
                    "Debe consultar una estructura específica usando "
                    "/campos/estructuras/<id_estructura>/"
                )
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    def obtener_mapping_estructura(self, campos=None):
        properties_valores = {}

        for campo in campos or []:
            campo_id = campo.get("campo_id")
            tipo_campo = campo.get("tipo_campo")

            if not campo_id:
                continue

            properties_valores[campo_id] = obtener_mapping_tipo_campo(tipo_campo)

        return {
            "mappings": {
                "properties": {
                    "id": {
                        "type": "keyword"
                    },
                    "aspecto_id": {
                        "type": "keyword"
                    },
                    "tipo_evidencia": {
                        "type": "keyword"
                    },
                    "nombre": {
                        "type": "text",
                        "fields": {
                            "keyword": {
                                "type": "keyword"
                            }
                        }
                    },
                    "campos": {
                        "type": "object",
                        "properties": {
                            "campo_id": {
                                "type": "keyword"
                            },
                            "orden": {
                                "type": "integer"
                            },
                            "nombre_campo": {
                                "type": "keyword"
                            },
                            "tipo_campo": {
                                "type": "keyword"
                            },
                            "activo": {
                                "type": "boolean"
                            }
                        }
                    },
                    "data": {
                        "type": "object",
                        "properties": {
                            "valores": {
                                "type": "object",
                                "properties": properties_valores
                            },
                            "activo": {
                                "type": "boolean"
                            },
                            "fecha_creacion": {
                                "type": "date"
                            },
                            "fecha_modificacion": {
                                "type": "date"
                            }
                        }
                    },
                    "activo": {
                        "type": "boolean"
                    },
                    "fecha_creacion": {
                        "type": "date"
                    },
                    "fecha_modificacion": {
                        "type": "date"
                    },
                }
            }
        }

    def create(self, request, *args, **kwargs):
        return Response(
            {
                "detalle": (
                    "La creación de estructuras se realiza desde "
                    "apps.estructuras. Este endpoint solo actualiza campos y data."
                )
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    def retrieve(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            if not EstructuraCamposModelo.existe(cliente, pk):
                return Response(
                    {"detalle": "No existe la estructura."},
                    status=status.HTTP_404_NOT_FOUND
                )

            estructura = EstructuraCamposModelo.obtener(cliente, pk)

            return Response(
                estructura,
                status=status.HTTP_200_OK
            )

        except NotFoundError:
            return Response(
                {"detalle": "No existe el documento de la estructura."},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as error:
            return Response(
                {
                    "detalle": "No fue posible consultar la estructura.",
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def validar_remocion_campos(self, estructura_actual, datos, campos_eliminados_data):
        if "campos" not in datos:
            return

        campos_actuales = estructura_actual.get("campos", [])
        campos_nuevos = datos.get("campos", [])

        nombres_actuales = {
            campo.get("nombre_campo")
            for campo in campos_actuales
            if campo.get("nombre_campo")
        }

        nombres_nuevos = {
            campo.get("nombre_campo")
            for campo in campos_nuevos
            if campo.get("nombre_campo")
        }

        campos_removidos = nombres_actuales - nombres_nuevos

        if not campos_removidos:
            return

        campos_sin_confirmacion = [
            campo
            for campo in campos_removidos
            if campo not in campos_eliminados_data
        ]

        if not campos_sin_confirmacion:
            return

        data = estructura_actual.get("data", [])

        for fila in data:
            if not isinstance(fila, dict):
                continue

            for campo in campos_sin_confirmacion:
                if campo in fila:
                    raise ValueError(
                        {
                            campo: (
                                "El campo tiene información registrada. "
                                "Para quitarlo debe enviarlo en eliminar_data_campos "
                                "o conservarlo en campos."
                            )
                        }
                    )

    def validar_campos_reservados(self, campos):
        for campo in campos or []:
            nombre_campo = campo.get("nombre_campo")

            if nombre_campo in self.CAMPOS_SISTEMA_DATA:
                raise ValueError(
                    {
                        nombre_campo: (
                            "Este nombre está reservado para auditoría interna "
                            "de los registros de data."
                        )
                    }
                )

    def obtener_mapping_indice(self, cliente, estructura_id):
        mapping = cliente.indices.get_mapping(index=estructura_id)
        return mapping.get(estructura_id, {})

    def actualizar_mapping_data(self, cliente, estructura_id, campos):
        mapping_actual = self.obtener_mapping_indice(cliente, estructura_id)

        propiedades_indice = mapping_actual.get("mappings", {}).get("properties", {})
        propiedades_data = propiedades_indice.get("data", {}).get("properties", {})
        propiedades_valores = propiedades_data.get("valores", {}).get("properties", {})

        nuevas_propiedades = {}

        for campo in campos or []:
            campo_id = campo.get("campo_id")
            tipo_campo = campo.get("tipo_campo")

            if not campo_id:
                continue

            if campo_id in propiedades_valores:
                continue

            nuevas_propiedades[campo_id] = obtener_mapping_tipo_campo(tipo_campo)

        if not nuevas_propiedades:
            return

        cliente.indices.put_mapping(
            index=estructura_id,
            body={
                "properties": {
                    "data": {
                        "properties": {
                            "valores": {
                                "properties": nuevas_propiedades
                            }
                        }
                    }
                }
            }
        )

    def update(self, request, pk=None, *args, **kwargs):
        serializer = EstructuraUpdateSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        datos = serializer.validated_data
        cliente = self.get_elasticsearch_client()

        campos_eliminados_data = datos.pop("eliminar_data_campos", [])

        try:
            if not EstructuraCamposModelo.existe(cliente, pk):
                return Response(
                    {"detalle": "No existe la estructura."},
                    status=status.HTTP_404_NOT_FOUND
                )

            estructura_actual = EstructuraCamposModelo.obtener(cliente, pk)

            data_llego_en_request = "data" in request.data
            campos_llegaron_en_request = "campos" in request.data

            campos_actuales = estructura_actual.get("campos", [])

            if campos_llegaron_en_request:
                try:
                    campos_finales, migraciones = normalizar_campos_con_ids(
                        datos.get("campos", []),
                        campos_actuales
                    )
                except ValueError as error:
                    return Response(
                        {"detalle": error.args[0]},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                campos_finales = campos_actuales
                migraciones = []

            if data_llego_en_request:
                data_final = datos.get("data", [])
            else:
                data_final = estructura_actual.get("data", [])

            if not isinstance(data_final, list):
                data_final = []

            if campos_eliminados_data:
                data_final = eliminar_campos_de_data(
                    data_final,
                    campos_eliminados_data
                )

            data_final = aplicar_migraciones_data(
                data_final,
                migraciones,
                campos_finales
            )

            if campos_llegaron_en_request:
                try:
                    self.actualizar_mapping_data(
                        cliente,
                        pk,
                        campos_finales
                    )
                except Exception as error:
                    return Response(
                        {
                            "detalle": "No fue posible actualizar el mapping de data.",
                            "error": str(error),
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            estructura_actualizada = {
                **estructura_actual,
                **datos,
                "id": pk,
                "campos": campos_finales,
                "data": data_final,
                "activo": estructura_actual.get("activo", True),
                "fecha_creacion": estructura_actual.get("fecha_creacion"),
                "fecha_modificacion": EstructuraCamposModelo.fecha_actual(),
            }

            estructura_actualizada = EstructuraCamposModelo.guardar(
                cliente,
                pk,
                estructura_actualizada
            )

            return Response(
                estructura_actualizada,
                status=status.HTTP_200_OK
            )

        except NotFoundError:
            return Response(
                {"detalle": "No existe el documento de la estructura."},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as error:
            return Response(
                {
                    "detalle": "No fue posible actualizar la estructura.",
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    def partial_update(self, request, pk=None, *args, **kwargs):
        return self.update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            if not EstructuraCamposModelo.existe(cliente, pk):
                return Response(
                    {"detalle": "No existe la estructura."},
                    status=status.HTTP_404_NOT_FOUND
                )

            estructura = EstructuraCamposModelo.obtener(cliente, pk)

            estructura["campos"] = []
            estructura["data"] = []

            estructura = EstructuraCamposModelo.guardar(
                cliente,
                pk,
                estructura
            )

            return Response(
                {
                    "detalle": "Campos y data eliminados correctamente.",
                    "estructura": estructura,
                },
                status=status.HTTP_200_OK
            )

        except Exception as error:
            return Response(
                {
                    "detalle": "No fue posible limpiar la estructura.",
                    "error": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def quitar_campos_sistema_registro(self, registro):
        return {
            clave: valor
            for clave, valor in registro.items()
            if clave not in self.CAMPOS_SISTEMA_DATA
        }


class DatosEstructuraDocumentoView(APIView):
    """
    Maneja la data guardada dentro del documento de la estructura.

    GET    /campos/datos/<id_estructura>/
    POST   /campos/datos/<id_estructura>/
    PUT    /campos/datos/<id_estructura>/<id_registro>/
    DELETE /campos/datos/<id_estructura>/<id_registro>/
    DELETE /campos/datos/<id_estructura>/
    """

    CAMPOS_SISTEMA_DATA = {
        "id",
        "activo",
        "fecha_creacion",
        "fecha_modificacion",
    }

    def get_elasticsearch_client(self):
        return get_elasticsearch_client()

    def obtener_estructura(self, cliente, estructura_id):
        return EstructuraCamposModelo.obtener(cliente, estructura_id)

    def guardar_estructura(self, cliente, estructura_id, estructura):
        return EstructuraCamposModelo.guardar(
            cliente,
            estructura_id,
            estructura
        )

    def quitar_campos_sistema_registro(self, registro):
        return {
            clave: valor
            for clave, valor in registro.items()
            if clave not in self.CAMPOS_SISTEMA_DATA
        }

    def preparar_registro_creacion(self, campos, data):
        valores = construir_valores_registro(
            campos,
            data
        )

        fecha_actual = EstructuraCamposModelo.fecha_actual()

        return {
            "valores": valores,
            "activo": True,
            "fecha_creacion": fecha_actual,
            "fecha_modificacion": fecha_actual,
        }

    def preparar_registro_actualizacion(self, campos, registro_actual, data):
        valores = construir_valores_registro(
            campos,
            data
        )

        return {
            "valores": valores,
            "activo": registro_actual.get("activo", True),
            "fecha_creacion": (
                registro_actual.get("fecha_creacion")
                or EstructuraCamposModelo.fecha_actual()
            ),
            "fecha_modificacion": EstructuraCamposModelo.fecha_actual(),
        }

    def actualizar_fecha_modificacion(self, estructura):
        estructura["fecha_modificacion"] = EstructuraCamposModelo.fecha_actual()
        estructura["activo"] = estructura.get("activo", True)
        estructura["fecha_creacion"] = (
            estructura.get("fecha_creacion")
            or EstructuraCamposModelo.fecha_actual()
        )

        return estructura

    def get(self, request, pk, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            estructura = self.obtener_estructura(cliente, pk)
        except Exception:
            return Response(
                {"detalle": "No existe la estructura."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = estructura.get("data", [])

        if not isinstance(data, list):
            data = []

        campos = estructura.get("campos", [])

        if not isinstance(campos, list):
            campos = []

        campos_activos = [
            campo
            for campo in campos
            if isinstance(campo, dict) and campo.get("activo") is not False
        ]

        campos_activos = sorted(
            campos_activos,
            key=lambda campo: campo.get("orden") or 999999
        )

        filas = []

        for index, item in enumerate(data):
            if not isinstance(item, dict):
                continue

            valores = item.get("valores", {})

            # Compatibilidad con registros viejos que todavía no tengan "valores"
            if not isinstance(valores, dict):
                valores = {}

            fila = {
                "id": str(index),
                "activo": item.get("activo", True),
                "fecha_creacion": item.get("fecha_creacion"),
                "fecha_modificacion": item.get("fecha_modificacion"),
            }

            for campo in campos_activos:
                campo_id = campo.get("campo_id")
                nombre_campo = campo.get("nombre_campo")

                if not campo_id or not nombre_campo:
                    continue

                if campo_id in valores:
                    fila[nombre_campo] = valores.get(campo_id)
                elif nombre_campo in item:
                    # Compatibilidad con registros antiguos planos:
                    # {"annos": 56}
                    fila[nombre_campo] = item.get(nombre_campo)
                else:
                    fila[nombre_campo] = None

            filas.append(fila)

        filas = aplicar_filtros(filas, request.GET)
        filas = aplicar_ordenamiento(
            filas,
            request.GET.get("ordering")
        )

        try:
            page = int(request.GET.get("page", 1))
            page_size = int(request.GET.get("page_size", 10))
        except Exception:
            page = 1
            page_size = 10

        return Response(
            paginar_resultados(filas, page, page_size),
            status=status.HTTP_200_OK
        )

    def post(self, request, pk, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            estructura = self.obtener_estructura(cliente, pk)
        except Exception:
            return Response(
                {"detalle": "No existe la estructura."},
                status=status.HTTP_404_NOT_FOUND
            )

        campos = estructura.get("campos", [])

        if not campos:
            return Response(
                {"detalle": "La estructura no tiene campos configurados."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nuevo_registro = self.preparar_registro_creacion(
                campos,
                request.data
            )
        except ValueError as error:
            return Response(
                {"detalle": error.args[0]},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = estructura.get("data", [])

        if not isinstance(data, list):
            data = []

        data.append(nuevo_registro)

        estructura["data"] = data
        estructura = self.actualizar_fecha_modificacion(estructura)

        self.guardar_estructura(cliente, pk, estructura)

        return Response(
            nuevo_registro,
            status=status.HTTP_201_CREATED
        )

    def put(self, request, pk, id_documento=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        if id_documento is None:
            return Response(
                {"detalle": "Debe enviar el identificador del registro."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            estructura = self.obtener_estructura(cliente, pk)
        except Exception:
            return Response(
                {"detalle": "No existe la estructura."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = estructura.get("data", [])

        if not isinstance(data, list):
            data = []

        try:
            index_registro = int(id_documento)
        except Exception:
            return Response(
                {"detalle": "El identificador del registro debe ser numérico."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if index_registro < 0 or index_registro >= len(data):
            return Response(
                {"detalle": "No existe el registro."},
                status=status.HTTP_404_NOT_FOUND
            )

        registro_actual = data[index_registro]

        if not isinstance(registro_actual, dict):
            registro_actual = {}

        try:
            registro_actualizado = self.preparar_registro_actualizacion(
                estructura.get("campos", []),
                registro_actual,
                request.data
            )
        except ValueError as error:
            return Response(
                {"detalle": error.args[0]},
                status=status.HTTP_400_BAD_REQUEST
            )

        data[index_registro] = registro_actualizado

        estructura["data"] = data
        estructura = self.actualizar_fecha_modificacion(estructura)

        self.guardar_estructura(cliente, pk, estructura)

        return Response(
            registro_actualizado,
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk, id_documento=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            estructura = self.obtener_estructura(cliente, pk)
        except Exception:
            return Response(
                {"detalle": "No existe la estructura."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = estructura.get("data", [])

        if not isinstance(data, list):
            data = []

        if id_documento is None:
            estructura["data"] = []
            estructura = self.actualizar_fecha_modificacion(estructura)

            self.guardar_estructura(cliente, pk, estructura)

            return Response(
                {"detalle": "Todos los registros fueron eliminados."},
                status=status.HTTP_200_OK
            )

        try:
            index_registro = int(id_documento)
        except Exception:
            return Response(
                {"detalle": "El identificador del registro debe ser numérico."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if index_registro < 0 or index_registro >= len(data):
            return Response(
                {"detalle": "No existe el registro."},
                status=status.HTTP_404_NOT_FOUND
            )

        data.pop(index_registro)

        estructura["data"] = data
        estructura = self.actualizar_fecha_modificacion(estructura)

        self.guardar_estructura(cliente, pk, estructura)

        return Response(
            {"detalle": "Registro eliminado correctamente."},
            status=status.HTTP_200_OK
        )

    def patch(self, request, pk, id_documento=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        if id_documento is None:
            return Response(
                {"detalle": "Debe enviar el identificador del registro."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            estructura = self.obtener_estructura(cliente, pk)
        except Exception:
            return Response(
                {"detalle": "No existe la estructura."},
                status=status.HTTP_404_NOT_FOUND
            )

        data = estructura.get("data", [])

        if not isinstance(data, list):
            data = []

        try:
            index_registro = int(id_documento)
        except Exception:
            return Response(
                {"detalle": "El identificador del registro debe ser numérico."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if index_registro < 0 or index_registro >= len(data):
            return Response(
                {"detalle": "No existe el registro."},
                status=status.HTTP_404_NOT_FOUND
            )

        registro_actual = data[index_registro]

        if not isinstance(registro_actual, dict):
            registro_actual = {}

        activo = request.data.get("activo", False)

        if not isinstance(activo, bool):
            return Response(
                {"detalle": "El campo activo debe ser booleano."},
                status=status.HTTP_400_BAD_REQUEST
            )

        registro_actual["activo"] = activo
        registro_actual["fecha_creacion"] = (
            registro_actual.get("fecha_creacion")
            or EstructuraCamposModelo.fecha_actual()
        )
        registro_actual["fecha_modificacion"] = EstructuraCamposModelo.fecha_actual()

        data[index_registro] = registro_actual

        estructura["data"] = data
        estructura = self.actualizar_fecha_modificacion(estructura)

        self.guardar_estructura(cliente, pk, estructura)

        return Response(
            {
                "detalle": (
                    "Registro activado correctamente."
                    if activo
                    else "Registro desactivado correctamente."
                ),
                "registro": registro_actual,
            },
            status=status.HTTP_200_OK
        )

class ArchivosDatosView(DatosEstructuraDocumentoView):
    """
    Se conserva la clase para no romper imports/rutas existentes.

    En el nuevo contrato no se maneja mapeo_archivos.
    Si el cliente consume /archivos/, se comporta igual que /datos/.
    """
