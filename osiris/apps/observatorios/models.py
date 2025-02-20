from django.db import models
from apps.elasticsearch_utils.models import ElasticCampo, ImagenCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
# Create your models here.



class ObservatorioModelo(AuditoriaModelo):
    nombre =  ElasticCampo(str)
    descripcion =  ElasticCampo(str)
    imagen =  ImagenCampo(str)

    

    
