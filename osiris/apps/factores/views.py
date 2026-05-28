from rest_framework import status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.elasticsearch_utils.utils import get_elasticsearch_client

from .serializers import FactorSerializer, FactorUpdateSerializer


class FactorViewSet(ViewSet):
    nombre_indice = "atlas_factores"

    def get_elasticsearch_client(self):
        return get_elasticsearch_client()

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        cliente = self.get_elasticsearch_client()

        if not cliente.indices.exists(index=self.nombre_indice):
            cliente.indices.create(index=self.nombre_indice)

    def normalizar_factor(self, elastic_id, source):
        return {
            "id": elastic_id,
            "nombre": source.get("nombre", ""),
            "descripcion": source.get("descripcion", "") or "",
            "calificacion": source.get("calificacion", "") or "",
            "activo": source.get("activo", True),
            "caracteristicas": source.get("caracteristicas") or [],
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

        documento = {
            "nombre": data.get("nombre"),
            "descripcion": data.get("descripcion") or "",
            "calificacion": data.get("calificacion") or "",
            "activo": data.get("activo", True),
            "caracteristicas": data.get("caracteristicas") or [],
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
        serializer = FactorUpdateSerializer(
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

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
                    "error": "No se encontró el factor"
                },
                status=status.HTTP_404_NOT_FOUND
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
                        "activo": False
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
