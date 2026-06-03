from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
class FactorModelo(AuditoriaModelo):
    proceso_id = ElasticCampo(str)
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    calificacion = ElasticCampo(float)
    caracteristicas = ElasticCampo(list)
    activo = ElasticCampo(bool)
    fecha_creacion = ElasticCampo(str)
    fecha_modificacion = ElasticCampo(str)

    indice = "atlas_factores"
