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

class GraficoUpdateSerializer(serializers.Serializer):
    nombre = serializers.CharField(required= False ,max_length=255)
    descripcion = serializers.CharField(required= False)