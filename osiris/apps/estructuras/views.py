import uuid
import re

from django.utils import timezone
from elasticsearch import NotFoundError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import (
    get_elasticsearch_client,
    normalizar_orden,
    ordenar_por_orden,
)

from .serializers import (
    EstructuraEvidenciaSerializer,
    EstructuraEvidenciaUpdateSerializer,
)


class EstructuraViewSet(ViewSet):
    indice_aspectos = "atlas_aspectos"
    prefijo_aplicacion = "atlas"
    contexto_indice = "estructura"

    estructura_mapping = {
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
                        "nombre_campo": {
                            "type": "keyword"
                        },
                        "tipo_campo": {
                            "type": "keyword"
                        }
                    }
                },
                "data": {
                    "type": "object",
                    "enabled": True
                },
                "orden": {
                    "type": "integer"
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

    def get_elasticsearch_client(self):
        return get_elasticsearch_client()

    def fecha_actual(self):
        return timezone.now().isoformat()

    def normalizar_segmento_indice(self, valor):
        if not valor:
            return "sin_tipo"

        segmento = str(valor).strip().lower().replace(" ", "_")
        segmento = re.sub(r"[^a-z0-9_-]", "", segmento)

        if not segmento:
            return "sin_tipo"

        return segmento

    def crear_indice_unico(self, cliente, tipo_evidencia=None):
        tipo_evidencia_normalizado = self.normalizar_segmento_indice(
            tipo_evidencia
        )

        for _ in range(5):
            uid = str(uuid.uuid4())
            nombre_indice = (
                f"{self.prefijo_aplicacion}_"
                f"{self.contexto_indice}_"
                f"{tipo_evidencia_normalizado}_"
                f"{uid}"
            )

            try:
                cliente.indices.create(
                    index=nombre_indice,
                    body=self.estructura_mapping
                )
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
            "orden": normalizar_orden(data.get("orden")),
            "activo": data.get("activo", True),
            "fecha_creacion": data.get("fecha_creacion"),
            "fecha_modificacion": data.get("fecha_modificacion"),
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
                    "estructuras_evidencias": estructuras_actualizadas,
                    "fecha_modificacion": self.fecha_actual(),
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
                    "estructuras_evidencias": estructuras_actualizadas,
                    "fecha_modificacion": self.fecha_actual(),
                }
            },
            refresh=True
        )

        return aspecto_id, estructuras_actualizadas

    def desactivar_estructura_en_aspecto(
        self,
        cliente,
        estructura_id,
        estructura_actualizada=None
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
                base = estructura_actualizada or item

                estructura_desactivada = {
                    **base,
                    "activo": False,
                }

                estructuras_actualizadas.append(
                    self.normalizar_estructura(estructura_desactivada)
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
                    "estructuras_evidencias": estructuras_actualizadas,
                    "fecha_modificacion": self.fecha_actual(),
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
                ordenar_por_orden(aspecto.get("estructuras_evidencias") or []),
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

            return Response(ordenar_por_orden(estructuras), status=status.HTTP_200_OK)

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

            fecha_actual = self.fecha_actual()

            orden = normalizar_orden(data.get("orden"))

            if orden is None:
                estructuras_aspecto = aspecto.get("estructuras_evidencias") or []
                ordenes = [
                    normalizar_orden(item.get("orden"), 0)
                    for item in estructuras_aspecto
                    if isinstance(item, dict)
                ]
                orden = (max(ordenes) if ordenes else 0) + 1

            estructura = {
                "id": indice_id,
                "aspecto_id": aspecto_id,
                "tipo_evidencia": data.get("tipo_evidencia"),
                "nombre": data.get("nombre"),
                "campos": data.get("campos", []),
                "data": data.get("data", []),
                "orden": orden,
                "activo": data.get("activo", True),
                "fecha_creacion": fecha_actual,
                "fecha_modificacion": fecha_actual,
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
        fecha_actual = self.fecha_actual()

        print("Payload validado para actualizar estructura evidencia:", data)

        cliente = self.get_elasticsearch_client()

        try:
            estructura_actual = cliente.get(
                index=pk,
                id=pk
            )["_source"]
        except Exception as error:
            print(f"No se encontró la estructura evidencia {pk}: {error}")

            return Response(
                {
                    "error": "No se encontró la estructura evidencia."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        aspecto_id = data.get(
            "aspecto_id",
            estructura_actual.get("aspecto_id")
        )

        doc_update = {
            "fecha_modificacion": fecha_actual,
        }

        if "aspecto_id" in data:
            doc_update["aspecto_id"] = data["aspecto_id"]

        if "tipo_evidencia" in data:
            doc_update["tipo_evidencia"] = data["tipo_evidencia"]

        if "nombre" in data:
            doc_update["nombre"] = data["nombre"]

        if "orden" in data:
            doc_update["orden"] = data["orden"]

        if "activo" in data:
            doc_update["activo"] = data["activo"]

        # Importante:
        # No actualizar campos ni data aquí si no vienen en la petición.
        # Así evitamos borrar la configuración de tabla/documental.
        try:
            cliente.update(
                index=pk,
                id=pk,
                body={
                    "doc": doc_update
                },
                refresh=True
            )
        except Exception as error:
            print(f"Error actualizando índice dinámico {pk}: {error}")

            return Response(
                {
                    "error": "No fue posible actualizar la estructura evidencia."
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        estructura_actualizada = cliente.get(
            index=pk,
            id=pk
        )["_source"]

        try:
            aspecto = cliente.get(
                index=self.indice_aspectos,
                id=aspecto_id
            )

            aspecto_source = aspecto["_source"]
            estructuras_evidencias = aspecto_source.get(
                "estructuras_evidencias"
            ) or []

            estructuras_actualizadas = []

            for estructura in estructuras_evidencias:
                if estructura.get("id") == pk:
                    estructura_actualizada_aspecto = {
                        **estructura,
                        "id": pk,
                        "tipo_evidencia": estructura_actualizada.get(
                            "tipo_evidencia",
                            estructura.get("tipo_evidencia")
                        ),
                        "nombre": estructura_actualizada.get(
                            "nombre",
                            estructura.get("nombre")
                        ),
                        "orden": estructura_actualizada.get(
                            "orden",
                            estructura.get("orden")
                        ),
                        "activo": estructura_actualizada.get(
                            "activo",
                            estructura.get("activo", True)
                        ),
                        "fecha_modificacion": fecha_actual,
                    }

                    estructuras_actualizadas.append(
                        estructura_actualizada_aspecto
                    )
                else:
                    estructuras_actualizadas.append(estructura)

            estructuras_actualizadas = ordenar_por_orden(
                estructuras_actualizadas
            )

            cliente.update(
                index=self.indice_aspectos,
                id=aspecto_id,
                body={
                    "doc": {
                        "estructuras_evidencias": estructuras_actualizadas,
                        "fecha_modificacion": fecha_actual,
                    }
                },
                refresh=True
            )

        except Exception as error:
            print(
                f"No se pudo actualizar la referencia en el aspecto "
                f"{aspecto_id}: {error}"
            )

            return Response(
                {
                    "error": "La estructura se actualizó, pero no fue posible "
                            "actualizar la referencia en el aspecto.",
                    "detalle": str(error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "estructura": self.normalizar_estructura(
                    estructura_actualizada
                ),
                "aspecto_id": aspecto_id,
                "estructuras_evidencias": estructuras_actualizadas,
            },
            status=status.HTTP_200_OK
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
                "fecha_modificacion": self.fecha_actual(),
            }

            estructura_actualizada = self.actualizar_documento_estructura(
                cliente,
                pk,
                estructura_actualizada
            )

            aspecto_id, estructuras_actualizadas = self.desactivar_estructura_en_aspecto(
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
