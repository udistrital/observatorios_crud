from django.utils import timezone

from apps.elasticsearch_utils.models import ElasticCampo
from apps.elasticsearch_utils.models import AuditoriaModelo


class EstructuraCamposDocumentoModelo(AuditoriaModelo):
    aspecto_id = ElasticCampo(str)
    tipo_evidencia = ElasticCampo(str)
    nombre = ElasticCampo(str)
    campos = ElasticCampo(list)
    data = ElasticCampo(list)
    activo = ElasticCampo(bool)
    fecha_creacion = ElasticCampo(str)
    fecha_modificacion = ElasticCampo(str)


class EstructuraCamposModelo:
    @staticmethod
    def fecha_actual():
        return timezone.now().isoformat()

    @staticmethod
    def preparar_para_guardar(estructura, estructura_id, actualizar_fecha_modificacion=True):
        fecha_actual = EstructuraCamposModelo.fecha_actual()

        estructura_preparada = {
            **estructura,
            "id": estructura_id,
            "activo": estructura.get("activo", True),
            "fecha_creacion": estructura.get("fecha_creacion") or fecha_actual,
            "fecha_modificacion": estructura.get("fecha_modificacion") or fecha_actual,
        }

        if actualizar_fecha_modificacion:
            estructura_preparada["fecha_modificacion"] = fecha_actual

        return estructura_preparada

    @staticmethod
    def obtener(cliente, estructura_id):
        respuesta = cliente.get(
            index=estructura_id,
            id=estructura_id
        )

        return respuesta["_source"]

    @staticmethod
    def guardar(cliente, estructura_id, estructura, actualizar_fecha_modificacion=True):
        estructura_preparada = EstructuraCamposModelo.preparar_para_guardar(
            estructura,
            estructura_id,
            actualizar_fecha_modificacion
        )

        cliente.index(
            index=estructura_id,
            id=estructura_id,
            document=estructura_preparada,
            refresh=True
        )

        return estructura_preparada

    @staticmethod
    def actualizar(cliente, estructura_id, datos):
        estructura = EstructuraCamposModelo.obtener(
            cliente,
            estructura_id
        )

        estructura_actualizada = {
            **estructura,
            **datos,
            "id": estructura_id,
        }

        return EstructuraCamposModelo.guardar(
            cliente,
            estructura_id,
            estructura_actualizada
        )

    @staticmethod
    def existe(cliente, estructura_id):
        return cliente.indices.exists(index=estructura_id)
