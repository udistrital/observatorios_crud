from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
from osiris.settings import ELASTICSEARCH_MAIN_INDEX


class AspectoModelo(AuditoriaModelo):
    caracteristica_id = ElasticCampo(str)
    nombre = ElasticCampo(str)
    activo = ElasticCampo(bool)
    estructuras_evidencias = ElasticCampo(list)

    indice = ELASTICSEARCH_MAIN_INDEX + "_aspectos"
