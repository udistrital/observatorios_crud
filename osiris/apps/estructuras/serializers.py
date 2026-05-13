from rest_framework import serializers


TIPOS_EVIDENCIA_PERMITIDOS = ["Documental", "Tabla"]


class EstructuraEvidenciaSerializer(serializers.Serializer):
    aspecto_id = serializers.CharField(required=True)
    tipo_evidencia = serializers.CharField(required=True)
    nombre = serializers.CharField(required=True, max_length=1000)
    activo = serializers.BooleanField(required=False, default=True)

    def validate_tipo_evidencia(self, value):
        value = value.strip()

        if value not in TIPOS_EVIDENCIA_PERMITIDOS:
            raise serializers.ValidationError(
                "El tipo de evidencia debe ser Documental o Tabla."
            )

        return value


class EstructuraEvidenciaUpdateSerializer(serializers.Serializer):
    aspecto_id = serializers.CharField(required=False)
    tipo_evidencia = serializers.CharField(required=False)
    nombre = serializers.CharField(
        required=False,
        max_length=1000,
        allow_blank=False,
        allow_null=False
    )
    activo = serializers.BooleanField(required=False)

    def validate_tipo_evidencia(self, value):
        value = value.strip()

        if value not in TIPOS_EVIDENCIA_PERMITIDOS:
            raise serializers.ValidationError(
                "El tipo de evidencia debe ser Documental o Tabla."
            )

        return value
