from elasticsearch import NotFoundError
from rest_framework import status
from rest_framework.response import Response
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
