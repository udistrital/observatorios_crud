from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .serializers import ProcesoSerializer, ProcesoUpdateSerializer


class ProcesoViewSet(ViewSet):
    nombre_indice = "atlas_procesos"

    proceso_mapping = {
        "mappings": {
            "properties": {
                "id": {
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
                "dependencia_responsable": {
                    "type": "text",
                    "fields": {
                        "keyword": {
                            "type": "keyword"
                        }
                    }
                },
                "objetivo": {
                    "type": "text"
                },
                "factores": {
                    "type": "keyword"
                },
                "fecha_inicio": {
                    "type": "date"
                },
                "fecha_fin": {
                    "type": "date"
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
                body=self.proceso_mapping
            )

    def normalizar_proceso(self, elastic_id, source):
        return {
            "id": source.get("id") or elastic_id,
            "nombre": source.get("nombre", ""),
            "descripcion": source.get("descripcion", "") or "",
            "dependencia_responsable": source.get("dependencia_responsable", "") or "",
            "objetivo": source.get("objetivo", "") or "",
            "factores": source.get("factores") or [],
            "fecha_inicio": source.get("fecha_inicio"),
            "fecha_fin": source.get("fecha_fin"),
            "activo": source.get("activo", True),
            "fecha_creacion": source.get("fecha_creacion"),
            "fecha_modificacion": source.get("fecha_modificacion"),
        }

    def list(self, request, *args, **kwargs):
        cliente = self.get_elasticsearch_client()

        resultado = cliente.search(
            index=self.nombre_indice,
            body={
                "query": {
                    "match_all": {}
                },
                "size": 1000
            }
        )

        data = [
            self.normalizar_proceso(
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
                    "error": "No se encontró el proceso"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        data = self.normalizar_proceso(
            resultado["_id"],
            resultado["_source"]
        )

        return Response(data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = ProcesoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        fecha_actual = self.fecha_actual()

        documento = {
            "nombre": data.get("nombre"),
            "descripcion": data.get("descripcion") or "",
            "dependencia_responsable": data.get("dependencia_responsable") or "",
            "objetivo": data.get("objetivo") or "",
            "factores": data.get("factores") or [],
            "fecha_inicio": data.get("fecha_inicio"),
            "fecha_fin": data.get("fecha_fin"),
            "activo": data.get("activo", True),
            "fecha_creacion": fecha_actual,
            "fecha_modificacion": fecha_actual,
        }

        cliente = self.get_elasticsearch_client()

        respuesta = cliente.index(
            index=self.nombre_indice,
            document=documento,
            refresh=True
        )

        elastic_id = respuesta["_id"]

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

        return Response(
            {
                **documento,
                "id": elastic_id,
            },
            status=status.HTTP_201_CREATED
        )

    def update(self, request, pk=None, *args, **kwargs):
        serializer = ProcesoUpdateSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        data["fecha_modificacion"] = self.fecha_actual()

        cliente = self.get_elasticsearch_client()

        try:
            cliente.update(
                index=self.nombre_indice,
                id=pk,
                body={
                    "doc": data
                },
                refresh=True
            )
        except Exception:
            return Response(
                {
                    "error": "No se encontró el proceso"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        resultado = cliente.get(
            index=self.nombre_indice,
            id=pk
        )

        response_data = self.normalizar_proceso(
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
                    "error": "No se encontró el proceso"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {
                "message": "Proceso desactivado correctamente",
                "id": pk
            },
            status=status.HTTP_200_OK
        )
