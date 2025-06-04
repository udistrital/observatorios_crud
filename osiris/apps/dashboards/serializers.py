from rest_framework import serializers
from apps.elasticsearch_utils.serializers import BaseSerializerAuditoria
from apps.graficos.utils import validar_configuracion

class DashboardSerializer(BaseSerializerAuditoria):
    activo = serializers.BooleanField(default=True)
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()
    observatorio = serializers.CharField()
    columnas = serializers.IntegerField()



class DashboardUpdateSerializer(BaseSerializerAuditoria):
    nombre = serializers.CharField(required= False ,max_length=255)
    descripcion = serializers.CharField(required= False)
    columnas = serializers.IntegerField(required =  False)


class GraficoSerializer(BaseSerializerAuditoria):
    nombre = serializers.CharField(max_length=255)
    descripcion = serializers.CharField()
    configuracion = serializers.DictField()
    columna = serializers.IntegerField()
    fila = serializers.IntegerField()
    estructura = serializers.CharField()

    #check if the configuracion is a valid json and not empty
    def validate_configuracion(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("La configuración debe ser un diccionario no vacío.")
        
        try:
            validar_configuracion(value)
        except Exception as e:
            raise serializers.ValidationError(f"Error en la configuración: {str(e)}")


        return value

class GraficoUpdateSerializer(BaseSerializerAuditoria):
    nombre = serializers.CharField(required= False ,max_length=255)
    descripcion = serializers.CharField(required= False)
    configuracion = serializers.DictField(required= False)
    columna = serializers.IntegerField(required= False)
    fila = serializers.IntegerField(required= False)
    estructura = serializers.CharField(required= False)

    def validate_configuracion(self, value):
        if not isinstance(value, dict) or not value:
            raise serializers.ValidationError("La configuración debe ser un diccionario no vacío.")
        
        try:
            validar_configuracion(value)
        except Exception as e:
            raise serializers.ValidationError(f"Error en la configuración: {str(e)}")

        return value