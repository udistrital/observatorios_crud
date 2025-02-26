from rest_framework import serializers


class ObservatorioSerializer(serializers.Serializer):
    activo = serializers.BooleanField(default=True)
    imagen = serializers.ImageField()
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()


class ObservatorioUPdateSerializer(serializers.Serializer):
    activo = serializers.BooleanField(required=False, default=True)
    imagen = serializers.ImageField(required=False, allow_null=True)
    nombre = serializers.CharField(max_length=255, required=False, allow_null=True)
    descripcion = serializers.CharField(required=False, allow_null=True)