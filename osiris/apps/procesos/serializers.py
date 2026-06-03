import json
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import serializers


class FechaFlexibleField(serializers.Field):
    """
    Acepta fechas enviadas por el cliente como YYYY-MM-DD o fecha/hora ISO.
    Guarda el valor como string compatible con el tipo date de Elasticsearch.
    """

    def to_internal_value(self, data):
        if data in [None, ""]:
            return None

        if not isinstance(data, str):
            raise serializers.ValidationError(
                "La fecha debe enviarse como texto en formato YYYY-MM-DD o ISO 8601."
            )

        value = data.strip()

        if parse_datetime(value) or parse_date(value):
            return value

        raise serializers.ValidationError(
            "La fecha debe tener formato YYYY-MM-DD o ISO 8601."
        )

    def to_representation(self, value):
        return value


class FactoresField(serializers.Field):
    def to_internal_value(self, data):
        if data in [None, ""]:
            return []

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "El campo factores debe ser una lista válida."
                )

        if not isinstance(data, list):
            raise serializers.ValidationError(
                "El campo factores debe ser una lista."
            )

        for item in data:
            if not isinstance(item, str):
                raise serializers.ValidationError(
                    "El campo factores solo debe contener IDs de Elasticsearch."
                )

        return data

    def to_representation(self, value):
        if isinstance(value, list):
            return value

        return []


class ProcesoSerializer(serializers.Serializer):
    nombre = serializers.CharField(
        max_length=1000
    )
    descripcion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    dependencia_responsable = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=1000
    )
    objetivo = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    fecha_inicio = FechaFlexibleField(
        required=True
    )
    fecha_fin = FechaFlexibleField(
        required=True
    )
    factores = FactoresField(
        required=False
    )
    activo = serializers.BooleanField(
        required=False,
        default=True
    )

class ProcesoUpdateSerializer(serializers.Serializer):
    nombre = serializers.CharField(
        max_length=1000,
        required=False,
        allow_blank=True,
        allow_null=True
    )
    descripcion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    dependencia_responsable = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=1000
    )
    objetivo = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    fecha_inicio = FechaFlexibleField(
        required=False
    )
    fecha_fin = FechaFlexibleField(
        required=False
    )
    factores = FactoresField(
        required=False
    )
    activo = serializers.BooleanField(
        required=False
    )
