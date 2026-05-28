from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
class FactorModelo(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    calificacion = ElasticCampo(str)
    activo = ElasticCampo(bool)
    caracteristicas = ElasticCampo(list)

    indice = "atlas_factores"
