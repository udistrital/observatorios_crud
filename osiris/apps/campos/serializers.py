from rest_framework import serializers


class CampoSerializer(serializers.Serializer):
    campo_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True
    )

    orden = serializers.IntegerField(
        required=False,
        allow_null=True
    )

    nombre_campo = serializers.CharField(
        required=True,
        allow_blank=False
    )

    tipo_campo = serializers.CharField(
        required=True,
        allow_blank=False
    )

    activo = serializers.BooleanField(
        required=False,
        default=True
    )

    # Se usa cuando el usuario cambia el tipo del campo.
    # Si viene en true, el backend intenta migrar el valor anterior
    # al nuevo campo_id generado.
    migrar_data = serializers.BooleanField(
        required=False,
        default=False
    )

    def validate_nombre_campo(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "El nombre del campo es obligatorio."
            )

        return value

    def validate_tipo_campo(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError(
                "El tipo del campo es obligatorio."
            )

        return value


class EstructuraSerializer(serializers.Serializer):
    aspecto_id = serializers.CharField(required=False)
    tipo_evidencia = serializers.CharField(required=False)
    nombre = serializers.CharField(required=False)
    activo = serializers.BooleanField(required=False)

    campos = CampoSerializer(
        many=True,
        required=False
    )

    data = serializers.ListField(
        required=False
    )

    def validate_data(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "El campo data debe ser una lista."
            )

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

    campos = CampoSerializer(
        many=True,
        required=False
    )

    data = serializers.ListField(
        required=False
    )

    # Este campo es solo una instrucción del request.
    # No se guarda dentro del documento.
    eliminar_data_campos = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    def validate_data(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                "El campo data debe ser una lista."
            )

        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    "Cada registro de data debe ser un objeto."
                )

        return value
