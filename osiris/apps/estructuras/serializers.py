from rest_framework import serializers


TIPOS_EVIDENCIA_PERMITIDOS = ["Documental", "Tabla"]

TIPOS_CAMPO_PERMITIDOS = [
    "text",
    "keyword",
    "long",
    "integer",
    "short",
    "byte",
    "double",
    "float",
    "half_float",
    "scaled_float",
    "boolean",
    "date",
    "date_nanos",
    "geo_point",
    "geo_shape",
    "ip",
    "binary",
    "object",
    "nested",
    "token_count",
    "integer_range",
    "float_range",
    "long_range",
    "double_range",
    "date_range",
    "ip_range",
    "constant_keyword",
    "flattened",
    "shape",
]


class CampoEstructuraSerializer(serializers.Serializer):
    nombre_campo = serializers.CharField(required=True)
    tipo_campo = serializers.CharField(required=True)

    def validate_nombre_campo(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("El nombre del campo es obligatorio.")

        if "." in value or "[" in value or "]" in value:
            raise serializers.ValidationError(
                "El nombre del campo no puede contener punto ni corchetes."
            )

        return value

    def validate_tipo_campo(self, value):
        value = value.strip()

        if value not in TIPOS_CAMPO_PERMITIDOS:
            raise serializers.ValidationError(
                f"Tipo de campo inválido: {value}."
            )

        return value


class EstructuraEvidenciaSerializer(serializers.Serializer):
    aspecto_id = serializers.CharField(required=True)
    tipo_evidencia = serializers.CharField(required=True)
    nombre = serializers.CharField(required=True, max_length=1000)
    activo = serializers.BooleanField(required=False, default=True)
    campos = CampoEstructuraSerializer(many=True, required=False, default=list)
    data = serializers.ListField(required=False, default=list)

    def validate_tipo_evidencia(self, value):
        value = value.strip()

        if value not in TIPOS_EVIDENCIA_PERMITIDOS:
            raise serializers.ValidationError(
                "El tipo de evidencia debe ser Documental o Tabla."
            )

        return value

    def validate_campos(self, value):
        nombres = [
            campo["nombre_campo"].lower()
            for campo in value
        ]

        if len(nombres) != len(set(nombres)):
            raise serializers.ValidationError(
                "No puede haber campos repetidos."
            )

        return value

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
    campos = CampoEstructuraSerializer(many=True, required=False)
    data = serializers.ListField(required=False)

    # Campo de acción. NO se guarda en el documento.
    eliminar_data_campos = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )

    def validate_tipo_evidencia(self, value):
        value = value.strip()

        if value not in TIPOS_EVIDENCIA_PERMITIDOS:
            raise serializers.ValidationError(
                "El tipo de evidencia debe ser Documental o Tabla."
            )

        return value

    def validate_campos(self, value):
        nombres = [
            campo["nombre_campo"].lower()
            for campo in value
        ]

        if len(nombres) != len(set(nombres)):
            raise serializers.ValidationError(
                "No puede haber campos repetidos."
            )

        return value

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
