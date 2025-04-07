from rest_framework import serializers

class DashboardSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()
    observatorio = serializers.CharField()

class DashboardUpdateSerializer(serializers.Serializer):
    nombre = serializers.CharField(required= False ,max_length=255)
    descripcion = serializers.CharField(required= False)


class GraficoSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()
    configuracion = serializers.DictField()

    #check if the configuracion is a valid json and not empty
    def validate_configuracion(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("La configuración debe ser un diccionario no vacío.")
        return value

class GraficoUpdateSerializer(serializers.Serializer):
    nombre = serializers.CharField(required= False ,max_length=255)
    descripcion = serializers.CharField(required= False)
    configuracion = serializers.DictField(required= False)