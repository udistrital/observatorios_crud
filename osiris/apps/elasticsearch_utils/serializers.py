from rest_framework import serializers

class BaseSerializerAuditoria(serializers.Serializer):
    """
    Serializador para la auditoría de los cambios en los campos de Elasticsearch.
    """
    activo = serializers.BooleanField(default=True, required=False)
    fecha_creacion = serializers.DateTimeField(required=False)
    fecha_modificacion = serializers.DateTimeField(required=False)