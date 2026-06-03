from django.utils import timezone
from elasticsearch import NotFoundError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .serializers import FactorSerializer, FactorUpdateSerializer


class FactorViewSet(ViewSet):
    nombre_indice = "atlas_factores"
    indice_procesos = "atlas_procesos"

    factor_mapping = {
        "mappings": {
            "properties": {
                "id": {
                    "type": "keyword"
                },
                "proceso_id": {
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
                    "type": "keyword"
                },
                "caracteristicas": {
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

        if not cliente.indices.exists(index=self.nombre_indice):
            cliente.indices.create(
                index=self.nombre_indice,
                body=self.factor_mapping
            )

    def normalizar_factor(self, elastic_id, source):
        return {
            "id": source.get("id") or elastic_id,
            "proceso_id": source.get("proceso_id", ""),
            "nombre": source.get("nombre", ""),
            "descripcion": source.get("descripcion", "") or "",
            "calificacion": source.get("calificacion", "") or "",
            "caracteristicas": source.get("caracteristicas") or [],
            "activo": source.get("activo", True),
            "fecha_creacion": source.get("fecha_creacion"),
            "fecha_modificacion": source.get("fecha_modificacion"),
        }

    def proceso_existe(self, cliente, proceso_id):
        try:
            return cliente.exists(
                index=self.indice_procesos,
                id=proceso_id
            )
        except Exception:
            return False

    def agregar_factor_a_proceso(self, cliente, proceso_id, factor_id):
        cliente.update(
            index=self.indice_procesos,
            id=proceso_id,
            body={
                "script": {
                    "lang": "painless",
                    "source": """
                        if (ctx._source.factores == null) {
                            ctx._source.factores = [];
                        }

                        if (!ctx._source.factores.contains(params.factor_id)) {
                            ctx._source.factores.add(params.factor_id);
                        }

                        ctx._source.fecha_modificacion = params.fecha_modificacion;
                    """,
                    "params": {
                        "factor_id": factor_id,
                        "fecha_modificacion": self.fecha_actual(),
                    }
                }
            },
            refresh=True
        )

    def remover_factor_de_proceso(self, cliente, proceso_id, factor_id):
        if not proceso_id:
            return

        try:
            cliente.update(
                index=self.indice_procesos,
                id=proceso_id,
                body={
                    "script": {
                        "lang": "painless",
                        "source": """
                            if (ctx._source.factores != null) {
                                ctx._source.factores.removeIf(item -> item == params.factor_id);
                            }

                            ctx._source.fecha_modificacion = params.fecha_modificacion;
                        """,
                        "params": {
                            "factor_id": factor_id,
                            "fecha_modificacion": self.fecha_actual(),
                        }
                    }
                },
                refresh=True
            )
        except NotFoundError:
            return

    def list(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()
        proceso_id = request.query_params.get("proceso_id")

        query = {
            "match_all": {}
        }

        if proceso_id:
            query = {
                "term": {
                    "proceso_id": proceso_id
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
            self.normalizar_factor(
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
                    "error": "No se encontró el factor"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = self.normalizar_factor(
            resultado["_id"],
            resultado["_source"]
        )

        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = FactorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        proceso_id = data.get("proceso_id")

        cliente = self.get_elasticsearch_client()

        if not self.proceso_existe(cliente, proceso_id):
            return Response(
                {
                    "error": "No se encontró el proceso asociado",
                    "detalle": "Debe enviar un proceso_id válido para crear el factor."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        fecha_actual = self.fecha_actual()

        documento = {
            "proceso_id": proceso_id,
            "nombre": data.get("nombre"),
            "descripcion": data.get("descripcion") or "",
            "calificacion": data.get("calificacion") or "",
            "caracteristicas": data.get("caracteristicas") or [],
            "activo": data.get("activo", True),
            "fecha_creacion": fecha_actual,
            "fecha_modificacion": fecha_actual,
        }

        respuesta = cliente.index(
            index=self.nombre_indice,
            document=documento,
            refresh=True
        )

        elastic_id = respuesta["_id"]

        try:
            cliente.update(
                index=self.nombre_indice,
                id=elastic_id,
                body={
                    "doc": {
                        "id": elastic_id
                    }
                },
                refresh=True
            )

            self.agregar_factor_a_proceso(
                cliente,
                proceso_id,
                elastic_id
            )

        except Exception as error:
            cliente.options(ignore_status=[404]).delete(
                index=self.nombre_indice,
                id=elastic_id,
                refresh=True
            )

            return Response(
                {
                    "error": "No fue posible asociar el factor al proceso",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                **documento,
                "id": elastic_id,
            },
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None, *args, **kwargs):
        serializer = FactorUpdateSerializer(
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
        except Exception:
            return Response(
                {
                    "error": "No se encontró el factor"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        source_actual = resultado_actual["_source"]
        proceso_id_actual = source_actual.get("proceso_id")
        proceso_id_nuevo = data.get("proceso_id", proceso_id_actual)

        if proceso_id_nuevo != proceso_id_actual:
            if not self.proceso_existe(cliente, proceso_id_nuevo):
                return Response(
                    {
                        "error": "No se encontró el nuevo proceso asociado",
                        "detalle": "El proceso_id enviado no existe."
                    },
                    status=status.HTTP_400_BAD_REQUEST
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

            if proceso_id_nuevo != proceso_id_actual:
                self.remover_factor_de_proceso(
                    cliente,
                    proceso_id_actual,
                    pk
                )

                self.agregar_factor_a_proceso(
                    cliente,
                    proceso_id_nuevo,
                    pk
                )

        except Exception as error:
            return Response(
                {
                    "error": "No fue posible actualizar el factor",
                    "detalle": str(error)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        resultado = cliente.get(
            index=self.nombre_indice,
            id=pk
        )

        response_data = self.normalizar_factor(
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
        except Exception:
            return Response(
                {
                    "error": "No se encontró el factor"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "message": "Factor desactivado correctamente",
                "id": pk
            },
            status=status.HTTP_200_OK
        )
