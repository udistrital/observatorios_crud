from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo


class AspectoModelo(AuditoriaModelo):
    caracteristica_id = ElasticCampo(str)
    nombre = ElasticCampo(str)
    estructuras_evidencias = ElasticCampo(list)
    activo = ElasticCampo(bool)
    fecha_creacion = ElasticCampo(str)
    fecha_modificacion = ElasticCampo(str)

    indice = "atlas_aspectos"
