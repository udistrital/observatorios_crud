from rest_framework import serializers 


class DatosSerializers(serializers.Serializer):
    archivo = serializers.FileField(required=False, allow_null=True)
    formato = serializers.ChoiceField(choices=['FORM', 'JSON', 'CSV'], default='FORM')