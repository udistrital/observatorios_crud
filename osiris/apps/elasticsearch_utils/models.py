from django.db import models

# Create your models here.


#TODO mejorar esta clase
class ElasticField:
    def __init__(self, field_type=None, validators=None, default = None ):
        self.field_type = field_type
        self.validators = validators or []
        if default: self.value =  default

    def set_value(self, value):
        """Método para actualizar el valor del campo y ejecutar validaciones."""
        self.value = value
        self._validate()

    def get_value(self):
        """Retorna el valor del campo."""
        return self.value

    def _validate(self):
        """Método que ejecuta las validaciones sobre el valor del campo."""
        if self.value and self.field_type:
            if not isinstance(self.value, self.field_type):
                raise ValueError(f"Expected type {self.field_type} for value, got {type(self.value)}")
        
        # Ejecutar validadores adicionales si están definidos
        for validator in self.validators:
            validator(self.value)


class ElasticSearchModel():

    def __init__(self, **kwargs):
        # Asigna valores desde kwargs a los campos ElasticField
        super().__init__()

        for key, field in self._get_elastic_fields():
            if key in kwargs:
                getattr(self, key).set_value(kwargs[key])


    def execute_validators(self):
        """Ejecuta validadores sobre los campos del observatorio."""
        for _, field in self._get_elastic_fields():
            field._validate()
        return "Validators executed successfully."


    def get_document(self):

        """Construye el documento a indexar para Elasticsearch."""
        document =  {key: field.get_value() for key, field in self._get_elastic_fields()}
        print(document)
        return document
    

    def create(self, es, index_name):
        """
        Crea un item del modelo desde un diccionario de datos.
        
        :param es: Cliente de Elasticsearch.
        :param data: Diccionario de datos.
        :param index_name: Nombre del índice.
        :return: Resultado de la operación.
        """

        
        # Ejecutar validadores
        self.execute_validators()

        # Crear el documento y guardarlo
        document = self.get_document()
        data =  es.index(index=index_name, body=document)
        print(data, document)
        return f"Observatory created and indexed."
        

    def _get_elastic_fields(self):
        # Retorna los nombres de los campos tipo ElasticField en la clase
        return [
            (name, getattr(self, name))  # Obtiene el valor real del atributo
            for name in dir(self)
            if isinstance(getattr(self, name), ElasticField)  # Filtra solo los de tipo ElasticField
        ]
    

class AuditModel(ElasticSearchModel):
    is_active =  ElasticField(bool, default=True)
