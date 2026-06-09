import json
from rest_framework import serializers

class CalificacionField(serializers.Field):
    def to_internal_value(self, data):
        if data in [None, ""]:
            return None

        try:
            return float(data)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                "El campo calificacion debe ser un número decimal."
            )

    def to_representation(self, value):
        if value in [None, ""]:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

class CaracteristicasField(serializers.Field):
    def to_internal_value(self, data):
        if data in [None, ""]:
            return []

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "El campo caracteristicas debe ser una lista válida."
                )

        if not isinstance(data, list):
            raise serializers.ValidationError(
                "El campo caracteristicas debe ser una lista."
            )

        for item in data:
            if not isinstance(item, str):
                raise serializers.ValidationError(
                    "El campo caracteristicas solo debe contener IDs de Elasticsearch."
                )

        return data

    def to_representation(self, value):
        if isinstance(value, list):
            return value

        return []


class FactorSerializer(serializers.Serializer):
    proceso_id = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False
    )
    nombre = serializers.CharField(
        max_length=1000
    )
    descripcion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    calificacion = CalificacionField(
        required=False
    )
    caracteristicas = CaracteristicasField(
        required=False
    )
    activo = serializers.BooleanField(
        required=False,
        default=True
    )


class FactorUpdateSerializer(serializers.Serializer):
    proceso_id = serializers.CharField(
        required=False,
        allow_blank=False,
        allow_null=False
    )
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
    calificacion = CalificacionField(
        required=False
    )
    caracteristicas = CaracteristicasField(
        required=False
    )
    activo = serializers.BooleanField(
        required=False
    )
