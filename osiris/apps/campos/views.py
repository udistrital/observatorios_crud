from elasticsearch import NotFoundError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .models import EstructuraCamposModelo
from .serializers import EstructuraSerializer, EstructuraUpdateSerializer
from .utils import (
    aplicar_filtros,
    aplicar_ordenamiento,
    eliminar_campos_de_data,
    obtener_tipos_campos,
    paginar_resultados,
    validar_registro_con_campos,
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

    Documento esperado:

    {
        "id": "...",
        "aspecto_id": "...",
        "tipo_evidencia": "Tabla",
        "nombre": "tabla prueba",
        "activo": true,
        "campos": [],
        "data": []
    }
    """

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

            try:
                self.validar_remocion_campos(
                    estructura_actual,
                    datos,
                    campos_eliminados_data
                )
            except ValueError as error:
                return Response(
                    {"detalle": error.args[0]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            estructura_actualizada = {
                **estructura_actual,
                **datos,
                "id": pk,
            }

            if campos_eliminados_data:
                estructura_actualizada["data"] = eliminar_campos_de_data(
                    estructura_actualizada.get("data", []),
                    campos_eliminados_data
                )

            EstructuraCamposModelo.guardar(
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

            EstructuraCamposModelo.guardar(cliente, pk, estructura)

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


class DatosEstructuraDocumentoView(APIView):
    """
    Maneja la data guardada dentro del documento de la estructura.

    GET    /campos/datos/<id_estructura>/
    POST   /campos/datos/<id_estructura>/
    PUT    /campos/datos/<id_estructura>/<id_registro>/
    DELETE /campos/datos/<id_estructura>/<id_registro>/
    DELETE /campos/datos/<id_estructura>/
    """

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

        filas = []

        for index, item in enumerate(data):
            if isinstance(item, dict):
                filas.append(
                    {
                        "id": str(index),
                        **item,
                    }
                )

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
            nuevo_registro = validar_registro_con_campos(
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

        try:
            registro_actualizado = validar_registro_con_campos(
                estructura.get("campos", []),
                request.data
            )
        except ValueError as error:
            return Response(
                {"detalle": error.args[0]},
                status=status.HTTP_400_BAD_REQUEST
            )

        data[index_registro] = registro_actualizado
        estructura["data"] = data

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

        self.guardar_estructura(cliente, pk, estructura)

        return Response(
            {"detalle": "Registro eliminado correctamente."},
            status=status.HTTP_200_OK
        )


class ArchivosDatosView(DatosEstructuraDocumentoView):
    """
    Se conserva la clase para no romper imports/rutas existentes.

    En el nuevo contrato no se maneja mapeo_archivos.
    Si el cliente consume /archivos/, se comporta igual que /datos/.
    """
