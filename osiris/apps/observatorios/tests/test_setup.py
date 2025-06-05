from rest_framework.test import APITestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image
import tempfile
from elasticsearch import helpers
from apps.observatorios.models import ObservatorioModelo
from apps.elasticsearch_utils.utils import get_elasticsearch_client
from unittest import mock


class TestSetUP(APITestCase):

    def setUp(self):

        
        ObservatorioModelo.indice = "test_observatorios"
        get_elasticsearch_client().indices.create(index="test_observatorios")


        image = Image.new('RGB', (100, 100))

        tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        image.save(tmp_file)
        tmp_file.seek(0)
        

        self.observatorios_link = reverse('Observatorio-list', kwargs={'version': 'v1'})
        self.observatorio_informacion = {
            "nombre" : "observatorio test",
            "descripcion" : "descripcion de datos",
            "imagen" : tmp_file
            
        }
        return super().setUp()
    
    def tearDown(self):

        get_elasticsearch_client().indices.delete(index="test_observatorios")
        return super().tearDown()