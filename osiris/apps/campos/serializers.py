from rest_framework import serializers


class EstructuraSerializer(serializers.Serializer):
    mapeo =  serializers.JSONField()
    observatorio = serializers.CharField(max_length=255)
    nombre = serializers.CharField()