from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .serializers import (CaracteristicaSerializer,CaracteristicaUpdateSerializer)


class CaracteristicaViewSet(ViewSet):
    nombre_indice = "atlas_caracteristicas"
    indice_factores = "atlas_factores"

    caracteristica_mapping = {
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "factor_id": {
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
                "descripcion": {
                    "type": "text"
                },
                "calificacion": {
                    "type": "double"
                },
                "aspectos": {
                    "type": "keyword"
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
        self.asegurar_indice_caracteristicas(cliente)

    def asegurar_indice_caracteristicas(self, cliente):
        if not cliente.indices.exists(index=self.nombre_indice):
            cliente.indices.create(
                index=self.nombre_indice,
                body=self.caracteristica_mapping
            )

    def existe_factor(self, factor_elastic_id):
        cliente = self.get_elasticsearch_client()

        try:
            return cliente.exists(
                index=self.indice_factores,
                id=factor_elastic_id
            )
        except Exception:
            return False

    def obtener_factor(self, cliente, factor_elastic_id):
        try:
            respuesta = cliente.get(
                index=self.indice_factores,
                id=factor_elastic_id
            )

            return respuesta["_source"]

        except Exception:
            return None

    def agregar_caracteristica_al_factor(
        self,
        cliente,
        factor_elastic_id,
        caracteristica_id
    ):
        factor = self.obtener_factor(cliente, factor_elastic_id)

        if not factor:
            return False

        caracteristicas = factor.get("caracteristicas") or []

        if caracteristica_id not in caracteristicas:
            caracteristicas.append(caracteristica_id)

        cliente.update(
            index=self.indice_factores,
            id=factor_elastic_id,
            body={
                "doc": {
                    "caracteristicas": caracteristicas,
                    "fecha_modificacion": self.fecha_actual(),
                }
            },
            refresh=True
        )

        return True

    def quitar_caracteristica_del_factor(
        self,
        cliente,
        factor_elastic_id,
        caracteristica_id
    ):
        factor = self.obtener_factor(cliente, factor_elastic_id)

        if not factor:
            return False

        caracteristicas = factor.get("caracteristicas") or []

        caracteristicas = [
            item for item in caracteristicas
            if item != caracteristica_id
        ]

        cliente.update(
            index=self.indice_factores,
            id=factor_elastic_id,
            body={
                "doc": {
                    "caracteristicas": caracteristicas,
                    "fecha_modificacion": self.fecha_actual(),
                }
            },
            refresh=True
        )

        return True

    def obtener_elastic_id_caracteristica(self, cliente, caracteristica_id):
        try:
            respuesta = cliente.get(
                index=self.nombre_indice,
                id=caracteristica_id
            )

            if respuesta.get("found"):
                return respuesta["_id"]

        except Exception:
            pass

        try:
            resultado = cliente.search(
                index=self.nombre_indice,
                body={
                    "query": {
                        "term": {
                            "id": caracteristica_id
                        }
                    },
                    "size": 1
                }
            )

            if resultado["hits"]["total"]["value"] > 0:
                return resultado["hits"]["hits"][0]["_id"]

        except Exception:
            pass

        return None

    def normalizar_caracteristica(self, elastic_id, source):
        return {
            "id": source.get("id") or elastic_id,
            "factor_id": source.get("factor_id"),
            "nombre": source.get("nombre", ""),
            "descripcion": source.get("descripcion", ""),
            "calificacion": source.get("calificacion"),
            "aspectos": source.get("aspectos") or [],
            "activo": source.get("activo", True),
            "fecha_creacion": source.get("fecha_creacion"),
            "fecha_modificacion": source.get("fecha_modificacion"),
        }

    def list(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        factor_id = request.query_params.get("factor_id")

        query = {
            "match_all": {}
        }

        if factor_id:
            query = {
                "term": {
                    "factor_id": factor_id
                }
            }

        resultado = cliente.search(
            index=self.nombre_indice,
            body={
                "query": query,
                "size": 1000
            }
        )

        data = [
            self.normalizar_caracteristica(
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
        except Exception:
            return Response(
                {
                    "error": "No se encontró la característica"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = self.normalizar_caracteristica(
            resultado["_id"],
            resultado["_source"]
        )

        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = CaracteristicaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        factor_elastic_id = data.get("factor_id")

        cliente = self.get_elasticsearch_client()

        factor = self.obtener_factor(
            cliente,
            factor_elastic_id
        )

        if not factor:
            return Response(
                {
                    "error": "No se encontró el factor relacionado",
                    "detalle": "El campo factor_id debe ser el id de Elasticsearch del factor."
                },
                status=status.HTTP_404_NOT_FOUND
            )

        fecha_actual = self.fecha_actual()

        documento = {
            "factor_id": factor_elastic_id,
            "nombre": data.get("nombre"),
            "descripcion": data.get("descripcion") or "",
            "calificacion": data.get("calificacion"),
            "aspectos": data.get("aspectos") or [],
            "activo": data.get("activo", True),
            "fecha_creacion": fecha_actual,
            "fecha_modificacion": fecha_actual,
        }

        respuesta = cliente.index(
            index=self.nombre_indice,
            document=documento,
            refresh=True
        )

        caracteristica_id = respuesta["_id"]

        cliente.update(
            index=self.nombre_indice,
            id=caracteristica_id,
            body={
                "doc": {
                    "id": caracteristica_id
                }
            },
            refresh=True
        )

        self.agregar_caracteristica_al_factor(
            cliente,
            factor_elastic_id,
            caracteristica_id
        )

        documento["id"] = caracteristica_id

        return Response(documento, status=status.HTTP_201_CREATED)

    def update(self, request, pk=None, *args, **kwargs):
        serializer = CaracteristicaUpdateSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        data["fecha_modificacion"] = self.fecha_actual()

        cliente = self.get_elasticsearch_client()

        elastic_id = self.obtener_elastic_id_caracteristica(
            cliente,
            pk
        )

        if not elastic_id:
            return Response(
                {
                    "error": "No se encontró la característica",
                    "id": pk
                },
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            respuesta_actual = cliente.get(
                index=self.nombre_indice,
                id=elastic_id
            )

            caracteristica_actual = respuesta_actual["_source"]

            factor_anterior = caracteristica_actual.get("factor_id")
            factor_nuevo = data.get("factor_id")

            if factor_nuevo and factor_nuevo != factor_anterior:
                factor = self.obtener_factor(
                    cliente,
                    factor_nuevo
                )

                if not factor:
                    return Response(
                        {
                            "error": "No se encontró el nuevo factor relacionado",
                            "detalle": "El campo factor_id debe ser el id de Elasticsearch del factor."
                        },
                        status=status.HTTP_404_NOT_FOUND
                    )

                if factor_anterior:
                    self.quitar_caracteristica_del_factor(
                        cliente,
                        factor_anterior,
                        elastic_id
                    )

                self.agregar_caracteristica_al_factor(
                    cliente,
                    factor_nuevo,
                    elastic_id
                )

            cliente.update(
                index=self.nombre_indice,
                id=elastic_id,
                body={
                    "doc": data
                },
                refresh=True
            )

            resultado = cliente.get(
                index=self.nombre_indice,
                id=elastic_id
            )

            response_data = self.normalizar_caracteristica(
                resultado["_id"],
                resultado["_source"]
            )

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible actualizar la característica",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

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
        except Exception:
            return Response(
                {
                    "error": "No se encontró la característica"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "message": "Característica desactivada correctamente",
                "id": pk
            },
            status=status.HTTP_200_OK
        )
