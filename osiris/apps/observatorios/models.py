from django.db import models
from apps.elasticsearch_utils.models import ElasticCampo, ImagenCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
# Create your models here.
from osiris.settings import ELASTICSEARCH_MAIN_INDEX


class ObservatorioModelo(AuditoriaModelo):
    nombre =  ElasticCampo(str)
    descripcion =  ElasticCampo(str)
    imagen =  ImagenCampo(str, guardar_en="observatorios_imagenes")
    indice =  ELASTICSEARCH_MAIN_INDEX + "_observatorios"

    
