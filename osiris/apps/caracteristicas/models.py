from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo

class CaracteristicaModelo(AuditoriaModelo):
    factor_id = ElasticCampo(str)
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    calificacion = ElasticCampo(float)
    aspectos = ElasticCampo(list)
    activo = ElasticCampo(bool)
    fecha_creacion = ElasticCampo(str)
    fecha_modificacion = ElasticCampo(str)

    indice = "atlas_caracteristicas"
