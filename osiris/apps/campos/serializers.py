from rest_framework import serializers
from .utils import ELASTICSEARCH_CAMPOS

class EstructuraSerializer(serializers.Serializer):
    mapeo =  serializers.JSONField()
    observatorio = serializers.CharField(max_length=255)
    nombre = serializers.CharField()

    def validate_mapeo(self, value):
        """
        Valida que el campo 'mapeo' sea una lista de objetos con 'nombre' y 'tipo'.
        También verifica que 'tipo' esté dentro de ELASTICSEARCH_CAMPOS.
        """
        if not isinstance(value, list):
            raise serializers.ValidationError("El campo 'mapeo' debe ser una lista de objetos.")

        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError("Cada elemento de 'mapeo' debe ser un diccionario con 'nombre' y 'tipo'.")

            if "nombre" not in item or "tipo" not in item:
                raise serializers.ValidationError("Cada objeto en 'mapeo' debe contener 'nombre' y 'tipo'.")

            if item["tipo"] not in ELASTICSEARCH_CAMPOS:
                raise serializers.ValidationError(f"El tipo '{item['tipo']}' no es válido. Tipos permitidos: {list(ELASTICSEARCH_CAMPOS.keys())}")

        return value