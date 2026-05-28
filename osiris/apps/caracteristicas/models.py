from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
class CaracteristicaModelo(AuditoriaModelo):
    factor_id = ElasticCampo(str)
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    calificacion = ElasticCampo(str)
    activo = ElasticCampo(bool)
    aspectos = ElasticCampo(list)

    indice = "atlas_caracteristicas"
