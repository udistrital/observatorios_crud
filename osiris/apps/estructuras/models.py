from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo


class EstructuraEvidenciaModelo(AuditoriaModelo):
    aspecto_id = ElasticCampo(str)
    tipo_evidencia = ElasticCampo(str)
    nombre = ElasticCampo(str)
    campos = ElasticCampo(list)
    data = ElasticCampo(list)
    activo = ElasticCampo(bool)
    fecha_creacion = ElasticCampo(str)
    fecha_modificacion = ElasticCampo(str)

    indice = "atlas_estructura"
