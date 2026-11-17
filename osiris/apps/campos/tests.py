import io
import json
import subprocess
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import urllib3
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.estructuras.serializers import CampoEstructuraSerializer

from .documentos import (
    DocumentoNoAsociado,
    ReferenciaDocumentoInvalida,
    cifrar_referencia_documento,
    descifrar_referencia_documento,
    validar_asociacion_documento,
)
from .utils import (
    LONGITUD_MAXIMA_ENLACE,
    TIPOS_CAMPOS_PERMITIDOS,
    aplicar_migraciones_data,
    construir_valores_registro,
    convertir_valor_por_tipo,
    normalizar_campos_con_ids,
    obtener_mapping_tipo_campo,
    obtener_tipos_campos,
)
from .views import (
    ErrorConsultaGestor,
    ErrorVistaPrevia,
    FIRMA_OLE,
    almacenar_respuesta_gestor,
    obtener_documento_gestor,
)


CLAVE_REFERENCIA_PRUEBA = Fernet.generate_key().decode("ascii")


class ConfiguracionDocumentalTests(SimpleTestCase):
    def test_constantes_operativas_globales_conservan_valor_y_tipo(self):
        esperadas = {
            "GESTOR_DOCUMENTAL_ALLOW_HTTP": False,
            "GESTOR_DOCUMENTAL_CONNECT_TIMEOUT_SECONDS": 5,
            "GESTOR_DOCUMENTAL_READ_TIMEOUT_SECONDS": 30,
            "GESTOR_DOCUMENTAL_TOTAL_TIMEOUT_SECONDS": 90,
            "DOCUMENT_PROXY_MAX_BYTES": 157286400,
            "DOCUMENT_PROXY_SPOOL_MAX_BYTES": 1048576,
            "DOCUMENT_PROXY_MAX_CONCURRENT": 2,
            "DOCUMENT_PROXY_RATE": "30/min",
            "DOCUMENT_REFERENCE_TTL_SECONDS": 604800,
        }

        for nombre, esperado in esperadas.items():
            with self.subTest(nombre=nombre):
                valor = getattr(settings, nombre)
                self.assertEqual(valor, esperado)
                self.assertIs(type(valor), type(esperado))


@override_settings(
    DOCUMENT_REFERENCE_KEY=CLAVE_REFERENCIA_PRUEBA,
    DOCUMENT_REFERENCE_TTL_SECONDS=604800,
    DOCUMENT_PROXY_MAX_BYTES=2 * 1024 * 1024,
    DOCUMENT_PROXY_SPOOL_MAX_BYTES=1024,
    GESTOR_DOCUMENTAL="https://gestor.example/api",
    GESTOR_DOCUMENTAL_ALLOW_HTTP=False,
)
class ReferenciaDocumentoTests(APITestCase):
    PROCESO_ID = "proceso-1"
    FACTOR_ID = "factor-1"
    CARACTERISTICA_ID = "caracteristica-1"
    ASPECTO_ID = "aspecto-1"
    ESTRUCTURA_ID = (
        "atlas_estructura_documental_"
        "11111111-1111-4111-8111-111111111111"
    )
    DOCUMENTO_ID = "689fb690-34de-458e-ba16-cee3ec4b5be7"
    CAMPO_HASH_ID = "campo_hash"

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token-prueba")
        self.url_referencia = reverse(
            "referencia-documento",
            kwargs={"version": "v1"},
        )

    def contexto(self, **cambios):
        contexto = {
            "proceso_id": self.PROCESO_ID,
            "factor_id": self.FACTOR_ID,
            "estructura_id": self.ESTRUCTURA_ID,
            "documento_id": self.DOCUMENTO_ID,
        }
        contexto.update(cambios)
        return contexto

    def crear_cliente_elasticsearch(
        self,
        documento_id=None,
        data=None,
        estructura_cambios=None,
        fuentes_cambios=None,
    ):
        documento_id = documento_id or self.DOCUMENTO_ID

        if data is None:
            data = [
                {
                    "valores": {
                        self.CAMPO_HASH_ID: documento_id,
                    },
                    "activo": True,
                }
            ]

        fuentes = {
            (self.ESTRUCTURA_ID, self.ESTRUCTURA_ID): {
                "id": self.ESTRUCTURA_ID,
                "tipo_evidencia": "Documental",
                "aspecto_id": self.ASPECTO_ID,
                "activo": True,
                "campos": [
                    {
                        "campo_id": self.CAMPO_HASH_ID,
                        "nombre_campo": "hash",
                        "tipo_campo": "text",
                        "activo": True,
                    }
                ],
                "data": data,
            },
            ("atlas_aspectos", self.ASPECTO_ID): {
                "id": self.ASPECTO_ID,
                "caracteristica_id": self.CARACTERISTICA_ID,
                "activo": True,
            },
            ("atlas_caracteristicas", self.CARACTERISTICA_ID): {
                "id": self.CARACTERISTICA_ID,
                "factor_id": self.FACTOR_ID,
                "activo": True,
            },
            ("atlas_factores", self.FACTOR_ID): {
                "id": self.FACTOR_ID,
                "proceso_id": self.PROCESO_ID,
                "activo": True,
            },
            ("atlas_procesos", self.PROCESO_ID): {
                "id": self.PROCESO_ID,
                "activo": True,
            },
        }
        fuentes[(self.ESTRUCTURA_ID, self.ESTRUCTURA_ID)].update(
            estructura_cambios or {}
        )

        for clave, cambios in (fuentes_cambios or {}).items():
            fuentes[clave].update(cambios)

        cliente = Mock()

        def obtener(index, id):
            fuente = fuentes.get((index, id))

            if fuente is None:
                raise DocumentoNoAsociado

            return {"_source": fuente}

        cliente.get.side_effect = obtener
        return cliente

    def test_cifra_descifra_y_rechaza_referencia_manipulada(self):
        referencia = cifrar_referencia_documento(self.contexto())

        self.assertTrue(referencia.startswith("v1_"))
        self.assertNotIn(self.DOCUMENTO_ID, referencia)
        self.assertEqual(
            descifrar_referencia_documento(referencia),
            self.contexto(),
        )

        posicion = len(referencia) // 2
        alterado = (
            referencia[:posicion]
            + ("A" if referencia[posicion] != "A" else "B")
            + referencia[posicion + 1:]
        )

        with self.assertRaises(ReferenciaDocumentoInvalida):
            descifrar_referencia_documento(alterado)

    def test_referencia_sigue_vigente_hasta_siete_dias(self):
        instante_emision = 1_000_000

        with patch(
            "cryptography.fernet.time.time",
            return_value=instante_emision,
        ):
            referencia = cifrar_referencia_documento(self.contexto())

        for edad in (15 * 60, 60 * 60, 7 * 24 * 60 * 60):
            with self.subTest(edad=edad):
                with patch(
                    "cryptography.fernet.time.time",
                    return_value=instante_emision + edad,
                ):
                    self.assertEqual(
                        descifrar_referencia_documento(referencia),
                        self.contexto(),
                    )

    def test_rechaza_referencia_despues_de_siete_dias(self):
        instante_emision = 1_000_000

        with patch(
            "cryptography.fernet.time.time",
            return_value=instante_emision,
        ):
            referencia = cifrar_referencia_documento(self.contexto())

        with patch(
            "cryptography.fernet.time.time",
            return_value=instante_emision + (7 * 24 * 60 * 60) + 1,
        ):
            with self.assertRaises(ReferenciaDocumentoInvalida):
                descifrar_referencia_documento(referencia)

    @override_settings(DOCUMENT_REFERENCE_KEY="clave-invalida")
    def test_rechaza_configuracion_sin_clave_fernet(self):
        with self.assertRaises(RuntimeError):
            cifrar_referencia_documento(self.contexto())

    def test_valida_cadena_elasticsearch_y_documento_exacto(self):
        cliente = self.crear_cliente_elasticsearch()

        self.assertEqual(
            validar_asociacion_documento(cliente, **self.contexto()),
            self.contexto(),
        )

        with self.assertRaises(DocumentoNoAsociado):
            validar_asociacion_documento(
                cliente,
                **self.contexto(factor_id="factor-ajeno"),
            )

    def test_rechaza_asociacion_ambigua_o_inactiva(self):
        duplicados = [
            {
                "valores": {self.CAMPO_HASH_ID: self.DOCUMENTO_ID},
                "activo": True,
            },
            {
                "valores": {self.CAMPO_HASH_ID: self.DOCUMENTO_ID},
                "activo": True,
            },
        ]

        for cliente in (
            self.crear_cliente_elasticsearch(data=duplicados),
            self.crear_cliente_elasticsearch(
                data=[
                    {
                        "valores": {
                            self.CAMPO_HASH_ID: self.DOCUMENTO_ID,
                        },
                        "activo": False,
                    }
                ]
            ),
        ):
            with self.subTest(cliente=cliente):
                with self.assertRaises(DocumentoNoAsociado):
                    validar_asociacion_documento(
                        cliente,
                        **self.contexto(),
                    )

    def test_rechaza_estructura_sin_unico_campo_hash_activo(self):
        campo_hash = {
            "campo_id": self.CAMPO_HASH_ID,
            "nombre_campo": "hash",
            "tipo_campo": "text",
            "activo": True,
        }

        for campos in ([], [campo_hash, {**campo_hash, "campo_id": "otro"}]):
            with self.subTest(campos=campos):
                cliente = self.crear_cliente_elasticsearch(
                    estructura_cambios={"campos": campos}
                )

                with self.assertRaises(DocumentoNoAsociado):
                    validar_asociacion_documento(
                        cliente,
                        **self.contexto(),
                    )

    def test_admite_registro_plano_legado_activo(self):
        cliente = self.crear_cliente_elasticsearch(
            data=[{"hash": self.DOCUMENTO_ID, "activo": True}]
        )

        self.assertEqual(
            validar_asociacion_documento(cliente, **self.contexto()),
            self.contexto(),
        )

    @patch("apps.campos.views.get_elasticsearch_client")
    def test_genera_referencia_solo_para_documento_asociado(self, get_cliente):
        get_cliente.return_value = self.crear_cliente_elasticsearch()

        response = self.client.post(
            self.url_referencia,
            self.contexto(),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        referencia = response.json()["referencia"]
        self.assertNotIn(self.DOCUMENTO_ID, referencia)

        response_ajeno = self.client.post(
            self.url_referencia,
            self.contexto(
                documento_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
            ),
            format="json",
        )

        self.assertEqual(response_ajeno.status_code, status.HTTP_404_NOT_FOUND)

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_rechaza_segmentos_de_ruta_sin_consultar_dependencias(
        self,
        get_cliente,
        obtener_gestor,
    ):
        response = self.client.post(
            self.url_referencia,
            self.contexto(documento_id=".."),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        get_cliente.assert_not_called()
        obtener_gestor.assert_not_called()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_revalida_y_transmite_documento_del_gestor(
        self,
        get_cliente,
        obtener_gestor,
    ):
        get_cliente.return_value = self.crear_cliente_elasticsearch()
        contenido = {
            "file:content": {
                "name": "archivo.pdf",
                "mime-type": "application/pdf",
            },
            "file": "JVBERi0=",
        }
        respuesta_gestor = Mock()
        respuesta_gestor.headers = {"Content-Type": "application/json"}
        respuesta_gestor.stream.return_value = [
            json.dumps(contenido).encode("utf-8")
        ]
        obtener_gestor.return_value = respuesta_gestor
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)
        cuerpo = b"".join(response.streaming_content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(json.loads(cuerpo), contenido)
        obtener_gestor.assert_called_once_with(
            self.DOCUMENTO_ID,
            "Bearer token-prueba",
        )
        respuesta_gestor.release_conn.assert_called_once()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_no_invoca_gestor_con_referencia_manipulada(
        self,
        get_cliente,
        obtener_gestor,
    ):
        referencia = cifrar_referencia_documento(self.contexto())
        referencia = referencia[:-1] + (
            "A" if referencia[-1] != "A" else "B"
        )
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        get_cliente.assert_not_called()
        obtener_gestor.assert_not_called()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_no_invoca_gestor_si_documento_fue_eliminado(
        self,
        get_cliente,
        obtener_gestor,
    ):
        get_cliente.return_value = self.crear_cliente_elasticsearch(data=[])
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        obtener_gestor.assert_not_called()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_no_invoca_gestor_si_estructura_esta_inactiva(
        self,
        get_cliente,
        obtener_gestor,
    ):
        get_cliente.return_value = self.crear_cliente_elasticsearch(
            estructura_cambios={"activo": False}
        )
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        obtener_gestor.assert_not_called()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_no_invoca_gestor_para_asociaciones_invalidas(
        self,
        get_cliente,
        obtener_gestor,
    ):
        campo_hash = {
            "campo_id": self.CAMPO_HASH_ID,
            "nombre_campo": "hash",
            "tipo_campo": "text",
            "activo": True,
        }
        casos = (
            self.crear_cliente_elasticsearch(
                data=[
                    {
                        "valores": {
                            self.CAMPO_HASH_ID: self.DOCUMENTO_ID,
                        },
                        "activo": True,
                    },
                    {
                        "valores": {
                            self.CAMPO_HASH_ID: self.DOCUMENTO_ID,
                        },
                        "activo": True,
                    },
                ]
            ),
            self.crear_cliente_elasticsearch(
                estructura_cambios={
                    "campos": [
                        campo_hash,
                        {**campo_hash, "campo_id": "otro_hash"},
                    ]
                }
            ),
            self.crear_cliente_elasticsearch(
                data=[
                    {
                        "valores": {
                            self.CAMPO_HASH_ID: self.DOCUMENTO_ID,
                        },
                        "activo": False,
                    }
                ]
            ),
            self.crear_cliente_elasticsearch(
                fuentes_cambios={
                    ("atlas_factores", self.FACTOR_ID): {
                        "proceso_id": "proceso-ajeno",
                    }
                }
            ),
        )
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        for cliente in casos:
            with self.subTest(cliente=cliente):
                get_cliente.return_value = cliente
                obtener_gestor.reset_mock()

                response = self.client.get(url)

                self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                obtener_gestor.assert_not_called()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_no_invoca_gestor_con_referencia_vencida(
        self,
        get_cliente,
        obtener_gestor,
    ):
        instante_emision = 1_000_000

        with patch(
            "cryptography.fernet.time.time",
            return_value=instante_emision,
        ):
            referencia = cifrar_referencia_documento(self.contexto())

        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        with patch(
            "cryptography.fernet.time.time",
            return_value=instante_emision + (7 * 24 * 60 * 60) + 1,
        ):
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        get_cliente.assert_not_called()
        obtener_gestor.assert_not_called()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_exige_bearer_sin_consultar_dependencias(
        self,
        get_cliente,
        obtener_gestor,
    ):
        self.client.credentials()
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        get_cliente.assert_not_called()
        obtener_gestor.assert_not_called()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_rechaza_bearer_malformado_sin_consultar_dependencias(
        self,
        get_cliente,
        obtener_gestor,
    ):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token otro")
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        get_cliente.assert_not_called()
        obtener_gestor.assert_not_called()

    @override_settings(GESTOR_DOCUMENTAL="http://gestor.example/api")
    @patch("apps.campos.views.urllib3.PoolManager")
    def test_no_envia_bearer_por_http(self, pool_manager):
        with self.assertRaises(ErrorConsultaGestor) as contexto:
            obtener_documento_gestor(
                self.DOCUMENTO_ID,
                "Bearer token-prueba",
            )

        self.assertEqual(
            contexto.exception.codigo_estado,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
        pool_manager.assert_not_called()

    @override_settings(
        DEBUG=False,
        GESTOR_DOCUMENTAL="http://gestor.example/api",
        GESTOR_DOCUMENTAL_ALLOW_HTTP=True,
    )
    @patch("apps.campos.views.urllib3.PoolManager")
    def test_no_permite_excepcion_http_fuera_de_debug(self, pool_manager):
        with self.assertRaises(ErrorConsultaGestor):
            obtener_documento_gestor(
                self.DOCUMENTO_ID,
                "Bearer token-prueba",
            )

        pool_manager.assert_not_called()

    @patch("apps.campos.views.urllib3.PoolManager")
    def test_consulta_gestor_con_tls_sin_redirects(self, pool_manager):
        respuesta = Mock(
            status=status.HTTP_200_OK,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        pool_manager.return_value.request.return_value = respuesta

        resultado = obtener_documento_gestor(
            self.DOCUMENTO_ID,
            "Bearer token-prueba",
        )

        self.assertIs(resultado, respuesta)
        _, url = pool_manager.return_value.request.call_args.args
        opciones = pool_manager.return_value.request.call_args.kwargs
        self.assertEqual(
            url,
            f"https://gestor.example/api/document/{self.DOCUMENTO_ID}",
        )
        self.assertEqual(
            opciones["headers"]["Authorization"],
            "Bearer token-prueba",
        )
        self.assertFalse(opciones["redirect"])
        self.assertFalse(opciones["retries"])
        self.assertFalse(opciones["preload_content"])

    @patch("apps.campos.views.urllib3.PoolManager")
    def test_mapea_respuestas_de_error_del_gestor(self, pool_manager):
        casos = {
            status.HTTP_401_UNAUTHORIZED: status.HTTP_403_FORBIDDEN,
            status.HTTP_403_FORBIDDEN: status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND: status.HTTP_404_NOT_FOUND,
            status.HTTP_500_INTERNAL_SERVER_ERROR: status.HTTP_502_BAD_GATEWAY,
        }

        for origen, esperado in casos.items():
            with self.subTest(origen=origen):
                respuesta = Mock(status=origen, headers={})
                pool_manager.return_value.request.return_value = respuesta

                with self.assertRaises(ErrorConsultaGestor) as contexto:
                    obtener_documento_gestor(
                        self.DOCUMENTO_ID,
                        "Bearer token-prueba",
                    )

                self.assertEqual(contexto.exception.codigo_estado, esperado)
                respuesta.release_conn.assert_called_once()

    @patch("apps.campos.views.urllib3.PoolManager")
    def test_rechaza_tipo_o_longitud_invalida_del_gestor(self, pool_manager):
        casos = (
            {"Content-Type": "text/html"},
            {
                "Content-Type": "application/json",
                "Content-Length": str(settings.DOCUMENT_PROXY_MAX_BYTES + 1),
            },
            {
                "Content-Type": "application/json",
                "Content-Length": "invalida",
            },
        )

        for headers in casos:
            with self.subTest(headers=headers):
                respuesta = Mock(status=status.HTTP_200_OK, headers=headers)
                pool_manager.return_value.request.return_value = respuesta

                with self.assertRaises(ErrorConsultaGestor):
                    obtener_documento_gestor(
                        self.DOCUMENTO_ID,
                        "Bearer token-prueba",
                    )

                respuesta.release_conn.assert_called_once()

    @override_settings(
        DOCUMENT_PROXY_MAX_BYTES=3,
        DOCUMENT_PROXY_SPOOL_MAX_BYTES=1,
    )
    def test_limita_respuesta_sin_content_length(self):
        respuesta = Mock()
        respuesta.stream.return_value = [b"1234"]

        with self.assertRaises(ErrorConsultaGestor) as contexto:
            almacenar_respuesta_gestor(respuesta)

        self.assertEqual(
            contexto.exception.codigo_estado,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )
        respuesta.release_conn.assert_called_once()

    def test_mapea_timeout_durante_lectura_del_gestor(self):
        respuesta = Mock()
        respuesta.stream.side_effect = urllib3.exceptions.ReadTimeoutError(
            None,
            "/document",
            "timeout",
        )

        with self.assertRaises(ErrorConsultaGestor) as contexto:
            almacenar_respuesta_gestor(respuesta)

        self.assertEqual(
            contexto.exception.codigo_estado,
            status.HTTP_504_GATEWAY_TIMEOUT,
        )
        respuesta.release_conn.assert_called_once()

    @patch("apps.campos.views.time.monotonic", side_effect=[0, 91])
    def test_aplica_timeout_total_a_respuesta_lenta(self, _monotonic):
        respuesta = Mock()
        respuesta.stream.return_value = [b"{}"]

        with self.assertRaises(ErrorConsultaGestor) as contexto:
            almacenar_respuesta_gestor(respuesta)

        self.assertEqual(
            contexto.exception.codigo_estado,
            status.HTTP_504_GATEWAY_TIMEOUT,
        )
        respuesta.close.assert_called_once()
        respuesta.release_conn.assert_called_once()

    @patch("apps.campos.views.threading.Timer")
    def test_cancela_lectura_al_agotar_plazo_total(self, timer_clase):
        temporizador = Mock()
        timer_clase.return_value = temporizador
        respuesta = Mock()
        respuesta.stream.side_effect = urllib3.exceptions.ProtocolError(
            "lectura cancelada"
        )

        def agotar_plazo():
            timer_clase.call_args.args[1]()

        temporizador.start.side_effect = agotar_plazo

        with self.assertRaises(ErrorConsultaGestor) as contexto:
            almacenar_respuesta_gestor(respuesta)

        self.assertEqual(
            contexto.exception.codigo_estado,
            status.HTTP_504_GATEWAY_TIMEOUT,
        )
        self.assertEqual(
            timer_clase.call_args.args[0],
            settings.GESTOR_DOCUMENTAL_TOTAL_TIMEOUT_SECONDS,
        )
        respuesta.shutdown.assert_called_once()
        respuesta.close.assert_called_once()
        respuesta.release_conn.assert_called_once()

    @patch("apps.campos.views.threading.Timer")
    def test_cierra_respuesta_si_shutdown_no_esta_disponible(self, timer_clase):
        temporizador = Mock()
        timer_clase.return_value = temporizador
        respuesta = Mock()
        respuesta.shutdown.side_effect = AttributeError("sin shutdown")
        respuesta.stream.side_effect = urllib3.exceptions.ProtocolError(
            "lectura cancelada"
        )

        def agotar_plazo():
            timer_clase.call_args.args[1]()

        temporizador.start.side_effect = agotar_plazo

        with self.assertRaises(ErrorConsultaGestor) as contexto:
            almacenar_respuesta_gestor(respuesta)

        self.assertEqual(
            contexto.exception.codigo_estado,
            status.HTTP_504_GATEWAY_TIMEOUT,
        )
        respuesta.shutdown.assert_called_once()
        self.assertEqual(respuesta.close.call_count, 2)
        respuesta.release_conn.assert_called_once()

    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_propaga_timeout_del_gestor(
        self,
        get_cliente,
        obtener_gestor,
    ):
        get_cliente.return_value = self.crear_cliente_elasticsearch()
        obtener_gestor.side_effect = ErrorConsultaGestor(
            "El Gestor Documental excedió el tiempo de respuesta.",
            status.HTTP_504_GATEWAY_TIMEOUT,
        )
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)

    @patch("apps.campos.views.SEMAFORO_PROXY_DOCUMENTAL")
    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_rechaza_proxy_ocupado_sin_consultar_gestor(
        self,
        get_cliente,
        obtener_gestor,
        semaforo,
    ):
        get_cliente.return_value = self.crear_cliente_elasticsearch()
        semaforo.acquire.return_value = False
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        obtener_gestor.assert_not_called()
        semaforo.release.assert_not_called()

    @patch("apps.campos.views.SEMAFORO_PROXY_DOCUMENTAL")
    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_conserva_cupo_hasta_cerrar_respuesta(
        self,
        get_cliente,
        obtener_gestor,
        semaforo,
    ):
        get_cliente.return_value = self.crear_cliente_elasticsearch()
        semaforo.acquire.return_value = True
        respuesta_gestor = Mock(
            headers={"Content-Type": "application/json"}
        )
        respuesta_gestor.stream.return_value = [b"{}"]
        obtener_gestor.return_value = respuesta_gestor
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        semaforo.release.assert_not_called()
        self.assertEqual(b"".join(response.streaming_content), b"{}")
        semaforo.release.assert_called_once()
        response.close()
        response.close()
        semaforo.release.assert_called_once()

    @patch("apps.campos.views.SEMAFORO_PROXY_DOCUMENTAL")
    @patch("apps.campos.views.obtener_documento_gestor")
    @patch("apps.campos.views.get_elasticsearch_client")
    def test_libera_cupo_si_cliente_cierra_antes_de_consumir(
        self,
        get_cliente,
        obtener_gestor,
        semaforo,
    ):
        get_cliente.return_value = self.crear_cliente_elasticsearch()
        semaforo.acquire.return_value = True
        respuesta_gestor = Mock(
            headers={"Content-Type": "application/json"}
        )
        respuesta_gestor.stream.return_value = [b"{}"]
        obtener_gestor.return_value = respuesta_gestor
        referencia = cifrar_referencia_documento(self.contexto())
        url = reverse(
            "contenido-documento",
            kwargs={"version": "v1", "referencia": referencia},
        )

        response = self.client.get(url)
        response.close()

        semaforo.release.assert_called_once()


class TipoCampoEnlaceTests(SimpleTestCase):
    def test_expone_enlace_en_catalogo_y_validadores(self):
        self.assertIn("link", TIPOS_CAMPOS_PERMITIDOS)
        self.assertIn(
            {"label": "Enlace", "value": "link"},
            obtener_tipos_campos(),
        )

        serializer = CampoEstructuraSerializer(
            data={"nombre_campo": "Sitio web", "tipo_campo": "link"}
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_mapea_enlace_como_keyword(self):
        self.assertEqual(
            obtener_mapping_tipo_campo("link"),
            {"type": "keyword"},
        )

    def test_convierte_enlaces_http_y_https(self):
        for enlace in (
            "http://example.org",
            "http://intranet",
            "http://[::1]",
            "https://münich.example",
            "https://example.org/ruta?consulta=1#seccion",
        ):
            with self.subTest(enlace=enlace):
                self.assertEqual(
                    convertir_valor_por_tipo(f"  {enlace}  ", "link"),
                    enlace,
                )

        self.assertIsNone(convertir_valor_por_tipo("", "link"))
        self.assertIsNone(convertir_valor_por_tipo("   ", "link"))

    def test_rechaza_enlaces_invalidos_o_no_permitidos(self):
        for enlace in (
            "example.org",
            "javascript:alert(1)",
            "data:text/html,contenido",
            "ftp://example.org/archivo",
            "https://",
            "https://example.org/ruta con espacios",
            "https://example.org\\@otro.example",
            "https://example.org:99999",
            "http:example.org",
            "http:///example.org",
            "http://example.org:0",
            "http://exa%mple.org",
            "http://%65xample.org",
            "http://256.256.256.256",
            "http://[v1.test]",
        ):
            with self.subTest(enlace=enlace):
                with self.assertRaisesRegex(
                    ValueError,
                    "esquema http:// o https://",
                ):
                    convertir_valor_por_tipo(enlace, "link")

    def test_rechaza_enlace_demasiado_largo(self):
        enlace = "https://example.org/" + (
            "a" * LONGITUD_MAXIMA_ENLACE
        )

        with self.assertRaisesRegex(ValueError, "2048 caracteres"):
            convertir_valor_por_tipo(enlace, "link")

    def test_asocia_error_de_enlace_con_nombre_de_campo(self):
        campos = [
            {
                "campo_id": "campo_enlace",
                "nombre_campo": "Sitio web",
                "tipo_campo": "link",
                "activo": True,
            }
        ]

        with self.assertRaises(ValueError) as contexto:
            construir_valores_registro(
                campos,
                {"Sitio web": "javascript:alert(1)"},
            )

        self.assertEqual(
            contexto.exception.args[0],
            {
                "Sitio web": (
                    "Debe ser una URL válida con esquema http:// o https://."
                )
            },
        )

    @patch("apps.campos.utils.generar_campo_id", return_value="campo_nuevo")
    def test_migra_enlace_desde_registro_plano_legado(self, _generar_id):
        campos, migraciones = normalizar_campos_con_ids(
            [
                {
                    "campo_id": "campo_anterior",
                    "nombre_campo": "Sitio web",
                    "tipo_campo": "link",
                    "migrar_data": True,
                }
            ],
            [
                {
                    "campo_id": "campo_anterior",
                    "nombre_campo": "Sitio web",
                    "tipo_campo": "text",
                }
            ],
        )

        resultado = aplicar_migraciones_data(
            [
                {
                    "Sitio web": "https://example.org/legado",
                    "activo": True,
                }
            ],
            migraciones,
            campos,
        )

        self.assertEqual(
            resultado[0]["valores"]["campo_nuevo"],
            "https://example.org/legado",
        )
        self.assertNotIn("Sitio web", resultado[0])

        resultado_reservado = aplicar_migraciones_data(
            [{"activo": False}],
            [
                {
                    "campo_anterior_id": "campo_anterior",
                    "campo_anterior_nombre": "activo",
                    "campo_nuevo_id": "campo_nuevo",
                    "tipo_nuevo": "link",
                    "migrar_data": True,
                }
            ],
            campos,
        )

        self.assertFalse(resultado_reservado[0]["activo"])
        self.assertIsNone(
            resultado_reservado[0]["valores"]["campo_nuevo"]
        )


@override_settings(
    DOCUMENT_PREVIEW_MAX_BYTES=2 * 1024 * 1024,
    DOCUMENT_PREVIEW_MAX_PDF_BYTES=2 * 1024 * 1024,
    DOCUMENT_PREVIEW_TIMEOUT_SECONDS=5,
    LIBREOFFICE_EXECUTABLE="/usr/bin/libreoffice",
)
class VistaPreviaDocumentoTests(APITestCase):
    MIME_POR_EXTENSION = {
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    def setUp(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer token-prueba")
        self.url = reverse(
            "vista-previa-documento",
            kwargs={"version": "v1"},
        )

    def crear_ooxml(self, extension):
        contenido = io.BytesIO()
        parte_principal = (
            "word/document.xml"
            if extension == ".docx"
            else "xl/workbook.xml"
        )
        content_type = (
            "application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document.main+xml"
            if extension == ".docx"
            else "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet.main+xml"
        )

        with zipfile.ZipFile(contenido, "w", zipfile.ZIP_DEFLATED) as paquete:
            paquete.writestr(
                "[Content_Types].xml",
                '<Types xmlns="http://schemas.openxmlformats.org/package/'
                '2006/content-types"><Override PartName="/'
                f'{parte_principal}" ContentType="{content_type}" /></Types>',
            )
            paquete.writestr(parte_principal, "<contenido />")

        return contenido.getvalue()

    def crear_archivo(self, extension, contenido=None, mime=None):
        if contenido is None:
            contenido = (
                self.crear_ooxml(extension)
                if extension in {".docx", ".xlsx"}
                else FIRMA_OLE + b"contenido-office"
            )

        return SimpleUploadedFile(
            f"documento{extension}",
            contenido,
            content_type=mime or self.MIME_POR_EXTENSION.get(extension),
        )

    @patch("apps.campos.views.convertir_documento_office_pdf")
    def test_genera_pdf_inline_para_formatos_ooxml(self, convertir):
        convertir.return_value = b"%PDF-1.4\ncontenido"

        for extension in (".docx", ".xlsx"):
            with self.subTest(extension=extension):
                response = self.client.post(
                    self.url,
                    {"archivo": self.crear_archivo(extension)},
                    format="multipart",
                )

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response["Content-Type"], "application/pdf")
                self.assertEqual(
                    response["Content-Disposition"],
                    'inline; filename="vista-previa.pdf"',
                )
                self.assertEqual(response.content, b"%PDF-1.4\ncontenido")

    def test_rechaza_solicitud_sin_archivo(self):
        response = self.client.post(self.url, {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rechaza_solicitud_sin_token(self):
        self.client.credentials()

        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".docx")},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response["WWW-Authenticate"], "Bearer")

    def test_rechaza_extension_no_permitida(self):
        response = self.client.post(
            self.url,
            {
                "archivo": SimpleUploadedFile(
                    "archivo.exe",
                    b"contenido",
                    content_type="application/octet-stream",
                )
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_rechaza_mime_incompatible(self):
        response = self.client.post(
            self.url,
            {
                "archivo": self.crear_archivo(
                    ".docx",
                    mime="application/javascript",
                )
            },
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    def test_rechaza_contenido_incompatible(self):
        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".xlsx", contenido=b"no-es-zip")},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        )

    @override_settings(DOCUMENT_PREVIEW_MAX_BYTES=10)
    def test_rechaza_archivo_que_supera_limite(self):
        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".doc", contenido=FIRMA_OLE + b"123")},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
        )

    @patch("apps.campos.views.convertir_documento_office_pdf")
    def test_controla_error_del_conversor(self, convertir):
        convertir.side_effect = ErrorVistaPrevia(
            "No fue posible generar la vista previa del documento.",
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

        response = self.client.post(
            self.url,
            {"archivo": self.crear_archivo(".docx")},
            format="multipart",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_422_UNPROCESSABLE_ENTITY,
        )
        self.assertEqual(response.json()["status"], "error")

    def test_libreoffice_convierte_los_cuatro_formatos_a_pdf(self):
        ejecutable = Path(settings.LIBREOFFICE_EXECUTABLE)

        if not ejecutable.is_file():
            self.skipTest("LibreOffice no esta instalado en este entorno")

        with tempfile.TemporaryDirectory(prefix="preview-fixtures-") as temporal:
            raiz = Path(temporal)

            for extension in self.MIME_POR_EXTENSION:
                with self.subTest(extension=extension):
                    directorio = raiz / extension.lstrip(".")
                    perfil = directorio / "perfil"
                    directorio.mkdir()
                    perfil.mkdir()

                    if extension in {".doc", ".docx"}:
                        fuente = directorio / "documento.fodt"
                        fuente.write_text(
                            '<?xml version="1.0" encoding="UTF-8"?>'
                            '<office:document xmlns:office="urn:oasis:names:tc:'
                            'opendocument:xmlns:office:1.0" '
                            'xmlns:text="urn:oasis:names:tc:opendocument:'
                            'xmlns:text:1.0" office:mimetype="application/'
                            'vnd.oasis.opendocument.text" office:version="1.3">'
                            "<office:body><office:text><text:p>Vista previa Word "
                            "con contenido verificable.</text:p></office:text>"
                            "</office:body></office:document>",
                            encoding="utf-8",
                        )
                    else:
                        fuente = directorio / "documento.csv"
                        fuente.write_text(
                            "columna,valor\nVista previa Excel,42\n",
                            encoding="utf-8",
                        )

                    resultado = subprocess.run(
                        [
                            str(ejecutable),
                            "--headless",
                            "--nologo",
                            "--nodefault",
                            "--nolockcheck",
                            "--nofirststartwizard",
                            f"-env:UserInstallation={perfil.resolve().as_uri()}",
                            "--convert-to",
                            extension.lstrip("."),
                            "--outdir",
                            str(directorio),
                            str(fuente),
                        ],
                        check=True,
                        capture_output=True,
                        timeout=20,
                    )

                    office = directorio / f"documento{extension}"
                    self.assertTrue(
                        office.is_file(),
                        msg=(
                            f"stdout={resultado.stdout!r}, stderr={resultado.stderr!r}, "
                            f"archivos={[ruta.name for ruta in directorio.iterdir()]}"
                        ),
                    )

                    response = self.client.post(
                        self.url,
                        {
                            "archivo": self.crear_archivo(
                                extension,
                                contenido=office.read_bytes(),
                            )
                        },
                        format="multipart",
                    )

                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                    self.assertEqual(response["Content-Type"], "application/pdf")
                    self.assertTrue(response.content.startswith(b"%PDF-"))
                    self.assertIn(b"%%EOF", response.content[-1024:])
