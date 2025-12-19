from rest_framework import serializers
from .utils import ELASTICSEARCH_CAMPOS
from apps.elasticsearch_utils.serializers import BaseSerializerAuditoria

class EstructuraSerializer(BaseSerializerAuditoria):
    mapeo =  serializers.JSONField()
    mapeo_archivos = serializers.JSONField(required=False)
    observatorio = serializers.CharField(max_length=255)
    nombre = serializers.CharField()

    #def validate_mapeo(self, value):
    #    """
    #    Valida que el campo 'mapeo' sea una lista de objetos con 'nombre' y 'tipo'.
    #    También verifica que 'tipo' esté dentro de ELASTICSEARCH_CAMPOS.
    #    """
    #    if not isinstance(value, list):
    #        raise serializers.ValidationError("El campo 'mapeo' debe ser una lista de objetos.")
    #
    #    for item in value:
    #        if not isinstance(item, dict):
    #            raise serializers.ValidationError("Cada elemento de 'mapeo' debe ser un diccionario con 'nombre' y 'tipo'.")
    #
    #        if "nombre" not in item or "tipo" not in item:
    #            raise serializers.ValidationError("Cada objeto en 'mapeo' debe contener 'nombre' y 'tipo'.")
    #
    #        if item["tipo"] not in ELASTICSEARCH_CAMPOS:
    #            raise serializers.ValidationError(f"El tipo '{item['tipo']}' no es válido. Tipos permitidos: {list(ELASTICSEARCH_CAMPOS.keys())}")
    #
    #    return value
    #

    def validate_mapeo(self, value):
        return self.validate_base_mapeo(value)

    def validate_mapeo_archivos(self, value):
        return self.validate_base_mapeo(value)

    def validate_base_mapeo(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("El campo debe ser una lista de objetos.")

        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Cada elemento debe ser un diccionario con 'nombre' y 'tipo'.")

            if "nombre" not in item or "tipo" not in item:
                raise serializers.ValidationError("Cada objeto debe contener 'nombre' y 'tipo'.")

            if item["tipo"] not in ELASTICSEARCH_CAMPOS:
                raise serializers.ValidationError(f"Tipo inválido '{item['tipo']}'. Permitidos: {list(ELASTICSEARCH_CAMPOS.keys())}")
        return value


class EstructuraUpdateSerializer(BaseSerializerAuditoria):
    """
    Serializador para actualizar una estructura de campos.
    """
    mapeo =  serializers.JSONField(required=False)
    mapeo_archivos = serializers.JSONField(required=False)
    nombre = serializers.CharField(required=False)

    def validate_mapeo(self, value):
        return self.validate_base_mapeo(value)

    def validate_mapeo_archivos(self, value):
        return self.validate_base_mapeo(value)

    def validate_base_mapeo(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("El campo debe ser una lista de objetos.")

        for item in value:
            if "nombre" not in item or "tipo" not in item:
                raise serializers.ValidationError("Cada objeto debe contener 'nombre' y 'tipo'.")
            if "valor_anterior" in item and not isinstance(item["valor_anterior"], str):
                raise serializers.ValidationError("valor_anterior debe ser string")
            if item["tipo"] not in ELASTICSEARCH_CAMPOS:
                raise serializers.ValidationError(f"Tipo inválido '{item['tipo']}'.")
        return value