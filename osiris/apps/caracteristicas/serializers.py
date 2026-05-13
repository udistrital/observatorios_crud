import json
from rest_framework import serializers


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
    calificacion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    activo = serializers.BooleanField(required=False, default=True)
    aspectos = AspectosField(required=False)


class CaracteristicaUpdateSerializer(serializers.Serializer):
    factor_id = serializers.CharField(required=False)
    nombre = serializers.CharField(required=False, max_length=1000)
    descripcion = serializers.CharField(required=False)
    calificacion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )
    activo = serializers.BooleanField(required=False)
    aspectos = AspectosField(required=False)
