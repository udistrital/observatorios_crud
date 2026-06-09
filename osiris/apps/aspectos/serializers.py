import json
from rest_framework import serializers

TIPOS_EVIDENCIA_PERMITIDOS = ["Documental", "Tabla"]

class EstructurasEvidenciasField(serializers.Field):
    def to_internal_value(self, data):
        if data in [None, ""]:
            return []

        if isinstance(data, str):
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                raise serializers.ValidationError(
                    "El campo estructuras_evidencias debe ser una lista válida."
                )

        if not isinstance(data, list):
            raise serializers.ValidationError(
                "El campo estructuras_evidencias debe ser una lista."
            )

        estructuras = []
        ids = set()

        for index, item in enumerate(data):
            if not isinstance(item, dict):
                raise serializers.ValidationError(
                    f"La estructura de evidencia en la posición {index} debe ser un objeto."
                )

            estructura_id = item.get("id")
            tipo_evidencia = item.get("tipo_evidencia")
            nombre = item.get("nombre")
            activo = item.get("activo", True)

            if not estructura_id:
                raise serializers.ValidationError(
                    f"La estructura de evidencia en la posición {index} debe tener id."
                )

            if not tipo_evidencia:
                raise serializers.ValidationError(
                    f"La estructura de evidencia en la posición {index} debe tener tipo_evidencia."
                )

            if tipo_evidencia not in TIPOS_EVIDENCIA_PERMITIDOS:
                raise serializers.ValidationError(
                    "El tipo de evidencia debe ser Documental o Tabla."
                )

            if not nombre:
                raise serializers.ValidationError(
                    f"La estructura de evidencia en la posición {index} debe tener nombre."
                )

            if not isinstance(activo, bool):
                raise serializers.ValidationError(
                    f"El campo activo de la estructura de evidencia en la posición {index} debe ser booleano."
                )

            if estructura_id in ids:
                raise serializers.ValidationError(
                    f"El id '{estructura_id}' está repetido en estructuras_evidencias."
                )

            ids.add(estructura_id)

            estructuras.append(
                {
                    "id": estructura_id,
                    "tipo_evidencia": tipo_evidencia,
                    "nombre": nombre,
                    "activo": activo,
                }
            )

        return estructuras

    def to_representation(self, value):
        if not isinstance(value, list):
            return []

        estructuras = []

        for item in value:
            if not isinstance(item, dict):
                continue

            estructuras.append(
                {
                    "id": item.get("id"),
                    "tipo_evidencia": item.get("tipo_evidencia"),
                    "nombre": item.get("nombre"),
                    "activo": item.get("activo", True),
                }
            )

        return estructuras


class AspectoSerializer(serializers.Serializer):
    caracteristica_id = serializers.CharField(required=True)
    nombre = serializers.CharField(required=True, max_length=1000)
    estructuras_evidencias = EstructurasEvidenciasField(required=False)
    activo = serializers.BooleanField(required=False, default=True)


class AspectoUpdateSerializer(serializers.Serializer):
    caracteristica_id = serializers.CharField(required=False)

    nombre = serializers.CharField(
        required=False,
        max_length=1000,
        allow_blank=True,
        allow_null=True
    )

    estructuras_evidencias = EstructurasEvidenciasField(required=False)

    activo = serializers.BooleanField(required=False)
