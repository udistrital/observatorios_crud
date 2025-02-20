from django.db import models
import os
from django.conf import settings
import uuid

# Create your models here.


#TODO mejorar esta clase
class ElasticCampo:
    def __init__(self, tipo_campo=None, validadores=None, valor_por_defecto=None, guardar_en = ""):
        
        self.guardar_en = guardar_en
        self.tipo_campo = tipo_campo
        self.validadores = validadores or []
        if valor_por_defecto:
            self.valor = valor_por_defecto

    def establecer_valor(self, valor):
        """Método para actualizar el valor del campo y ejecutar validaciones."""
        self.valor = valor
        self._validar()

    def obtener_valor(self):
        """Retorna el valor del campo."""
        return self.valor

    def _validar(self):
        """Método que ejecuta las validaciones sobre el valor del campo."""
        if self.valor and self.tipo_campo:
            if not isinstance(self.valor, self.tipo_campo):
                raise ValueError(f"Se esperaba un tipo {self.tipo_campo} para el valor, pero se obtuvo {type(self.valor)}")
        
        # Ejecutar validadores adicionales si están definidos
        for validador in self.validadores:
            validador(self.valor)

class ImagenCampo(ElasticCampo):

    archivo_carga =  None

    def obtener_valor(self):
        """Retorna el valor del campo."""
        return self.valor
    
    
    def save(self):
        # Guardar el archivo manualmente
        file = self.archivo_carga
        id = uuid.uuid1()

        file_path = os.path.join(settings.MEDIA_ROOT,self.guardar_en, id + file.name)

        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)
            
        return file_path


class ModeloElasticSearch:

    id =  ElasticCampo(str)

    def __init__(self, **kwargs):
        # Asigna valores desde kwargs a los campos CampoElástico
        super().__init__()

        for clave, campo in self._obtener_campos_elastic():
            if clave in kwargs:

                if isinstance(campo, (ImagenCampo)): 
                    campo.archivo_carga = kwargs.get(clave)
                    kwargs[clave] = kwargs.get(clave).name

                getattr(self, clave).establecer_valor(kwargs.get(clave))

                

    def ejecutar_validadores(self):
        """Ejecuta los validadores sobre los campos del modelo."""

        for _, campo in self._obtener_campos_elastic():
            campo._validar()
        return "Validadores ejecutados exitosamente."

    def obtener_documento(self):
        """Construye el documento a indexar en Elasticsearch."""

        documento = {clave: campo.obtener_valor() for clave, campo in self._obtener_campos_elastic()}
        return documento

    def guardar_campos_archivos(self, es, nombre_indice):
        
        urls = {}
        
        for clave, campo in self._obtener_campos_elastic():
            if isinstance(campo, (ImagenCampo)): urls[clave] = campo.save() 

        es.update(
            index=nombre_indice,  # El índice de Elasticsearch
            id=self.id,
            body={"doc": urls}
        )


    def crear(self, es, nombre_indice):
        """
        Crea un ítem del modelo desde un diccionario de datos.
        
        :param es: Cliente de Elasticsearch.
        :param nombre_indice: Nombre del índice.
        :return: Resultado de la operación.
        """

        # Ejecutar validadores
        self.ejecutar_validadores()

        # Crear el documento y guardarlo
        documento = self.obtener_documento()
        datos = es.index(index=nombre_indice, body=documento)
        self.id =  datos["_id"]

        self.guardar_campos_archivos(es,nombre_indice)


        return {**documento, "id": datos["_id"]}

    def _obtener_campos_elastic(self):
        """Retorna los nombres de los campos de tipo ElasticCampo en la clase."""
        return [
            (nombre, getattr(self, nombre))  # Obtiene el valor real del atributo
            for nombre in dir(self)
            if isinstance(getattr(self, nombre), (ElasticCampo, ImagenCampo))
        ]
    

    def get(self, es, nombre_indice, item_id):
        """
        Obtiene un ítem desde Elasticsearch por su ID.
        
        :param es: Cliente de Elasticsearch.
        :param nombre_indice: Nombre del índice donde buscar.
        :param item_id: ID del documento a recuperar.
        :return: Instancia del modelo 
        """
        respuesta = es.get(index=nombre_indice, id=item_id)

        if respuesta["found"]:
            
            documento= {**respuesta["_source"] , "id" :respuesta["_id"]}
            objeto = ModeloElasticSearch(**documento)
            return objeto

    @staticmethod
    def generar_datos_masivos(data, index_name):
        for record in data:
            yield {
                "_index": index_name,
                "_source": record
            }


class AuditoriaModelo(ModeloElasticSearch):
    activo =  ElasticCampo(bool, valor_por_defecto=True)
    #TODO: Fecha de craciòn, modificaciòn y usuario