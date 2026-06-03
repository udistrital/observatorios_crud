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


class AspectosField(serializers.Field):
    def to_internal_value(self, data):
        if data in [None, ""]:
            return []

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "El campo aspectos debe ser una lista válida."
                )

        if not isinstance(data, list):
            raise serializers.ValidationError(
                "El campo aspectos debe ser una lista."
            )

        for item in data:
            if not isinstance(item, str):
                raise serializers.ValidationError(
                    "El campo aspectos solo debe contener IDs de Elasticsearch."
                )

        return data

    def to_representation(self, value):
        if isinstance(value, list):
            return value

        return []


class CaracteristicaSerializer(serializers.Serializer):
    factor_id = serializers.CharField(required=True)
    nombre = serializers.CharField(required=True, max_length=1000)
    descripcion = serializers.CharField(required=True)
    calificacion = CalificacionField(required=False)
    aspectos = AspectosField(required=False)
    activo = serializers.BooleanField(required=False, default=True)


class CaracteristicaUpdateSerializer(serializers.Serializer):
    factor_id = serializers.CharField(required=False)
    nombre = serializers.CharField(required=False, max_length=1000)
    descripcion = serializers.CharField(required=False)
    calificacion = CalificacionField(required=False)
    aspectos = AspectosField(required=False)
    activo = serializers.BooleanField(required=False)
