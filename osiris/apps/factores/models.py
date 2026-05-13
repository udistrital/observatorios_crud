from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
from osiris.settings import ELASTICSEARCH_MAIN_INDEX


class FactorModelo(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    calificacion = ElasticCampo(str)
    activo = ElasticCampo(bool)
    caracteristicas = ElasticCampo(list)

    indice = ELASTICSEARCH_MAIN_INDEX + "_factores"
