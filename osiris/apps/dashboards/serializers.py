from rest_framework import serializers

class DashboardSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()

class DashboardUpdateSerializer(serializers.Serializer):
    nombre = serializers.CharField(required= False ,max_length=255)
    descripcion = serializers.CharField(required= False)


class GraficoSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()
    type = serializers.CharField()
    agregacion = serializers.CharField()

class GraficoUpdateSerializer(serializers.Serializer):
    nombre = serializers.CharField(required=False, max_length=255)
    descripcion = serializers.CharField(required=False)
    x_inicio = serializers.IntegerField(required=False)
    y_inicio = serializers.IntegerField(required=False)
    x_final = serializers.IntegerField(required=False)
    y_final = serializers.IntegerField(required=False)
    type = serializers.CharField(required=False)
    agregacion = serializers.CharField(required=False)