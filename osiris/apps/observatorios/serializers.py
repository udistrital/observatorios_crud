from rest_framework import serializers


class ObservatorioSerializer(serializers.Serializer):
    activo = serializers.BooleanField(default=True)
    imagen = serializers.ImageField()
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()