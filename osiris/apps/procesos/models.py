from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo
class ProcesoModelo(AuditoriaModelo):
    nombre = ElasticCampo(str)
    descripcion = ElasticCampo(str)
    dependencia_responsable = ElasticCampo(str)
    objetivo = ElasticCampo(str)
    factores = ElasticCampo(list)
    fecha_inicio = ElasticCampo(str)
    fecha_fin = ElasticCampo(str)
    activo = ElasticCampo(bool)
    fecha_creacion = ElasticCampo(str)
    fecha_modificacion = ElasticCampo(str)

    indice = "atlas_procesos"
