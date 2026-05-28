from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
class AspectoModelo(AuditoriaModelo):
    caracteristica_id = ElasticCampo(str)
    nombre = ElasticCampo(str)
    activo = ElasticCampo(bool)
    estructuras_evidencias = ElasticCampo(list)

    indice = "atlas_aspectos"
