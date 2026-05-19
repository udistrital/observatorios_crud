from rest_framework import serializers

from .utils import ELASTICSEARCH_CAMPOS, normalizar_campos


class CampoSerializer(serializers.Serializer):
    nombre_campo = serializers.CharField(required=True)
    tipo_campo = serializers.CharField(required=True)

    def validate_tipo_campo(self, value):
        value = value.strip()

        if value not in ELASTICSEARCH_CAMPOS:
            raise serializers.ValidationError(
                f"Tipo inválido '{value}'. Permitidos: {list(ELASTICSEARCH_CAMPOS.keys())}"
            )

        return value

    def validate_nombre_campo(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("El nombre del campo es obligatorio.")

        return value


class EstructuraSerializer(serializers.Serializer):
    aspecto_id = serializers.CharField(required=False)
    tipo_evidencia = serializers.CharField(required=False)
    nombre = serializers.CharField(required=False)
    activo = serializers.BooleanField(required=False)
    campos = CampoSerializer(many=True, required=False)
    data = serializers.ListField(required=False)

    def validate_campos(self, value):
        try:
            return normalizar_campos(value)
        except ValueError as error:
            raise serializers.ValidationError(str(error))

    def validate_data(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("El campo data debe ser una lista.")

        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    "Cada registro de data debe ser un objeto."
                )

        return value


class EstructuraUpdateSerializer(serializers.Serializer):
    aspecto_id = serializers.CharField(required=False)
    tipo_evidencia = serializers.CharField(required=False)
    nombre = serializers.CharField(required=False)
    activo = serializers.BooleanField(required=False)
    campos = CampoSerializer(many=True, required=False)
    data = serializers.ListField(required=False)

    # Este campo es solo una instrucción del request.
    # No se guarda dentro del documento.
    eliminar_data_campos = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    def validate_campos(self, value):
        try:
            return normalizar_campos(value)
        except ValueError as error:
            raise serializers.ValidationError(str(error))

    def validate_data(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("El campo data debe ser una lista.")

        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    "Cada registro de data debe ser un objeto."
                )

        return value
