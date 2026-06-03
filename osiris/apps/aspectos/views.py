from django.utils import timezone
from elasticsearch import NotFoundError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .serializers import AspectoSerializer, AspectoUpdateSerializer


class AspectoViewSet(ViewSet):
    nombre_indice = "atlas_aspectos"
    indice_caracteristicas = "atlas_caracteristicas"

    aspecto_mapping = {
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "caracteristica_id": {
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
                "estructuras_evidencias": {
                    "type": "object",
                    "properties": {
                        "id": {
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
                        "activo": {
                            "type": "boolean"
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

    def get_elasticsearch_client(self):
        return get_elasticsearch_client()

    def fecha_actual(self):
        return timezone.now().isoformat()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        cliente = self.get_elasticsearch_client()

        if not cliente.indices.exists(index=self.nombre_indice):
            cliente.indices.create(
                index=self.nombre_indice,
                body=self.aspecto_mapping
            )

    def normalizar_aspecto(self, elastic_id, source):
        return {
            "id": source.get("id") or elastic_id,
            "caracteristica_id": source.get("caracteristica_id"),
            "nombre": source.get("nombre", ""),
            "estructuras_evidencias": source.get("estructuras_evidencias") or [],
            "activo": source.get("activo", True),
            "fecha_creacion": source.get("fecha_creacion"),
            "fecha_modificacion": source.get("fecha_modificacion"),
        }

    def obtener_caracteristica(self, cliente, caracteristica_id):
        try:
            respuesta = cliente.get(
                index=self.indice_caracteristicas,
                id=caracteristica_id
            )

            return respuesta["_source"]

        except NotFoundError:
            return None

        except Exception:
            return None

    def agregar_aspecto_a_caracteristica(
        self,
        cliente,
        caracteristica_id,
        aspecto_id
    ):
        caracteristica = self.obtener_caracteristica(
            cliente,
            caracteristica_id
        )

        if not caracteristica:
            return False

        aspectos = caracteristica.get("aspectos") or []

        if aspecto_id not in aspectos:
            aspectos.append(aspecto_id)

        cliente.update(
            index=self.indice_caracteristicas,
            id=caracteristica_id,
            body={
                "doc": {
                    "aspectos": aspectos,
                    "fecha_modificacion": self.fecha_actual(),
                }
            },
            refresh=True
        )

        return True

    def quitar_aspecto_de_caracteristica(
        self,
        cliente,
        caracteristica_id,
        aspecto_id
    ):
        caracteristica = self.obtener_caracteristica(
            cliente,
            caracteristica_id
        )

        if not caracteristica:
            return False

        aspectos = caracteristica.get("aspectos") or []

        aspectos = [
            item for item in aspectos
            if item != aspecto_id
        ]

        cliente.update(
            index=self.indice_caracteristicas,
            id=caracteristica_id,
            body={
                "doc": {
                    "aspectos": aspectos,
                    "fecha_modificacion": self.fecha_actual(),
                }
            },
            refresh=True
        )

        return True

    def list(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        caracteristica_id = request.query_params.get("caracteristica_id")

        query = {
            "match_all": {}
        }

        if caracteristica_id:
            query = {
                "term": {
                    "caracteristica_id": caracteristica_id
                }
            }

        try:
            resultado = cliente.search(
                index=self.nombre_indice,
                body={
                    "query": query,
                    "size": 1000
                }
            )

        except NotFoundError:
            return Response([], status=status.HTTP_200_OK)

        data = [
            self.normalizar_aspecto(
                item["_id"],
                item["_source"]
            )
            for item in resultado["hits"]["hits"]
        ]

        return Response(data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            resultado = cliente.get(
                index=self.nombre_indice,
                id=pk
            )

        except NotFoundError:
            return Response(
                {
                    "error": "No se encontró el aspecto"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = self.normalizar_aspecto(
            resultado["_id"],
            resultado["_source"]
        )

        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = AspectoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        caracteristica_id = data.get("caracteristica_id")

        cliente = self.get_elasticsearch_client()

        caracteristica = self.obtener_caracteristica(
            cliente,
            caracteristica_id
        )

        if not caracteristica:
            return Response(
                {
                    "error": "No se encontró la característica relacionada",
                    "detalle": "El campo caracteristica_id debe ser el id de Elasticsearch de la característica."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        fecha_actual = self.fecha_actual()

        documento = {
            "caracteristica_id": caracteristica_id,
            "nombre": data.get("nombre"),
            "estructuras_evidencias": data.get("estructuras_evidencias") or [],
            "activo": data.get("activo", True),
            "fecha_creacion": fecha_actual,
            "fecha_modificacion": fecha_actual,
        }

        try:
            respuesta = cliente.index(
                index=self.nombre_indice,
                document=documento,
                refresh=True
            )

            aspecto_id = respuesta["_id"]

            cliente.update(
                index=self.nombre_indice,
                id=aspecto_id,
                body={
                    "doc": {
                        "id": aspecto_id
                    }
                },
                refresh=True
            )

            self.agregar_aspecto_a_caracteristica(
                cliente,
                caracteristica_id,
                aspecto_id
            )

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible crear el aspecto en Elasticsearch",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        documento["id"] = aspecto_id

        return Response(documento, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        serializer = AspectoUpdateSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        cliente = self.get_elasticsearch_client()

        try:
            resultado_actual = cliente.get(
                index=self.nombre_indice,
                id=pk
            )

        except NotFoundError:
            return Response(
                {
                    "error": "No se encontró el aspecto"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        aspecto_actual = resultado_actual["_source"]

        caracteristica_anterior = aspecto_actual.get("caracteristica_id")
        caracteristica_nueva = data.get("caracteristica_id")

        if caracteristica_nueva and caracteristica_nueva != caracteristica_anterior:
            nueva_caracteristica = self.obtener_caracteristica(
                cliente,
                caracteristica_nueva
            )

            if not nueva_caracteristica:
                return Response(
                    {
                        "error": "No se encontró la nueva característica relacionada",
                        "detalle": "El campo caracteristica_id debe ser el id de Elasticsearch de la característica."
                    },
                    status=status.HTTP_404_NOT_FOUND
                )

            if caracteristica_anterior:
                self.quitar_aspecto_de_caracteristica(
                    cliente,
                    caracteristica_anterior,
                    pk
                )

            self.agregar_aspecto_a_caracteristica(
                cliente,
                caracteristica_nueva,
                pk
            )

        data["fecha_modificacion"] = self.fecha_actual()

        try:
            cliente.update(
                index=self.nombre_indice,
                id=pk,
                body={
                    "doc": data
                },
                refresh=True
            )

            resultado = cliente.get(
                index=self.nombre_indice,
                id=pk
            )

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible actualizar el aspecto",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response_data = self.normalizar_aspecto(
            resultado["_id"],
            resultado["_source"]
        )

        return Response(response_data, status=status.HTTP_200_OK)

    def partial_update(self, request, pk=None, *args, **kwargs):
        return self.update(request, pk, *args, **kwargs)

    def destroy(self, request, pk=None, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        try:
            cliente.update(
                index=self.nombre_indice,
                id=pk,
                body={
                    "doc": {
                        "activo": False,
                        "fecha_modificacion": self.fecha_actual(),
                    }
                },
                refresh=True
            )

        except NotFoundError:
            return Response(
                {
                    "error": "No se encontró el aspecto"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible desactivar el aspecto",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "message": "Aspecto desactivado correctamente",
                "id": pk
            },
            status=status.HTTP_200_OK
        )
