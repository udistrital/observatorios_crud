import uuid
import re

from elasticsearch import NotFoundError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .serializers import (
    EstructuraEvidenciaSerializer,
    EstructuraEvidenciaUpdateSerializer,
)


class EstructuraViewSet(ViewSet):
    indice_aspectos = "atlas_aspectos"
    prefijo_aplicacion = "atlas"
    contexto_indice = "estructura"

    def get_elasticsearch_client(self):
        return get_elasticsearch_client()

    def generar_nombre_indice(self):
        uid = str(uuid.uuid4())
        return f"{self.prefijo_aplicacion}_{self.contexto_indice}_{uid}"

    def normalizar_segmento_indice(self, valor):
        if not valor:
            return "sin_tipo"

        segmento = str(valor).strip().lower().replace(" ", "_")
        segmento = re.sub(r"[^a-z0-9_-]", "", segmento)

        if not segmento:
            return "sin_tipo"

        return segmento

    def crear_indice_unico(self, cliente, tipo_evidencia=None):
        tipo_evidencia_normalizado = self.normalizar_segmento_indice(tipo_evidencia)

        for _ in range(5):
            uid = str(uuid.uuid4())
            nombre_indice = (
                f"{self.prefijo_aplicacion}_"
                f"{self.contexto_indice}_"
                f"{tipo_evidencia_normalizado}_"
                f"{uid}"
            )

            try:
                cliente.indices.create(index=nombre_indice)
                return nombre_indice
            except Exception:
                continue

        raise Exception("No fue posible generar un índice único para la estructura.")

    def obtener_aspecto(self, cliente, aspecto_id):
        try:
            respuesta = cliente.get(
                index=self.indice_aspectos,
                id=aspecto_id
            )

            return respuesta["_source"]

        except NotFoundError:
            return None

        except Exception:
            return None

    def normalizar_estructura(self, data):
        return {
            "id": data.get("id"),
            "tipo_evidencia": data.get("tipo_evidencia"),
            "nombre": data.get("nombre"),
            "activo": data.get("activo", True),
        }

    def guardar_documento_estructura(self, cliente, estructura):
        cliente.index(
            index=estructura["id"],
            id=estructura["id"],
            document=estructura,
            refresh=True
        )

    def obtener_documento_estructura(self, cliente, estructura_id):
        respuesta = cliente.get(
            index=estructura_id,
            id=estructura_id
        )

        return respuesta["_source"]

    def actualizar_documento_estructura(self, cliente, estructura_id, estructura):
        cliente.update(
            index=estructura_id,
            id=estructura_id,
            body={
                "doc": estructura
            },
            refresh=True
        )

        return self.obtener_documento_estructura(cliente, estructura_id)

    def buscar_aspecto_por_estructura(self, cliente, estructura_id):
        try:
            resultado = cliente.search(
                index=self.indice_aspectos,
                body={
                    "query": {
                        "term": {
                            "estructuras_evidencias.id.keyword": estructura_id
                        }
                    },
                    "size": 1
                }
            )

            if resultado["hits"]["total"]["value"] > 0:
                hit = resultado["hits"]["hits"][0]

                return hit["_id"], hit["_source"]

        except Exception:
            pass

        try:
            resultado = cliente.search(
                index=self.indice_aspectos,
                body={
                    "query": {
                        "match_all": {}
                    },
                    "size": 1000
                }
            )

            for hit in resultado["hits"]["hits"]:
                aspecto = hit["_source"]
                estructuras = aspecto.get("estructuras_evidencias") or []

                for estructura in estructuras:
                    if (
                        isinstance(estructura, dict)
                        and estructura.get("id") == estructura_id
                    ):
                        return hit["_id"], aspecto

        except Exception:
            pass

        return None, None

    def agregar_estructura_al_aspecto(
        self,
        cliente,
        aspecto_id,
        estructura
    ):
        aspecto = self.obtener_aspecto(cliente, aspecto_id)

        if not aspecto:
            return None

        estructuras = aspecto.get("estructuras_evidencias") or []
        estructura_normalizada = self.normalizar_estructura(estructura)

        estructuras_actualizadas = []
        existe = False

        for item in estructuras:
            if (
                isinstance(item, dict)
                and item.get("id") == estructura_normalizada.get("id")
            ):
                estructuras_actualizadas.append(estructura_normalizada)
                existe = True
            else:
                estructuras_actualizadas.append(item)

        if not existe:
            estructuras_actualizadas.append(estructura_normalizada)

        cliente.update(
            index=self.indice_aspectos,
            id=aspecto_id,
            body={
                "doc": {
                    "estructuras_evidencias": estructuras_actualizadas
                }
            },
            refresh=True
        )

        return estructuras_actualizadas

    def actualizar_estructura_en_aspecto(
        self,
        cliente,
        estructura_id,
        estructura
    ):
        aspecto_id = estructura.get("aspecto_id")
        aspecto = None

        if aspecto_id:
            aspecto = self.obtener_aspecto(cliente, aspecto_id)
        else:
            aspecto_id, aspecto = self.buscar_aspecto_por_estructura(
                cliente,
                estructura_id
            )

        if not aspecto_id or not aspecto:
            return None, None

        estructuras = aspecto.get("estructuras_evidencias") or []

        estructuras_actualizadas = []
        encontrada = False

        for item in estructuras:
            if isinstance(item, dict) and item.get("id") == estructura_id:
                estructuras_actualizadas.append(
                    self.normalizar_estructura(estructura)
                )
                encontrada = True
            else:
                estructuras_actualizadas.append(item)

        if not encontrada:
            return None, None

        cliente.update(
            index=self.indice_aspectos,
            id=aspecto_id,
            body={
                "doc": {
                    "estructuras_evidencias": estructuras_actualizadas
                }
            },
            refresh=True
        )

        return aspecto_id, estructuras_actualizadas

    def desactivar_estructura_en_aspecto(
        self,
        cliente,
        estructura_id
    ):
        aspecto_id, aspecto = self.buscar_aspecto_por_estructura(
            cliente,
            estructura_id
        )

        if not aspecto_id or not aspecto:
            return None, None

        estructuras = aspecto.get("estructuras_evidencias") or []

        estructuras_actualizadas = []
        encontrada = False

        for item in estructuras:
            if isinstance(item, dict) and item.get("id") == estructura_id:
                estructura_actualizada = {
                    **item,
                    "activo": False,
                }

                estructuras_actualizadas.append(
                    self.normalizar_estructura(estructura_actualizada)
                )

                encontrada = True
            else:
                estructuras_actualizadas.append(item)

        if not encontrada:
            return None, None

        cliente.update(
            index=self.indice_aspectos,
            id=aspecto_id,
            body={
                "doc": {
                    "estructuras_evidencias": estructuras_actualizadas
                }
            },
            refresh=True
        )

        return aspecto_id, estructuras_actualizadas

    def list(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        aspecto_id = request.query_params.get("aspecto_id")

        if aspecto_id:
            aspecto = self.obtener_aspecto(cliente, aspecto_id)

            if not aspecto:
                return Response([], status=status.HTTP_200_OK)

            return Response(
                aspecto.get("estructuras_evidencias") or [],
                status=status.HTTP_200_OK
            )

        try:
            resultado = cliente.search(
                index=self.indice_aspectos,
                body={
                    "query": {
                        "match_all": {}
                    },
                    "size": 1000
                }
            )

            estructuras = []

            for hit in resultado["hits"]["hits"]:
                aspecto = hit["_source"]
                estructuras_aspecto = aspecto.get("estructuras_evidencias") or []

                for estructura in estructuras_aspecto:
                    if isinstance(estructura, dict):
                        estructuras.append(
                            {
                                **self.normalizar_estructura(estructura),
                                "aspecto_id": hit["_id"],
                            }
                        )

            return Response(estructuras, status=status.HTTP_200_OK)

        except NotFoundError:
            return Response([], status=status.HTTP_200_OK)

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible listar las estructuras",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def retrieve(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            existe = cliente.indices.exists(index=pk)

            if not existe:
                return Response(
                    {
                        "error": "No se encontró el índice de la estructura"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            estructura = self.obtener_documento_estructura(cliente, pk)

            return Response(
                estructura,
                status=status.HTTP_200_OK
            )

        except NotFoundError:
            return Response(
                {
                    "error": "No se encontró el documento de la estructura"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible consultar la estructura",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def create(self, request, *args, **kwargs):
        serializer = EstructuraEvidenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        cliente = self.get_elasticsearch_client()

        aspecto_id = data.get("aspecto_id")

        aspecto = self.obtener_aspecto(cliente, aspecto_id)

        if not aspecto:
            return Response(
                {
                    "error": "No se encontró el aspecto relacionado",
                    "detalle": "El campo aspecto_id debe ser el id de Elasticsearch del aspecto."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        indice_id = None

        try:
            indice_id = self.crear_indice_unico(
                cliente,
                data.get("tipo_evidencia")
            )

            estructura = {
                "id": indice_id,
                "aspecto_id": aspecto_id,
                "tipo_evidencia": data.get("tipo_evidencia"),
                "nombre": data.get("nombre"),
                "activo": data.get("activo", True),
                "campos": data.get("campos", []),
                "data": data.get("data", []),
            }

            self.guardar_documento_estructura(cliente, estructura)

            estructuras_actualizadas = self.agregar_estructura_al_aspecto(
                cliente,
                aspecto_id,
                estructura
            )

            if estructuras_actualizadas is None:
                cliente.indices.delete(index=indice_id, ignore=[404])

                return Response(
                    {
                        "error": "No fue posible asociar la estructura al aspecto"
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as error:
            if indice_id:
                cliente.indices.delete(index=indice_id, ignore=[404])

            return Response(
                {
                    "error": "No fue posible crear la estructura",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "estructura": estructura,
                "estructuras_evidencias": estructuras_actualizadas,
            },
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None, *args, **kwargs):
        serializer = EstructuraEvidenciaUpdateSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        cliente = self.get_elasticsearch_client()

        campos_eliminados_data = data.pop("eliminar_data_campos", [])

        try:
            existe = cliente.indices.exists(index=pk)

            if not existe:
                return Response(
                    {
                        "error": "No se encontró el índice de la estructura"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            estructura_actual = self.obtener_documento_estructura(cliente, pk)

            estructura_actualizada = {
                **estructura_actual,
                **data,
                "id": pk,
            }

            if campos_eliminados_data:
                estructura_actualizada["data"] = self.eliminar_campos_de_data(
                    estructura_actualizada.get("data", []),
                    campos_eliminados_data
                )

            self.actualizar_documento_estructura(
                cliente,
                pk,
                estructura_actualizada
            )

            aspecto_id, estructuras_actualizadas = self.actualizar_estructura_en_aspecto(
                cliente,
                pk,
                estructura_actualizada
            )

            if estructuras_actualizadas is None:
                return Response(
                    {
                        "error": "No se encontró la estructura dentro de ningún aspecto"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "estructura": estructura_actualizada,
                    "aspecto_id": aspecto_id,
                    "estructuras_evidencias": estructuras_actualizadas,
                },
                status=status.HTTP_200_OK
            )

        except NotFoundError:
            return Response(
                {
                    "error": "No se encontró el documento de la estructura"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible actualizar la estructura",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def partial_update(self, request, pk=None, *args, **kwargs):
        return self.update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            existe = cliente.indices.exists(index=pk)

            if not existe:
                return Response(
                    {
                        "error": "No se encontró el índice de la estructura"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            estructura_actual = self.obtener_documento_estructura(cliente, pk)

            estructura_actualizada = {
                **estructura_actual,
                "activo": False,
            }

            self.actualizar_documento_estructura(
                cliente,
                pk,
                estructura_actualizada
            )

            aspecto_id, estructuras_actualizadas = self.desactivar_estructura_en_aspecto(
                cliente,
                pk
            )

            if estructuras_actualizadas is None:
                return Response(
                    {
                        "error": "No se encontró la estructura dentro de ningún aspecto"
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response(
                {
                    "message": "Estructura desactivada correctamente",
                    "estructura": estructura_actualizada,
                    "id": pk,
                    "aspecto_id": aspecto_id,
                    "estructuras_evidencias": estructuras_actualizadas,
                },
                status=status.HTTP_200_OK
            )

        except NotFoundError:
            return Response(
                {
                    "error": "No se encontró el documento de la estructura"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible desactivar la estructura",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def eliminar_campos_de_data(self, data, campos_eliminados):
        if not isinstance(data, list):
            return []

        if not campos_eliminados:
            return data

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
